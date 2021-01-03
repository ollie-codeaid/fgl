# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Balance, Game, Gameweek, Result, Season

# Register your models here.
admin.site.register(Season)
admin.site.register(Gameweek)
admin.site.register(Balance)
admin.site.register(Game)
admin.site.register(Result)
