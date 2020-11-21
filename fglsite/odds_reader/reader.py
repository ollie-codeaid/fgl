from json import loads
import os

from django.conf import settings


OUTPUT_DIR = os.path.dirname(settings.ODDS_OUTPUT_DIR)


def _read_from_disk():
    with open(os.path.join(OUTPUT_DIR, "output.json"), "r") as file:
        return file.read()


def read_odds():
    odds_json = loads(_read_from_disk())

    odds = [
        {
            "hometeam": game["home_team"],
            "awayteam": game["away_team"],
            "homenumerator": game["home_numerator"],
            "homedenominator": game["home_denominator"],
            "drawnumerator": game["draw_numerator"],
            "drawdenominator": game["draw_denominator"],
            "awaynumerator": game["away_numerator"],
            "awaydenominator": game["away_denominator"],
            "meta": {"start_time": game["start_time"]},
        }
        for game in odds_json
    ]

    return odds
