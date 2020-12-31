from django import template

register = template.Library()


@register.inclusion_tag("gambling/long_term_odds.html")
def long_term_odds(container, request):
    return {
        "container": container,
        "request": request,
    }
