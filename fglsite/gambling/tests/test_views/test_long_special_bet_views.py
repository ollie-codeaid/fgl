# -*- coding: utf-8 -*-
import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from fglsite.bets.models import Gameweek, Season
from fglsite.gambling.models import (
    BetContainer,
    LongSpecial,
    LongSpecialBet,
    LongSpecialContainer,
)


class LongSpecialBetViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user_one", password="password")
        season = Season.objects.create(
            name="test",
            commissioner=User.objects.create_user(username="comm", password="comm"),
            weekly_allowance=100.0,
        )
        self.gameweek = Gameweek.objects.create(
            season=season,
            number=1,
            deadline_date=datetime.date(2017, 11, 1),
            deadline_time=datetime.time(13, 00),
            spiel="not empty",
        )
        self.bet_container = BetContainer.objects.create(
            owner=self.user, gameweek=self.gameweek
        )
        self.long_special_container = LongSpecialContainer.objects.create(
            description="SOME_DESCRIPTION",
            allowance=100.0,
            created_gameweek=self.gameweek,
        )
        self.choice_one = LongSpecial.objects.create(
            container=self.long_special_container,
            description="CHOICE_ONE",
            numerator=10,
            denominator=11,
        )
        self.choice_two = LongSpecial.objects.create(
            container=self.long_special_container,
            description="CHOICE_TWO",
            numerator=20,
            denominator=29,
        )

    def test_GET_on_create_visible_to_bet_container_owner(self):
        url = reverse(
            "create-longterm-bet",
            kwargs={
                "bet_container_id": self.bet_container.id,
                "long_special_container_id": self.long_special_container.id,
            },
        )

        self.client.force_login(self.user)
        response = self.client.get(url)

        assert response.status_code == 200
        assert (
            response.context["form"]
            .fields["long_special"]
            .valid_value(self.choice_one.id)
        )
        assert (
            response.context["form"]
            .fields["long_special"]
            .valid_value(self.choice_two.id)
        )

    def test_GET_on_create_non_user_forbidden(self):
        url = reverse(
            "create-longterm-bet",
            kwargs={
                "bet_container_id": self.bet_container.id,
                "long_special_container_id": self.long_special_container.id,
            },
        )

        response = self.client.get(url)

        assert response.status_code == 403

    def test_GET_on_create_non_owner_user_forbidden(self):
        url = reverse(
            "create-longterm-bet",
            kwargs={
                "bet_container_id": self.bet_container.id,
                "long_special_container_id": self.long_special_container.id,
            },
        )

        user_two = User.objects.create_user(username="user_two", password="password")
        self.client.force_login(user_two)
        response = self.client.get(url)

        assert response.status_code == 403

    def test_POST_on_create_saves_long_special_bet(self):
        form_data = {"long_special": self.choice_one.id}

        url = reverse(
            "create-longterm-bet",
            kwargs={
                "bet_container_id": self.bet_container.id,
                "long_special_container_id": self.long_special_container.id,
            },
        )
        self.client.force_login(self.user)
        self.client.post(url, data=form_data)

        assert self.bet_container.longspecialbet_set.count() == 1

        long_special_bet = self.bet_container.longspecialbet_set.get()
        assert long_special_bet.long_special == self.choice_one

    def test_POST_on_create_non_user_forbidden(self):
        form_data = {"long_special": self.choice_one.id}

        url = reverse(
            "create-longterm-bet",
            kwargs={
                "bet_container_id": self.bet_container.id,
                "long_special_container_id": self.long_special_container.id,
            },
        )
        response = self.client.post(url, data=form_data)

        assert response.status_code == 403
        assert self.bet_container.longspecialbet_set.count() == 0

    def test_POST_on_create_non_owner_user_forbidden(self):
        form_data = {"long_special": self.choice_one.id}

        url = reverse(
            "create-longterm-bet",
            kwargs={
                "bet_container_id": self.bet_container.id,
                "long_special_container_id": self.long_special_container.id,
            },
        )
        user_two = User.objects.create_user(username="user_two", password="password")
        self.client.force_login(user_two)
        response = self.client.post(url, data=form_data)

        assert response.status_code == 403
        assert self.bet_container.longspecialbet_set.count() == 0

    def test_GET_on_update_displays_form_with_correct_choices(self):
        long_special_bet = LongSpecialBet.objects.create(
            bet_container=self.bet_container, long_special=self.choice_one
        )
        url = reverse("update-longterm-bet", kwargs={"pk": long_special_bet.pk})

        self.client.force_login(self.user)
        response = self.client.get(url)

        assert "form" in response.context
        bet_form = response.context["form"]
        assert bet_form.initial.get("long_special") == self.choice_one.id

    def test_GET_on_update_non_user_forbidden(self):
        long_special_bet = LongSpecialBet.objects.create(
            bet_container=self.bet_container, long_special=self.choice_one
        )
        url = reverse("update-longterm-bet", kwargs={"pk": long_special_bet.pk})

        response = self.client.get(url)

        assert response.status_code == 403

    def test_GET_on_update_non_owner_user_forbidden(self):
        long_special_bet = LongSpecialBet.objects.create(
            bet_container=self.bet_container, long_special=self.choice_one
        )
        url = reverse("update-longterm-bet", kwargs={"pk": long_special_bet.pk})

        user_two = User.objects.create_user(username="user_two", password="password")
        self.client.force_login(user_two)
        response = self.client.get(url)

        assert response.status_code == 403

    def test_POST_on_update_saves_long_special_bet(self):
        long_special_bet = LongSpecialBet.objects.create(
            bet_container=self.bet_container, long_special=self.choice_one
        )
        form_data = {"long_special": self.choice_two.id}

        url = reverse("update-longterm-bet", kwargs={"pk": long_special_bet.pk})
        self.client.force_login(self.user)
        self.client.post(url, data=form_data)

        assert self.bet_container.longspecialbet_set.count() == 1

        long_special_bet = self.bet_container.longspecialbet_set.get()
        assert long_special_bet.long_special == self.choice_two

    def test_POST_on_update_non_user_forbidden(self):
        long_special_bet = LongSpecialBet.objects.create(
            bet_container=self.bet_container, long_special=self.choice_one
        )
        form_data = {"long_special": self.choice_two.id}

        url = reverse("update-longterm-bet", kwargs={"pk": long_special_bet.pk})
        response = self.client.post(url, data=form_data)

        assert response.status_code == 403
        assert self.bet_container.longspecialbet_set.count() == 1

        long_special_bet = self.bet_container.longspecialbet_set.get()
        assert long_special_bet.long_special == self.choice_one

    def test_POST_on_update_non_owner_user_forbidden(self):
        long_special_bet = LongSpecialBet.objects.create(
            bet_container=self.bet_container, long_special=self.choice_one
        )
        form_data = {"long_special": self.choice_two.id}

        url = reverse("update-longterm-bet", kwargs={"pk": long_special_bet.pk})

        user_two = User.objects.create_user(username="user_two", password="password")
        self.client.force_login(user_two)
        response = self.client.post(url, data=form_data)

        assert response.status_code == 403
        assert self.bet_container.longspecialbet_set.count() == 1

        long_special_bet = self.bet_container.longspecialbet_set.get()
        assert long_special_bet.long_special == self.choice_one
