# -*- coding: utf-8 -*-
import datetime
from unittest.mock import Mock, patch

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from fglsite.bets.forms import GameweekForm
from fglsite.bets.models import Game, Gameweek, Season

single_game_output = """
[{
"home_team": "Sheffield United",
"away_team": "Manchester City",
"home_numerator": 49,
"home_denominator": 1,
"draw_numerator": 21,
"draw_denominator": 2,
"away_numerator": 1,
"away_denominator": 9,
"start_time": 1604147545
}] 
"""


class GameweekViewsTest(TestCase):
    def setUp(self):
        Group.objects.create(name="Commissioners")

        self.user = User.objects.create_user(username="comm", password="comm")
        self.season = Season.objects.create(
            name="test", commissioner=self.user, weekly_allowance=100.0
        )

    def _create_management_data(self, form_count):
        return {
            "form-TOTAL_FORMS": form_count,
            "form-INITIAL_FORMS": form_count,
            "form-MAX_NUM_FORMS": form_count,
            "form-TOTAL_FORM_COUNT": form_count,
        }

    def _create_game_data(self, game_num, home, away):
        return {
            "form-{0}-hometeam".format(game_num): home,
            "form-{0}-awayteam".format(game_num): away,
            "form-{0}-homenumerator".format(game_num): 1,
            "form-{0}-homedenominator".format(game_num): 2,
            "form-{0}-drawnumerator".format(game_num): 3,
            "form-{0}-drawdenominator".format(game_num): 4,
            "form-{0}-awaynumerator".format(game_num): 5,
            "form-{0}-awaydenominator".format(game_num): 6,
        }

    def _create_basic_gameweek_form_data(self):
        gameweek_data = {
            "deadline_date": datetime.date(2017, 12, 1),
            "deadline_time": datetime.time(12, 00),
            "spiel": "empty",
        }
        gameweek_data.update(self._create_management_data(1))
        gameweek_data.update(self._create_game_data(0, "Manchester Utd", "Chelsea"))

        return gameweek_data

    def _assert_gameweek_persisted(self, data, season):
        assert season.gameweek_set.count() == 1

        gameweek = season.gameweek_set.get()
        assert gameweek.deadline_date == data["deadline_date"]
        assert gameweek.deadline_time == data["deadline_time"]
        assert gameweek.spiel == data["spiel"]
        assert gameweek.game_set.count() == 1

        game = gameweek.game_set.get()
        game_data = self._create_game_data(0, "Manchester Utd", "Chelsea")
        for key, value in game_data.items():
            assert getattr(game, key.replace("form-0-", "")) == value

    @patch("fglsite.odds_reader.reader._read_from_disk", Mock(return_value="[]"))
    def test_commissioner_can_view_create_gameweek_form(self):
        url = reverse("create-gameweek", args=(self.season.pk,))
        self.client.force_login(self.user)
        response = self.client.get(url)

        assert "form" in response.context
        assert type(response.context["form"]) == GameweekForm
        assert "game_formset" in response.context

    def test_unauthenticated_user_cannot_view_create_gameweek_form(self):
        url = reverse("create-gameweek", args=(self.season.pk,))
        response = self.client.get(url)

        assert response.status_code == 403

    def test_non_commissioner_user_cannot_view_create_gameweek_form(self):
        user = User.objects.create_user(username="non_comm", password="non_comm")
        self.client.force_login(user)
        url = reverse("create-gameweek", args=(self.season.pk,))
        response = self.client.get(url)

        assert response.status_code == 403

    @patch(
        "fglsite.odds_reader.reader._read_from_disk",
        Mock(return_value=single_game_output),
    )
    def test_initial_games_taken_from_output_during_create(self):
        url = reverse("create-gameweek", args=(self.season.pk,))
        self.client.force_login(self.user)
        response = self.client.get(url)

        assert "form" in response.context
        assert type(response.context["form"]) == GameweekForm
        assert "game_formset" in response.context
        assert response.context["game_formset"].forms[0].initial == {
            "hometeam": "Sheffield United",
            "awayteam": "Manchester City",
            "homenumerator": 49,
            "homedenominator": 1,
            "drawnumerator": 21,
            "drawdenominator": 2,
            "awaynumerator": 1,
            "awaydenominator": 9,
        }

    @patch("fglsite.odds_reader.reader._read_from_disk", Mock(side_effect=Exception()))
    def test_exception_reading_odds_displays_empty_form(self):
        url = reverse("create-gameweek", args=(self.season.pk,))
        self.client.force_login(self.user)
        response = self.client.get(url)

        assert "form" in response.context
        assert type(response.context["form"]) == GameweekForm
        assert "game_formset" in response.context
        assert response.context["game_formset"].forms[0].initial == {}

    def test_commissioner_can_create_gameweek(self):
        form_data = self._create_basic_gameweek_form_data()

        url = reverse("create-gameweek", args=(self.season.pk,))
        self.client.force_login(self.user)
        self.client.post(url, data=form_data)

        self._assert_gameweek_persisted(form_data, self.season)

    def test_unauthenticated_user_cannot_create_gameweek(self):
        form_data = self._create_basic_gameweek_form_data()

        url = reverse("create-gameweek", args=(self.season.pk,))
        response = self.client.post(url, data=form_data)

        assert response.status_code == 403
        assert self.season.gameweek_set.count() == 0

    def test_non_commissioner_user_cannot_create_gameweek(self):
        form_data = self._create_basic_gameweek_form_data()
        user = User.objects.create_user(username="non_comm", password="non_comm")

        url = reverse("create-gameweek", args=(self.season.pk,))
        self.client.force_login(user)
        response = self.client.post(url, data=form_data)

        assert response.status_code == 403
        assert self.season.gameweek_set.count() == 0

    def _create_gameweek_with_single_game(self):
        gameweek = Gameweek.objects.create(
            season=self.season,
            number=1,
            deadline_date=datetime.date(2017, 11, 1),
            deadline_time=datetime.time(13, 00),
            spiel="not empty",
        )

        Game.objects.create(
            gameweek=gameweek,
            hometeam="Watford",
            awayteam="Reading",
            homenumerator=6,
            homedenominator=5,
            drawnumerator=4,
            drawdenominator=3,
            awaynumerator=2,
            awaydenominator=1,
        )

        return gameweek

    def test_commissioner_can_view_update_gameweek_form(self):
        gameweek = self._create_gameweek_with_single_game()
        url = reverse("update-gameweek", args=(gameweek.pk,))
        self.client.force_login(self.user)
        response = self.client.get(url)

        assert "form" in response.context
        assert type(response.context["form"]) == GameweekForm
        assert "game_formset" in response.context

    def test_unauthenticated_user_cannot_view_update_gameweek_form(self):
        gameweek = self._create_gameweek_with_single_game()
        url = reverse("update-gameweek", args=(gameweek.pk,))
        response = self.client.get(url)

        assert response.status_code == 403

    def test_non_commissioner_user_cannot_view_update_gameweek_form(self):
        user = User.objects.create_user(username="non_comm", password="non_comm")
        self.client.force_login(user)
        gameweek = self._create_gameweek_with_single_game()
        url = reverse("update-gameweek", args=(gameweek.pk,))
        response = self.client.get(url)

        assert response.status_code == 403

    def test_commissioner_can_update_gameweek(self):
        gameweek = self._create_gameweek_with_single_game()
        form_data = self._create_basic_gameweek_form_data()

        url = reverse("update-gameweek", args=(gameweek.id,))
        self.client.force_login(self.user)
        self.client.post(url, data=form_data)

        self._assert_gameweek_persisted(form_data, self.season)

    def test_unauthenticated_user_cannot_update_gameweek(self):
        gameweek = self._create_gameweek_with_single_game()
        form_data = self._create_basic_gameweek_form_data()

        url = reverse("update-gameweek", args=(gameweek.id,))
        response = self.client.post(url, data=form_data)

        assert response.status_code == 403
        gameweek.refresh_from_db()
        assert gameweek.game_set.get().hometeam == "Watford"

    def test_non_commissioner_user_cannot_update_gameweek(self):
        gameweek = self._create_gameweek_with_single_game()
        form_data = self._create_basic_gameweek_form_data()
        user = User.objects.create_user(username="non_comm", password="non_comm")

        url = reverse("update-gameweek", args=(gameweek.id,))
        self.client.force_login(user)
        response = self.client.post(url, data=form_data)

        assert response.status_code == 403
        gameweek.refresh_from_db()
        assert gameweek.game_set.get().hometeam == "Watford"
