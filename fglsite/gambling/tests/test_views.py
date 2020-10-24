# -*- coding: utf-8 -*-
from django.test import TestCase

import datetime

from fglsite.bets.models import (
    Season,
    Gameweek,
    Game,
)
from fglsite.gambling.models import (
    BetContainer,
    Accumulator,
    BetPart,
)
from django.contrib.auth.models import User
from django.urls import reverse


def _create_test_season():
    commissioner = User.objects.create_user(username='comm', password='comm')
    season = Season(name='test',
                    commissioner=commissioner,
                    weekly_allowance=100.0)
    season.save()
    return season


def _create_test_season_with_game():
    season = _create_test_season()
    gameweek = Gameweek(
            season=season,
            number=1,
            deadline_date=datetime.date(2017, 11, 1),
            deadline_time=datetime.time(13, 00),
            spiel='not empty')
    gameweek.save()
    game = Game(
            gameweek=gameweek,
            hometeam='Watford',
            awayteam='Reading',
            homenumerator=6, homedenominator=5,
            drawnumerator=4, drawdenominator=3,
            awaynumerator=2, awaydenominator=1)
    game.save()

    return season, gameweek, game


class ViewsTest(TestCase):

    def _create_management_data(self, form_count):
        return {
                'form-TOTAL_FORMS': form_count,
                'form-INITIAL_FORMS': form_count,
                'form-MAX_NUM_FORMS': form_count,
                'form-TOTAL_FORM_COUNT': form_count,
                }

    def _create_bet_data(self, bet_num, game, result):
        return {
                'form-{0}-game'.format(bet_num): game.id,
                'form-{0}-result'.format(bet_num): result,
                }

    def _create_basic_accumulator_form_data(self, game):
        accumulator_data = {
                'stake': 100.0,
                }
        accumulator_data.update(self._create_management_data(1))
        accumulator_data.update(self._create_bet_data(0, game, 'H'))

        return accumulator_data

    def test_add_bet(self):
        season, gameweek, game = _create_test_season_with_game()
        betcontainer = BetContainer(
                owner=User.objects.create_user(
                    username='user_one',
                    password='test'),
                gameweek=gameweek)
        betcontainer.save()

        form_data = self._create_basic_accumulator_form_data(game)

        self.assertEquals(0, len(betcontainer.accumulator_set.all()))

        url = reverse('add-bet', args=(betcontainer.id,))
        self.client.login(username='user_one', password='test')
        self.client.post(url, data=form_data)
        self.client.logout()

        self.assertEquals(1, len(betcontainer.accumulator_set.all()))
        accumulator = betcontainer.accumulator_set.all()[0]

        self.assertEquals(100., accumulator.stake)
        self.assertEquals(1, len(accumulator.betpart_set.all()))
        betpart = accumulator.betpart_set.all()[0]

        self.assertEquals(game, betpart.game)
        self.assertEquals('H', betpart.result)

    def test_delete_bet(self):
        season, gameweek, game = _create_test_season_with_game()
        betcontainer = BetContainer(
                owner=User.objects.create_user(
                    username='user_one',
                    password='test'),
                gameweek=gameweek)
        betcontainer.save()
        accumulator = Accumulator.objects.create(bet_container=betcontainer, stake=100.0)
        betpart = BetPart(accumulator=accumulator, game=game, result='H')
        betpart.save()

        self.assertEquals(1, len(betcontainer.accumulator_set.all()))

        url = reverse('delete-bet', args=(betcontainer.id, accumulator.id,))
        self.client.login(username='user_one', password='test')
        self.client.post(url)
        self.client.logout()

        self.assertEquals(0, len(betcontainer.accumulator_set.all()))
