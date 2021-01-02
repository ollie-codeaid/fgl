# -*- coding: utf-8 -*-
from django.test import TestCase

import datetime

from fglsite.bets.models import (
    Season,
    Gameweek,
)
from fglsite.gambling.models import LongSpecialContainer, LongSpecial, LongSpecialResult
from django.contrib.auth.models import User
from django.urls import reverse


class LongSpecialResultViewTest(TestCase):
    def setUp(self):
        self.commissioner = User.objects.create_user(username="comm", password="comm")
        season = Season.objects.create(
            name="test",
            commissioner=self.commissioner,
            weekly_allowance=100.0,
        )
        self.gameweek = Gameweek.objects.create(
            season=season,
            number=1,
            deadline_date=datetime.date(2017, 11, 1),
            deadline_time=datetime.time(13, 00),
            spiel="not empty",
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

        self.url = reverse(
            "add-longterm-result",
            kwargs={
                "pk": self.long_special_container.id,
                "gameweek_id": self.gameweek.id,
            },
        )

    def test_GET_visible_to_commissioner(self):
        self.client.force_login(self.commissioner)
        response = self.client.get(self.url)

        assert response.status_code == 200
        form = response.context["form"]
        assert form.fields["long_special"].valid_value(self.choice_one.id)
        assert form.fields["long_special"].valid_value(self.choice_two.id)
        assert form.initial["completed_gameweek"] == self.gameweek.id

    def test_GET_non_user_forbidden(self):
        response = self.client.get(self.url)

        assert response.status_code == 403

    def test_GET_on_create_non_owner_user_forbidden(self):
        user = User.objects.create_user(username="user", password="password")
        self.client.force_login(user)
        response = self.client.get(self.url)

        assert response.status_code == 403

    def test_POST_saves_long_special_result(self):
        form_data = {
            "long_special": self.choice_one.id,
            "completed_gameweek": self.gameweek.id,
        }

        self.client.force_login(self.commissioner)
        self.client.post(self.url, data=form_data)

        assert LongSpecialResult.objects.count() == 1
        result = LongSpecialResult.objects.get()

        assert result.long_special == self.choice_one
        assert result.completed_gameweek == self.gameweek

    def test_POST_non_user_forbidden(self):
        form_data = {
            "long_special": self.choice_one.id,
            "completed_gameweek": self.gameweek.id,
        }

        response = self.client.post(self.url, data=form_data)
        assert response.status_code == 403

        assert LongSpecialResult.objects.count() == 0

    def test_POST_non_commissioner_forbidden(self):
        form_data = {
            "long_special": self.choice_one.id,
            "completed_gameweek": self.gameweek.id,
        }

        user = User.objects.create_user(username="user", password="password")
        self.client.force_login(user)
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == 403

        assert LongSpecialResult.objects.count() == 0

    def test_POST_updates_existing_long_special_result(self):
        LongSpecialResult.objects.create(
            long_special=self.choice_two, completed_gameweek=self.gameweek
        )

        form_data = {
            "long_special": self.choice_one.id,
            "completed_gameweek": self.gameweek.id,
        }

        self.client.force_login(self.commissioner)
        self.client.post(self.url, data=form_data)

        assert LongSpecialResult.objects.count() == 1
        result = LongSpecialResult.objects.get()

        assert result.long_special == self.choice_one
        assert result.completed_gameweek == self.gameweek
