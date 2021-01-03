# -*- coding: utf-8 -*-
import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from fglsite.bets.models import Game, Gameweek, Season
from fglsite.gambling.models import Accumulator, BetContainer, BetPart


def _create_test_season():
    commissioner = User.objects.create_user(username="comm", password="comm")
    season = Season(name="test", commissioner=commissioner, weekly_allowance=100.0)
    season.save()
    return season


def _create_test_season_with_game():
    season = _create_test_season()
    gameweek = Gameweek(
        season=season,
        number=1,
        deadline_date=datetime.date(2017, 11, 1),
        deadline_time=datetime.time(13, 00),
        spiel="not empty",
    )
    gameweek.save()
    game = Game(
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
    game.save()

    return season, gameweek, game


def _create_management_data(form_count):
    return {
        "form-TOTAL_FORMS": form_count,
        "form-INITIAL_FORMS": form_count,
        "form-MAX_NUM_FORMS": form_count,
        "form-TOTAL_FORM_COUNT": form_count,
    }


def _create_bet_data(bet_num, game_id, result):
    return {
        "form-{0}-game".format(bet_num): game_id,
        "form-{0}-result".format(bet_num): result,
    }


def _create_basic_accumulator_form_data(bet_container_id, game_id, result, stake=100.0):
    accumulator_data = {"stake": stake, "bet_container": bet_container_id}
    accumulator_data.update(_create_management_data(1))
    accumulator_data.update(_create_bet_data(0, game_id, result))

    return accumulator_data


def _assert_accumulator_matches_expectations(accumulator, stake, game, result):
    assert accumulator.stake == stake
    assert accumulator.betpart_set.count() == 1

    betpart = accumulator.betpart_set.get()
    assert betpart.game == game
    assert betpart.result == result


class AccumulatorViewTest(TestCase):
    def setUp(self):
        season, gameweek, game = _create_test_season_with_game()
        self.game = game
        self.gameweek = gameweek
        self.user = User.objects.create_user(username="user_one", password="test")
        self.bet_container = BetContainer.objects.create(
            gameweek=gameweek, owner=self.user
        )

    def test_GET_on_create_displays_form_with_correct_games(self):
        url = reverse("add-bet", kwargs={"bet_container_id": self.bet_container.id})

        self.client.force_login(self.user)
        response = self.client.get(url)

        assert "betpart_formset" in response.context
        betpart_formset = response.context["betpart_formset"]
        assert len(betpart_formset.forms) == 1
        betpart_form = betpart_formset.forms[0]
        assert betpart_form.fields.get("game").valid_value(self.gameweek.id)

    def test_GET_on_create_non_user_forbidden(self):
        url = reverse("add-bet", kwargs={"bet_container_id": self.bet_container.id})

        response = self.client.get(url)

        assert response.status_code == 403

    def test_GET_on_create_non_owner_user_forbidden(self):
        url = reverse("add-bet", kwargs={"bet_container_id": self.bet_container.id})

        user_two = User.objects.create_user(username="user_two", password="test")
        self.client.force_login(user_two)

        response = self.client.get(url)

        assert response.status_code == 403

    def test_POST_on_create_saves_accumulator(self):
        form_data = _create_basic_accumulator_form_data(
            self.bet_container.id, self.game.id, "H"
        )

        url = reverse("add-bet", kwargs={"bet_container_id": self.bet_container.id})
        self.client.force_login(self.user)
        self.client.post(url, data=form_data)

        assert self.bet_container.accumulator_set.count() == 1

        accumulator = self.bet_container.accumulator_set.get()
        _assert_accumulator_matches_expectations(accumulator, 100.0, self.game, "H")

    def test_POST_fails_on_create_if_stake_too_big(self):
        form_data = _create_basic_accumulator_form_data(
            self.bet_container.id, self.game.id, "H", stake=300.0
        )

        url = reverse("add-bet", kwargs={"bet_container_id": self.bet_container.id})
        self.client.force_login(self.user)
        response = self.client.post(url, data=form_data)

        assert (
            response.context["form"].errors["stake"][0]
            == "Stake may not be greater than 100.0"
        )
        assert self.bet_container.accumulator_set.count() == 0

    def test_POST_on_create_non_user_forbidden(self):
        form_data = _create_basic_accumulator_form_data(
            self.bet_container.id, self.game.id, "H"
        )

        url = reverse("add-bet", kwargs={"bet_container_id": self.bet_container.id})
        response = self.client.post(url, data=form_data)

        assert response.status_code == 403
        assert self.bet_container.accumulator_set.count() == 0

    def test_POST_on_create_non_owner_user_forbidden(self):
        form_data = _create_basic_accumulator_form_data(
            self.bet_container.id, self.game.id, "H"
        )

        url = reverse("add-bet", kwargs={"bet_container_id": self.bet_container.id})

        user_two = User.objects.create_user(username="user_two", password="test")
        self.client.force_login(user_two)
        response = self.client.post(url, data=form_data)

        assert response.status_code == 403
        assert self.bet_container.accumulator_set.count() == 0

    def test_GET_on_update_displays_form_with_correct_games(self):
        accumulator = Accumulator.objects.create(
            bet_container=self.bet_container, stake=100.0
        )
        BetPart.objects.create(accumulator=accumulator, game=self.game, result="A")
        url = reverse("update-bet", kwargs={"pk": accumulator.pk})

        self.client.force_login(self.user)
        response = self.client.get(url)

        assert "betpart_formset" in response.context
        betpart_formset = response.context["betpart_formset"]
        assert len(betpart_formset.forms) == 1
        betpart_form = betpart_formset.forms[0]
        assert betpart_form.fields.get("game").valid_value(self.gameweek.id)

    def test_GET_on_update_non_user_forbidden(self):
        accumulator = Accumulator.objects.create(
            bet_container=self.bet_container, stake=100.0
        )

        url = reverse("update-bet", kwargs={"pk": accumulator.pk})

        response = self.client.get(url)

        assert response.status_code == 403

    def test_GET_on_update_non_owner_user_forbidden(self):
        accumulator = Accumulator.objects.create(
            bet_container=self.bet_container, stake=100.0
        )

        url = reverse("update-bet", kwargs={"pk": accumulator.pk})

        user_two = User.objects.create_user(username="user_two", password="test")
        self.client.force_login(user_two)

        response = self.client.get(url)

        assert response.status_code == 403

    def test_POST_on_update_saves_accumulator(self):
        accumulator = Accumulator.objects.create(
            bet_container=self.bet_container, stake=50.0
        )
        BetPart.objects.create(accumulator=accumulator, game=self.game, result="A")

        form_data = _create_basic_accumulator_form_data(
            self.bet_container.id, self.game.id, "H"
        )

        url = reverse("update-bet", kwargs={"pk": accumulator.pk})
        self.client.force_login(self.user)
        self.client.post(url, data=form_data)

        assert self.bet_container.accumulator_set.count() == 1

        accumulator = self.bet_container.accumulator_set.get()
        _assert_accumulator_matches_expectations(accumulator, 100.0, self.game, "H")

    def test_POST_fails_on_update_if_stake_too_big(self):
        accumulator = Accumulator.objects.create(
            bet_container=self.bet_container, stake=50.0
        )
        BetPart.objects.create(accumulator=accumulator, game=self.game, result="A")

        form_data = _create_basic_accumulator_form_data(
            self.bet_container.id, self.game.id, "H", stake=300.0
        )

        url = reverse("update-bet", kwargs={"pk": accumulator.pk})
        self.client.force_login(self.user)
        response = self.client.post(url, data=form_data)

        assert (
            response.context["form"].errors["stake"][0]
            == "Stake may not be greater than 100.0"
        )
        assert self.bet_container.accumulator_set.count() == 1

        accumulator = self.bet_container.accumulator_set.get()
        _assert_accumulator_matches_expectations(accumulator, 50.0, self.game, "A")

    def test_POST_on_update_non_user_forbidden(self):
        accumulator = Accumulator.objects.create(
            bet_container=self.bet_container, stake=50.0
        )
        BetPart.objects.create(accumulator=accumulator, game=self.game, result="A")

        form_data = _create_basic_accumulator_form_data(
            self.bet_container.id, self.game.id, "H"
        )

        url = reverse("update-bet", kwargs={"pk": accumulator.pk})
        response = self.client.post(url, data=form_data)

        assert response.status_code == 403
        assert self.bet_container.accumulator_set.count() == 1

        accumulator = self.bet_container.accumulator_set.get()
        _assert_accumulator_matches_expectations(accumulator, 50.0, self.game, "A")

    def test_POST_on_update_non_owner_user_forbidden(self):
        accumulator = Accumulator.objects.create(
            bet_container=self.bet_container, stake=50.0
        )
        BetPart.objects.create(accumulator=accumulator, game=self.game, result="A")

        form_data = _create_basic_accumulator_form_data(
            self.bet_container.id, self.game.id, "H"
        )

        url = reverse("update-bet", kwargs={"pk": accumulator.pk})

        user_two = User.objects.create_user(username="user_two", password="test")
        self.client.force_login(user_two)
        response = self.client.post(url, data=form_data)

        assert response.status_code == 403
        assert self.bet_container.accumulator_set.count() == 1

        accumulator = self.bet_container.accumulator_set.get()
        _assert_accumulator_matches_expectations(accumulator, 50.0, self.game, "A")

    def test_DELETE_bet(self):
        accumulator = Accumulator.objects.create(
            bet_container=self.bet_container, stake=50.0
        )

        url = reverse(
            "delete-bet",
            args=(accumulator.id,),
        )
        self.client.force_login(self.user)
        self.client.post(url)

        assert self.bet_container.accumulator_set.count() == 0

    def test_DELETE_bet_non_user_forbidden(self):
        accumulator = Accumulator.objects.create(
            bet_container=self.bet_container, stake=50.0
        )

        url = reverse(
            "delete-bet",
            args=(accumulator.id,),
        )
        response = self.client.post(url)

        assert response.status_code == 403
        assert self.bet_container.accumulator_set.count() == 1

    def test_DELETE_bet_non_owner_user_forbidden(self):
        accumulator = Accumulator.objects.create(
            bet_container=self.bet_container, stake=50.0
        )

        url = reverse(
            "delete-bet",
            args=(accumulator.id,),
        )

        user_two = User.objects.create_user(username="user_two", password="test")
        self.client.force_login(user_two)
        response = self.client.post(url)

        assert response.status_code == 403
        assert self.bet_container.accumulator_set.count() == 1
