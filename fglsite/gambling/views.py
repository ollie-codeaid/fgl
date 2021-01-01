# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from functools import partial

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.forms.formsets import formset_factory
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    UpdateView,
)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from fglsite.bets.forms import BaseResultFormSet
from fglsite.bets.models import Gameweek, Balance
from fglsite.bets.views import SeasonCommissionerAllowedMixin
from .models import (
    BetContainer,
    Accumulator,
    BetPart,
    LongSpecialContainer,
    LongSpecial,
    LongSpecialBet,
    LongSpecialResult,
)
from .forms import (
    AccumulatorForm,
    BetContainerForm,
    BetPartForm,
    LongSpecialContainerForm,
    LongSpecialForm,
    BaseLongSpecialFormSet,
    LongSpecialBetForm,
    LongSpecialResultForm,
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
        return {"data": {"gameweek": self.gameweek.id, "owner": self.request.user.id}}

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class BetContainerOwnerAllowedMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user != self.bet_container.owner:
            return HttpResponseForbidden()

        return super().dispatch(request, *args, **kwargs)


class BetContainerDetailView(
    BetContainerOwnerAllowedMixin, LoginRequiredMixin, DetailView
):
    model = BetContainer

    def dispatch(self, request, pk, *args, **kwargs):
        self.bet_container = get_object_or_404(BetContainer, pk=pk)
        return super().dispatch(request, pk, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        long_special_containers = (
            self.bet_container.gameweek.longspecialcontainer_set.all()
        )
        long_special_bets = self.bet_container.longspecialbet_set.all()

        long_specials = {
            long_special_container: long_special_bets.filter(
                long_special__container=long_special_container
            ).first()
            for long_special_container in long_special_containers
        }

        context_data.update({"long_specials": long_specials})
        return context_data


class AccumulatorView(BetContainerOwnerAllowedMixin, LoginRequiredMixin):
    model = Accumulator
    form_class = AccumulatorForm
    formset_class = formset_factory(BetPartForm, formset=BaseResultFormSet)

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
        context_data.update(
            {"betpart_formset": self.get_formset(), "bet_container": self.bet_container}
        )
        return context_data

    def dispatch(self, request, bet_container_id, *args, **kwargs):
        self.bet_container = get_object_or_404(BetContainer, pk=bet_container_id)
        return super().dispatch(request, bet_container_id, *args, **kwargs)

    def get_initial_stake(self):
        return 0

    def post(self, *args, **kwargs):
        accumulator_form = self.get_form()
        bet_formset = self.get_formset()

        if (
            accumulator_form.is_valid(initial_stake=self.get_initial_stake())
            and bet_formset.is_valid()
        ):
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
            )
            for betpart_form in formset.forms
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
        return {"bet_container": self.bet_container}

    def save_accumulator(self, form):
        return Accumulator.objects.create(
            bet_container=self.bet_container, stake=form.cleaned_data.get("stake")
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


class AccumulatorDeleteView(
    BetContainerOwnerAllowedMixin, LoginRequiredMixin, DeleteView
):
    model = Accumulator

    def dispatch(self, request, pk, *args, **kwargs):
        self.bet_container = get_object_or_404(Accumulator, pk=pk).bet_container
        return super().dispatch(request, pk, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy("update-bet-container", args=[self.bet_container.pk])


class LongSpecialManagementView(
    SeasonCommissionerAllowedMixin, LoginRequiredMixin, DetailView
):
    model = Gameweek
    template_name = "gambling/manage_longterms.html"

    def get_season(self, *args, **kwargs):
        return self.gameweek.season

    def dispatch(self, request, pk, *args, **kwargs):
        self.gameweek = get_object_or_404(Gameweek, pk=pk)
        return super().dispatch(request, pk, *args, **kwargs)


class LongSpecialContainerView(SeasonCommissionerAllowedMixin, LoginRequiredMixin):
    model = LongSpecialContainer
    form_class = LongSpecialContainerForm
    formset_class = formset_factory(LongSpecialForm, formset=BaseLongSpecialFormSet)

    def get_season(self, *args, **kwargs):
        return self.gameweek.season

    def get_success_url(self):
        return reverse_lazy("gameweek", args=[self.gameweek.pk])

    def get_formset(self):
        if self.request.POST:
            return self.formset_class(self.request.POST)
        else:
            self.formset_class.extra = self.extra
            return self.formset_class(initial=self.get_formset_initial())

    def get_formset_initial(self):
        return []

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data.update(
            {
                "long_special_formset": self.get_formset(),
                "gameweek_id": self.gameweek.id,
            }
        )
        return context_data

    def dispatch(self, request, gameweek_id, *args, **kwargs):
        self.gameweek = get_object_or_404(Gameweek, pk=gameweek_id)
        return super().dispatch(request, gameweek_id, *args, **kwargs)

    def post(self, *args, **kwargs):
        container_form = self.get_form()
        long_special_formset = self.get_formset()

        if container_form.is_valid() and long_special_formset.is_valid():
            return self.form_valid(container_form, long_special_formset)
        else:
            self.object = None
            return self.form_invalid(container_form, long_special_formset)

    def form_valid(self, form, formset):
        container = self.save_container(form)

        new_long_specials = [
            LongSpecial(
                container=container,
                description=long_special_form.cleaned_data.get("description"),
                numerator=long_special_form.cleaned_data.get("numerator"),
                denominator=long_special_form.cleaned_data.get("denominator"),
            )
            for long_special_form in formset.forms
        ]

        try:
            with transaction.atomic():
                self.clear_existing_long_specials(container)
                LongSpecial.objects.bulk_create(new_long_specials)
                messages.success(self.request, self.success_message)
        except Exception as err:
            messages.error(self.request, "Error saving new long special.")
            messages.error(self.request, err)

        return redirect(self.get_success_url())

    def clear_existing_long_specials(self, container):
        # Do nothing
        return

    def form_invalid(self, form, formset):
        """If the form is invalid, render the invalid form."""
        return self.render_to_response(
            self.get_context_data(form=form, formset=formset)
        )


class LongSpecialCreateView(LongSpecialContainerView, CreateView):
    extra = 1
    success_message = "Created long special."

    def save_container(self, form):
        return LongSpecialContainer.objects.create(
            created_gameweek=self.gameweek,
            description=form.cleaned_data.get("description"),
            allowance=form.cleaned_data.get("allowance"),
        )


class LongSpecialUpdateView(LongSpecialContainerView, UpdateView):
    extra = 0
    success_message = "Updated long special."

    def get_formset_initial(self):
        return [
            {
                "container": long_special.container,
                "description": long_special.description,
                "numerator": long_special.numerator,
                "denominator": long_special.denominator,
            }
            for long_special in self.get_object().longspecial_set.all()
        ]

    def dispatch(self, request, pk, *args, **kwargs):
        container = get_object_or_404(LongSpecialContainer, pk=pk)

        if container.has_bets():
            messages.error(
                request,
                (
                    "Cannot update specials that already have bets,"
                    " speak to Ollie if required"
                ),
            )
            return redirect("gameweek", pk=container.created_gameweek.id)

        return super().dispatch(request, container.created_gameweek.id, *args, **kwargs)

    def save_container(self, form):
        container = self.get_object()
        container.description = form.cleaned_data.get("description")
        container.allowance = form.cleaned_data.get("allowance")
        container.save()
        return container

    def clear_existing_long_specials(self, container):
        LongSpecial.objects.filter(container=container).delete()


class LongSpecialBetView(BetContainerOwnerAllowedMixin, LoginRequiredMixin):
    model = LongSpecialBet
    form_class = LongSpecialBetForm

    def get_success_url(self):
        return reverse_lazy("update-bet-container", args=[self.bet_container.pk])

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data.update(
            {
                "bet_container": self.bet_container,
                "long_special_container": self.long_special_container,
            }
        )
        return context_data

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update({"long_special_container": self.long_special_container})
        return form_kwargs


class LongSpecialBetCreateView(LongSpecialBetView, CreateView):
    def dispatch(
        self, request, bet_container_id, long_special_container_id, *args, **kwargs
    ):
        self.bet_container = get_object_or_404(BetContainer, pk=bet_container_id)
        self.long_special_container = get_object_or_404(
            LongSpecialContainer, pk=long_special_container_id
        )
        return super().dispatch(
            request, bet_container_id, long_special_container_id, *args, **kwargs
        )

    def form_valid(self, form):
        self.object = LongSpecialBet.objects.create(
            long_special=form.cleaned_data["long_special"],
            bet_container=self.bet_container,
        )
        return HttpResponseRedirect(self.get_success_url())


class LongSpecialBetUpdateView(LongSpecialBetView, UpdateView):
    def dispatch(self, request, pk, *args, **kwargs):
        long_special_bet = get_object_or_404(LongSpecialBet, pk=pk)
        self.bet_container = long_special_bet.bet_container
        self.long_special_container = long_special_bet.long_special.container
        return super().dispatch(request, pk, *args, **kwargs)


class LongSpecialResultFormView(
    SeasonCommissionerAllowedMixin, LoginRequiredMixin, FormView
):
    form_class = LongSpecialResultForm
    template_name = "gambling/longspecialresult_form.html"

    def get_success_url(self):
        return reverse_lazy("manage-longterms", args=[self.gameweek.id])

    def get_season(self, *args, **kwargs):
        return self.gameweek.season

    def dispatch(self, request, pk, gameweek_id, *args, **kwargs):
        self.long_special_container = get_object_or_404(LongSpecialContainer, pk=pk)
        self.gameweek = get_object_or_404(Gameweek, pk=gameweek_id)
        return super().dispatch(request, pk, gameweek_id, *args, **kwargs)

    def get_initial(self):
        return {"completed_gameweek": self.gameweek.id}

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update({"long_special_container": self.long_special_container})
        return form_kwargs

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update(
            {
                "long_special_container": self.long_special_container,
                "gameweek": self.gameweek,
            }
        )
        return context_data

    def form_valid(self, form):
        existing_result = LongSpecialResult.objects.filter(
            long_special__container=self.long_special_container,
            completed_gameweek=self.gameweek,
        ).first()

        long_special_bets = LongSpecialBet.objects.filter(
            long_special__container=self.long_special_container
        )

        with transaction.atomic():
            for long_special_bet in long_special_bets:
                change_in_balance = float(
                    long_special_bet.project_winnings(form.cleaned_data["long_special"])
                )
                if existing_result:
                    change_in_balance -= float(
                        long_special_bet.project_winnings(existing_result.long_special)
                    )

                Balance.objects.create_with_longterm(
                    self.gameweek,
                    long_special_bet.bet_container.owner,
                    change_in_balance,
                )

            if existing_result:
                existing_result.delete()
            form.save()

        return HttpResponseRedirect(self.get_success_url())
