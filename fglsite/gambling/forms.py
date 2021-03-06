from django import forms
from django.forms import ModelForm
from django.forms.formsets import BaseFormSet

from fglsite.bets.models import Game
from .models import (
    Accumulator,
    BetContainer,
    BetPart,
    LongSpecialContainer,
    LongSpecial,
    LongSpecialBet,
    LongSpecialResult,
)


class BetContainerForm(ModelForm):
    class Meta:
        model = BetContainer
        fields = ["gameweek", "owner"]


class AccumulatorForm(ModelForm):
    class Meta:
        model = Accumulator
        fields = ["bet_container", "stake"]

    def is_valid(self, initial_stake):
        is_valid = super().is_valid()

        total_stake_left = self.cleaned_data[
            "bet_container"
        ].get_allowance_unused() + float(initial_stake)

        if total_stake_left < self.cleaned_data["stake"]:
            self.add_error("stake", f"Stake may not be greater than {total_stake_left}")
            return False

        return is_valid


class BetPartForm(ModelForm):
    def __init__(self, *args, **kwargs):
        gameweek = kwargs.pop("gameweek")
        super(BetPartForm, self).__init__(*args, **kwargs)
        self.fields["game"].queryset = Game.objects.filter(gameweek=gameweek)

    class Meta:
        model = BetPart
        fields = ["game", "result"]


class LongSpecialContainerForm(ModelForm):
    class Meta:
        model = LongSpecialContainer
        fields = ["description", "allowance"]


class LongSpecialForm(ModelForm):
    class Meta:
        model = LongSpecial
        fields = ["description", "numerator", "denominator"]


class BaseLongSpecialFormSet(BaseFormSet):
    def clean(self):
        """
        Adds validation to check that no duplicate specials exist
        """
        if any(self.errors):
            return

        specials = []

        for form in self.forms:
            if form.cleaned_data:
                special = form.cleaned_data["description"]

                if special in specials:
                    raise forms.ValidationError(
                        "Specials must be unique", code="duplicate_specials"
                    )

                specials.append(special)


class LongSpecialBetForm(ModelForm):
    def __init__(self, long_special_container, *args, **kwargs):
        super(LongSpecialBetForm, self).__init__(*args, **kwargs)
        self.fields["long_special"].queryset = LongSpecial.objects.filter(
            container=long_special_container,
        )

    class Meta:
        model = LongSpecialBet
        fields = ["long_special"]


class LongSpecialResultForm(ModelForm):
    class Meta:
        model = LongSpecialResult
        fields = ["long_special", "completed_gameweek"]

    def __init__(self, long_special_container, *args, **kwargs):
        super(LongSpecialResultForm, self).__init__(*args, **kwargs)
        self.fields["long_special"].queryset = LongSpecial.objects.filter(
            container=long_special_container,
        )
