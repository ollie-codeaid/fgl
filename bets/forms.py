from django.forms import ModelForm, inlineformset_factory

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

GameweekGameFormSet = inlineformset_factory(Gameweek, Game, form=GameForm, extra=2)
