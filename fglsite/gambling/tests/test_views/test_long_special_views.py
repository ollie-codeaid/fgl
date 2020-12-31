# -*- coding: utf-8 -*-
from django.test import TestCase

import datetime

from fglsite.bets.models import (
    Season,
    Gameweek,
)
from fglsite.gambling.models import BetPart, LongSpecialContainer, LongSpecial
from django.contrib.auth.models import User
from django.urls import reverse


def _create_management_data(form_count):
    return {
        "form-TOTAL_FORMS": form_count,
        "form-INITIAL_FORMS": form_count,
        "form-MAX_NUM_FORMS": form_count,
        "form-TOTAL_FORM_COUNT": form_count,
    }


def _create_choice_data(choice_num, description, numerator, denominator):
    return {
        "form-{0}-description".format(choice_num): description,
        "form-{0}-numerator".format(choice_num): numerator,
        "form-{0}-denominator".format(choice_num): denominator,
    }


def _create_basic_long_special_container_form_data():
    long_special_container_data = {
        "description": "SOME_DESCRIPTION",
        "allowance": 200.0,
    }
    long_special_container_data.update(_create_management_data(2))
    long_special_container_data.update(_create_choice_data(0, "CHOICE_ONE", 1, 2))
    long_special_container_data.update(_create_choice_data(1, "CHOICE_TWO", 3, 4))

    return long_special_container_data


def _assert_long_special_container_matches_expectations(long_special_container):
    assert long_special_container.description == "SOME_DESCRIPTION"
    assert long_special_container.allowance == 200.0
    assert long_special_container.longspecial_set.count() == 2

    choice_one = long_special_container.longspecial_set.get(description="CHOICE_ONE")
    assert choice_one.numerator == 1
    assert choice_one.denominator == 2

    choice_two = long_special_container.longspecial_set.get(description="CHOICE_TWO")
    assert choice_two.numerator == 3
    assert choice_two.denominator == 4


class LongSpecialContainerViewTest(TestCase):
    def setUp(self):
        self.commissioner = User.objects.create_user(username="comm", password="comm")
        season = Season.objects.create(
            name="test", commissioner=self.commissioner, weekly_allowance=100.0
        )
        self.gameweek = Gameweek.objects.create(
            season=season,
            number=1,
            deadline_date=datetime.date(2017, 11, 1),
            deadline_time=datetime.time(13, 00),
            spiel="not empty",
        )

    def test_GET_on_create_visible_to_commissioner(self):
        url = reverse("create-longterm", kwargs={"gameweek_id": self.gameweek.id})

        self.client.force_login(self.commissioner)
        response = self.client.get(url)

        assert response.status_code == 200

    def test_GET_on_create_non_user_forbidden(self):
        url = reverse("create-longterm", kwargs={"gameweek_id": self.gameweek.id})

        response = self.client.get(url)

        assert response.status_code == 403

    def test_GET_on_create_non_commissioner_forbidden(self):
        url = reverse("create-longterm", kwargs={"gameweek_id": self.gameweek.id})

        user = User.objects.create_user(username="user_two", password="test")
        self.client.force_login(user)

        response = self.client.get(url)

        assert response.status_code == 403

    def test_POST_on_create_saves_long_special_container(self):
        form_data = _create_basic_long_special_container_form_data()

        url = reverse("create-longterm", kwargs={"gameweek_id": self.gameweek.id})
        self.client.force_login(self.commissioner)
        self.client.post(url, data=form_data)

        assert self.gameweek.longspecialcontainer_set.count() == 1

        long_special_container = self.gameweek.longspecialcontainer_set.get()
        _assert_long_special_container_matches_expectations(long_special_container)

    def test_POST_on_create_non_user_forbidden(self):
        form_data = _create_basic_long_special_container_form_data()

        url = reverse("create-longterm", kwargs={"gameweek_id": self.gameweek.id})
        response = self.client.post(url, data=form_data)

        assert response.status_code == 403
        assert self.gameweek.longspecialcontainer_set.count() == 0

    def test_POST_on_create_non_commissioner_forbidden(self):
        form_data = _create_basic_long_special_container_form_data()

        url = reverse("create-longterm", kwargs={"gameweek_id": self.gameweek.id})
        user = User.objects.create_user(username="user_two", password="test")
        self.client.force_login(user)
        response = self.client.post(url, data=form_data)

        assert response.status_code == 403
        assert self.gameweek.longspecialcontainer_set.count() == 0

    def test_GET_on_update_displays_form_with_correct_choices(self):
        long_special_container = LongSpecialContainer.objects.create(
            description="SOME_OTHER_DESCRIPTION",
            allowance=100.0,
            created_gameweek=self.gameweek,
        )
        LongSpecial.objects.create(
            container=long_special_container,
            description="OLD_CHOICE_ONE",
            numerator=10,
            denominator=11,
        )
        url = reverse("update-longterm", kwargs={"pk": long_special_container.pk})

        self.client.force_login(self.commissioner)
        response = self.client.get(url)

        assert "long_special_formset" in response.context
        long_special_formset = response.context["long_special_formset"]
        assert len(long_special_formset.forms) == 1
        long_special_form = long_special_formset.forms[0]
        assert long_special_form.initial.get("description") == "OLD_CHOICE_ONE"
        assert long_special_form.initial.get("numerator") == 10
        assert long_special_form.initial.get("denominator") == 11

    def test_GET_on_update_non_user_forbidden(self):
        long_special_container = LongSpecialContainer.objects.create(
            description="SOME_OTHER_DESCRIPTION",
            allowance=100.0,
            created_gameweek=self.gameweek,
        )
        LongSpecial.objects.create(
            container=long_special_container,
            description="OLD_CHOICE_ONE",
            numerator=10,
            denominator=11,
        )

        url = reverse("update-longterm", kwargs={"pk": long_special_container.pk})

        response = self.client.get(url)

        assert response.status_code == 403

    def test_GET_on_update_non_commissioner_forbidden(self):
        long_special_container = LongSpecialContainer.objects.create(
            description="SOME_OTHER_DESCRIPTION",
            allowance=100.0,
            created_gameweek=self.gameweek,
        )
        LongSpecial.objects.create(
            container=long_special_container,
            description="OLD_CHOICE_ONE",
            numerator=10,
            denominator=11,
        )

        url = reverse("update-longterm", kwargs={"pk": long_special_container.pk})

        user = User.objects.create_user(username="user_two", password="test")
        self.client.force_login(user)

        response = self.client.get(url)

        assert response.status_code == 403

    def test_POST_on_update_saves_long_special_container(self):
        long_special_container = LongSpecialContainer.objects.create(
            description="SOME_OTHER_DESCRIPTION",
            allowance=100.0,
            created_gameweek=self.gameweek,
        )
        LongSpecial.objects.create(
            container=long_special_container,
            description="OLD_CHOICE_ONE",
            numerator=10,
            denominator=11,
        )

        form_data = _create_basic_long_special_container_form_data()

        url = reverse("update-longterm", kwargs={"pk": long_special_container.pk})
        self.client.force_login(self.commissioner)
        self.client.post(url, data=form_data)

        assert self.gameweek.longspecialcontainer_set.count() == 1

        long_special_container = self.gameweek.longspecialcontainer_set.get()
        _assert_long_special_container_matches_expectations(long_special_container)

    def test_POST_on_update_non_user_forbidden(self):
        long_special_container = LongSpecialContainer.objects.create(
            description="SOME_OTHER_DESCRIPTION",
            allowance=100.0,
            created_gameweek=self.gameweek,
        )
        LongSpecial.objects.create(
            container=long_special_container,
            description="OLD_CHOICE_ONE",
            numerator=10,
            denominator=11,
        )

        form_data = _create_basic_long_special_container_form_data()

        url = reverse("update-longterm", kwargs={"pk": long_special_container.pk})
        response = self.client.post(url, data=form_data)

        assert response.status_code == 403
        assert self.gameweek.longspecialcontainer_set.count() == 1

        long_special_container.refresh_from_db()
        assert long_special_container.description == "SOME_OTHER_DESCRIPTION"
        assert long_special_container.allowance == 100.0
        assert long_special_container.longspecial_set.count() == 1

    def test_POST_on_update_non_commissioner_forbidden(self):
        long_special_container = LongSpecialContainer.objects.create(
            description="SOME_OTHER_DESCRIPTION",
            allowance=100.0,
            created_gameweek=self.gameweek,
        )
        LongSpecial.objects.create(
            container=long_special_container,
            description="OLD_CHOICE_ONE",
            numerator=10,
            denominator=11,
        )

        form_data = _create_basic_long_special_container_form_data()

        url = reverse("update-longterm", kwargs={"pk": long_special_container.pk})
        user = User.objects.create_user(username="user_two", password="test")
        self.client.force_login(user)
        response = self.client.post(url, data=form_data)

        assert response.status_code == 403
        assert self.gameweek.longspecialcontainer_set.count() == 1

        long_special_container.refresh_from_db()
        assert long_special_container.description == "SOME_OTHER_DESCRIPTION"
        assert long_special_container.allowance == 100.0
        assert long_special_container.longspecial_set.count() == 1
