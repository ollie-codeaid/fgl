# -*- coding: utf-8 -*-
from decimal import Decimal
from uuid import uuid4

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from fglsite.bets.models import Balance, Game, Gameweek, Season
from fglsite.gambling.models import Accumulator, BetContainer, BetPart


def _build_game(gameweek):
    # User uuids as team names since we don't really care about testing those here
    return Game.objects.create(
        gameweek=gameweek,
        hometeam=str(uuid4()),
        awayteam=str(uuid4()),
        homenumerator=1,
        homedenominator=2,
        drawnumerator=3,
        drawdenominator=4,
        awaynumerator=5,
        awaydenominator=6,
    )


def _build_accumulator(bet_container, stake, betparts):
    accumulator = Accumulator.objects.create(bet_container=bet_container, stake=stake)
    for betpart in betparts:
        BetPart.objects.create(
            accumulator=accumulator, game=betpart["game"], result=betpart["result"]
        )

    return accumulator


def _build_test_form_data(game_id_one, game_id_two):
    return {
        "form-TOTAL_FORMS": 2,
        "form-INITIAL_FORMS": 2,
        "form-MAX_NUM_FORMS": 2,
        "form-TOTAL_FORM_COUNT": 2,
        "form-0-game": game_id_one,
        "form-0-result": "H",
        "form-1-game": game_id_two,
        "form-1-result": "A",
    }


class ResultViewsBalanceTest(TestCase):
    """This is an integration style test to cover balance creation."""

    def setUp(self):
        self.commissioner = User.objects.create_user(username="comm", password="comm")
        self.season = Season.objects.create(
            name="test", commissioner=self.commissioner, weekly_allowance=100.0
        )
        self.gameweek = Gameweek.objects.create(season=self.season, number=1, spiel="")
        self.game_one = _build_game(gameweek=self.gameweek)
        self.game_two = _build_game(gameweek=self.gameweek)

        self.user_one = User.objects.create_user(
            username="user_one", password="password"
        )
        self.user_two = User.objects.create_user(
            username="user_two", password="password"
        )

    def test_user_balances_saved_correctly_week_one(self):
        user_one_bets = BetContainer.objects.create(
            owner=self.user_one, gameweek=self.gameweek
        )
        _build_accumulator(
            user_one_bets, 100.0, [{"game": self.game_one, "result": "H"}]
        )

        user_two_bets = BetContainer.objects.create(
            owner=self.user_two, gameweek=self.gameweek
        )
        _build_accumulator(
            user_two_bets, 50.0, [{"game": self.game_one, "result": "A"}]
        )
        _build_accumulator(
            user_two_bets, 25.0, [{"game": self.game_two, "result": "A"}]
        )
        _build_accumulator(
            user_two_bets,
            25.0,
            [
                {"game": self.game_one, "result": "H"},
                {"game": self.game_two, "result": "A"},
            ],
        )

        url = reverse("add-gameweek-results", args=(self.gameweek.pk,))
        self.client.force_login(self.commissioner)
        self.client.post(
            url,
            data=_build_test_form_data(
                game_id_one=self.game_one.id, game_id_two=self.game_two.id
            ),
        )

        self.assertEqual(
            Balance.objects.filter(gameweek=self.gameweek, user=self.user_one).count(),
            1,
        )
        user_one_balance = Balance.objects.get(
            gameweek=self.gameweek, user=self.user_one
        )
        self.assertEqual(user_one_balance.week, Decimal("50.00"))
        self.assertEqual(user_one_balance.provisional, Decimal("50.00"))
        self.assertEqual(user_one_balance.special, Decimal("0.00"))
        self.assertEqual(user_one_balance.banked, Decimal("0.00"))

        self.assertEqual(
            Balance.objects.filter(gameweek=self.gameweek, user=self.user_two).count(),
            1,
        )
        user_two_balance = Balance.objects.get(
            gameweek=self.gameweek, user=self.user_two
        )
        self.assertEqual(user_two_balance.week, Decimal("14.58"))
        self.assertEqual(user_two_balance.provisional, Decimal("14.58"))
        self.assertEqual(user_two_balance.special, Decimal("0.00"))
        self.assertEqual(user_two_balance.banked, Decimal("0.00"))

    def test_user_balances_saved_correctly_week_two(self):
        Balance.objects.create(
            gameweek=self.gameweek,
            user=self.user_one,
            week=Decimal("50.00"),
            provisional=Decimal("50.00"),
            special=Decimal("0.00"),
            banked=Decimal("0.00"),
        )

        Balance.objects.create(
            gameweek=self.gameweek,
            user=self.user_two,
            week=Decimal("14.58"),
            provisional=Decimal("14.58"),
            special=Decimal("0.00"),
            banked=Decimal("0.00"),
        )

        gameweek_two = Gameweek.objects.create(season=self.season, number=2, spiel="")
        game_three = _build_game(gameweek=gameweek_two)
        game_four = _build_game(gameweek=gameweek_two)

        user_one_bets = BetContainer.objects.create(
            owner=self.user_one, gameweek=gameweek_two
        )
        _build_accumulator(user_one_bets, 20.0, [{"game": game_three, "result": "H"}])
        _build_accumulator(user_one_bets, 20.0, [{"game": game_three, "result": "D"}])
        _build_accumulator(user_one_bets, 20.0, [{"game": game_three, "result": "A"}])
        _build_accumulator(user_one_bets, 40.0, [{"game": game_four, "result": "A"}])

        user_two_bets = BetContainer.objects.create(
            owner=self.user_two, gameweek=gameweek_two
        )
        _build_accumulator(user_two_bets, 50.0, [{"game": game_three, "result": "A"}])
        _build_accumulator(user_two_bets, 25.0, [{"game": game_four, "result": "A"}])
        _build_accumulator(
            user_two_bets,
            25.0,
            [{"game": game_three, "result": "H"}, {"game": game_four, "result": "A"}],
        )

        url = reverse("add-gameweek-results", args=(gameweek_two.pk,))
        self.client.force_login(self.commissioner)
        self.client.post(
            url,
            data=_build_test_form_data(
                game_id_one=game_three.id, game_id_two=game_four.id
            ),
        )

        self.assertEqual(
            Balance.objects.filter(gameweek=gameweek_two, user=self.user_one).count(), 1
        )
        user_one_balance = Balance.objects.get(
            gameweek=gameweek_two, user=self.user_one
        )
        self.assertEqual(user_one_balance.week, Decimal("3.33"))
        self.assertEqual(user_one_balance.provisional, Decimal("53.33"))
        self.assertEqual(user_one_balance.special, Decimal("0.00"))
        self.assertEqual(user_one_balance.banked, Decimal("50.00"))

        self.assertEqual(
            Balance.objects.filter(gameweek=gameweek_two, user=self.user_two).count(), 1
        )
        user_two_balance = Balance.objects.get(
            gameweek=gameweek_two, user=self.user_two
        )
        self.assertEqual(user_two_balance.week, Decimal("14.58"))
        self.assertEqual(user_two_balance.provisional, Decimal("29.16"))
        self.assertEqual(user_two_balance.special, Decimal("0.00"))
        self.assertEqual(user_two_balance.banked, Decimal("14.58"))

    def test_user_gets_negative_allowance_weekly_winnings_if_no_bet_placed(self):
        Balance.objects.create(
            gameweek=self.gameweek,
            user=self.user_one,
            week=Decimal("50.00"),
            provisional=Decimal("50.00"),
            special=Decimal("0.00"),
            banked=Decimal("0.00"),
        )

        gameweek_two = Gameweek.objects.create(season=self.season, number=2, spiel="")
        game_three = _build_game(gameweek=gameweek_two)
        game_four = _build_game(gameweek=gameweek_two)

        url = reverse("add-gameweek-results", args=(gameweek_two.pk,))
        self.client.force_login(self.commissioner)
        self.client.post(
            url,
            data=_build_test_form_data(
                game_id_one=game_three.id, game_id_two=game_four.id
            ),
        )

        self.assertEqual(
            Balance.objects.filter(gameweek=gameweek_two, user=self.user_one).count(), 1
        )
        user_one_balance = Balance.objects.get(
            gameweek=gameweek_two, user=self.user_one
        )
        self.assertEqual(user_one_balance.week, Decimal("-100.00"))
        self.assertEqual(user_one_balance.provisional, Decimal("-50.00"))
        self.assertEqual(user_one_balance.special, Decimal("0.00"))
        self.assertEqual(user_one_balance.banked, Decimal("-50.00"))

    def test_balance_correctly_recalculated_if_results_are_updated(self):
        user_one_bets = BetContainer.objects.create(
            owner=self.user_one, gameweek=self.gameweek
        )
        _build_accumulator(
            user_one_bets, 100.0, [{"game": self.game_one, "result": "A"}]
        )

        Balance.objects.create(
            gameweek=self.gameweek,
            user=self.user_one,
            week=Decimal("50.00"),
            provisional=Decimal("150.00"),
            special=Decimal("100.00"),
            banked=Decimal("100.00"),
        )

        url = reverse("add-gameweek-results", args=(self.gameweek.pk,))
        self.client.force_login(self.commissioner)
        self.client.post(
            url,
            data=_build_test_form_data(
                game_id_one=self.game_one.id, game_id_two=self.game_two.id
            ),
        )

        self.assertEqual(
            Balance.objects.filter(gameweek=self.gameweek, user=self.user_one).count(),
            1,
        )
        user_one_balance = Balance.objects.get(
            gameweek=self.gameweek, user=self.user_one
        )
        self.assertEqual(user_one_balance.week, Decimal("-100.00"))
        self.assertEqual(user_one_balance.provisional, Decimal("0.00"))
        self.assertEqual(user_one_balance.special, Decimal("100.00"))
        self.assertEqual(user_one_balance.banked, Decimal("0.00"))
