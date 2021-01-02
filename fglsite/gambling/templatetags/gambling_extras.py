from django import template

register = template.Library()


@register.inclusion_tag("gambling/long_term_odds.html")
def long_term_odds(container, gameweek, show_management_links):
    return {
        "container": container,
        "gameweek": gameweek,
        "show_management_links": show_management_links,
    }
