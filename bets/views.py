# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Season, Gameweek

# Create your views here.
def index(request):
    season_list = Season.objects.all()
    context = {'season_list': season_list}
    return render(request, 'bets/index.html', context)

def season(request, season_id):
    season = get_object_or_404(Season, pk=season_id)
    gameweek_list = season.gameweek_set.all()
    context = {'gameweek_list': gameweek_list}
    return render(request, 'bets/season.html', context)
