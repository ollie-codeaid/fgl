from django.test import TestCase

from fglsite.bets.models import Season, Gameweek, Game, Result
from fglsite.gambling.models import BetContainer, Accumulator, BetPart
from django.contrib.auth.models import User
from datetime import date, time


def _create_test_season():
    commissioner = User.objects.create_user("comm")
    season = Season(name="test", commissioner=commissioner, weekly_allowance=100.0)
    season.save()
    return season


def _create_test_gameweek(season):
    gameweek = Gameweek(
        season=season,
        number=season.get_next_gameweek_id(),
        deadline_date=date(2017, 11, 1),
        deadline_time=time(12, 00),
        spiel="",
    )
    gameweek.save()
    return gameweek


def _create_test_game(gameweek):
    game = Game(
        gameweek=gameweek,
        hometeam="Chelsea",
        awayteam="Liverpool",
        homenumerator=1,
        homedenominator=50,
        drawnumerator=1,
        drawdenominator=20,
        awaynumerator=100,
        awaydenominator=1,
    )
    game.save()
    return game


def _create_test_bet_container(gameweek, user):
    betcontainer = BetContainer(gameweek=gameweek, owner=user)
    betcontainer.save()
    return betcontainer


def _create_test_result(game, result):
    result = Result(game=game, result=result)
    result.save()
    return result


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
    def test_calc_winnings(self):
        season = _create_test_season()
        gameweek = _create_test_gameweek(season)
        game = _create_test_game(gameweek)
        user = User.objects.create_user("user_one")
        bet_container = _create_test_bet_container(gameweek, user)
        accumulator = Accumulator(bet_container=bet_container, stake=100.0)
        accumulator.save()
        bet_part = BetPart(accumulator=accumulator, game=game, result="H")
        bet_part.save()

        result = _create_test_result(game, "H")
        self.assertEquals(102.0, accumulator.calc_winnings())

        result.result = "D"
        result.save()
        self.assertEquals(0.0, accumulator.calc_winnings())

        result.result = "A"
        result.save()
        self.assertEquals(0.0, accumulator.calc_winnings())
