# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-12 18:11
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bets', '0012_auto_20170611_1654'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='betcontainer',
            name='gameweek',
        ),
        migrations.RemoveField(
            model_name='betcontainer',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='betgameresult',
            name='bet',
        ),
        migrations.RemoveField(
            model_name='betgameresult',
            name='game',
        ),
        migrations.RemoveField(
            model_name='betslim',
            name='betcontainer',
        ),
        migrations.DeleteModel(
            name='BetContainer',
        ),
        migrations.DeleteModel(
            name='BetGameResult',
        ),
        migrations.DeleteModel(
            name='BetSlim',
        ),
    ]