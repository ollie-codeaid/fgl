from django import template

register = template.Library()


@register.inclusion_tag("gambling/long_term_odds.html")
def long_term_odds(container, request):
    return {
        "container": container,
        "request": request,
    }


@register.simple_tag
def get_longterm_choice_by_user(longspecial_container, request):
    return longspecial_container.get_choice_by_user(request.user)
