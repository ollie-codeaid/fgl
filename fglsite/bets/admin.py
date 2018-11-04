# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import (
    Season,
    Gameweek,
    Balance,
    Game,
    Result,
    BetContainer,
    Accumulator,
    BetPart,
    LongSpecialContainer,
    LongSpecial,
    LongSpecialResult,
    LongSpecialBet,
)

# Register your models here.
admin.site.register(Season)
admin.site.register(Gameweek)
admin.site.register(Balance)
admin.site.register(Game)
admin.site.register(Result)
admin.site.register(BetContainer)
admin.site.register(Accumulator)
admin.site.register(BetPart)
admin.site.register(LongSpecialContainer)
admin.site.register(LongSpecial)
admin.site.register(LongSpecialResult)
admin.site.register(LongSpecialBet)
