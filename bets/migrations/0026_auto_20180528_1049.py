# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-05-28 10:49
from __future__ import unicode_literals

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('bets', '0025_auto_20180525_1526'),
    ]

    operations = [
        migrations.AddField(
            model_name='season',
            name='added',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='season',
            name='public',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='gameweek',
            name='deadline_date',
            field=models.DateField(default=datetime.date(2018, 5, 28)),
        ),
        migrations.AlterField(
            model_name='season',
            name='commissioner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
