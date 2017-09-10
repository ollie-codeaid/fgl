from django.forms import ModelForm
from django.forms.formsets import BaseFormSet
from django.shortcuts import get_object_or_404

from .models import Gameweek, Game

class GameweekForm(ModelForm):
    class Meta:
        model = Gameweek
        fields = ['deadline']

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

