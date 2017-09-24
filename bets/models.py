# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

from django.db import models

from django import forms
from django.contrib.auth.models import User
from django.utils.timezone import now

from wagtail.wagtailsnippets.models import register_snippet


# Create your models here.
@register_snippet
class Season(models.Model):
    name = models.CharField(max_length=255)
    weekly_allowance = models.DecimalField(default=100.0, decimal_places=2, max_digits=99)

    def __str__(self):
        return self.name

    def get_next_gameweek_id(self):
        return len(self.gameweek_set.all()) + 1

    def get_latest_winnings(self):
        gameweek = self.get_latest_gameweek()
        return self.calculate_winnings_to_gameweek(gameweek)

    def get_latest_gameweek(self):
        gameweek_latest = None
        for gameweek in self.gameweek_set.all():
            if gameweek_latest:
                if gameweek_latest.deadline < gameweek.deadline:
                    gameweek_latest = gameweek
            else:
                gameweek_latest = gameweek
        return gameweek_latest

    def calculate_winnings_to_gameweek(self, gameweek):
        # needs work, won't calculate banked winnings correctly
        winnings_map = {}
        for gameweekit in self.gameweek_set.all():
            if gameweekit.deadline < gameweek.deadline:
                for k, v in gameweekit.calculate_winnings().items():
                    if k in winnings_map:
                        winnings_map[k]['Banked'] += v
                    else:
                        winnings_map[k] = {}
                        winnings_map[k] = {'Banked':v}
        for k, v in gameweek.calculate_winnings().items():
            if k not in winnings_map:
                winnings_map[k] = {'Banked':0.0}
            winnings_map[k]['Week'] = v
            winnings_map[k]['Provisional'] = v + winnings_map[k]['Banked']
        return winnings_map

@register_snippet
class Gameweek(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    number = models.IntegerField(default=0)
    deadline = models.DateTimeField("bets deadline")

    def __str__(self):
        return str(self.number)

    def has_bets(self):
        if len(self.bet_set.all()) > 0:
            return True
        else:
            return False

    def deadline_passed(self):
        return now() > self.deadline

    def results_complete(self):
        results_count = 0
        for game in self.game_set.all():
            if game.result_set.count > 0:
                results_count += 1
        return results_count == self.game_set.count()

    def user_vote_set(self):
        users_voted = set()
        for bet in self.bet_set.all():
            users_voted.add(bet.owner)
        return users_voted

    def calculate_winnings(self):
        winnings_map = {}
        for betcontainer in self.betcontainer_set.all():
            if betcontainer.owner in winnings_map:
                winnings_map[betcontainer.owner] += betcontainer.calc_winnings()
            else:
                winnings_map[betcontainer.owner] = betcontainer.calc_winnings()
        return winnings_map

    def calculate_season_winnings(self):
        return self.season.calculate_winnings_to_gameweek(self)

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
        aresult = ""
        for result in self.result_set.all():
            aresult = result.result
        return aresult

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
    
    def is_correct(self):
        if len(self.game.result_set.all()) != 1:
            return False
        
        result = next(iter(self.game.result_set.all()))

        if result.result == self.result:
            return True
        else:
            return False
