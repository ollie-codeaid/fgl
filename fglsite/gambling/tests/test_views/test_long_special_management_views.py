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


class LongSpecialManagementViewTest(TestCase):
    def setUp(self):
        self.commissioner = User.objects.create_user(username="comm", password="comm")
        self.season = Season.objects.create(
            name="test",
            commissioner=self.commissioner,
            weekly_allowance=100.0,
        )
        self.gameweek = Gameweek.objects.create(
            season=self.season,
            number=1,
            deadline_date=datetime.date(2017, 11, 1),
            deadline_time=datetime.time(13, 00),
            spiel="not empty",
        )

    def test_GET_visible_to_commissioner(self):
        url = reverse("manage-longterms", args=[self.gameweek.id])

        self.client.force_login(self.commissioner)
        response = self.client.get(url)

        assert response.status_code == 200

    def test_GET_non_user_forbidden(self):
        url = reverse("manage-longterms", args=[self.gameweek.id])

        response = self.client.get(url)

        assert response.status_code == 403

    def test_GET_non_commissioner_forbidden(self):
        url = reverse("manage-longterms", args=[self.gameweek.id])

        user = User.objects.create_user(username="user", password="password")
        self.client.force_login(user)
        response = self.client.get(url)

        assert response.status_code == 403

    def test_create_long_term_link_shown_if_gameweek_not_passed_deadline(self):
        url = reverse("manage-longterms", args=[self.gameweek.id])

        self.gameweek.deadline_date = datetime.datetime.now() + datetime.timedelta(
            days=1
        )
        self.gameweek.save()

        self.client.force_login(self.commissioner)
        response = self.client.get(url)

        expected_url = reverse("create-longterm", args=[self.gameweek.id])
        response_content = str(response.content)
        assert "Add long term" in response_content
        assert f'<a href="{expected_url}">' in response_content

    def test_create_long_term_link_not_shown_if_gameweek_passed_deadline(self):
        url = reverse("manage-longterms", args=[self.gameweek.id])

        self.gameweek.deadline_date = datetime.datetime.now() - datetime.timedelta(
            days=1
        )
        self.gameweek.save()

        self.client.force_login(self.commissioner)
        response = self.client.get(url)

        expected_url = reverse("create-longterm", args=[self.gameweek.id])
        response_content = str(response.content)
        assert "Add long term" not in response_content
        assert f'<a href="{expected_url}">' not in response_content

    def test_long_term_created_this_week_shown_and_updatable_if_gameweek_not_passed_deadline(
        self,
    ):
        url = reverse("manage-longterms", args=[self.gameweek.id])

        long_special_container = LongSpecialContainer.objects.create(
            description="SOME_DESCRIPTION",
            allowance=100.0,
            created_gameweek=self.gameweek,
        )

        self.gameweek.deadline_date = datetime.datetime.now() + datetime.timedelta(
            days=1
        )
        self.gameweek.save()

        self.client.force_login(self.commissioner)
        response = self.client.get(url)

        update_url = reverse("update-longterm", args=[long_special_container.id])
        complete_url = reverse(
            "add-longterm-result", args=[long_special_container.id, self.gameweek.id]
        )
        response_content = str(response.content)
        assert "SOME_DESCRIPTION" in response_content
        assert f'<a href="{update_url}">' in response_content
        assert f'<a href="{complete_url}">' not in response_content

    def test_long_term_created_this_week_shown_and_completable_if_gameweek_not_passed_deadline(
        self,
    ):
        url = reverse("manage-longterms", args=[self.gameweek.id])

        long_special_container = LongSpecialContainer.objects.create(
            description="SOME_DESCRIPTION",
            allowance=100.0,
            created_gameweek=self.gameweek,
        )

        self.gameweek.deadline_date = datetime.datetime.now() - datetime.timedelta(
            days=1
        )
        self.gameweek.save()

        self.client.force_login(self.commissioner)
        response = self.client.get(url)

        update_url = reverse("update-longterm", args=[long_special_container.id])
        complete_url = reverse(
            "add-longterm-result", args=[long_special_container.id, self.gameweek.id]
        )
        response_content = str(response.content)
        assert "SOME_DESCRIPTION" in response_content
        assert f'<a href="{update_url}">' not in response_content
        assert f'<a href="{complete_url}">' in response_content

    def test_long_term_created_last_week_shown_not_actionable_if_gameweek_not_passed_deadline(
        self,
    ):
        long_special_container = LongSpecialContainer.objects.create(
            description="SOME_DESCRIPTION",
            allowance=100.0,
            created_gameweek=self.gameweek,
        )
        LongSpecial.objects.create(
            container=long_special_container,
            description="CHOICE_ONE",
            numerator=10,
            denominator=11,
        )

        gameweek_two = Gameweek.objects.create(
            season=self.season,
            number=2,
            deadline_date=datetime.datetime.now() + datetime.timedelta(days=1),
            deadline_time=datetime.time(13, 00),
            spiel="not empty",
        )

        url = reverse("manage-longterms", args=[gameweek_two.id])

        self.client.force_login(self.commissioner)
        response = self.client.get(url)

        update_url = reverse("update-longterm", args=[long_special_container.id])
        complete_url = reverse(
            "add-longterm-result", args=[long_special_container.id, gameweek_two.id]
        )
        response_content = str(response.content)
        assert "SOME_DESCRIPTION" in response_content
        assert f'<a href="{update_url}">' not in response_content
        assert f'<a href="{complete_url}">' not in response_content

    def test_long_term_created_last_week_completable_if_gameweek_passed_deadline(self):
        long_special_container = LongSpecialContainer.objects.create(
            description="SOME_DESCRIPTION",
            allowance=100.0,
            created_gameweek=self.gameweek,
        )
        LongSpecial.objects.create(
            container=long_special_container,
            description="CHOICE_ONE",
            numerator=10,
            denominator=11,
        )

        gameweek_two = Gameweek.objects.create(
            season=self.season,
            number=2,
            deadline_date=datetime.datetime.now() - datetime.timedelta(days=1),
            deadline_time=datetime.time(13, 00),
            spiel="not empty",
        )

        url = reverse("manage-longterms", args=[gameweek_two.id])

        self.client.force_login(self.commissioner)
        response = self.client.get(url)

        update_url = reverse("update-longterm", args=[long_special_container.id])
        complete_url = reverse(
            "add-longterm-result", args=[long_special_container.id, gameweek_two.id]
        )
        response_content = str(response.content)
        assert "SOME_DESCRIPTION" in response_content
        assert f'<a href="{update_url}">' not in response_content
        assert f'<a href="{complete_url}">' in response_content

    def test_long_term_created_this_week_shown_and_completable_if_gameweek_already_completed(
        self,
    ):
        url = reverse("manage-longterms", args=[self.gameweek.id])

        long_special_container = LongSpecialContainer.objects.create(
            description="SOME_DESCRIPTION",
            allowance=100.0,
            created_gameweek=self.gameweek,
        )
        long_special = LongSpecial.objects.create(
            container=long_special_container,
            description="CHOICE_ONE",
            numerator=10,
            denominator=11,
        )
        LongSpecialResult.objects.create(
            long_special=long_special, completed_gameweek=self.gameweek
        )

        self.gameweek.deadline_date = datetime.datetime.now() - datetime.timedelta(
            days=1
        )
        self.gameweek.save()

        self.client.force_login(self.commissioner)
        response = self.client.get(url)

        update_url = reverse("update-longterm", args=[long_special_container.id])
        complete_url = reverse(
            "add-longterm-result", args=[long_special_container.id, self.gameweek.id]
        )
        response_content = str(response.content)
        assert "SOME_DESCRIPTION" in response_content
        assert f'<a href="{update_url}">' not in response_content
        assert f'<a href="{complete_url}">' in response_content

    def test_long_term_completed_last_week_not_shown_this_week(self):
        long_special_container = LongSpecialContainer.objects.create(
            description="SOME_DESCRIPTION",
            allowance=100.0,
            created_gameweek=self.gameweek,
        )
        long_special = LongSpecial.objects.create(
            container=long_special_container,
            description="CHOICE_ONE",
            numerator=10,
            denominator=11,
        )
        LongSpecialResult.objects.create(
            long_special=long_special, completed_gameweek=self.gameweek
        )

        gameweek_two = Gameweek.objects.create(
            season=self.season,
            number=2,
            deadline_date=datetime.datetime.now() + datetime.timedelta(days=1),
            deadline_time=datetime.time(13, 00),
            spiel="not empty",
        )

        url = reverse("manage-longterms", args=[gameweek_two.id])

        self.gameweek.deadline_date = datetime.datetime.now() - datetime.timedelta(
            days=1
        )
        self.gameweek.save()

        self.client.force_login(self.commissioner)
        response = self.client.get(url)

        update_url = reverse("update-longterm", args=[long_special_container.id])
        complete_url = reverse(
            "add-longterm-result", args=[long_special_container.id, gameweek_two.id]
        )
        response_content = str(response.content)
        assert "SOME_DESCRIPTION" not in response_content
        assert f'<a href="{update_url}">' not in response_content
        assert f'<a href="{complete_url}">' not in response_content
