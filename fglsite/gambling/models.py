# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

from django.db import models

from django.contrib.auth.models import User
import logging

from fglsite.bets.models import Gameweek, Game

logger = logging.getLogger(__name__)


class BetContainer(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    gameweek = models.ForeignKey(Gameweek, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.gameweek) + "," + self.owner.username

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

    def calculate_winnings(self):
        winnings = 0.0
        for accumulator in self.accumulator_set.all():
            winnings += accumulator.calculate_winnings()

        true_winnings = winnings - float(self.gameweek.season.weekly_allowance)

        return float("{0:.2f}".format(true_winnings))


class Accumulator(models.Model):
    bet_container = models.ForeignKey(BetContainer, on_delete=models.CASCADE)
    stake = models.DecimalField(default=0.0, decimal_places=2, max_digits=99)

    def __str__(self):
        name = str(self.bet_container) + "," + str(self.stake)
        for betpart in self.betpart_set.all():
            name = name + "," + str(betpart)

        return name

    def calculate_winnings(self):
        """ Calculate winnings for this accumulator """
        odds = 1.0
        for betpart in self.betpart_set.all():
            if betpart.is_void():
                continue
            if betpart.is_correct():
                odds = odds * (1 + betpart.get_odds())
            else:
                return 0.0

        return odds * float(self.stake)


class BetPart(models.Model):
    accumulator = models.ForeignKey(Accumulator, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    RESULTS = (("H", "Home"), ("D", "Draw"), ("A", "Away"))
    result = models.CharField(max_length=1, choices=RESULTS, default="H")

    def __str__(self):
        return str(self.game) + "," + str(self.result)

    def is_correct(self):
        if self.game.result_set.count() != 1:
            return False

        result = self.game.result_set.get()
        return result.result == self.result

    def is_void(self):
        return self.game.get_result().result == "P"

    def get_odds(self):
        return self.game.get_numerator(self.result) / self.game.get_denominator(
            self.result
        )


class LongSpecialContainer(models.Model):
    description = models.CharField(max_length=255)
    allowance = models.DecimalField(default=100.0, decimal_places=2, max_digits=99)
    created_gameweek = models.ForeignKey(Gameweek, on_delete=models.CASCADE)

    def __str__(self):
        return self.description

    def has_bets(self):
        return False

    def is_complete(self):
        return all(
            [longspecial.is_correct() for longspecial in self.longspecial_set.all()]
        )


class LongSpecial(models.Model):
    container = models.ForeignKey(LongSpecialContainer, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    numerator = models.IntegerField(default=0)
    denominator = models.IntegerField(default=1)

    def __str__(self):
        return (
            self.description + ": " + str(self.numerator) + "/" + str(self.denominator)
        )

    def chosen_by(self):
        users = ""
        for bet in self.longspecialbet_set.all():
            if users:
                users += ", " + bet.bet_container.owner.username
            else:
                users = bet.bet_container.owner.username

        return users

    def is_correct(self):
        return self.longspecialresult_set.count() == 1


class LongSpecialResult(models.Model):
    long_special = models.ForeignKey(LongSpecial, on_delete=models.CASCADE)
    completed_gameweek = models.ForeignKey(Gameweek, on_delete=models.CASCADE)

    def __str__(self):
        return (
            str(self.long_special.container.description)
            + " - "
            + str(self.long_special)
        )


class LongSpecialBet(models.Model):
    bet_container = models.ForeignKey(BetContainer, on_delete=models.CASCADE)
    long_special = models.ForeignKey(LongSpecial, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.long_special)

    def is_correct(self):
        self.long_special.is_correct()

    def project_winnings(self, long_special):
        if self.long_special == long_special:
            return (long_special.numerator / long_special.denominator) * float(
                long_special.container.allowance
            )
        else:
            return -long_special.container.allowance
