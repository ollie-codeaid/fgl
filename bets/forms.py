from django import forms
from django.forms import Form, ModelForm
from django.forms.formsets import BaseFormSet
from django.forms.widgets import DateInput, TimeInput, Textarea

from .models import (
        Season, Gameweek, Game, Result, Accumulator,
        BetPart, LongSpecialContainer, LongSpecial,
        LongSpecialBet)


class SeasonForm(ModelForm):
    class Meta:
        model = Season
        fields = ['name', 'weekly_allowance', 'public']


class FindSeasonForm(Form):
    name = forms.CharField(required=False)
    commissioner = forms.CharField(required=False)


class GameweekForm(ModelForm):
    class Meta:
        model = Gameweek
        fields = ['deadline_date', 'deadline_time', 'spiel']
        widgets = {
            'deadline_date': DateInput(attrs={'class': 'u-full-width'}),
            'deadline_time': TimeInput(attrs={'class': 'u-full-width'}),
            'spiel': Textarea(attrs={'class': 'u-full-width'}),
        }


class GameForm(ModelForm):
    class Meta:
        model = Game
        fields = [
                'hometeam', 'awayteam',
                'homenumerator', 'homedenominator',
                'drawnumerator', 'drawdenominator',
                'awaynumerator', 'awaydenominator',
                ]


class BaseGameFormSet(BaseFormSet):
    def clean(self):
        """
        Adds validation to check that no duplicate games exist
        """
        if any(self.errors):
            return

        teams = []

        for form in self.forms:
            if form.cleaned_data:
                home = form.cleaned_data['hometeam']
                away = form.cleaned_data['awayteam']

                if home in teams or away in teams:
                    raise forms.ValidationError(
                        'Teams must be unique',
                        code='duplicate_teams'
                    )

                teams.append(home)
                teams.append(away)


class ResultForm(ModelForm):
    def __init__(self, *args, **kwargs):
        gameweek = kwargs.pop('gameweek')
        super(ResultForm, self).__init__(*args, **kwargs)
        self.fields['game'].queryset = Game.objects.filter(gameweek=gameweek)

    class Meta:
        model = Result
        fields = ['game', 'result']


class BaseResultFormSet(BaseFormSet):
    def clean(self):
        """
        Adds validation to check that no duplicate games exist
        """
        if any(self.errors):
            return

        games = []

        for form in self.forms:
            if form.cleaned_data:
                game = form.cleaned_data['game']

                if game in games:
                    raise forms.ValidationError(
                        'Games must be unique',
                        code='duplicate_games'
                    )

                games.append(game)


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
