# -*- coding: utf-8 -*-
from django.test import TestCase

import datetime

from fglsite.bets.models import (Season, Gameweek,
                         Game, BetContainer, Accumulator,
                         BetPart)
from fglsite.management.models import JoinRequest
from django.contrib.auth.models import Group, User
from django.urls import reverse


def _create_test_season():
    commissioner = User.objects.create_user(username='comm', password='comm')
    season = Season(name='test',
                    commissioner=commissioner,
                    weekly_allowance=100.0)
    season.save()
    return season


def _create_test_season_with_game():
    season = _create_test_season()
    gameweek = Gameweek(
            season=season,
            number=1,
            deadline_date=datetime.date(2017, 11, 1),
            deadline_time=datetime.time(13, 00),
            spiel='not empty')
    gameweek.save()
    game = Game(
            gameweek=gameweek,
            hometeam='Watford',
            awayteam='Reading',
            homenumerator=6, homedenominator=5,
            drawnumerator=4, drawdenominator=3,
            awaynumerator=2, awaydenominator=1)
    game.save()

    return season, gameweek, game


class ViewsTest(TestCase):

    def setUp(self):
        Group.objects.create(name='Commissioners')

    def test_index(self):
        season = _create_test_season()
        player_one = User.objects.create_user(
                username='player_one', password='pass')
        User.objects.create_user(
                username='player_two', password='pass')
        season.players = [player_one, ]
        season.save()

        url = reverse('index')
        self.client.login(username='player_one', password='pass')
        response = self.client.post(url)
        self.client.logout()

        self.assertIn(season, response.context['season_list'])

        self.client.login(username='player_two', password='pass')
        response = self.client.post(url)
        self.client.logout()

        self.assertNotIn(season, response.context['season_list'])

    def test_season(self):
        season = _create_test_season()
        url = reverse('season', args=(season.id,))
        response = self.client.get(url)
        self.assertIn('test', response.content)

    def test_find_season(self):
        player_one = User.objects.create_user(
                username='player_one', password='pass')
        season_one = Season(
                name='test_one',
                weekly_allowance=100.0,
                commissioner=player_one)
        season_one.save()
        season_two = Season(
                name='test_two',
                weekly_allowance=100.0,
                commissioner=player_one)
        season_two.save()

        url = reverse('find-season')
        data = {'name': 'one'}
        response = self.client.get(url, data=data)
        self.assertEquals(1, len(response.context['season_list'].all()))
        self.assertIn(season_one, response.context['season_list'])

        url = reverse('find-season')
        data = {'name': 'two', 'commissioner': player_one.username}
        response = self.client.get(url, data=data)
        self.assertEquals(1, len(response.context['season_list'].all()))
        self.assertIn(season_two, response.context['season_list'])

        url = reverse('find-season')
        data = {'name': '', 'commissioner': player_one.username}
        response = self.client.get(url, data=data)
        self.assertEquals(2, len(response.context['season_list'].all()))
        self.assertIn(season_one, response.context['season_list'])
        self.assertIn(season_two, response.context['season_list'])

    def test_create_season(self):
        player_one = User.objects.create_user(
                username='player_one', password='pass')

        form_data = {
                'name': 'test_season',
                'weekly_allowance': 123.0,
                'public': True,
                }

        url = reverse('create-season')
        self.client.login(username='player_one', password='pass')
        self.client.post(url, data=form_data)
        self.client.logout()

        season_set = Season.objects.filter(name='test_season')
        self.assertEquals(1, len(season_set))
        season = season_set[0]
        self.assertEquals(123.0, season.weekly_allowance)
        self.assertEquals(player_one, season.commissioner)
        self.assertTrue(season.public)
        self.assertIn(player_one, season.players.all())

    def test_join_season(self):
        player_one = User.objects.create_user(
                username='player_one', password='pass')
        season = _create_test_season()

        url = reverse('join-season', args=(season.id,))
        self.client.login(username='player_one', password='pass')
        self.client.post(url)
        self.client.logout()

        self.assertEquals(1, len(season.joinrequest_set.all()))
        self.assertEquals(player_one, season.joinrequest_set.first().player)

    def test_join_season_public(self):
        player_one = User.objects.create_user(
                username='player_one', password='pass')
        comm = User.objects.create_user(username='comm')
        season = Season(name='test',
                        commissioner=comm,
                        weekly_allowance=100.0,
                        public=True)
        season.save()

        url = reverse('join-season', args=(season.id,))
        self.client.login(username='player_one', password='pass')
        self.client.post(url)
        self.client.logout()

        self.assertIn(player_one, season.players.all())

    def test_accept_request(self):
        player_one = User.objects.create_user(
                username='player_one', password='pass')
        season = _create_test_season()
        request = JoinRequest(season=season, player=player_one)
        request.save()

        url = reverse('accept-request', args=(request.id,))
        self.client.login(username='comm', password='comm')
        self.client.post(url)
        self.client.logout()

        self.assertEquals(0, len(season.joinrequest_set.all()))
        self.assertIn(player_one, season.players.all())

    def test_reject_request(self):
        player_one = User.objects.create_user(
                username='player_one', password='pass')
        season = _create_test_season()
        request = JoinRequest(season=season, player=player_one)
        request.save()

        url = reverse('reject-request', args=(request.id,))
        self.client.login(username='comm', password='comm')
        self.client.post(url)
        self.client.logout()

        self.assertEquals(0, len(season.joinrequest_set.all()))
        self.assertNotIn(player_one, season.players.all())

    def _create_management_data(self, form_count):
        return {
                'form-TOTAL_FORMS': form_count,
                'form-INITIAL_FORMS': form_count,
                'form-MAX_NUM_FORMS': form_count,
                'form-TOTAL_FORM_COUNT': form_count,
                }

    def _create_game_data(self, game_num, home, away):
        return {
                'form-{0}-hometeam'.format(game_num): home,
                'form-{0}-awayteam'.format(game_num): away,
                'form-{0}-homenumerator'.format(game_num): 1,
                'form-{0}-homedenominator'.format(game_num): 2,
                'form-{0}-drawnumerator'.format(game_num): 3,
                'form-{0}-drawdenominator'.format(game_num): 4,
                'form-{0}-awaynumerator'.format(game_num): 5,
                'form-{0}-awaydenominator'.format(game_num): 6,
                }

    def _create_basic_gameweek_form_data(self):
        gameweek_data = {
                'deadline_date': datetime.date(2017, 12, 1),
                'deadline_time': datetime.time(12, 00),
                'spiel': 'empty',
                }
        gameweek_data.update(self._create_management_data(1))
        gameweek_data.update(
            self._create_game_data(0, 'Manchester Utd', 'Chelsea'))

        return gameweek_data

    def _assert_base_gameweek_response_correct(self, response, data, season):
        self.assertEquals(1, len(season.gameweek_set.all()))

        gameweek = season.gameweek_set.all()[0]
        self.assertEquals(data['deadline_date'], gameweek.deadline_date)
        self.assertEquals(data['deadline_time'], gameweek.deadline_time)
        self.assertEquals(data['spiel'], gameweek.spiel)
        self.assertEquals(1, len(gameweek.game_set.all()))

        game = gameweek.game_set.all()[0]
        game_data = self._create_game_data(0, 'Manchester Utd', 'Chelsea')
        for key, value in game_data.iteritems():
            self.assertEquals(value, getattr(game, key.replace('form-0-', '')))

    def test_create_gameweek(self):
        season = _create_test_season()

        form_data = self._create_basic_gameweek_form_data()

        url = reverse('create-gameweek', args=(season.id,))
        self.client.login(username='comm', password='comm')
        response = self.client.post(url, data=form_data)
        self.client.logout()

        self._assert_base_gameweek_response_correct(
                response, form_data, season)

    def test_update_gameweek(self):
        season, gameweek, game = _create_test_season_with_game()

        form_data = self._create_basic_gameweek_form_data()

        url = reverse('update-gameweek', args=(gameweek.id,))
        self.client.login(username='comm', password='comm')
        response = self.client.post(url, data=form_data)
        self.client.logout()

        self._assert_base_gameweek_response_correct(
                response, form_data, season)

    def _create_bet_data(self, bet_num, game, result):
        return {
                'form-{0}-game'.format(bet_num): game.id,
                'form-{0}-result'.format(bet_num): result,
                }

    def _create_basic_accumulator_form_data(self, game):
        accumulator_data = {
                'stake': 100.0,
                }
        accumulator_data.update(self._create_management_data(1))
        accumulator_data.update(self._create_bet_data(0, game, 'H'))

        return accumulator_data

    def test_add_bet(self):
        season, gameweek, game = _create_test_season_with_game()
        betcontainer = BetContainer(
                owner=User.objects.create_user(
                    username='user_one',
                    password='test'),
                gameweek=gameweek)
        betcontainer.save()

        form_data = self._create_basic_accumulator_form_data(game)

        self.assertEquals(0, len(betcontainer.accumulator_set.all()))

        url = reverse('add-bet', args=(betcontainer.id,))
        self.client.login(username='user_one', password='test')
        self.client.post(url, data=form_data)
        self.client.logout()

        self.assertEquals(1, len(betcontainer.accumulator_set.all()))
        accumulator = betcontainer.accumulator_set.all()[0]

        self.assertEquals(100., accumulator.stake)
        self.assertEquals(1, len(accumulator.betpart_set.all()))
        betpart = accumulator.betpart_set.all()[0]

        self.assertEquals(game, betpart.game)
        self.assertEquals('H', betpart.result)

    def test_delete_bet(self):
        season, gameweek, game = _create_test_season_with_game()
        betcontainer = BetContainer(
                owner=User.objects.create_user(
                    username='user_one',
                    password='test'),
                gameweek=gameweek)
        betcontainer.save()
        accumulator = Accumulator(bet_container=betcontainer, stake=100.0)
        accumulator.save()
        betpart = BetPart(accumulator=accumulator, game=game, result='H')
        betpart.save()

        self.assertEquals(1, len(betcontainer.accumulator_set.all()))

        url = reverse('delete-bet', args=(betcontainer.id, accumulator.id,))
        self.client.login(username='user_one', password='test')
        self.client.post(url)
        self.client.logout()

        self.assertEquals(0, len(betcontainer.accumulator_set.all()))