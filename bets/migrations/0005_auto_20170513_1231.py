# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-13 12:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bets', '0004_betpage_gameweek'),
    ]

    operations = [
        migrations.AlterField(
            model_name='betpage',
            name='gameweek',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bets.Gameweek'),
        ),
    ]
