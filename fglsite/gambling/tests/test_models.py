from django.test import TestCase

from fglsite.bets.models import Season, Gameweek, Game, Result
from fglsite.gambling.models import BetContainer, Accumulator, BetPart
from django.contrib.auth.models import User
from datetime import date, time
from uuid import uuid4


def _create_test_season():
    commissioner = User.objects.create_user("comm")
    return Season.objects.create(
        name="test", commissioner=commissioner, weekly_allowance=100.0
    )


def _create_test_gameweek(season):
    return Gameweek.objects.create(
        season=season,
        number=season.get_next_gameweek_id(),
        deadline_date=date(2017, 11, 1),
        deadline_time=time(12, 00),
        spiel="",
    )


def _create_test_game(gameweek):
    return Game.objects.create(
        gameweek=gameweek,
        hometeam=str(uuid4()),
        awayteam=str(uuid4()),
        homenumerator=3,
        homedenominator=1,
        drawnumerator=4,
        drawdenominator=1,
        awaynumerator=5,
        awaydenominator=1,
    )


class GameweekTest(TestCase):
    def test_has_bets(self):
        season = _create_test_season()
        gameweek = _create_test_gameweek(season)

        user_one = User.objects.create_user("user_one")
        user_one.save()

        self.assertFalse(gameweek.has_bets())

        bet_container = BetContainer(owner=user_one, gameweek=gameweek)
        bet_container.save()
        self.assertTrue(gameweek.has_bets())

    def test__get_users_with_ready_bets_as_string(self):
        season = _create_test_season()
        gameweek = _create_test_gameweek(season)

        user_one = User.objects.create_user("user_one")
        user_one.save()
        user_two = User.objects.create_user("user_two")
        user_two.save()

        bet_container = BetContainer(owner=user_one, gameweek=gameweek)
        bet_container.save()
        accumulator = Accumulator(bet_container=bet_container, stake=100.0)
        accumulator.save()

        users_with_ready_bets = gameweek.get_users_with_ready_bets_as_string()

        self.assertIn(user_one.username, users_with_ready_bets)
        self.assertNotIn(user_two.username, users_with_ready_bets)


class AccumulatorTest(TestCase):
    def setUp(self):
        self.season = _create_test_season()
        self.gameweek = _create_test_gameweek(self.season)
        self.game_one = _create_test_game(self.gameweek)
        self.game_two = _create_test_game(self.gameweek)
        self.game_three = _create_test_game(self.gameweek)

    def test_calc_winnings_single_game_correct(self):
        user = User.objects.create_user("user")
        bet_container = BetContainer.objects.create(gameweek=self.gameweek, owner=user)
        accumulator = Accumulator.objects.create(
            bet_container=bet_container, stake=100.0
        )
        BetPart.objects.create(accumulator=accumulator, game=self.game_one, result="H")
        Result.objects.create(game=self.game_one, result="H")

        self.assertEquals(400.0, accumulator.calculate_winnings())

    def test_calc_winnings_single_game_incorrect(self):
        user = User.objects.create_user("user")
        bet_container = BetContainer.objects.create(gameweek=self.gameweek, owner=user)
        accumulator = Accumulator.objects.create(
            bet_container=bet_container, stake=100.0
        )
        BetPart.objects.create(accumulator=accumulator, game=self.game_one, result="H")
        Result.objects.create(game=self.game_one, result="D")

        self.assertEquals(0.0, accumulator.calculate_winnings())

    def test_calc_winnings_single_game_postponed(self):
        user = User.objects.create_user("user")
        bet_container = BetContainer.objects.create(gameweek=self.gameweek, owner=user)
        accumulator = Accumulator.objects.create(
            bet_container=bet_container, stake=100.0
        )
        BetPart.objects.create(accumulator=accumulator, game=self.game_one, result="H")
        Result.objects.create(game=self.game_one, result="P")

        self.assertEquals(100.0, accumulator.calculate_winnings())

    def test_calc_winnings_multiple_game_correct(self):
        user = User.objects.create_user("user")
        bet_container = BetContainer.objects.create(gameweek=self.gameweek, owner=user)
        accumulator = Accumulator.objects.create(
            bet_container=bet_container, stake=100.0
        )
        BetPart.objects.create(accumulator=accumulator, game=self.game_one, result="H")
        BetPart.objects.create(accumulator=accumulator, game=self.game_two, result="D")
        BetPart.objects.create(
            accumulator=accumulator, game=self.game_three, result="A"
        )
        Result.objects.create(game=self.game_one, result="H")
        Result.objects.create(game=self.game_two, result="D")
        Result.objects.create(game=self.game_three, result="A")

        self.assertEquals(12000.0, accumulator.calculate_winnings())

    def test_calc_winnings_multiple_game_incorrect(self):
        user = User.objects.create_user("user")
        bet_container = BetContainer.objects.create(gameweek=self.gameweek, owner=user)
        accumulator = Accumulator.objects.create(
            bet_container=bet_container, stake=100.0
        )
        BetPart.objects.create(accumulator=accumulator, game=self.game_one, result="H")
        BetPart.objects.create(accumulator=accumulator, game=self.game_two, result="D")
        BetPart.objects.create(
            accumulator=accumulator, game=self.game_three, result="A"
        )
        Result.objects.create(game=self.game_one, result="D")
        Result.objects.create(game=self.game_two, result="D")
        Result.objects.create(game=self.game_three, result="A")

        self.assertEquals(0.0, accumulator.calculate_winnings())

    def test_calc_winnings_multiple_game_postponed(self):
        user = User.objects.create_user("user")
        bet_container = BetContainer.objects.create(gameweek=self.gameweek, owner=user)
        accumulator = Accumulator.objects.create(
            bet_container=bet_container, stake=100.0
        )
        BetPart.objects.create(accumulator=accumulator, game=self.game_one, result="H")
        BetPart.objects.create(accumulator=accumulator, game=self.game_two, result="D")
        BetPart.objects.create(
            accumulator=accumulator, game=self.game_three, result="A"
        )
        Result.objects.create(game=self.game_one, result="P")
        Result.objects.create(game=self.game_two, result="D")
        Result.objects.create(game=self.game_three, result="A")

        self.assertEquals(3000.0, accumulator.calculate_winnings())
