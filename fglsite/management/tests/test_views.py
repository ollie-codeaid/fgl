# -*- coding: utf-8 -*-
from django.test import TestCase

from fglsite.bets.models import Season
from fglsite.management.models import JoinRequest
from django.contrib.auth.models import User
from django.urls import reverse


class ViewsTest(TestCase):

    COMM_PASS = 'comm'
    PLAY_PASS = 'play'

    def setUp(self):
        self.commissioner = User.objects.create_user(
                username='comm',
                password=self.COMM_PASS)

        self.player = User.objects.create_user(
                username='player',
                password=self.PLAY_PASS)

        self.season = Season.objects.create(
                name='test',
                commissioner=self.commissioner,
                weekly_allowance=100.0)

    def test_join_private_season_with_credentials(self):
        url = reverse('join-season', args=(self.season.id,))
        self.client.login(
                username=self.player.username,
                password=self.PLAY_PASS)
        self.client.post(url)
        self.client.logout()

        self.assertEquals(1, len(self.season.joinrequest_set.all()))
        self.assertEquals(
                self.player,
                self.season.joinrequest_set.first().player)
        self.assertEquals(0, len(self.season.players.all()))

    def test_join_private_season_without_credentials(self):
        url = reverse('join-season', args=(self.season.id,))
        response = self.client.post(url, follow=True)

        message = list(response.context.get('messages'))[0]

        self.assertEquals(message.message, 'Must be logged in to join season')
        self.assertEquals(0, len(self.season.joinrequest_set.all()))
        self.assertEquals(0, len(self.season.players.all()))

    def test_join_public_season_with_credentials(self):
        self.season.public = True
        self.season.save()

        url = reverse('join-season', args=(self.season.id,))
        self.client.login(
                username=self.player.username,
                password=self.PLAY_PASS)
        self.client.post(url)
        self.client.logout()

        self.assertIn(self.player, self.season.players.all())

    def test_attempt_second_join(self):
        self.season.players.add(self.player)
        self.season.save()

        url = reverse('join-season', args=(self.season.id,))
        self.client.login(
                username=self.player.username,
                password=self.PLAY_PASS)
        response = self.client.post(url, follow=True)
        self.client.logout()

        message = list(response.context.get('messages'))[0]

        self.assertEquals(message.message, 'Already joined season')
        self.assertEquals(0, len(self.season.joinrequest_set.all()))
        self.assertEquals(1, len(self.season.players.all()))

    def test_attempt_second_send_request(self):
        JoinRequest.objects.create(
                season=self.season,
                player=self.player)

        url = reverse('join-season', args=(self.season.id,))
        self.client.login(
                username=self.player.username,
                password=self.PLAY_PASS)
        response = self.client.post(url, follow=True)
        self.client.logout()

        message = list(response.context.get('messages'))[0]

        self.assertEquals(message.message, 'Join request already sent to commissioner')
        self.assertEquals(1, len(self.season.joinrequest_set.all()))
        self.assertEquals(0, len(self.season.players.all()))

    def test_accept_request(self):
        request = JoinRequest.objects.create(
                season=self.season,
                player=self.player)

        url = reverse('accept-request', args=(request.id,))
        self.client.login(
                username=self.commissioner.username,
                password=self.COMM_PASS)
        self.client.post(url)
        self.client.logout()

        self.assertEquals(0, len(self.season.joinrequest_set.all()))
        self.assertIn(self.player, self.season.players.all())

    def test_accept_request_as_non_commissioner(self):
        request = JoinRequest.objects.create(
                season=self.season,
                player=self.player)

        url = reverse('accept-request', args=(request.id,))
        self.client.login(
                username=self.player.username,
                password=self.PLAY_PASS)
        response = self.client.post(url, follow=True)
        self.client.logout()

        message = list(response.context.get('messages'))[0]
        self.assertEquals(message.message, 'Only season Commissioner can approve/reject requests')
        self.assertEquals(1, len(self.season.joinrequest_set.all()))
        self.assertNotIn(self.player, self.season.players.all())

    def test_reject_request(self):
        request = JoinRequest.objects.create(
                season=self.season,
                player=self.player)

        url = reverse('reject-request', args=(request.id,))
        self.client.login(
                username=self.commissioner.username,
                password=self.COMM_PASS)
        self.client.post(url)
        self.client.logout()

        self.assertEquals(0, len(self.season.joinrequest_set.all()))
        self.assertNotIn(self.player, self.season.players.all())

    def test_manage_joinrequests(self):
        request = JoinRequest.objects.create(
                season=self.season,
                player=self.player)

        url = reverse('manage-requests', args=(request.id,))
        self.client.login(
                username=self.commissioner.username,
                password=self.COMM_PASS)
        response = self.client.post(url)
        self.client.logout()

        self.assertIn(request.player.username, response.content)
        self.assertIn(str(request.id), response.content)
        
