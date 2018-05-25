# -*- coding: utf-8 -*-
from django.test import TestCase

import datetime

from bets.models import Season, Gameweek, Game
from django.contrib.auth.models import Group
from django.urls import reverse

def _create_test_season():
    season = Season(name='test', 
                    weekly_allowance=100.0)
    season.save()
    return season

class ViewsTest(TestCase):

    def _create_management_data(self, form_count):
        return {
            'form-TOTAL_FORMS': form_count,
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '',
        }

    def _create_game_data(self, game_num, home, away):
        return {
            'form-{0}-hometeam'.format(game_num):home,
            'form-{0}-awayteam'.format(game_num):away,
            'form-{0}-homenumerator'.format(game_num):1,
            'form-{0}-homedenominator'.format(game_num):2,
            'form-{0}-drawnumerator'.format(game_num):3,
            'form-{0}-drawdenominator'.format(game_num):4,
            'form-{0}-awaynumerator'.format(game_num):5,
            'form-{0}-awaydenominator'.format(game_num):6,
        }

    def setUp(self):
        Group.objects.create(name='Commissioners')

    def test_season(self):
        season = _create_test_season()
        url = reverse('season', args=(season.id,))
        response = self.client.get(url)
        self.assertIn('test', response.content )

    def _create_basic_form_data(self):
        gameweek_data = {
                'deadline_date':datetime.date(2017, 12, 1),
                'deadline_time':datetime.time(12, 00),
                'spiel':'empty',
                }
        management_data = self._create_management_data(1)
        game_data = self._create_game_data(0, 'Manchester Utd', 'Chelsea')

        form_data = {}
        form_data.update( gameweek_data )
        form_data.update( management_data )
        form_data.update( game_data)

        return form_data

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

        form_data = self._create_basic_form_data()

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

        form_data = self._create_basic_form_data()

        url = reverse('update-gameweek', args=(gameweek.id,))
        response = self.client.post(url, data = form_data)

        self._assert_base_gameweek_response_correct(response, form_data, season)


