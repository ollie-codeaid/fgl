# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from functools import partial

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError, transaction
from django.forms.formsets import formset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import CreateView, DetailView, UpdateView
from django.urls import reverse, reverse_lazy

from fglsite.bets.models import Season, Gameweek, Game, Result
from fglsite.bets.forms import (
    SeasonForm,
    FindSeasonForm,
    GameweekForm,
    GameForm,
    BaseGameFormSet,
    ResultForm,
    BaseResultFormSet
)
from fglsite.odds_reader.reader import read_odds


class SeasonDetailView(DetailView):
    model = Season


class SeasonCreateView(LoginRequiredMixin, CreateView):
    model = Season
    form_class = SeasonForm

    def get_success_url(self):
        return reverse_lazy("season", args=[self.object.pk])

    def form_valid(self, form):
        self.object = Season.objects.create(
            commissioner=self.request.user,
            name=form.cleaned_data.get('name'),
            weekly_allowance=form.cleaned_data.get('weekly_allowance'),
            public=form.cleaned_data.get('public')
        )
        return HttpResponseRedirect(self.get_success_url())


def find_season(request):
    find_season_form = FindSeasonForm(request.GET)

    if find_season_form.is_valid():
        name = find_season_form.cleaned_data.get('name', '')
        commissioner = find_season_form.cleaned_data.get('commissioner', '')

        season_list = Season.objects.filter(
                name__contains=name).filter(
                        commissioner__username__contains=commissioner)
    else:
        find_season_form = FindSeasonForm()
        season_list = Season.objects.all()

    context = {'season_list': season_list,
               'find_season_form': find_season_form}

    return render(request, 'bets/find_season.html', context)


class GameweekDetailView(DetailView):
    model = Gameweek


class SeasonCommissionerAllowedMixin:
    def dispatch(self, request, *args, **kwargs):
        season = self.get_season(*args, **kwargs)
        if request.user != season.commissioner:
            return HttpResponseRedirect(
                reverse_lazy("season", args=[season.id])
            )

        return super().dispatch(request, *args, **kwargs)


def build_games_from_formset(gameweek, game_formset):
    return [
        Game(
            gameweek=gameweek,
            hometeam=game_form.cleaned_data.get('hometeam'),
            awayteam=game_form.cleaned_data.get('awayteam'),
            homenumerator=game_form.cleaned_data.get('homenumerator'),
            homedenominator=game_form.cleaned_data.get('homedenominator'),
            drawnumerator=game_form.cleaned_data.get('drawnumerator'),
            drawdenominator=game_form.cleaned_data.get('drawdenominator'),
            awaynumerator=game_form.cleaned_data.get('awaynumerator'),
            awaydenominator=game_form.cleaned_data.get('awaydenominator')
        ) for game_form in game_formset
    ]


class GameweekCreateView(SeasonCommissionerAllowedMixin, LoginRequiredMixin, CreateView):
    model = Gameweek
    form_class = GameweekForm
    formset_class = formset_factory(GameForm, formset=BaseGameFormSet)

    def get_success_url(self):
        return reverse_lazy("gameweek", args=[self.gameweek.pk])

    def get_season(self, season_id, *args, **kwargs):
        return get_object_or_404(Season, pk=season_id)

    def _build_formset(self):
        try:
            odds = read_odds()
        except Exception:
            odds = []

        for odd in odds:
            odd.pop("meta")
        return self.formset_class(initial=odds)

    def get_context_data(self, formset=None, **kwargs):
        context_data = super().get_context_data(**kwargs)

        if not formset:
            formset = self._build_formset()

        context_data.update({
            "game_formset": formset
        })
        return context_data

    def post(self, request, season_id, *args, **kwargs):
        gameweek_form = self.get_form()
        game_formset = self.formset_class(request.POST)
        season = get_object_or_404(Season, pk=season_id)

        if gameweek_form.is_valid() and game_formset.is_valid():
            return self.form_valid(season, gameweek_form, game_formset)
        else:
            self.object = None
            return self.form_invalid(gameweek_form, game_formset)

    def form_valid(self, season, form, formset):
        self.gameweek = Gameweek.objects.create(
            season=season,
            number=season.get_next_gameweek_id(),
            deadline_date=form.cleaned_data.get('deadline_date'),
            deadline_time=form.cleaned_data.get('deadline_time'),
            spiel=form.cleaned_data.get('spiel')
        )

        new_games = build_games_from_formset(gameweek=self.gameweek, game_formset=formset)

        try:
            with transaction.atomic():
                Game.objects.bulk_create(new_games)
                messages.success(self.request, 'Successfully created gameweek.')
        except Exception:
            messages.error(self.request, 'Something went wrong creating gameweek.')
            return HttpResponseRedirect(reverse('update-gameweek', args=[self.gameweek.id]))

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, formset):
        """If the form is invalid, render the invalid form."""
        return self.render_to_response(self.get_context_data(form=form, formset=formset))


class GameweekUpdateView(SeasonCommissionerAllowedMixin, LoginRequiredMixin, UpdateView):
    model = Gameweek
    form_class = GameweekForm
    formset_class = formset_factory(GameForm, formset=BaseGameFormSet, extra=0)

    def get_success_url(self):
        return reverse_lazy("gameweek", args=[self.get_object().pk])

    def get_season(self, *args, **kwargs):
        return self.get_object().season

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
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
        } for g in self.object.game_set.all()]

        context_data.update({
            "game_formset": self.formset_class(initial=current_games)
        })
        return context_data

    def post(self, request, *args, **kwargs):
        gameweek_form = self.get_form()
        game_formset = self.formset_class(request.POST)

        if self.get_object().has_bets():
            messages.error(
                request,
                ('Cannot update gameweek that already has bets,'
                 ' speak to Ollie if required')
            )
            return self.get_success_url()

        if gameweek_form.is_valid() and game_formset.is_valid():
            return self.form_valid(gameweek_form, game_formset)
        else:
            return self.form_invalid(gameweek_form)

    def form_valid(self, form, formset):
        gameweek = self.get_object()
        gameweek.deadline_date = form.cleaned_data.get('deadline_date')
        gameweek.deadline_time = form.cleaned_data.get('deadline_time')
        gameweek.spiel = form.cleaned_data.get('spiel')
        gameweek.save()

        new_games = build_games_from_formset(gameweek=gameweek, game_formset=formset)

        try:
            with transaction.atomic():
                Game.objects.filter(gameweek=gameweek).delete()
                Game.objects.bulk_create(new_games)
                messages.success(self.request, 'Successfully updated gameweek.')
        except Exception:
            messages.error(self.request, 'Something went wrong updating gameweek.')
            return HttpResponseRedirect(reverse('update-gameweek', args=[gameweek.id]))

        return HttpResponseRedirect(self.get_success_url())


def add_gameweek_results(request, gameweek_id):
    gameweek = get_object_or_404(Gameweek, pk=gameweek_id)
    ResultFormSet = formset_factory(ResultForm,
                                    formset=BaseResultFormSet,
                                    extra=0)
    ResultFormSet.form = staticmethod(partial(ResultForm, gameweek=gameweek))

    if (request.method == 'POST'
            and request.user.is_authenticated
            and request.user == gameweek.season.commissioner):
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

                    for betcontainer in gameweek.betcontainer_set.all():
                        gameweek.set_balance_by_user(
                            user=betcontainer.owner,
                            week_winnings=betcontainer.calc_winnings(),
                            week_unused=betcontainer.get_allowance_unused())

                    gameweek.update_no_bet_users()

                    return redirect('gameweek', gameweek_id=gameweek.id)

            except IntegrityError as err:
                messages.error(request, 'Error saving gameweek.')
                messages.error(request, err)
                return redirect(
                    'add-gameweek-results',
                    gameweek_id=gameweek.id)

    else:
        results = [{'game': g} for g in gameweek.game_set.all()]
        result_formset = ResultFormSet(initial=results)

    if not (request.user.is_authenticated
            and request.user == gameweek.season.commissioner):
        messages.error(
            request,
            ('Only season commissioner ({0}) allowed to '
                'add bet results').format(
                    season.commissioner.username))

    context = {
        'gameweek_id': gameweek_id,
        'result_formset': result_formset
    }

    return render(request, 'bets/add_gameweek_results.html', context)
