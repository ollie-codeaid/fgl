# -*- coding: utf-8 -*-
from django.test import TestCase

import datetime

from bets.models import Season
from django.contrib.auth.models import Group
from django.urls import reverse

def _create_test_season():
    season = Season(name='test', 
                    weekly_allowance=100.0)
    season.save()
    return season

class ViewsTest(TestCase):

    management_data = {
        'form-TOTAL_FORMS': '1',
        'form-INITIAL_FORMS': '0',
        'form-MAX_NUM_FORMS': '',
    }

    def _create_game_data(self):
        return {
            'form-0-hometeam':'Manchester United',
            'form-0-awayteam':'Chelsea',
            'form-0-homenumerator':1,
            'form-0-homedenominator':2,
            'form-0-drawnumerator':3,
            'form-0-drawdenominator':4,
            'form-0-awaynumerator':5,
            'form-0-awaydenominator':6,
        }

    def setUp(self):
        Group.objects.create(name='Commissioners')

    def test_season(self):
        season = _create_test_season()
        url = reverse('season', args=(season.id,))
        response = self.client.get(url)
        self.assertIn('test', response.content )

    def test_create_gameweek(self):
        season = _create_test_season()
        data = {
                'deadline_date':datetime.date(2017, 12, 1),
                'deadline_time':datetime.time(12, 00),
                'spiel':'empty',
                }
        data.update(self.management_data)
        data.update(self._create_game_data())
        url = reverse('create-gameweek', args=(season.id,))
        response = self.client.post(url, data=data)
        self.assertEquals(200, response.status_code)
        self.assertEquals(1, len(season.gameweek_set.all()))
