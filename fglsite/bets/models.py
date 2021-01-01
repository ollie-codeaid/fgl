# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

import datetime

from django.db import models

from django.contrib.auth.models import User
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


# Create your models here.
class Season(models.Model):
    commissioner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    weekly_allowance = models.DecimalField(
        default=100.0, decimal_places=2, max_digits=99
    )
    added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_next_gameweek_id(self):
        """ Get id for next gameweek """
        return len(self.gameweek_set.all()) + 1

    def _get_gameweek_by_id(self, gameweek_id):
        return self.gameweek_set.filter(number=gameweek_id)[0]

    def balances_available(self):
        """Check if balances are available (e.g. for display
        on season root page)"""
        next_gameweek_number = self.get_next_gameweek_id()

        if next_gameweek_number == 1:
            # No balances if there is no gameweek
            return False
        elif next_gameweek_number > 2:
            # Must be balances if gameweek 1 is complete
            return True
        else:
            # Check if gameweek 1 is complete
            gameweek = self._get_gameweek_by_id(1)
            return gameweek.results_complete()

    def get_latest_complete_gameweek(self):
        """ Get latest gameweek that has a complete set of results """
        gameweek = self.get_latest_gameweek()
        if gameweek.results_complete():
            return gameweek
        else:
            return self._get_gameweek_by_id(gameweek.number - 1)

    def get_latest_gameweek(self):
        """ Get latest gameweek """
        if self.get_next_gameweek_id() == 1:
            return None

        latest_gameweek_number = self.get_next_gameweek_id() - 1

        return self._get_gameweek_by_id(latest_gameweek_number)

    def can_create_gameweek(self):
        """ Check whether new gameweek can be created """
        if self.get_next_gameweek_id() > 1:
            if not self.get_latest_gameweek().results_complete():
                return False
        return True

    def long_specials_outstanding(self):
        long_specials_outstanding = []
        for gameweek in self.gameweek_set.all():
            long_specials_outstanding += gameweek.long_specials_outstanding()

        return long_specials_outstanding


class Gameweek(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    number = models.IntegerField(default=0)
    deadline_date = models.DateField(default=datetime.date.today)
    deadline_time = models.TimeField(default=datetime.time(12, 00))
    spiel = models.TextField(default=None, blank=True)

    def __str__(self):
        return str(self.season) + "," + str(self.number)

    def is_first_gameweek(self):
        return self.number == 1

    def is_latest_gameweek(self):
        return self == self.season.get_latest_gameweek()

    def get_prev_gameweek(self):
        if self.is_first_gameweek():
            raise Exception("Called get_prev_gameweek on first gameweek")
        return self.season._get_gameweek_by_id(self.number - 1)

    def get_next_gameweek(self):
        if self.is_latest_gameweek():
            raise Exception("Called get_next_gameweek on latest gameweek")
        return self.season._get_gameweek_by_id(self.number + 1)

    def update_no_bet_users(self):
        """For users who have no betcontainer for this week, set weekly winnings
        as -100, weekly unused as all available rollable and update balance
        accordingly"""
        if self.number > 1:
            users = self._get_users_with_bets()
            prev_gameweek = self.get_prev_gameweek()
            prev_balance_set = prev_gameweek.balance_set.all()

            for balance in prev_balance_set:
                if balance.user not in users:
                    if balance.week > 0:
                        unused = float(balance.week)
                    else:
                        unused = 0.0
                    self.set_balance_by_user(
                        user=balance.user,
                        week_winnings=float(self.season.weekly_allowance * -1),
                        week_unused=unused,
                    )

    def get_prev_banked(self, user):
        # If Gameweek 1 then last banked must be 0
        if self.number == 1:
            return 0.0
        else:
            prev_gameweek = self.get_prev_gameweek()
            prev_balance = prev_gameweek._get_balance_by_user(user)
            return prev_balance.banked

    def set_balance_by_user(self, user, week_winnings, week_unused):
        with transaction.atomic():
            if self.user_has_balance(user):
                old_user_balance = self.balance_set.get(user=user)
                old_user_balance.delete()

            Balance.objects.create_with_weekly(
                gameweek=self,
                user=user,
                week_winnings=week_winnings,
                week_unused=week_unused,
            )

    def _get_balance_by_user(self, user):
        """ Get user balance """
        if len(self.balance_set.filter(user=user)) == 0:
            return None
        else:
            return self.balance_set.filter(user=user)[0]

    def has_bets(self):
        """ Check if any users have placed bets """
        if len(self.betcontainer_set.all()) > 0:
            return True
        else:
            return False

    def deadline_passed(self):
        """ Check if deadline has passed """
        return (
            datetime.datetime.now().date() == self.deadline_date
            and datetime.datetime.now().time() >= self.deadline_time
        ) or datetime.datetime.now().date() > self.deadline_date

    def results_complete(self):
        """ Check if ALL results have been posted """
        results_count = 0
        game_set = self.game_set.all()
        for game in game_set:
            if len(game.result_set.all()) > 0:
                results_count += 1
        return results_count == len(game_set)

    def _get_allowance_by_user(self, user):
        """ Get allowance + rollable for this user """
        allowance = self.season.weekly_allowance
        rollable_allowances = self.get_rollable_allowances()

        if rollable_allowances and user in rollable_allowances:
            return allowance + rollable_allowances[user]
        else:
            return allowance

    def get_rollable_allowances(self):
        """ Get ALL the rollable allowances """
        if self.number == 1:
            return None
        else:
            prev_gameweek = self.get_prev_gameweek()
            prev_balances = prev_gameweek.balance_set.all()
            rollable_allowances = {}
            for balance in prev_balances:
                if balance.week > 0.0:
                    rollable_allowances[balance.user] = balance.week
            return rollable_allowances

    def _get_user_positions(self):
        user_positions = {}
        position = 0
        for balance in self.balance_set.order_by("-provisional"):
            user_positions.update({balance.user: position})
            position += 1

        return user_positions

    def _get_change_icon(self, positions, prev_positions, user):
        change_icon = "-"
        if user in prev_positions:
            diff = prev_positions[user] - positions[user]
            if diff > 0:
                change_icon = "/\\"
            elif diff < 0:
                change_icon = "\\/"

        return change_icon

    def get_ordered_results(self):
        """ Get full results ordered by provisional descending"""
        results = []

        positions = self._get_user_positions()
        if self.number > 1:
            prev_positions = self.get_prev_gameweek()._get_user_positions()
        else:
            prev_positions = {}

        for balance in self.balance_set.order_by("-provisional"):
            change_icon = self._get_change_icon(positions, prev_positions, balance.user)
            results.append(
                [
                    balance.user,
                    balance.week,
                    balance.provisional,
                    balance.special,
                    balance.banked,
                    change_icon,
                ]
            )

        return results

    def _get_users_with_bets(self):
        users = []
        for betcontainer in self.betcontainer_set.all():
            users.append(betcontainer.owner)
        return users

    def get_users_with_ready_bets_as_string(self):
        """ Print usernames of users who have already placed valid bets """
        users = ""
        for betcontainer in self.betcontainer_set.all():
            total_bet = 0.0
            for accumulator in betcontainer.accumulator_set.all():
                total_bet += float(accumulator.stake)
            if total_bet >= self.season.weekly_allowance:
                users += betcontainer.owner.username + ", "
        return users

    def user_has_balance(self, user):
        """ Check if user has a balance """
        return len(self.balance_set.filter(user=user)) > 0

    def long_specials_outstanding(self):
        return [container for container in self.longspecialcontainer_set.all() if not container.is_complete()]


class BalanceManager(models.Manager):
    def get_existing(self, gameweek, user):
        return Balance.objects.filter(gameweek=gameweek, user=user).first()

    def create_with_weekly(self, gameweek, user, week_winnings, week_unused):
        """Create or recreate balance for this gameweek for this user.
        If the balance already exists then we need to add any existing special money.

        Weekly = week_winnings
        Special = long_term_winnings
        Provisional = banked + weekly winnings (if positive) + special
        Banked = last week banked + week_unused + any weekly losses + special
        """

        existing_balance = self.get_existing(gameweek, user)
        long_term_winnings = existing_balance.special if existing_balance else 0.0

        # If user made a loss then that has to be realized immediately
        enforce_banked = week_winnings if week_winnings < 0.0 else 0.0
        prev_banked = gameweek.get_prev_banked(user)
        banked = float(prev_banked) + week_unused + enforce_banked + long_term_winnings

        provisional = banked if week_winnings <= 0.0 else banked + week_winnings

        with transaction.atomic():
            if existing_balance:
                existing_balance.delete()
            return super().create(
                gameweek=gameweek,
                user=user,
                week=week_winnings,
                provisional=provisional,
                special=long_term_winnings,
                banked=banked,
            )

    def create_with_longterm(self, gameweek, user, long_term_winnings):
        """Create or recreate balance for this gameweek for this user.
        If the balance already exists then we need to account for any existing special money and any existing
        weekly winnings.

        Be careful when updating the result of a long term. This method must be called with the difference to ensure
        updated long terms are not double counted.
        """

        existing_balance = self.get_existing(gameweek, user)
        special = float(existing_balance.special) + float(long_term_winnings) if existing_balance else long_term_winnings
        week_winnings = existing_balance.week if existing_balance else 0.0
        provisional = float(existing_balance.provisional) + float(long_term_winnings) if existing_balance else long_term_winnings
        banked = float(existing_balance.banked) + float(long_term_winnings) if existing_balance else long_term_winnings

        with transaction.atomic():
            if existing_balance:
                existing_balance.delete()
            return super().create(
                gameweek=gameweek,
                user=user,
                week=week_winnings,
                provisional=provisional,
                special=special,
                banked=banked,
            )


class Balance(models.Model):
    gameweek = models.ForeignKey(Gameweek, null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    week = models.DecimalField(default=0.0, decimal_places=2, max_digits=99)
    provisional = models.DecimalField(default=0.0, decimal_places=2, max_digits=99)
    special = models.DecimalField(default=0.0, decimal_places=2, max_digits=99)
    banked = models.DecimalField(default=0.0, decimal_places=2, max_digits=99)
    objects = BalanceManager()

    def __str__(self):
        return str(self.gameweek) + ":" + self.user.username


class Game(models.Model):
    gameweek = models.ForeignKey(Gameweek, on_delete=models.CASCADE)
    hometeam = models.CharField(max_length=255)
    awayteam = models.CharField(max_length=255)
    homenumerator = models.IntegerField(default=0)
    homedenominator = models.IntegerField(default=1)
    drawnumerator = models.IntegerField(default=0)
    drawdenominator = models.IntegerField(default=1)
    awaynumerator = models.IntegerField(default=0)
    awaydenominator = models.IntegerField(default=1)

    def __str__(self):
        return self.hometeam + " vs " + self.awayteam

    def get_numerator(self, result):
        """ Get numerator value for result """
        if result == "H":
            return self.homenumerator
        elif result == "D":
            return self.drawnumerator
        else:
            return self.awaynumerator

    def get_denominator(self, result):
        """ Get denominator value for result """
        if result == "H":
            return self.homedenominator
        elif result == "D":
            return self.drawdenominator
        else:
            return self.awaydenominator

    def get_result(self):
        """ Get result """
        return self.result_set.all()[0]


class Result(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    RESULTS = (("H", "Home"), ("D", "Draw"), ("A", "Away"))
    result = models.CharField(max_length=1, choices=RESULTS, default="H")

    def __str__(self):
        return str(self.game) + " - " + str(self.result)
