# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-09-30 14:51
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bets', '0016_auto_20170924_1827'),
    ]

    operations = [
        migrations.CreateModel(
            name='Balance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week', models.DecimalField(decimal_places=2, default=0.0, max_digits=99)),
                ('provisional', models.DecimalField(decimal_places=2, default=0.0, max_digits=99)),
                ('banked', models.DecimalField(decimal_places=2, default=0.0, max_digits=99)),
            ],
        ),
        migrations.CreateModel(
            name='BalanceMap',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gameweek', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bets.Gameweek')),
            ],
        ),
        migrations.AddField(
            model_name='balance',
            name='balancemap',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bets.BalanceMap'),
        ),
        migrations.AddField(
            model_name='balance',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
