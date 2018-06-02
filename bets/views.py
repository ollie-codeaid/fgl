# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import IntegrityError, transaction
from django.forms.formsets import formset_factory
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.functional import curry
from .models import (Season, JoinRequest, Gameweek, Game, Result,
                     BetContainer, Accumulator, BetPart)
from .forms import (SeasonForm, FindSeasonForm, GameweekForm, GameForm,
                    BaseGameFormSet, ResultForm, BaseResultFormSet,
                    AccumulatorForm, BetPartForm)


# Create your views here.
def index(request):
    season_list = Season.objects.all()

    user_season_list = []
    for season in season_list:
        if request.user in season.players.all():
            user_season_list.append(season)
    context = {'season_list': user_season_list}
    return render(request, 'bets/index.html', context)


def season(request, season_id):
    season = get_object_or_404(Season, pk=season_id)
    context = {'season': season}
    return render(request, 'bets/season.html', context)


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


def create_season(request):
    if request.method == 'POST':
        season_form = SeasonForm(request.POST)

        if season_form.is_valid() and request.user.is_authenticated():
            with transaction.atomic():
                season = Season(
                    commissioner=request.user,
                    name=season_form.cleaned_data.get('name'),
                    weekly_allowance=season_form.cleaned_data.get('weekly_allowance'),
                    public=season_form.cleaned_data.get('public'))
                season.save()

                season.players.add(request.user)
                season.save()

            return redirect('season', season_id=season.id)
        else:
            messages.error(request, 'Invalid form or unauthenticated user.')

    season_form = SeasonForm(request.POST)

    context = {
        'season_form': season_form,
    }

    return render(request, 'bets/create_season.html', context)


def join_season(request, season_id):
    season = get_object_or_404(Season, pk=season_id)

    if not request.user.is_authenticated():
        messages.error(request, 'Must be logged in to join season')
    elif request.user in season.players.all():
        messages.error(request, 'Already joined season')
    elif len(season.joinrequest_set.filter(player=request.user)) == 1:
        messages.error(request, 'Join request already sent to commissioner')
    elif season.public:
        season.players.add(request.user)
        season.save()
        messages.success(request, 'Added to season.')
    else:
        join_request = JoinRequest(season=season, player=request.user)
        join_request.save()
        messages.success(request, 'Join request sent to commissioner')
    return redirect('season', season_id=season.id)


def manage_joinrequests(request, season_id):
    season = get_object_or_404(Season, pk=season_id)
    return render(request, 'bets/manage_requests.html', {'season': season})


def _manage_joinrequest(request, joinrequest_id, accept):
    joinrequest = get_object_or_404(JoinRequest, pk=joinrequest_id)
    season = joinrequest.season
    if request.user != season.commissioner:
        messages.error(request,
                       'Only season Commissioner can approve/reject requests')
        return redirect(reverse('manage-requests', args=(season.id,)))

    player = joinrequest.player
    action = 'accept' if accept else 'reject'

    try:
        with transaction.atomic():
            if accept:
                season.players.add(player)
                season.save()
            joinrequest.delete()
    except IntegrityError as err:
        messages.error(request, 'Error {0}ing request'.format(action))
        messages.error(request, err)
        return redirect(reverse('manage-requests', args=(season.id,)))

    messages.success(
        request,
        '{0}\'s request {1}ed'.format(player.username, action))
    return redirect(reverse('manage-requests', args=(season.id,)))


def accept_joinrequest(request, joinrequest_id):
    return _manage_joinrequest(request, joinrequest_id, True)


def reject_joinrequest(request, joinrequest_id):
    return _manage_joinrequest(request, joinrequest_id, False)


def gameweek(request, gameweek_id):
    gameweek = get_object_or_404(Gameweek, pk=gameweek_id)
    context = {'gameweek': gameweek}
    return render(request, 'bets/gameweek.html', context)


def _process_new_games(game_formset, gameweek, request):

    if gameweek.has_bets():
        messages.error(
            request,
            ('Cannot update gameweek that already has bets,'
             ' speak to Ollie if required'))
        return redirect('gameweek', gameweek_id=gameweek.id)

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


def _manage_gameweek(request, gameweek, season):
    is_new_gameweek = gameweek is None

    if is_new_gameweek:
        GameFormSet = formset_factory(GameForm, formset=BaseGameFormSet)
    else:
        GameFormSet = formset_factory(GameForm,
                                      formset=BaseGameFormSet,
                                      extra=0)

    if (request.method == 'POST'
            and request.user.is_authenticated
            and request.user == season.commissioner):
        gameweek_form = GameweekForm(request.POST)
        game_formset = GameFormSet(request.POST)

        if gameweek_form.is_valid() and game_formset.is_valid():
            if is_new_gameweek:
                gameweek = Gameweek(
                    season=season,
                    number=season.get_next_gameweek_id(),
                    deadline_date=gameweek_form.cleaned_data.get('deadline_date'),
                    deadline_time=gameweek_form.cleaned_data.get('deadline_time'),
                    spiel=gameweek_form.cleaned_data.get('spiel'))
            else:
                gameweek.deadline_date = gameweek_form.cleaned_data.get('deadline_date')
                gameweek.deadline_time = gameweek_form.cleaned_data.get('deadline_time')
                gameweek.spiel = gameweek_form.cleaned_data.get('spiel')
            gameweek.save()

            _process_new_games(game_formset, gameweek, request)
            return redirect('gameweek', gameweek_id=gameweek.id)
        else:
            messages.error(request, 'Invalid form')

    if not (request.user.is_authenticated()
            and request.user == season.commissioner):
        messages.error(
            request,
            ('Only season commissioner ({0}) allowed to '
                'create or update gameweek').format(
                    season.commissioner.username))

    if is_new_gameweek:
        gameweek_form = GameweekForm()
        game_formset = GameFormSet()
    else:
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

        gameweek_form = GameweekForm(
                initial={'deadline_date': gameweek.deadline_date,
                         'deadline_time': gameweek.deadline_time,
                         'spiel': gameweek.spiel})
        game_formset = GameFormSet(initial=current_games)

    context = {
        'season_id': season.id,
        'gameweek_form': gameweek_form,
        'game_formset': game_formset
    }

    return render(request, 'bets/create_gameweek.html', context)


def create_gameweek(request, season_id):
    season = get_object_or_404(Season, pk=season_id)

    return _manage_gameweek(request, None, season)


def update_gameweek(request, gameweek_id):
    gameweek = get_object_or_404(Gameweek, pk=gameweek_id)
    season = gameweek.season

    return _manage_gameweek(request, gameweek, season)


def add_gameweek_results(request, gameweek_id):
    gameweek = get_object_or_404(Gameweek, pk=gameweek_id)
    ResultFormSet = formset_factory(ResultForm,
                                    formset=BaseResultFormSet,
                                    extra=0)
    ResultFormSet.form = staticmethod(curry(ResultForm, gameweek=gameweek))

    if (request.method == 'POST'
            and request.user.is_authenticated()
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


def manage_bet_container(request, gameweek_id):
    gameweek = get_object_or_404(Gameweek, pk=gameweek_id)
    owner = request.user

    gameweek_bets = gameweek.betcontainer_set.all()
    user_bets = gameweek_bets.filter(owner=owner)

    if len(user_bets) > 1:
        messages.error(
            request,
            'Error on bet creation, user already has bets.')
        return redirect('gameweek', gameweek_id=gameweek.id)
    elif len(user_bets) == 1:
        bet_container = user_bets.first()
    else:
        bet_container = BetContainer(gameweek=gameweek, owner=owner)
        bet_container.save()

    return redirect('bet-container', bet_container.pk)


def bet_container(request, bet_container_id):
    bet_container = get_object_or_404(BetContainer, pk=bet_container_id)
    context = {'bet_container': bet_container}
    return render(request, 'bets/bet_container.html', context)


def _manage_accumulator(request, accumulator, bet_container):
    gameweek = bet_container.gameweek
    is_new_bet = accumulator is None

    if is_new_bet:
        BetPartFormSet = formset_factory(
            BetPartForm,
            formset=BaseResultFormSet,
            extra=1)
    else:
        BetPartFormSet = formset_factory(
            BetPartForm,
            formset=BaseResultFormSet,
            extra=0)
    BetPartFormSet.form = staticmethod(curry(BetPartForm, gameweek=gameweek))

    if (request.method == 'POST'
            and request.user.is_authenticated()
            and request.user == bet_container.owner):
        accumulator_form = AccumulatorForm(request.POST)
        betpart_formset = BetPartFormSet(request.POST)

        if accumulator_form.is_valid() and betpart_formset.is_valid():
            for betpart_form in betpart_formset:
                if betpart_form.cleaned_data.get('game') is None:
                    messages.error(request, 'Game missing from selection.')
                    return redirect(
                        'add-bet',
                        bet_container_id=bet_container.id)

            if is_new_bet:
                old_stake = 0.0
            else:
                old_stake = float(accumulator.stake)
            stake = accumulator_form.cleaned_data.get('stake')
            full = float(bet_container.get_allowance())
            used = float(bet_container.get_allowance_used())
            remaining_allowance = full - used + old_stake

            if float(stake) > remaining_allowance:
                messages.error(
                    request,
                    'Stake greater than remaining allowance: {0}'.format(
                        remaining_allowance))
                return redirect('add-bet', bet_container_id=bet_container.id)

            if is_new_bet:
                accumulator = Accumulator(
                    bet_container=bet_container,
                    stake=stake)
            else:
                accumulator.stake = stake
            accumulator.save()

            new_betparts = []

            for betpart_form in betpart_formset:
                game = betpart_form.cleaned_data.get('game')
                result = betpart_form.cleaned_data.get('result')

                new_betparts.append(BetPart(
                    accumulator=accumulator,
                    game=game,
                    result=result))

            try:
                with transaction.atomic():
                    if not is_new_bet:
                        BetPart.objects.filter(
                            accumulator=accumulator).delete()
                    BetPart.objects.bulk_create(
                        new_betparts)

                messages.success(request, 'Bet created.')
                return redirect(
                    'bet-container',
                    bet_container_id=bet_container.id)

            except IntegrityError as err:
                messages.error(request, 'Error saving bet.')
                messages.error(request, err)
        else:
            messages.error(request, 'Invalid bet.')

    if not (request.user.is_authenticated()
            and request.user == bet_container.owner):
        messages.error(
            request,
            ('Only bet owner ({0}) allowed to '
                'create or update bet').format(
                    bet_container.owner.username))

    if is_new_bet:
        accumulator_form = AccumulatorForm()
        betpart_formset = BetPartFormSet()
    else:
        current_betparts = [
            {
                'game': bp.game,
                'result': bp.result
            } for bp in accumulator.betpart_set.all()]
        accumulator_form = AccumulatorForm(
            initial={'stake': accumulator.stake})
        betpart_formset = BetPartFormSet(initial=current_betparts)

    context = {
        'bet_container_id': bet_container.id,
        'accumulator_form': accumulator_form,
        'betpart_formset': betpart_formset
    }

    return render(request, 'bets/create_bet.html', context)


def add_bet(request, bet_container_id):
    bet_container = get_object_or_404(BetContainer, pk=bet_container_id)

    return _manage_accumulator(request, None, bet_container)


def update_bet(request, accumulator_id):
    accumulator = get_object_or_404(Accumulator, pk=accumulator_id)
    bet_container = accumulator.bet_container

    return _manage_accumulator(request, accumulator, bet_container)


def delete_bet(request, accumulator_id, bet_container_id):
    betcontainer = get_object_or_404(BetContainer, pk=bet_container_id)
    if (request.user.is_authenticated()
            and request.user == betcontainer.owner):
        Accumulator.objects.filter(pk=accumulator_id).delete()
        messages.success(request, 'Bet deleted')
    else:
        messages.error(
            request,
            ('Only bet owner ({0}) allowed '
                'to delete'.format(
                    betcontainer.owner.username)))
    return bet_container(request, bet_container_id)
