# -*- coding: utf-8 -*-
from django.test import TestCase

from django.contrib.auth.models import User
from django.urls import reverse

from fglsite.bets.models import Season


def _create_test_season():
    commissioner = User.objects.create_user(username='comm', password='comm')
    season = Season(name='test',
                    commissioner=commissioner,
                    weekly_allowance=100.0)
    season.save()
    return season


class ViewsTest(TestCase):
    def test_index(self):
        season = _create_test_season()
        player_one = User.objects.create_user(
                username='player_one', password='pass')
        User.objects.create_user(
                username='player_two', password='pass')
        season.players.set([player_one,])
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
