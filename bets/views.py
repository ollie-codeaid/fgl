# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse_lazy, reverse
from django.db import IntegrityError, transaction
from django.forms.formsets import formset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import CreateView, UpdateView
from .models import Season, Gameweek, Game, Result
from .forms import GameweekForm, GameForm, BaseGameFormSet, ResultForm, BaseResultFormSet

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

def _process_new_games(game_formset, gameweek, request):

    if gameweek.has_bets():
        messages.error(request, 'Cannot update gameweek that already has bets, speak to Ollie if required')
        return redirect(reverse('update-gameweek', args=(gameweek.id)))
    
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
        return redirect(reverse('update-gameweek', args=(gameweek.id)))
    

def create_gameweek(request, season_id):
    gameweek_form = GameweekForm()
    GameFormSet =formset_factory(GameForm, formset=BaseGameFormSet)

    if request.method == 'POST':
        gameweek_form = GameweekForm(request.POST)
        game_formset = GameFormSet(request.POST)

        if gameweek_form.is_valid() and game_formset.is_valid():
            season = get_object_or_404(Season, pk=season_id)
            gameweek_number = season.get_next_gameweek_id()
            deadline = gameweek_form.cleaned_data.get('deadline')
            gameweek = Gameweek(season=season, number=gameweek_number, deadline=deadline)
            gameweek.save()
            
            _process_new_games(game_formset, gameweek, request)

    else:
        gameweek_form = GameweekForm()
        game_formset = GameFormSet()

    context = {
        'season_id': season_id,
        'gameweek_form': gameweek_form,
        'game_formset': game_formset
    }

    return render(request, 'bets/create_gameweek.html', context)


def update_gameweek(request, gameweek_id):
    gameweek = get_object_or_404(Gameweek, pk=gameweek_id)
    season = gameweek.season
    
    GameFormSet =formset_factory(GameForm, formset=BaseGameFormSet)

    current_games = [{
        'gameweek': g.gameweek,
        'hometeam': g.hometeam,
        'awayteam': g.awayteam,
        'homenumerator': g.homenumerator,
        'homedenominator': g.homedenominator,
        'drawnumerator': g.drawnumerator,
        'drawdenominator': g.drawdenominator,
        'awaynumerator': g.awaynumerator,
        'awaydenominator': g.awaydenominator
        } for g in gameweek.game_set.all()]

    if request.method == 'POST':
        gameweek_form = GameweekForm(request.POST)
        game_formset = GameFormSet(request.POST)

        if gameweek_form.is_valid() and game_formset.is_valid():
            gameweek.deadline = gameweek_form.cleaned_data.get('deadline')
            gameweek.save()

            _process_new_games(game_formset, gameweek, request)

    else:
        gameweek_form = GameweekForm(initial={'deadline': gameweek.deadline})
        game_formset = GameFormSet(initial=current_games)

    context = {
        'season_id': season.id,
        'gameweek_form': gameweek_form,
        'game_formset': game_formset
    }

    return render(request, 'bets/create_gameweek.html', context)


def add_gameweek_results(request, gameweek_id): 
    gameweek = get_object_or_404(Gameweek, pk=gameweek_id)
    ResultFormSet = formset_factory(ResultForm, formset=BaseResultFormSet, extra=0)

    if request.method == 'POST':
        result_formset = ResultFormSet(request.POST)
        if result_formset.is_valid():
            results = []
            for result_form in result_formset:
                game = result_form.cleaned_data.get('game')
                result = result_form.cleaned_data.get('result')

                results.append(Result(game=game, result=result))

            try:
                with transaction.atomic():
                    for game in gameweek.game_set.all():
                        Result.objects.filter(game=game).delete()
                    Result.objects.bulk_create(results)

                    messages.success(request, 'Successfully created gameweek.')
                    return redirect('gameweek', gameweek_id=gameweek.id)

            except IntegrityError as err:
                messages.error(request, 'Error saving gameweek.')
                messages.error(request, err)
                return redirect('add-gameweek-results', gameweek_id=gameweek.id)

    else:
        results = [{ 'game': g } for g in gameweek.game_set.all()]
        result_formset = ResultFormSet(initial=results)

    context = {
        'gameweek_id': gameweek_id,
        'result_formset': result_formset
    }

    return render(request, 'bets/add_gameweek_results.html', context)
