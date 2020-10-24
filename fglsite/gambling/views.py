# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from functools import partial

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.forms.formsets import formset_factory
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from fglsite.bets.forms import BaseResultFormSet
from fglsite.bets.models import Gameweek
from .models import (BetContainer, Accumulator, BetPart,
                     LongSpecialContainer, LongSpecial, LongSpecialBet)
from .forms import (AccumulatorForm, BetPartForm, LongSpecialContainerForm,
                    LongSpecialForm, BaseLongSpecialFormSet,
                    LongSpecialBetForm)


# Create your views here.
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
    return render(request, 'gambling/bet_container.html', context)


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
    BetPartFormSet.form = staticmethod(partial(BetPartForm, gameweek=gameweek))

    if (request.method == 'POST'
            and request.user.is_authenticated
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

    if not (request.user.is_authenticated
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

    return render(request, 'gambling/create_bet.html', context)


def add_bet(request, bet_container_id):
    bet_container = get_object_or_404(BetContainer, pk=bet_container_id)

    return _manage_accumulator(request, None, bet_container)


def update_bet(request, accumulator_id):
    accumulator = get_object_or_404(Accumulator, pk=accumulator_id)
    bet_container = accumulator.bet_container

    return _manage_accumulator(request, accumulator, bet_container)


def delete_bet(request, accumulator_id, bet_container_id):
    betcontainer = get_object_or_404(BetContainer, pk=bet_container_id)
    if (request.user.is_authenticated
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


def _process_new_specials(special_formset, container, request):

    if container.has_bets():
        messages.error(
            request,
            ('Cannot update specials that already have bets,'
             ' speak to Ollie if required'))
        return redirect('gameweek', gameweek_id=container.created_gameweek.id)

    new_specials = []

    for special_form in special_formset:
        description = special_form.cleaned_data.get('description')
        numerator = special_form.cleaned_data.get('numerator')
        denominator = special_form.cleaned_data.get('denominator')

        new_specials.append(LongSpecial(
            container=container,
            description=description,
            numerator=numerator,
            denominator=denominator))

    try:
        with transaction.atomic():
            LongSpecial.objects.filter(container=container).delete()
            LongSpecial.objects.bulk_create(new_specials)

            messages.success(
                    request, 'Successfully created long term special.')

    except IntegrityError as err:
        messages.error(request, 'Error saving long term special.')
        messages.error(request, err)
        return redirect(reverse('update-longterm', args=(container.id)))


def _manage_longterm(request, container, gameweek):
    is_new_container = container is None

    if is_new_container:
        LongSpecialFormSet = formset_factory(
                LongSpecialForm,
                formset=BaseLongSpecialFormSet)
    else:
        LongSpecialFormSet = formset_factory(
                LongSpecialForm,
                formset=BaseLongSpecialFormSet,
                extra=0)

    if (request.method == 'POST'
            and request.user.is_authenticated
            and request.user == gameweek.season.commissioner):
        container_form = LongSpecialContainerForm(request.POST)
        long_special_formset = LongSpecialFormSet(request.POST)

        if container_form.is_valid() and long_special_formset.is_valid():
            if is_new_container:
                container = LongSpecialContainer(
                        description=container_form.cleaned_data.get('description'),
                        allowance=container_form.cleaned_data.get('allowance'),
                        created_gameweek=gameweek)
            else:
                container.description = container_form.cleaned_data.get('description')
                container.allowance = container_form.cleaned_data.get('allowance')
            container.save()

            _process_new_specials(long_special_formset, container, request)
            return redirect('gameweek', gameweek_id=gameweek.id)
        else:
            messages.error(request, 'Invalid form')

    if not (request.user.is_authenticated
            and request.user == gameweek.season.commissioner):
        messages.error(
            request,
            ('Only season commissioner ({0}) allowed to '
                'create or update gameweek').format(
                    gameweek.season.commissioner.username))

    if is_new_container:
        container_form = LongSpecialContainerForm()
        long_special_formset = LongSpecialFormSet()
    else:
        current_long_specials = [{
            'container': ls.container,
            'description': ls.description,
            'numerator': ls.numerator,
            'denominator': ls.denominator,
            } for ls in container.longspecial_set.all()]

        container_form = LongSpecialContainerForm(
                initial={
                    'description': container.description,
                    'allowance': container.allowance,
                    'created_gameweek': gameweek
                    })
        long_special_formset = LongSpecialFormSet(initial=current_long_specials)

    context = {
        'gameweek_id': gameweek.id,
        'container_form': container_form,
        'long_special_formset': long_special_formset
    }

    return render(request, 'gambling/create_long_term.html', context)


def create_longterm(request, gameweek_id):
    gameweek = get_object_or_404(Gameweek, pk=gameweek_id)

    return _manage_longterm(request, None, gameweek)


def update_longterm(request, longspecial_id):
    container = get_object_or_404(LongSpecialContainer, pk=longspecial_id)
    gameweek = container.created_gameweek

    return _manage_longterm(request, container, gameweek)


def manage_longterm_bet(request, bet_container_id, longspecial_id):
    existing_bet = LongSpecialBet.objects.filter(
                bet_container=bet_container_id
            ).filter(
                long_special__container=longspecial_id
            ).first()

    return _manage_longterm_bet(
            request,
            bet_container_id,
            longspecial_id,
            existing_bet)


def _manage_longterm_bet(
        request,
        bet_container_id,
        longspecial_id,
        existing_bet):
    bet_container = get_object_or_404(BetContainer, pk=bet_container_id)
    container = get_object_or_404(
            LongSpecialContainer,
            pk=longspecial_id)

    if request.method == 'POST':
        form = LongSpecialBetForm(
                longspecial_id,
                request.POST)

        if form.is_valid() and request.user.is_authenticated:
            if existing_bet:
                bet = existing_bet
                bet.long_special = form.cleaned_data.get('long_special')
            else:
                bet = LongSpecialBet(
                        long_special=form.cleaned_data.get('long_special'),
                        bet_container=bet_container)
            bet.save()

            return redirect(
                    'gameweek',
                    gameweek_id=container.created_gameweek.id
                    )
        else:
            messages.error(request, 'Invalid form or unauthenticated user.')

    initial = {}

    if existing_bet:
        initial = {
                'long_special': existing_bet.long_special,
                }

    form = LongSpecialBetForm(
            longspecial_id,
            initial=initial)

    context = {
        'special_form': form,
        'container': container,
    }

    return render(request, 'gambling/create_long_term_bet.html', context)
