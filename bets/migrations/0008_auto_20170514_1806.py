# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-14 18:06
from __future__ import unicode_literals

import bets.models
from django.db import migrations
import wagtail.wagtailcore.blocks
import wagtail.wagtailcore.fields
import wagtail.wagtailsnippets.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('bets', '0007_remove_betpage_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='betpage',
            name='bets',
            field=wagtail.wagtailcore.fields.StreamField([('bets_list', wagtail.wagtailcore.blocks.ListBlock(wagtail.wagtailcore.blocks.StructBlock([('stake', wagtail.wagtailcore.blocks.DecimalBlock(required=True)), ('gameresults', wagtail.wagtailcore.blocks.ListBlock(wagtail.wagtailcore.blocks.StructBlock([('game', wagtail.wagtailsnippets.blocks.SnippetChooserBlock(bets.models.Game, required=True)), ('result', wagtail.wagtailcore.blocks.ChoiceBlock(choices=[('H', 'Home'), ('D', 'Draw'), ('A', 'Away')]))])))])))]),
        ),
    ]
