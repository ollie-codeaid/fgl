from django import template

register = template.Library()


@register.inclusion_tag('bets/user_balances.html')
def user_balances(gameweek):
    return {'gameweek': gameweek}


@register.inclusion_tag('bets/gameweek_odds.html')
def gameweek_odds(gameweek):
    return {'gameweek': gameweek}
