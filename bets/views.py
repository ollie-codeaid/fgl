# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic import CreateView

from .models import Season, Gameweek
from .forms import GameweekForm, GameweekGameFormSet

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
        form = GameweekForm(request.POST)
        formset = GameweekGameFormSet(request.POST)
    else:
        form = GameweekForm(request.POST)
        formset = GameweekGameFormSet()
    context = { 'form': form, 
            'formset': formset}
    return render(request, 'bets/create_gameweek.html', context)
