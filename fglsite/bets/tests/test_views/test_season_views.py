# -*- coding: utf-8 -*-
from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from fglsite.bets.models import Season


class SeasonViewsTest(TestCase):

    def setUp(self):
        Group.objects.create(name='Commissioners')

        self.user = User.objects.create_user(
            username='player_one', password='pass'
        )

        self.season_one = Season.objects.create(
            name='test_one',
            weekly_allowance=100.0,
            commissioner=self.user
        )
        self.season_two = Season.objects.create(
            name='test_two',
            weekly_allowance=100.0,
            commissioner=self.user
        )

    def test_get_season(self):
        url = reverse('season', args=(self.season_one.id,))
        response = self.client.get(url)
        self.assertIn('test_one', str(response.content))

    def test_create_season(self):
        self.client.force_login(self.user)
        self.client.post(
            reverse('create-season'),
            data={
                'name': 'test_season',
                'weekly_allowance': 123.0,
                'public': True,
            }
        )
        season = Season.objects.get(name='test_season')
        assert season.weekly_allowance == 123.0
        assert season.commissioner == self.user
        assert season.public

    def test_create_season_not_possible_for_unauthorized_user(self):
        self.client.post(
            reverse('create-season'),
            data={
                'name': 'test_season',
                'weekly_allowance': 123.0,
                'public': True,
            }
        )

        assert Season.objects.filter(name='test_season').count() == 0

    def test_find_season_by_name(self):
        response = self.client.get(
            f"{reverse('find-season')}?name={self.season_one.name}"
        )
        assert response.context['season_list'].count() == 1
        assert self.season_one in response.context['season_list']

    def test_find_season_by_name_and_commissioner(self):
        response = self.client.get(
            f"{reverse('find-season')}?name={self.season_one.name}&commissioner={self.user.username}"
        )
        assert response.context['season_list'].count() == 1
        assert self.season_one in response.context['season_list']

    def test_find_season_by_commissioner(self):
        response = self.client.get(
            f"{reverse('find-season')}?commissioner={self.user.username}"
        )
        assert response.context['season_list'].count() == 2
        assert self.season_one in response.context['season_list']
        assert self.season_two in response.context['season_list']
