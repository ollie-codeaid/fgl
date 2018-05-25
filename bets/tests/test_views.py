# -*- coding: utf-8 -*-
from django.test import TestCase

import datetime

from bets.models import Season, Gameweek, Game, BetContainer
from django.contrib.auth.models import Group, User
from django.urls import reverse

def _create_test_season():
    season = Season(name='test', 
                    weekly_allowance=100.0)
    season.save()
    return season

class ViewsTest(TestCase):

    def setUp(self):
        Group.objects.create(name='Commissioners')

    def test_season(self):
        season = _create_test_season()
        url = reverse('season', args=(season.id,))
        response = self.client.get(url)
        self.assertIn('test', response.content )


    def _create_management_data(self, form_count):
        return {
                'form-TOTAL_FORMS'      : form_count,
                'form-INITIAL_FORMS'    : form_count,
                'form-MAX_NUM_FORMS'    : form_count,
                'form-TOTAL_FORM_COUNT' : form_count,
                }

    def _create_game_data(self, game_num, home, away):
        return {
                'form-{0}-hometeam'.format(game_num)        : home,
                'form-{0}-awayteam'.format(game_num)        : away,
                'form-{0}-homenumerator'.format(game_num)   : 1,
                'form-{0}-homedenominator'.format(game_num) : 2,
                'form-{0}-drawnumerator'.format(game_num)   : 3,
                'form-{0}-drawdenominator'.format(game_num) : 4,
                'form-{0}-awaynumerator'.format(game_num)   : 5,
                'form-{0}-awaydenominator'.format(game_num) : 6,
                }

    def _create_basic_gameweek_form_data(self):
        gameweek_data = {
                'deadline_date':datetime.date(2017, 12, 1),
                'deadline_time':datetime.time(12, 00),
                'spiel':'empty',
                }
        gameweek_data.update( self._create_management_data(1) )
        gameweek_data.update( self._create_game_data(0, 'Manchester Utd', 'Chelsea' ) )

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
        response = self.client.post(url, data=form_data)

        self._assert_base_gameweek_response_correct(response, form_data, season)

    def test_update_gameweek(self):
        season = _create_test_season()
        gameweek = Gameweek(season=season,
                deadline_date=datetime.date(2017, 11, 1),
                deadline_time=datetime.time(13, 00),
                spiel = 'not empty')
        gameweek.save()
        game = Game(gameweek=gameweek,
                hometeam='Watford',
                awayteam='Reading',
                homenumerator=6, homedenominator=5,
                drawnumerator=4, drawdenominator=3,
                awaynumerator=2, awaydenominator=1)
        game.save()

        form_data = self._create_basic_gameweek_form_data()

        url = reverse('update-gameweek', args=(gameweek.id,))
        response = self.client.post(url, data = form_data)

        self._assert_base_gameweek_response_correct(response, form_data, season)


    def _create_bet_data(self, bet_num, game, result):
        return {
                'form-{0}-game'.format(bet_num)     : game.id,
                'form-{0}-result'.format(bet_num)   : result,
                }

    def _create_basic_accumulator_form_data(self, game):
        accumulator_data = {
                'stake' : 100.0,
                }
        accumulator_data.update( self._create_management_data(1) )
        accumulator_data.update( self._create_bet_data( 0, game, 'H' ))

        return accumulator_data


    def test_add_bet(self):
        season = _create_test_season()
        gameweek = Gameweek(season=season,
                number=1,
                deadline_date=datetime.date(2017, 11, 1),
                deadline_time=datetime.time(13, 00),
                spiel = 'not empty')
        gameweek.save()
        game = Game(gameweek=gameweek,
                hometeam='Watford',
                awayteam='Reading',
                homenumerator=6, homedenominator=5,
                drawnumerator=4, drawdenominator=3,
                awaynumerator=2, awaydenominator=1)
        game.save()
        betcontainer = BetContainer(
                owner=User.objects.create_user('user_one'),
                gameweek=gameweek )
        betcontainer.save()

        form_data = self._create_basic_accumulator_form_data(game)

        self.assertEquals(0, len(betcontainer.accumulator_set.all()))

        url = reverse('add-bet', args=(betcontainer.id,))
        response = self.client.post(url, data = form_data)

        self.assertEquals(1, len(betcontainer.accumulator_set.all()))
        accumulator = betcontainer.accumulator_set.all()[0]

        self.assertEquals(100., accumulator.stake)
        self.assertEquals(1, len(accumulator.betpart_set.all()))
        betpart = accumulator.betpart_set.all()[0]

        self.assertEquals(game, betpart.game)
        self.assertEquals('H', betpart.result)
        
        
