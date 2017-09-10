# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse_lazy, reverse
from django.db import IntegrityError, transaction
from django.forms.formsets import formset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import CreateView, UpdateView
from .models import Season, Gameweek, Game
from .forms import GameweekForm, GameForm, BaseGameFormSet

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
    gameweek_form = GameweekForm()
    GameFormSet =formset_factory(GameForm, formset=BaseGameFormSet)

    if request.method == 'POST':
        gameweek_form = GameweekForm(request.POST)
        game_formset = GameFormSet(request.POST)

        if gameweek_form.is_valid() and game_formset.is_valid():
            season = get_object_or_404(Season, pk=season_id)
            deadline = gameweek_form.cleaned_data.get('deadline')
            gameweek = Gameweek(season=season, number=0, deadline=deadline)
            gameweek.save()

            new_games = []

            for game_form in game_formset:
                home = game_form.cleaned_data.get('hometeam')
                away = game_form.cleaned_data.get('awayteam')
                homenumerator = game_form.cleaned_data.get('homenumerator')
                homedenominator = game_form.cleaned_data.get('homedenominator')
                drawnumerator = game_form.cleaned_data.get('drawnumerator')
                drawdenominator = game_form.cleaned_data.get('drawdenominator')
                awaynumerator = game_form.cleaned_data.get('awaynumerator')
                awaydenominator = game_form.cleaned_data.get('awaydenominator')

                new_games.append(Game(
                    gameweek=gameweek,
                    hometeam=home, awayteam=away,
                    homenumerator=homenumerator, homedenominator=homedenominator,
                    drawnumerator=drawnumerator, drawdenominator=drawdenominator,
                    awaynumerator=awaynumerator, awaydenominator=awaydenominator))

            try:
                with transaction.atomic():
                    Game.objects.filter(gameweek=gameweek).delete()
                    Game.objects.bulk_create(new_games)

                    messages.success(request, 'Successfully created gameweek.')

            except IntegrityError as err:
                messages.error(request, 'Error saving gameweek.')
                messages.error(request, err)
                return redirect(reverse('create-gameweek', args=(season_id)))

    else:
        gameweek_form = GameweekForm()
        game_formset = GameFormSet()

    context = {
        'gameweek_form': gameweek_form,
        'game_formset': game_formset
    }

    return render(request, 'bets/create_gameweek.html', context)





#def create_gameweek(request, season_id):
#   form = GameweekForm()
#   game_set = GameFormSet(prefix='game_set')
#   
#   if request.method == 'POST':
#       if 'add_game' in request.POST:
#           form = GameweekForm(request.POST)
#           copy = request.POST.copy()
#           copy['game_set-TOTAL_FORMS'] = int(copy['game_set-TOTAL_FORMS']) + 1
#           game_set = GameFormSet(copy, prefix='game_set')
#       else:
#           form = GameweekForm(request.POST, season_id=season_id)
#           game_set = GameFormSet(request.POST)
#           if not 'remove_games' in request.POST:
#               if form.is_valid() and game_set.is_valid():
#                   form.save()
#                   game_set.save()
#                  season = get_object_or_404(Season, pk=season_id)
#                  context = {'season': season}
#                   return render(request, 'bets/season.html', context)
#   
#   context = { 'form': form, 
#           'game_set': game_set}
#   return render(request, 'bets/create_gameweek.html', context)
