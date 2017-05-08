# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Season(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Gameweek(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    number = models.IntegerField(default=0)
    deadline = models.DateTimeField("bets deadline")

    def __str__(self):
        return self.number

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
        return self.hometeam + " vs " + awayteam
