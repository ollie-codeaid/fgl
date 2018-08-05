from django import template

register = template.Library()


@register.inclusion_tag('bets/login_header.html')
def login_header(request):
    return {'request': request}


@register.inclusion_tag('bets/user_balances.html')
def user_balances(gameweek):
    return {'gameweek': gameweek}


@register.inclusion_tag('bets/render_messages.html')
def render_messages(messages):
    return {'messages': messages}


@register.inclusion_tag('bets/gameweek_odds.html')
def gameweek_odds(gameweek):
    return {'gameweek': gameweek}


@register.inclusion_tag('bets/long_term_odds.html')
def long_term_odds(container):
    return {'container': container}
