from django import template

register = template.Library()


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
def long_term_odds(container, request):
    return {
            'container': container,
            'request': request,
            }


@register.simple_tag
def get_longterm_choice_by_user(longspecial_container, request):
    return longspecial_container.get_choice_by_user(request.user)
