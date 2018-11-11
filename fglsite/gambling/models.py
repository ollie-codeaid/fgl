# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

from django.db import models

from django.contrib.auth.models import User
import logging

from fglsite.bets.models import Gameweek, Game

from __builtin__ import True

logger = logging.getLogger(__name__)


# Create your models here.
class BetContainer(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    gameweek = models.ForeignKey(Gameweek, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.gameweek) + ',' + self.owner.username

    def get_balance(self):
        return self.gameweek._get_balance_by_user(user=self.owner)

    def get_allowance(self):
        return self.gameweek._get_allowance_by_user(self.owner)

    def get_allowance_used(self):
        allowance_used = 0.0
        for accumulator in self.accumulator_set.all():
            allowance_used += float(accumulator.stake)
        return allowance_used

    def get_allowance_unused(self):
        return float(self.get_allowance()) - self.get_allowance_used()

    def get_game_count(self):
        game_count = 0
        for accumulator in self.accumulator_set.all():
            game_count += len(accumulator.betpart_set.all())

        return game_count

    def calc_winnings(self):
        winnings = 0.0
        for accumulator in self.accumulator_set.all():
            winnings += accumulator.calc_winnings()

        true_winnings = winnings - float(self.gameweek.season.weekly_allowance)

        return float("{0:.2f}".format(true_winnings))


class Accumulator(models.Model):
    bet_container = models.ForeignKey(BetContainer, on_delete=models.CASCADE)
    stake = models.DecimalField(default=0.0, decimal_places=2, max_digits=99)

    def __str__(self):
        name = str(self.bet_container) + ',' + str(self.stake)
        for betpart in self.betpart_set.all():
            name = name + ',' + str(betpart)

        return name

    def calc_winnings(self):
        ''' Calculate winnings for this accumulator '''
        correct = True
        odds = 1.0
        for betpart in self.betpart_set.all():
            if not betpart.is_correct():
                correct = False
                break
            else:
                game = betpart.game
                result = betpart.result
                num = 1
                denom = 1
                if result == 'H':
                    num = game.homenumerator
                    denom = game.homedenominator
                elif result == 'D':
                    num = game.drawnumerator
                    denom = game.drawdenominator
                elif result == 'A':
                    num = game.awaynumerator
                    denom = game.awaydenominator
                odds = odds * float(num + denom) / float(denom)

        if correct:
            return odds * float(self.stake)
        else:
            return 0.0


class BetPart(models.Model):
    accumulator = models.ForeignKey(Accumulator, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    RESULTS = (('H', 'Home'), ('D', 'Draw'), ('A', 'Away'))
    result = models.CharField(max_length=1, choices=RESULTS, default='H')

    def __str__(self):
        return str(self.game) + ',' + str(self.result)

    def is_correct(self):
        if len(self.game.result_set.all()) != 1:
            return False

        result = next(iter(self.game.result_set.all()))

        if result.result == self.result:
            return True
        else:
            return False


class LongSpecialContainer(models.Model):
    description = models.CharField(max_length=255)
    allowance = models.DecimalField(
            default=100.0, decimal_places=2, max_digits=99)
    created_gameweek = models.ForeignKey(
            Gameweek,
            on_delete=models.CASCADE)

    def __str__(self):
        return self.description

    def has_bets(self):
        return False

    def complete(self):
        return False

    def get_choice_by_user(self, user):
        user_container = BetContainer.objects.filter(
                    gameweek=self.created_gameweek
                ).filter(
                    owner=user
                )

        if not user_container:
            return None

        choice = LongSpecialBet.objects.filter(
                    bet_container=user_container
                ).filter(
                    long_special__container=self
                ).first()

        return choice


class LongSpecial(models.Model):
    container = models.ForeignKey(
            LongSpecialContainer,
            on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    numerator = models.IntegerField(default=0)
    denominator = models.IntegerField(default=1)

    def __str__(self):
        return self.description + ': ' + str(self.numerator) + '/' + str(self.denominator)

    def chosen_by(self):
        users = ''
        for bet in self.longspecialbet_set.all():
            if users:
                users += ', ' + bet.bet_container.owner.username
            else:
                users = bet.bet_container.owner.username

        return users


class LongSpecialResult(models.Model):
    long_special = models.ForeignKey(Game, on_delete=models.CASCADE)
    result = models.BooleanField()
    completed_gameweek = models.ForeignKey(
            Gameweek,
            on_delete=models.CASCADE)

    def __str__(self):
        return str(self.long_special) + " - " + str(self.result)


class LongSpecialBet(models.Model):
    bet_container = models.ForeignKey(BetContainer, on_delete=models.CASCADE)
    long_special = models.ForeignKey(LongSpecial, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.long_special)

    def is_correct(self):
        if len(self.long_special.longspecialresult_set.all()) != 1:
            return False

        result = next(iter(self.long_special.longspecialresult_set.all()))

        return result.result
