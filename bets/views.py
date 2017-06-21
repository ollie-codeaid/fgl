# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic import CreateView

from .models import Season, Gameweek
from .forms import GameweekForm, GameFormSet

# Create your views here.
def index(request):
    season_list = Season.objects.all()
    context = {'season_list': season_list}
    return render(request, 'bets/index.html', context)

def season(request, season_id):
    season = get_object_or_404(Season, pk=season_id)
    context = {'season': season}
    return render(request, 'bets/season.html', context)

def gameweek(request, gameweek_id):
    gameweek = get_object_or_404(Gameweek, pk=gameweek_id)
    context = {'gameweek': gameweek}
    return render(request, 'bets/gameweek.html', context)

def create_gameweek(request, season_id):
    if request.method == 'POST':
        if 'add_game' in request.POST:
            copy = request.POST.copy()
            copy['game_set-TOTAL_FORMS'] = int(copy['game_set-TOTAL_FORMS']) + 1
            game_set = GameFormSet(copy, prefix='game_set')
        else:
            game_set = GameFormSet(request.POST)
        form = GameweekForm(request.POST)
    else:
        form = GameweekForm()
        game_set = GameFormSet(prefix='game_set')
    context = { 'form': form, 
            'game_set': game_set}
    return render(request, 'bets/create_gameweek.html', context)
