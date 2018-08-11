# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

import datetime

from django.db import models

from django.contrib.auth.models import User
from django.db import transaction
import logging

from wagtail.wagtailsnippets.models import register_snippet
from __builtin__ import True

logger = logging.getLogger(__name__)


# Create your models here.
@register_snippet
class Season(models.Model):
    commissioner = models.ForeignKey(User, on_delete=models.CASCADE)
    players = models.ManyToManyField(User, related_name='season_players')
    name = models.CharField(max_length=255)
    weekly_allowance = models.DecimalField(
            default=100.0, decimal_places=2, max_digits=99)
    public = models.BooleanField(default=False)
    added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_next_gameweek_id(self):
        ''' Get id for next gameweek '''
        return len(self.gameweek_set.all()) + 1

    def _get_gameweek_by_id(self, gameweek_id):
        return self.gameweek_set.filter(number=gameweek_id)[0]

    def balances_available(self):
        ''' Check if balances are available (e.g. for display
        on season root page) '''
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
        ''' Get latest gameweek that has a complete set of results '''
        gameweek = self.get_latest_gameweek()
        if gameweek.results_complete():
            return gameweek
        else:
            return self._get_gameweek_by_id(gameweek.number - 1)

    def get_latest_gameweek(self):
        ''' Get latest gameweek '''
        if self.get_next_gameweek_id() == 1:
            return None

        latest_gameweek_number = self.get_next_gameweek_id() - 1

        return self._get_gameweek_by_id(latest_gameweek_number)

    def can_create_gameweek(self):
        ''' Check whether new gameweek can be created '''
        if self.get_next_gameweek_id() > 1:
            if not self.get_latest_gameweek().results_complete():
                return False
        return True


@register_snippet
class Gameweek(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    number = models.IntegerField(default=0)
    deadline_date = models.DateField(default=datetime.date(
        datetime.datetime.now().year,
        datetime.datetime.now().month,
        datetime.datetime.now().day))
    deadline_time = models.TimeField(default=datetime.time(12, 00))
    spiel = models.TextField(default=None, blank=True)

    def __str__(self):
        return str(self.season) + ',' + str(self.number)

    def is_first_gameweek(self):
        return self.number == 1

    def is_latest_gameweek(self):
        return self == self.season.get_latest_gameweek()

    def get_prev_gameweek(self):
        if self.is_first_gameweek():
            raise Exception('Called get_prev_gameweek on first gameweek')
        return self.season._get_gameweek_by_id(self.number-1)

    def get_next_gameweek(self):
        if self.is_latest_gameweek():
            raise Exception('Called get_next_gameweek on latest gameweek')
        return self.season._get_gameweek_by_id(self.number+1)

    def update_no_bet_users(self):
        ''' For users who have no betcontainer for this week, set weekly winnings
            as -100, weekly unused as all available rollable and update balance
            accordingly '''
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
                        week_unused=unused
                        )

    def _calc_enforce_banked(self, week_winnings):
        # If user made a loss then that has to be realized immediately
        if week_winnings < 0.0:
            enforce_banked = week_winnings
        else:
            enforce_banked = 0.0
        return enforce_banked

    def _get_prev_banked(self, user):
        # If Gameweek 1 then last banked must be 0
        if self.number == 1:
            prev_banked = 0.0
        else:
            prev_gameweek = self.get_prev_gameweek()
            prev_balance = prev_gameweek._get_balance_by_user(user)
            prev_banked = prev_balance.banked
        return prev_banked

    def set_balance_by_user(self, user, week_winnings, week_unused):
        ''' Set the balance for this gameweek for this user.
            Weekly = week_winnings
            Provisional = banked + week winnings (if positive)
            Banked = last week banked + week_unused + any weekly losses '''
        enforce_banked = self._calc_enforce_banked(week_winnings)

        prev_banked = self._get_prev_banked(user)
        banked = float(prev_banked) + week_unused + enforce_banked
        if (week_winnings > 0.0):
            provisional = banked + week_winnings
        else:
            provisional = banked

        user_balance = Balance(
                gameweek=self,
                user=user,
                week=week_winnings,
                provisional=provisional,
                banked=banked)

        with transaction.atomic():
            if self.user_has_balance(user):
                old_user_balance = self.balance_set.filter(user=user)[0]
                old_user_balance.delete()
            user_balance.save()

    def _get_balance_by_user(self, user):
        ''' Get user balance '''
        if len(self.balance_set.filter(user=user)) == 0:
            return None
        else:
            return self.balance_set.filter(user=user)[0]

    def has_bets(self):
        ''' Check if any users have placed bets '''
        if len(self.betcontainer_set.all()) > 0:
            return True
        else:
            return False

    def deadline_passed(self):
        ''' Check if deadline has passed '''
        return ((datetime.datetime.now().date() == self.deadline_date
                and datetime.datetime.now().time() >= self.deadline_time)
                or datetime.datetime.now().date() > self.deadline_date)

    def results_complete(self):
        ''' Check if ALL results have been posted '''
        results_count = 0
        game_set = self.game_set.all()
        for game in game_set:
            if len(game.result_set.all()) > 0:
                results_count += 1
        return results_count == len(game_set)

    def _get_allowance_by_user(self, user):
        ''' Get allowance + rollable for this user '''
        allowance = self.season.weekly_allowance
        rollable_allowances = self.get_rollable_allowances()

        if rollable_allowances and user in rollable_allowances:
            return allowance + rollable_allowances[user]
        else:
            return allowance

    def get_rollable_allowances(self):
        ''' Get ALL the rollable allowances '''
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
        for balance in self.balance_set.order_by('-provisional'):
            user_positions.update({balance.user: position})
            position += 1

        return user_positions

    def _get_change_icon(self, positions, prev_positions, user):
        change_icon = '-'
        if user in prev_positions:
            diff = prev_positions[user] - positions[user]
            if diff > 0:
                change_icon = '/\\'
            elif diff < 0:
                change_icon = '\\/'

        return change_icon

    def get_ordered_results(self):
        ''' Get full results ordered by provisional descending'''
        results = []

        positions = self._get_user_positions()
        if self.number > 1:
            prev_positions = self.get_prev_gameweek()._get_user_positions()
        else:
            prev_positions = {}

        for balance in self.balance_set.order_by('-provisional'):
            change_icon = self._get_change_icon(
                    positions, prev_positions, balance.user)
            results.append([
                balance.user,
                balance.week,
                balance.provisional,
                balance.banked,
                change_icon])

        return results

    def _get_users_with_bets(self):
        users = []
        for betcontainer in self.betcontainer_set.all():
            users.append(betcontainer.owner)
        return users

    def get_users_with_ready_bets_as_string(self):
        ''' Print usernames of users who have already placed valid bets '''
        users = ''
        for betcontainer in self.betcontainer_set.all():
            total_bet = 0.0
            for accumulator in betcontainer.accumulator_set.all():
                total_bet += float(accumulator.stake)
            if total_bet >= self.season.weekly_allowance:
                users += betcontainer.owner.username + ', '
        return users

    def user_has_balance(self, user):
        ''' Check if user has a balance '''
        return len(self.balance_set.filter(user=user)) > 0


@register_snippet
class Balance(models.Model):
    gameweek = models.ForeignKey(Gameweek, null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    week = models.DecimalField(default=0.0, decimal_places=2, max_digits=99)
    provisional = models.DecimalField(
            default=0.0, decimal_places=2, max_digits=99)
    banked = models.DecimalField(default=0.0, decimal_places=2, max_digits=99)

    def __str__(self):
        return str(self.gameweek) + ':' + self.user.username


@register_snippet
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
        ''' Get numerator value for result '''
        if result == 'H':
            return self.homenumerator
        elif result == 'D':
            return self.drawnumerator
        else:
            return self.awaynumerator

    def get_denominator(self, result):
        ''' Get denominator value for result '''
        if result == 'H':
            return self.homedenominator
        elif result == 'D':
            return self.drawdenominator
        else:
            return self.awaydenominator

    def get_result(self):
        ''' Get result '''
        return self.result_set.all()[0]


@register_snippet
class Result(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    RESULTS = (('H', 'Home'), ('D', 'Draw'), ('A', 'Away'))
    result = models.CharField(max_length=1, choices=RESULTS, default='H')

    def __str__(self):
        return str(self.game) + " - " + str(self.result)


@register_snippet
class BetContainer(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    gameweek = models.ForeignKey(Gameweek, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.gameweek) + ',' + self.owner.username

    def get_balance(self):
        return self.gameweek._get_balance_by_user(user=self.owner)

    def get_allowance(self):
        return self.gameweek._get_allowance_by_user(self.owner)

    def get_allowance_used(self):
        allowance_used = 0.0
        for accumulator in self.accumulator_set.all():
            allowance_used += float(accumulator.stake)
        return allowance_used

    def get_allowance_unused(self):
        return float(self.get_allowance()) - self.get_allowance_used()

    def get_game_count(self):
        game_count = 0
        for accumulator in self.accumulator_set.all():
            game_count += len(accumulator.betpart_set.all())

        return game_count

    def calc_winnings(self):
        winnings = 0.0
        for accumulator in self.accumulator_set.all():
            winnings += accumulator.calc_winnings()

        true_winnings = winnings - float(self.gameweek.season.weekly_allowance)

        return float("{0:.2f}".format(true_winnings))


@register_snippet
class Accumulator(models.Model):
    bet_container = models.ForeignKey(BetContainer, on_delete=models.CASCADE)
    stake = models.DecimalField(default=0.0, decimal_places=2, max_digits=99)

    def __str__(self):
        name = str(self.bet_container) + ',' + str(self.stake)
        for betpart in self.betpart_set.all():
            name = name + ',' + str(betpart)

        return name

    def calc_winnings(self):
        ''' Calculate winnings for this accumulator '''
        correct = True
        odds = 1.0
        for betpart in self.betpart_set.all():
            if not betpart.is_correct():
                correct = False
                break
            else:
                game = betpart.game
                result = betpart.result
                num = 1
                denom = 1
                if result == 'H':
                    num = game.homenumerator
                    denom = game.homedenominator
                elif result == 'D':
                    num = game.drawnumerator
                    denom = game.drawdenominator
                elif result == 'A':
                    num = game.awaynumerator
                    denom = game.awaydenominator
                odds = odds * float(num + denom) / float(denom)

        if correct:
            return odds * float(self.stake)
        else:
            return 0.0


@register_snippet
class BetPart(models.Model):
    accumulator = models.ForeignKey(Accumulator, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    RESULTS = (('H', 'Home'), ('D', 'Draw'), ('A', 'Away'))
    result = models.CharField(max_length=1, choices=RESULTS, default='H')

    def __str__(self):
        return str(self.game) + ',' + str(self.result)

    def is_correct(self):
        if len(self.game.result_set.all()) != 1:
            return False

        result = next(iter(self.game.result_set.all()))

        if result.result == self.result:
            return True
        else:
            return False


@register_snippet
class LongSpecialContainer(models.Model):
    description = models.CharField(max_length=255)
    allowance = models.DecimalField(
            default=100.0, decimal_places=2, max_digits=99)
    created_gameweek = models.ForeignKey(
            Gameweek,
            on_delete=models.CASCADE)

    def __str__(self):
        return self.description

    def has_bets(self):
        return False

    def complete(self):
        return False

    def get_choice_by_user(self, user):
        user_container = BetContainer.objects.filter(
                    gameweek=self.created_gameweek
                ).filter(
                    owner=user
                )

        if not user_container:
            return None

        choice = LongSpecialBet.objects.filter(
                    bet_container=user_container
                ).filter(
                    long_special__container=self
                ).first()

        return choice


@register_snippet
class LongSpecial(models.Model):
    container = models.ForeignKey(
            LongSpecialContainer,
            on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    numerator = models.IntegerField(default=0)
    denominator = models.IntegerField(default=1)

    def __str__(self):
        return self.description + ': ' + str(self.numerator) + '/' + str(self.denominator)

    def chosen_by(self):
        users = ''
        for bet in self.longspecialbet_set.all():
            if users:
                users += ', ' + bet.bet_container.owner.username
            else:
                users = bet.bet_container.owner.username

        return users


@register_snippet
class LongSpecialResult(models.Model):
    long_special = models.ForeignKey(Game, on_delete=models.CASCADE)
    result = models.BooleanField()
    completed_gameweek = models.ForeignKey(
            Gameweek,
            on_delete=models.CASCADE)

    def __str__(self):
        return str(self.long_special) + " - " + str(self.result)


@register_snippet
class LongSpecialBet(models.Model):
    bet_container = models.ForeignKey(BetContainer, on_delete=models.CASCADE)
    long_special = models.ForeignKey(LongSpecial, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.long_special)

    def is_correct(self):
        if len(self.long_special.longspecialresult_set.all()) != 1:
            return False

        result = next(iter(self.long_special.longspecialresult_set.all()))

        return result.result
