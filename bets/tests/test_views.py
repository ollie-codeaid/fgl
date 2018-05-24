# -*- coding: utf-8 -*-
from django.test import TestCase

from bets.models import Season
from django.contrib.auth.models import Group
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
