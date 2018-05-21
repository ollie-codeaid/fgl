# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-05-21 13:59
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bets', '0022_auto_20180114_1530'),
    ]

    operations = [
        migrations.AddField(
            model_name='balance',
            name='gameweek',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bets.Gameweek'),
        ),
        migrations.AlterField(
            model_name='gameweek',
            name='deadline_date',
            field=models.DateField(default=datetime.date(2018, 5, 21)),
        ),
    ]
