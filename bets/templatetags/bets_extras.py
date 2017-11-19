from django import template

register = template.Library()

@register.inclusion_tag('bets/login_header.html')
def login_header(request):
    return { 'request': request }
