# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import (
    BetContainer,
    Accumulator,
    BetPart,
    LongSpecialContainer,
    LongSpecial,
    LongSpecialResult,
    LongSpecialBet,
)

# Register your models here.
admin.site.register(BetContainer)
admin.site.register(Accumulator)
admin.site.register(BetPart)
admin.site.register(LongSpecialContainer)
admin.site.register(LongSpecial)
admin.site.register(LongSpecialResult)
admin.site.register(LongSpecialBet)
