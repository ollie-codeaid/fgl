# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

from django.db import models

from django import forms
from django.contrib.auth.models import User
from django.utils.timezone import now

from wagtail.wagtailadmin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.wagtailcore import blocks
from wagtail.wagtailcore.fields import StreamField
from wagtail.wagtailsnippets.blocks import SnippetChooserBlock
from wagtail.wagtailsnippets.models import register_snippet


# Create your models here.
@register_snippet
class Season(models.Model):
    name = models.CharField(max_length=255)

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
        for bet in self.bet_set.all():
            if bet.owner in winnings_map:
                winnings_map[bet.owner] += bet.calculate_winnings()
            else:
                winnings_map[bet.owner] = bet.calculate_winnings()
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
class Bet(models.Model):
    owner = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    gameweek = models.ForeignKey(Gameweek, null=True, on_delete=models.SET_NULL)
    bets = StreamField([('bets_list', blocks.ListBlock(blocks.StructBlock([
        ('stake', blocks.DecimalBlock(required=True)),
        ('gameresults', blocks.ListBlock(blocks.StructBlock([
            ('game', SnippetChooserBlock(Game, required=True)),
            ('result', blocks.ChoiceBlock(choices=[
                ('H', 'Home'),
                ('D', 'Draw'),
                ('A', 'Away')
            ]))
        ])))
     ])))])

    panels = [
        FieldPanel('owner'),
        FieldPanel('gameweek'),
        StreamFieldPanel('bets')
    ]

    def __str__(self):
        return str(self.owner) + ", " + str(self.gameweek)

    def get_game_count(self):
        count = 0
        for bets_list in self.bets:
            for bet in bets_list.value:
                for block in bet.items():
                    if block[0] == 'gameresults':
                        count += len(block[1])

        return count

    def calculate_winnings(self):
        winnings = 0.0
        debug = ""
        for bets_list in self.bets:
            for bet_portion in bets_list.value:
               stake = 0
               numerator = 1
               denominator = 1

               for block in bet_portion.items():
                   if block[0] == 'stake':
                       debug += ";stake: " + block[1]
                       stake += int(block[1])
                   elif block[0] == 'gameresults':
                       for gameresult in block[1]:
                           result_actual = "pending"
                           result_predict = ""
                           debug += ";gameresult: "
                           for grblock in gameresult.items():
                               if grblock[0] == 'game':
                                   for result in grblock[1].result_set.all():
                                       result_actual = result.result
                                       gnumerator = grblock[1].get_numerator(result_actual)
                                       gdenominator = grblock[1].get_denominator(result_actual)
                                       debug += "; result_actual: " + result_actual + "; gnumerator: " + str(gnumerator) + "; gdenominator: " + str(gdenominator)
                                       numerator = numerator * (gnumerator + gdenominator)
                                       denominator = denominator * gdenominator
                               if grblock[0] == 'result':
                                   result_predict = grblock[1]
                                   debug += "; result_predict: " + result_predict
                           if result_actual != result_predict:
                               numerator = 0
               winnings += stake * (numerator / denominator)
               debug += "; winnings += " + str(stake) + " * (" + str(numerator) + "/" + str(denominator) + ")"
               debug += " = " + str(stake * (numerator / denominator))
        return float("{0:.2f}".format(winnings - 100))
