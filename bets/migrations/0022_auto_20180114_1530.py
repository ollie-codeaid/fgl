# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-01-14 15:30
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bets', '0021_auto_20171227_1239'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gameweek',
            name='deadline_date',
            field=models.DateField(default=datetime.date(2018, 1, 14)),
        ),
    ]