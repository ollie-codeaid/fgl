from django import template

register = template.Library()

@register.inclusion_tag('bets/login_header.html')
def login_header(request):
    return { 'request': request }

@register.inclusion_tag('bets/user_balances.html')
def user_balances(gameweek):
	return { 'gameweek': gameweek }