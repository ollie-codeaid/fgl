# -*- coding: utf-8 -*-
from django.contrib.auth.models import Group, User
from django.urls import reverse
from django.test import TestCase

from fglsite.bets.models import Season, Gameweek, Game


class ResultViewsTest(TestCase):
    def setUp(self):
        Group.objects.create(name="Commissioners")

        self.user = User.objects.create_user(username="comm", password="comm")
        self.season = Season.objects.create(
            name="test", commissioner=self.user, weekly_allowance=100.0
        )
        self.gameweek = Gameweek.objects.create(season=self.season, number=1, spiel="")
        self.game_one = Game.objects.create(
            gameweek=self.gameweek,
            hometeam="Man City",
            awayteam="Man Utd",
            homenumerator=1,
            homedenominator=2,
            drawnumerator=3,
            drawdenominator=4,
            awaynumerator=5,
            awaydenominator=6,
        )
        self.game_two = Game.objects.create(
            gameweek=self.gameweek,
            hometeam="Arsenal",
            awayteam="Tottenham",
            homenumerator=1,
            homedenominator=2,
            drawnumerator=3,
            drawdenominator=4,
            awaynumerator=5,
            awaydenominator=6,
        )

    def test_commissioner_can_view_results_form(self):
        url = reverse("add-gameweek-results", args=(self.gameweek.pk,))
        self.client.force_login(self.user)
        response = self.client.get(url)

        assert "form" in response.context
        assert response.context["form"].initial == [
            {"game": self.game_one},
            {"game": self.game_two},
        ]

    def test_unauthenticated_user_cannot_view_results_form(self):
        url = reverse("add-gameweek-results", args=(self.gameweek.pk,))
        response = self.client.get(url)

        assert response.status_code == 403

    def test_non_commissioner_user_cannot_view_results_form(self):
        user = User.objects.create_user(username="non_comm", password="non_comm")
        self.client.force_login(user)
        url = reverse("add-gameweek-results", args=(self.gameweek.pk,))
        response = self.client.get(url)

        assert response.status_code == 403

    def _build_test_form_data(self):
        return {
            "form-TOTAL_FORMS": 2,
            "form-INITIAL_FORMS": 2,
            "form-MAX_NUM_FORMS": 2,
            "form-TOTAL_FORM_COUNT": 2,
            "form-0-game": self.game_one.id,
            "form-0-result": "H",
            "form-1-game": self.game_two.id,
            "form-1-result": "A",
        }

    def _assert_test_form_data_persisted(self):
        assert self.game_one.result_set.count() == 1
        assert self.game_one.result_set.get().result == "H"
        assert self.game_two.result_set.count() == 1
        assert self.game_two.result_set.get().result == "A"

    def test_commissioner_can_add_results(self):
        url = reverse("add-gameweek-results", args=(self.gameweek.pk,))
        self.client.force_login(self.user)
        self.client.post(url, data=self._build_test_form_data())

        self._assert_test_form_data_persisted()

    def test_unauthenticated_user_cannot_add_results(self):
        url = reverse("add-gameweek-results", args=(self.gameweek.pk,))
        response = self.client.post(url, data=self._build_test_form_data())

        assert response.status_code == 403
        assert self.game_one.result_set.count() == 0

    def test_non_commissioner_user_cannot_create_gameweek(self):
        user = User.objects.create_user(username="non_comm", password="non_comm")

        url = reverse("add-gameweek-results", args=(self.gameweek.pk,))
        self.client.force_login(user)
        response = self.client.post(url, data=self._build_test_form_data())

        assert response.status_code == 403
        assert self.game_one.result_set.count() == 0
