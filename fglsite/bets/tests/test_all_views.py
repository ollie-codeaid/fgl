# -*- coding: utf-8 -*-
from django.test import TestCase

import datetime

from fglsite.bets.models import (
    Season,
    Gameweek,
    Game,
)
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
        for key, value in game_data.items():
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
