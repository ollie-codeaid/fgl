# Generated by Django 2.1.15 on 2020-12-31 10:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bets', '0002_auto_20201107_1532'),
    ]

    operations = [
        migrations.AddField(
            model_name='balance',
            name='special',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=99),
        ),
    ]