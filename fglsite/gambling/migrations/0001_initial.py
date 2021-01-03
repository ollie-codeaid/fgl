# Generated by Django 2.1.15 on 2020-10-29 17:18

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bets', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Accumulator',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stake', models.DecimalField(decimal_places=2, default=0.0, max_digits=99)),
            ],
        ),
        migrations.CreateModel(
            name='BetContainer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gameweek', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bets.Gameweek')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='BetPart',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result', models.CharField(choices=[('H', 'Home'), ('D', 'Draw'), ('A', 'Away')], default='H', max_length=1)),
                ('accumulator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gambling.Accumulator')),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bets.Game')),
            ],
        ),
        migrations.CreateModel(
            name='LongSpecial',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=255)),
                ('numerator', models.IntegerField(default=0)),
                ('denominator', models.IntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='LongSpecialBet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bet_container', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gambling.BetContainer')),
                ('long_special', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gambling.LongSpecial')),
            ],
        ),
        migrations.CreateModel(
            name='LongSpecialContainer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=255)),
                ('allowance', models.DecimalField(decimal_places=2, default=100.0, max_digits=99)),
                ('created_gameweek', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bets.Gameweek')),
            ],
        ),
        migrations.CreateModel(
            name='LongSpecialResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result', models.BooleanField()),
                ('completed_gameweek', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bets.Gameweek')),
                ('long_special', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bets.Game')),
            ],
        ),
        migrations.AddField(
            model_name='longspecial',
            name='container',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gambling.LongSpecialContainer'),
        ),
        migrations.AddField(
            model_name='accumulator',
            name='bet_container',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gambling.BetContainer'),
        ),
    ]
