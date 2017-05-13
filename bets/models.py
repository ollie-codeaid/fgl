# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from django import forms

from wagtail.wagtailadmin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.wagtailcore import blocks
from wagtail.wagtailcore.fields import StreamField
from wagtail.wagtailcore.models import Page
from wagtail.wagtailsnippets.blocks import SnippetChooserBlock
from wagtail.wagtailsnippets.models import register_snippet

# Create your models here.
@register_snippet
class Season(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

@register_snippet
class Gameweek(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    number = models.IntegerField(default=0)
    deadline = models.DateTimeField("bets deadline")

    def __str__(self):
        return self.number

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
        return self.hometeam + " vs " + awayteam

@register_snippet
class Result(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    RESULTS = (('H', 'Home'), ('D', 'Draw'), ('A', 'Away'))
    result = models.CharField(max_length=1, choices=RESULTS, default='H')

class BetPage(Page):
    gameweek = models.ForeignKey(Gameweek, null=True, on_delete=models.SET_NULL)
    bets = StreamField([('bets_list', blocks.ListBlock(blocks.StructBlock([
        ('stake', blocks.DecimalBlock(required=True)),
        ('bets', blocks.ListBlock(blocks.StructBlock([
            ('game', SnippetChooserBlock(Game, required=True)),
            ('result', blocks.ChoiceBlock(choices=[
                ('H', 'Home'),
                ('D', 'Draw'),
                ('A', 'Away')
            ]))
        ])))
     ])))])

    content_panels = Page.content_panels + [
        FieldPanel('gameweek'),
        StreamFieldPanel('bets')
    ]
