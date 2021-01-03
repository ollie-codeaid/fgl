from decimal import Decimal

from django import template

register = template.Library()


@register.inclusion_tag("bets/user_balance_table.html")
def user_balance_table(gameweek, force_show_specials=False):
    ordered_results = gameweek.get_ordered_results()

    if force_show_specials:
        show_specials = True
    else:
        show_specials = any(
            [result[0].special != Decimal("0.00") for result in ordered_results]
        )

    return {"ordered_results": ordered_results, "show_specials": show_specials}


@register.inclusion_tag("bets/user_balance_row.html")
def user_balance_row(ordered_result, show_specials):
    balance = ordered_result[0]
    change_icon = ordered_result[1]

    return {
        "balance": balance,
        "change_icon": change_icon,
        "show_specials": show_specials,
    }


@register.inclusion_tag("bets/gameweek_odds.html")
def gameweek_odds(gameweek):
    return {"gameweek": gameweek}
