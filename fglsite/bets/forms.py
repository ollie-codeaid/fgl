from django import forms
from django.forms import Form, ModelForm
from django.forms.formsets import BaseFormSet
from django.forms.widgets import DateInput, TimeInput, Textarea

from .models import Season, Gameweek, Game, Result


class SeasonForm(ModelForm):
    class Meta:
        model = Season
        fields = ["name", "weekly_allowance"]


class FindSeasonForm(Form):
    name = forms.CharField(required=False)
    commissioner = forms.CharField(required=False)


class GameweekForm(ModelForm):
    class Meta:
        model = Gameweek
        fields = ["deadline_date", "deadline_time", "spiel"]
        widgets = {
            "deadline_date": DateInput(attrs={"class": "u-full-width"}),
            "deadline_time": TimeInput(attrs={"class": "u-full-width"}),
            "spiel": Textarea(attrs={"class": "u-full-width"}),
        }


class GameForm(ModelForm):
    class Meta:
        model = Game
        fields = [
            "hometeam",
            "awayteam",
            "homenumerator",
            "homedenominator",
            "drawnumerator",
            "drawdenominator",
            "awaynumerator",
            "awaydenominator",
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
                home = form.cleaned_data["hometeam"]
                away = form.cleaned_data["awayteam"]

                if home in teams or away in teams:
                    raise forms.ValidationError(
                        "Teams must be unique", code="duplicate_teams"
                    )

                teams.append(home)
                teams.append(away)


class ResultForm(ModelForm):
    class Meta:
        model = Result
        fields = ["game", "result"]


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
                game = form.cleaned_data["game"]

                if game in games:
                    raise forms.ValidationError(
                        "Games must be unique", code="duplicate_games"
                    )

                games.append(game)
