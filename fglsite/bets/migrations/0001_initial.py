# Generated by Django 2.1.15 on 2020-10-29 17:18

import datetime

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
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
            name='Game',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hometeam', models.CharField(max_length=255)),
                ('awayteam', models.CharField(max_length=255)),
                ('homenumerator', models.IntegerField(default=0)),
                ('homedenominator', models.IntegerField(default=1)),
                ('drawnumerator', models.IntegerField(default=0)),
                ('drawdenominator', models.IntegerField(default=1)),
                ('awaynumerator', models.IntegerField(default=0)),
                ('awaydenominator', models.IntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='Gameweek',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField(default=0)),
                ('deadline_date', models.DateField(default=datetime.date.today)),
                ('deadline_time', models.TimeField(default=datetime.time(12, 0))),
                ('spiel', models.TextField(blank=True, default=None)),
            ],
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result', models.CharField(choices=[('H', 'Home'), ('D', 'Draw'), ('A', 'Away')], default='H', max_length=1)),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bets.Game')),
            ],
        ),
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('weekly_allowance', models.DecimalField(decimal_places=2, default=100.0, max_digits=99)),
                ('public', models.BooleanField(default=False)),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('commissioner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('players', models.ManyToManyField(related_name='seasons', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='gameweek',
            name='season',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bets.Season'),
        ),
        migrations.AddField(
            model_name='game',
            name='gameweek',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bets.Gameweek'),
        ),
        migrations.AddField(
            model_name='balance',
            name='gameweek',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bets.Gameweek'),
        ),
        migrations.AddField(
            model_name='balance',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
