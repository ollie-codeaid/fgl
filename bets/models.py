# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

import datetime

from django.db import models

from django.contrib.auth.models import User
from django.db import transaction

from wagtail.wagtailsnippets.models import register_snippet
from __builtin__ import True

#
# Create your models here.
@register_snippet
class Season(models.Model):
    name = models.CharField(max_length=255)
    weekly_allowance = models.DecimalField(default=100.0, decimal_places=2, max_digits=99)

    def __str__(self):
        return self.name

    def get_next_gameweek_id(self):
        return len(self.gameweek_set.all()) + 1

    def balances_available(self):
        latest_gameweek_number = len(self.gameweek_set.all())
        
        if latest_gameweek_number == 0:
            # No balances if no gameweek
            return False
        elif latest_gameweek_number > 1:
            # Must be balances if gameweek 1 complete
            return True
        else:
            # Check if gameweek 1 complete
            gameweek = self.gameweek_set.filter(number=1)[0]
            return gameweek.results_complete()
        
    def get_latest_complete_gameweek(self):
        gameweek = self.get_latest_gameweek()
        if gameweek.results_complete():
            return gameweek
        else:
            return self.gameweek_set.filter(number=gameweek.number-1)[0]

    def get_latest_winnings(self):
        gameweek = self.get_latest_gameweek()
        return self.calculate_winnings_to_gameweek(gameweek)

    def get_latest_gameweek(self):
        latest_gameweek_number = len(self.gameweek_set.all())

        return self.gameweek_set.filter(number=latest_gameweek_number)[0]

    def get_latest_user_balances(self):
        if self.get_next_gameweek_id() == 1:
            return None

        latest_gameweek = self.get_latest_gameweek()

        if latest_gameweek.results_complete():
            gameweek = latest_gameweek
        else:
            number = latest_gameweek.number
            if number == 1:
                return None
            gameweek = self.gameweek_set.filter(number=number-1)[0]
            
        return gameweek.balancemap_set.all()[0].balance_set.all()

    def can_create_gameweek(self):
        if self.get_next_gameweek_id() > 1:
            if not self.get_latest_gameweek().results_complete():
                return False
        return True

@register_snippet
class Gameweek(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    number = models.IntegerField(default=0)
    deadline_date = models.DateField(default=datetime.date(
        datetime.datetime.now().year,
        datetime.datetime.now().month,
        datetime.datetime.now().day))
    deadline_time = models.TimeField(default=datetime.time(12, 00))
    spiel = models.TextField(default=None, blank=True)

    def __str__(self):
        return str(self.season) + ',' + str(self.number)

    def is_latest(self):
        return self.number == len(self.season.gameweek_set.all())

    def update_no_bet_users(self):
        if self.number > 1:
            users = []
            for betcontainer in self.betcontainer_set.all():
                users.append(betcontainer.owner)

            prev_gameweek = self.season.gameweek_set.filter(number=self.number-1)[0]
            for balance in prev_gameweek.balancemap_set.all()[0].balance_set.all():
                if balance.user not in users:
                    self.set_balance_by_user(balance.user,
                            self.season.weekly_allowance * -1,
                            balance.week - self.season.weekly_allowance)

    def set_balance_by_user(self, user, week_winnings, week_unused):
        if len(self.balancemap_set.all()) == 0:
            balancemap = BalanceMap(gameweek=self)
            balancemap.save()
        else:
            balancemap = self.balancemap_set.all()[0]

        if week_winnings < 0.0:
            enforce_banked = week_winnings
        else:
            enforce_banked = 0

        if len(self.balancemap_set.all()[0].balance_set.filter(user=user)) == 0:

            if len(self.balancemap_set.all()) == 0:
                balancemap = BalanceMap(gameweek=self)
                balancemap.save()

            if self.number==1:
                user_balance = Balance(balancemap=balancemap, 
                        user=user, 
                        week=week_winnings, 
                        provisional=week_winnings,
                        banked=enforce_banked)
            else:
                last_banked = self.get_banked_by_user(user, self.number-1)

                user_balance = Balance(balancemap=balancemap, 
                        user=user, 
                        week=week_winnings,
                        provisional=last_banked + week_winnings,
                        banked=last_banked + week_unused + enforce_banked)

            user_balance.save()
        else:
            old_user_balance = balancemap.balance_set.filter(user=user)[0]

            if self.number==1:
                user_balance = Balance(balancemap=balancemap, 
                        user=user, 
                        week=week_winnings, 
                        provisional=week_winnings,
                        banked=enforce_banked)
            else:
                last_banked = self.get_banked_by_user(user, self.number-1)

                user_balance = Balance(balancemap=balancemap, 
                        user=user, 
                        week=week_winnings,
                        provisional=last_banked + week_winnings,
                        banked=last_banked + week_unused + enforce_banked)
            with transaction.atomic():
                old_user_balance.delete()
                user_balance.save()

    def get_banked_by_user(self, user, number):
        season = self.season
        last_gameweek = season.gameweek_set.filter(number=number)[0]
        user_balance = last_gameweek.get_balance_by_user(user)
        return user_balance.banked

    def get_balance_by_user(self, user):
        if len(self.balancemap_set.all()) == 0:
            return None
        else:
            balancemap = self.balancemap_set.all()[0]

            if len(balancemap.balance_set.filter(user=user)) == 0:
                return None
            else:
                return balancemap.balance_set.filter(user=user)[0]

    def has_bets(self):
        if len(self.betcontainer_set.all()) > 0:
            return True
        else:
            return False

    def deadline_passed(self):
        return ((datetime.datetime.now().date() == self.deadline_date
                and datetime.datetime.now().time() >= self.deadline_time)
                or datetime.datetime.now().date() > self.deadline_date)
    
    def results_complete(self):
        results_count = 0
        for game in self.game_set.all():
            if len(game.result_set.all()) > 0:
                results_count += 1
        return results_count == len(self.game_set.all())

    def get_allowance_by_user(self, user):
        allowance = self.season.weekly_allowance
        rollable_allowances = self.get_rollable_allowances()

        if rollable_allowances and user in rollable_allowances:
            return allowance + self.get_rollable_allowances()[user]
        else:
            return allowance

    def get_rollable_allowances(self):
        if self.number == 1:
            return None
        else:
            prev_gameweek = self.season.gameweek_set.filter(number=self.number-1)[0]
            prev_balances = prev_gameweek.balancemap_set.all()[0]
            rollable_allowances = {}
            for balance in prev_balances.balance_set.all():
                if balance.week > 0.0:
                    rollable_allowances[balance.user] = balance.week
            return rollable_allowances

class BalanceMap(models.Model):
    gameweek = models.ForeignKey(Gameweek, on_delete=models.CASCADE)

class Balance(models.Model):
    balancemap = models.ForeignKey(BalanceMap, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    week = models.DecimalField(default=0.0, decimal_places=2, max_digits=99)
    provisional = models.DecimalField(default=0.0, decimal_places=2, max_digits=99)
    banked = models.DecimalField(default=0.0, decimal_places=2, max_digits=99)

@register_snippet
class Game(models.Model):
    gameweek = models.ForeignKey(Gameweek, on_delete=models.CASCADE)
    hometeam = models.CharField(max_length=255)
    awayteam = models.CharField(max_length=255)
    homenumerator = models.IntegerField(default=0)
    homedenominator = models.IntegerField(default=1)
    drawnumerator = models.IntegerField(default=0)
    drawdenominator = models.IntegerField(default=1)
    awaynumerator = models.IntegerField(default=0)
    awaydenominator = models.IntegerField(default=1)

    def __str__(self):
        return self.hometeam + " vs " + self.awayteam

    def get_numerator(self, result):
        if result == 'H':
            return self.homenumerator
        elif result == 'D':
            return self.drawnumerator
        else:
            return self.awaynumerator

    def get_denominator(self, result):
        if result == 'H':
            return self.homedenominator
        elif result == 'D':
            return self.drawdenominator
        else:
            return self.awaydenominator

    def get_result(self):
        return self.result_set.all()[0]

@register_snippet
class Result(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    RESULTS = (('H', 'Home'), ('D', 'Draw'), ('A', 'Away'))
    result = models.CharField(max_length=1, choices=RESULTS, default='H')

    def __str__(self):
        return str(self.game) + " - " + str(self.result)

@register_snippet
class BetContainer(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    gameweek = models.ForeignKey(Gameweek, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.gameweek) + ',' + self.owner.username

    def get_balance(self):
        return self.gameweek.get_balance_by_user(user=self.owner)

    def get_allowance(self):
        return self.gameweek.get_allowance_by_user(self.owner)

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
            for betpart in accumulator.betpart_set.all():
                game_count += 1

        return game_count

    def calc_winnings(self):
        winnings = 0.0
        for accumulator in self.accumulator_set.all():
            winnings += accumulator.calc_winnings()

        return float("{0:.2f}".format(winnings - float(self.gameweek.season.weekly_allowance)))

@register_snippet
class Accumulator(models.Model):
    bet_container = models.ForeignKey(BetContainer, on_delete=models.CASCADE)
    stake = models.DecimalField(default=0.0, decimal_places=2, max_digits=99)

    def __str__(self):
        name = str(self.bet_container) + ',' + str(self.stake)
        for betpart in self.betpart_set.all():
            name = name + ',' + str(betpart)

        return name

    def calc_winnings(self):
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
                odds = odds * (num + denom) / denom

        if correct:
            return odds * float(self.stake)
        else:
            return 0.0

@register_snippet
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
