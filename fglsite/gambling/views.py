# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from functools import partial

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError, transaction
from django.forms.formsets import formset_factory
from django.http import HttpResponseForbidden
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from fglsite.bets.forms import BaseResultFormSet
from fglsite.bets.models import Gameweek
from .models import (
    BetContainer,
    Accumulator,
    BetPart,
    LongSpecialContainer,
    LongSpecial,
    LongSpecialBet,
)
from .forms import (
    AccumulatorForm,
    BetContainerForm,
    BetPartForm,
    LongSpecialContainerForm,
    LongSpecialForm,
    BaseLongSpecialFormSet,
    LongSpecialBetForm,
)


class BetContainerCreateView(LoginRequiredMixin, CreateView):
    model = BetContainer
    form_class = BetContainerForm

    def dispatch(self, request, gameweek_id, *args, **kwargs):
        self.gameweek = get_object_or_404(Gameweek, pk=gameweek_id)
        user_bets = self.gameweek.betcontainer_set.filter(owner=request.user)

        if len(user_bets) == 0:
            return super().dispatch(request, gameweek_id, *args, **kwargs)
        else:
            return redirect("update-bet-container", user_bets.first().pk)

    def get_success_url(self):
        return reverse_lazy("update-bet-container", args=[self.object.pk])

    def get_form_kwargs(self):
        return {
            "data": {
                "gameweek": self.gameweek.id,
                "owner": self.request.user.id
            }
        }

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class BetContainerOwnerAllowedMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user != self.bet_container.owner:
            return HttpResponseForbidden()

        return super().dispatch(request, *args, **kwargs)


class BetContainerDetailView(BetContainerOwnerAllowedMixin, LoginRequiredMixin, DetailView):
    model = BetContainer

    def dispatch(self, request, pk, *args, **kwargs):
        self.bet_container = get_object_or_404(BetContainer, pk=pk)
        return super().dispatch(request, pk, *args, **kwargs)


class AccumulatorView(BetContainerOwnerAllowedMixin, LoginRequiredMixin):
    model = Accumulator
    form_class = AccumulatorForm
    formset_class = formset_factory(
        BetPartForm,
        formset=BaseResultFormSet
    )

    def get_success_url(self):
        return reverse_lazy("update-bet-container", args=[self.bet_container.pk])

    def get_formset(self):
        self.formset_class.form = staticmethod(
            partial(BetPartForm, gameweek=self.bet_container.gameweek)
        )
        if self.request.POST:
            return self.formset_class(self.request.POST)
        else:
            self.formset_class.extra = self.extra
            return self.formset_class(initial=self.get_formset_initial())

    def get_formset_initial(self):
        return []

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data.update({
            "betpart_formset": self.get_formset(),
            "bet_container": self.bet_container
        })
        return context_data

    def dispatch(self, request, bet_container_id, *args, **kwargs):
        self.bet_container = get_object_or_404(BetContainer, pk=bet_container_id)
        return super().dispatch(request, bet_container_id, *args, **kwargs)

    def get_initial_stake(self):
        return 0

    def post(self, *args, **kwargs):
        accumulator_form = self.get_form()
        bet_formset = self.get_formset()

        if accumulator_form.is_valid(initial_stake=self.get_initial_stake()) and bet_formset.is_valid():
            return self.form_valid(accumulator_form, bet_formset)
        else:
            self.object = None
            return self.form_invalid(accumulator_form, bet_formset)

    def form_valid(self, form, formset):
        accumulator = self.save_accumulator(form)

        new_betparts = [
            BetPart(
                accumulator=accumulator,
                game=betpart_form.cleaned_data.get("game"),
                result=betpart_form.cleaned_data.get("result"),
            ) for betpart_form in formset.forms
        ]

        try:
            with transaction.atomic():
                self.clear_existing_betparts(accumulator)
                BetPart.objects.bulk_create(new_betparts)
                messages.success(self.request, self.success_message)
        except Exception as err:
            messages.error(self.request, "Error saving bet.")
            messages.error(self.request, err)

        return redirect(self.get_success_url())

    def clear_existing_betparts(self, accumulator):
        # Do nothing
        return

    def form_invalid(self, form, formset):
        """If the form is invalid, render the invalid form."""
        return self.render_to_response(
            self.get_context_data(form=form, formset=formset)
        )


class AccumulatorCreateView(AccumulatorView, CreateView):
    extra = 1
    success_message = "Created bet."

    def get_initial(self):
        return {
            "bet_container": self.bet_container
        }

    def save_accumulator(self, form):
        return Accumulator.objects.create(
            bet_container=self.bet_container,
            stake=form.cleaned_data.get("stake")
        )


class AccumulatorUpdateView(AccumulatorView, UpdateView):
    extra = 0
    success_message = "Updated bet."

    def get_formset_initial(self):
        return [
            {"game": bp.game, "result": bp.result}
            for bp in self.get_object().betpart_set.all()
        ]

    def dispatch(self, request, pk, *args, **kwargs):
        accumulator = get_object_or_404(Accumulator, pk=pk)
        return super().dispatch(request, accumulator.bet_container.id, *args, **kwargs)

    def get_initial_stake(self):
        return self.get_object().stake

    def save_accumulator(self, form):
        accumulator = self.get_object()
        accumulator.stake = form.cleaned_data.get("stake")
        accumulator.save()
        return accumulator

    def clear_existing_betparts(self, accumulator):
        BetPart.objects.filter(accumulator=accumulator).delete()


class AccumulatorDeleteView(BetContainerOwnerAllowedMixin, LoginRequiredMixin, DeleteView):
    model = Accumulator

    def dispatch(self, request, pk, *args, **kwargs):
        self.bet_container = get_object_or_404(Accumulator, pk=pk).bet_container
        return super().dispatch(request, pk, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy("update-bet-container", args=[self.bet_container.pk])


def _process_new_specials(special_formset, container, request):

    if container.has_bets():
        messages.error(
            request,
            (
                "Cannot update specials that already have bets,"
                " speak to Ollie if required"
            ),
        )
        return redirect("gameweek", gameweek_id=container.created_gameweek.id)

    new_specials = []

    for special_form in special_formset:
        description = special_form.cleaned_data.get("description")
        numerator = special_form.cleaned_data.get("numerator")
        denominator = special_form.cleaned_data.get("denominator")

        new_specials.append(
            LongSpecial(
                container=container,
                description=description,
                numerator=numerator,
                denominator=denominator,
            )
        )

    try:
        with transaction.atomic():
            LongSpecial.objects.filter(container=container).delete()
            LongSpecial.objects.bulk_create(new_specials)

            messages.success(request, "Successfully created long term special.")

    except IntegrityError as err:
        messages.error(request, "Error saving long term special.")
        messages.error(request, err)
        return redirect(reverse("update-longterm", args=(container.id)))


def _manage_longterm(request, container, gameweek):
    is_new_container = container is None

    if is_new_container:
        LongSpecialFormSet = formset_factory(
            LongSpecialForm, formset=BaseLongSpecialFormSet
        )
    else:
        LongSpecialFormSet = formset_factory(
            LongSpecialForm, formset=BaseLongSpecialFormSet, extra=0
        )

    if (
        request.method == "POST"
        and request.user.is_authenticated
        and request.user == gameweek.season.commissioner
    ):
        container_form = LongSpecialContainerForm(request.POST)
        long_special_formset = LongSpecialFormSet(request.POST)

        if container_form.is_valid() and long_special_formset.is_valid():
            if is_new_container:
                container = LongSpecialContainer(
                    description=container_form.cleaned_data.get("description"),
                    allowance=container_form.cleaned_data.get("allowance"),
                    created_gameweek=gameweek,
                )
            else:
                container.description = container_form.cleaned_data.get("description")
                container.allowance = container_form.cleaned_data.get("allowance")
            container.save()

            _process_new_specials(long_special_formset, container, request)
            return redirect("gameweek", gameweek_id=gameweek.id)
        else:
            messages.error(request, "Invalid form")

    if not (
        request.user.is_authenticated and request.user == gameweek.season.commissioner
    ):
        messages.error(
            request,
            (
                "Only season commissioner ({0}) allowed to " "create or update gameweek"
            ).format(gameweek.season.commissioner.username),
        )

    if is_new_container:
        container_form = LongSpecialContainerForm()
        long_special_formset = LongSpecialFormSet()
    else:
        current_long_specials = [
            {
                "container": ls.container,
                "description": ls.description,
                "numerator": ls.numerator,
                "denominator": ls.denominator,
            }
            for ls in container.longspecial_set.all()
        ]

        container_form = LongSpecialContainerForm(
            initial={
                "description": container.description,
                "allowance": container.allowance,
                "created_gameweek": gameweek,
            }
        )
        long_special_formset = LongSpecialFormSet(initial=current_long_specials)

    context = {
        "gameweek_id": gameweek.id,
        "container_form": container_form,
        "long_special_formset": long_special_formset,
    }

    return render(request, "gambling/create_long_term.html", context)


def create_longterm(request, gameweek_id):
    gameweek = get_object_or_404(Gameweek, pk=gameweek_id)

    return _manage_longterm(request, None, gameweek)


def update_longterm(request, longspecial_id):
    container = get_object_or_404(LongSpecialContainer, pk=longspecial_id)
    gameweek = container.created_gameweek

    return _manage_longterm(request, container, gameweek)


def manage_longterm_bet(request, bet_container_id, longspecial_id):
    existing_bet = (
        LongSpecialBet.objects.filter(bet_container=bet_container_id)
        .filter(long_special__container=longspecial_id)
        .first()
    )

    return _manage_longterm_bet(request, bet_container_id, longspecial_id, existing_bet)


def _manage_longterm_bet(request, bet_container_id, longspecial_id, existing_bet):
    bet_container = get_object_or_404(BetContainer, pk=bet_container_id)
    container = get_object_or_404(LongSpecialContainer, pk=longspecial_id)

    if request.method == "POST":
        form = LongSpecialBetForm(longspecial_id, request.POST)

        if form.is_valid() and request.user.is_authenticated:
            if existing_bet:
                bet = existing_bet
                bet.long_special = form.cleaned_data.get("long_special")
            else:
                bet = LongSpecialBet(
                    long_special=form.cleaned_data.get("long_special"),
                    bet_container=bet_container,
                )
            bet.save()

            return redirect("gameweek", gameweek_id=container.created_gameweek.id)
        else:
            messages.error(request, "Invalid form or unauthenticated user.")

    initial = {}

    if existing_bet:
        initial = {
            "long_special": existing_bet.long_special,
        }

    form = LongSpecialBetForm(longspecial_id, initial=initial)

    context = {
        "special_form": form,
        "container": container,
    }

    return render(request, "gambling/create_long_term_bet.html", context)
