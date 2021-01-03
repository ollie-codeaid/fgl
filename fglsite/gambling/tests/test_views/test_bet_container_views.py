# -*- coding: utf-8 -*-
import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from fglsite.bets.models import Gameweek, Season
from fglsite.gambling.models import BetContainer


def _create_test_season():
    commissioner = User.objects.create_user(username="comm", password="comm")
    return Season.objects.create(
        name="test", commissioner=commissioner, weekly_allowance=100.0
    )


def _create_test_season_with_gameweek():
    season = _create_test_season()
    return Gameweek.objects.create(
        season=season,
        number=1,
        deadline_date=datetime.date(2017, 11, 1),
        deadline_time=datetime.time(13, 00),
        spiel="not empty",
    )


class BetContainerViewsTest(TestCase):
    def setUp(self):
        self.gameweek = _create_test_season_with_gameweek()
        self.user = User.objects.create_user(username="player_one", password="pass")

    def test_bet_container_created_if_none_exists(self):
        self.client.force_login(self.user)
        url = reverse("manage-bet-container", kwargs={"gameweek_id": self.gameweek.id})
        self.client.get(url)

        assert BetContainer.objects.all().count() == 1
        bet_container = BetContainer.objects.get()

        assert bet_container.gameweek == self.gameweek
        assert bet_container.owner == self.user

    def test_bet_container_not_created_if_already_exists(self):
        self.client.force_login(self.user)
        url = reverse("manage-bet-container", kwargs={"gameweek_id": self.gameweek.id})

        BetContainer.objects.create(gameweek=self.gameweek, owner=self.user)
        self.client.get(url)

        assert BetContainer.objects.all().count() == 1

    def test_user_can_view_own_bet_container(self):
        self.client.force_login(self.user)

        bet_container = BetContainer.objects.create(
            gameweek=self.gameweek, owner=self.user
        )
        url = reverse("update-bet-container", kwargs={"pk": bet_container.id})

        response = self.client.get(url)

        assert response.status_code == 200
        assert response.context["object"] == bet_container

    def test_user_cannot_view_other_users_bet_container(self):
        self.client.force_login(self.user)

        other_user = User.objects.create_user(username="player_two", password="pass")
        bet_container = BetContainer.objects.create(
            gameweek=self.gameweek, owner=other_user
        )
        url = reverse("update-bet-container", kwargs={"pk": bet_container.id})

        response = self.client.get(url)

        assert response.status_code == 403

    def test_anonymous_user_cannot_view_users_bet_container(self):
        bet_container = BetContainer.objects.create(
            gameweek=self.gameweek, owner=self.user
        )
        url = reverse("update-bet-container", kwargs={"pk": bet_container.id})

        response = self.client.get(url)

        assert response.status_code == 403
