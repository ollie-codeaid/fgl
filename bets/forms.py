from django.forms import ModelForm
from django.forms.formsets import BaseFormSet
from django.forms.widgets import DateInput, TimeInput, Textarea
from django.shortcuts import get_object_or_404

from .models import Season, Gameweek, Game, Result, BetContainer, Accumulator, BetPart

class SeasonForm(ModelForm):
    class Meta:
        model = Season
        fields = ['name', 'weekly_allowance', 'players']

class GameweekForm(ModelForm):
    class Meta:
        model = Gameweek
        fields = ['deadline_date', 'deadline_time', 'spiel']
        widgets = {
            'deadline_date' : DateInput(attrs={ 'class': 'u-full-width' }),
            'deadline_time' : TimeInput(attrs={ 'class': 'u-full-width' }),
            'spiel' : Textarea(attrs={ 'class': 'u-full-width' }),
        }

class GameForm(ModelForm):
    class Meta:
        model = Game
        fields = ['hometeam', 'awayteam',
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
        dupes = []
        duplicates = False

        for form in self.forms:
            if form.cleaned_data:
                home = form.cleaned_data['hometeam']
                away = form.cleaned_data['awayteam']

                if home in teams or away in teams:
                    duplicates = True

                if duplicates:
                    raise forms.ValidationError(
                        'Teams must be unique',
                        code='duplicate_teams'
                    )

                if not away:
                    raise forms.ValidationError(
                        'No away team.',
                        code='missing_away'
                    )

                if not home:
                    raise forms.ValidationError(
                        'No home team.',
                        code='missing_home'
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
        duplicates = False

        for form in self.forms:
            if form.cleaned_data:
                game = form.cleaned_data['game']
                
                if game in games:
                    duplicates = True

                if duplicates:
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
