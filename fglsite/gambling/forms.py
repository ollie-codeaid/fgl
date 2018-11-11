from django import forms
from django.forms import ModelForm
from django.forms.formsets import BaseFormSet

from fglsite.bets.models import Game
from .models import (
        Accumulator, BetPart, LongSpecialContainer, LongSpecial,
        LongSpecialBet)


class AccumulatorForm(ModelForm):
    class Meta:
        model = Accumulator
        fields = ['stake']


class BetPartForm(ModelForm):
    def __init__(self, *args, **kwargs):
        gameweek = kwargs.pop('gameweek')
        super(BetPartForm, self).__init__(*args, **kwargs)
        self.fields['game'].queryset = Game.objects.filter(gameweek=gameweek)

    class Meta:
        model = BetPart
        fields = ['game', 'result']


class LongSpecialContainerForm(ModelForm):
    class Meta:
        model = LongSpecialContainer
        fields = ['description', 'allowance']


class LongSpecialForm(ModelForm):
    class Meta:
        model = LongSpecial
        fields = ['description', 'numerator', 'denominator']


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
                special = form.cleaned_data['description']

                if special in specials:
                    raise forms.ValidationError(
                        'Specials must be unique',
                        code='duplicate_specials'
                    )

                specials.append(special)


class LongSpecialBetForm(ModelForm):
    def __init__(self, longspecial_id, *args, **kwargs):
        super(LongSpecialBetForm, self).__init__(*args, **kwargs)
        self.fields['long_special'].queryset = LongSpecial.objects.filter(
                container=longspecial_id,
                )

    class Meta:
        model = LongSpecialBet
        fields = ['long_special']
