# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import (
    Accumulator,
    BetContainer,
    BetPart,
    LongSpecial,
    LongSpecialBet,
    LongSpecialContainer,
    LongSpecialResult,
)

# Register your models here.
admin.site.register(BetContainer)
admin.site.register(Accumulator)
admin.site.register(BetPart)
admin.site.register(LongSpecialContainer)
admin.site.register(LongSpecial)
admin.site.register(LongSpecialResult)
admin.site.register(LongSpecialBet)
