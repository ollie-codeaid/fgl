# -*- coding: utf-8 -*-
from django.test import TestCase
from django.urls import reverse


class ViewsTest(TestCase):
    def test_index(self):
        url = reverse("index")
        response = self.client.get(url)
        self.assertIn("What is a FGL?", response.content.decode())
