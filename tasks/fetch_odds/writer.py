import os
from json import dumps
from typing import List

from tasks.fetch_odds.parser import Game


OUTPUT_DIR = os.path.dirname(os.environ["ODDS_OUTPUT_DIR"])


def _write_to_disk(output_data: str):
    with open(os.path.join(OUTPUT_DIR, "output.json"), "w") as file:
        file.write(output_data)


def write_odds_to_disk(games: List[Game]):
    output_json = [
        {
            "home_team": game.home_team,
            "away_team": game.away_team,
            "home_numerator": game.home_numerator,
            "home_denominator": game.home_denominator,
            "draw_numerator": game.draw_numerator,
            "draw_denominator": game.draw_denominator,
            "away_numerator": game.away_numerator,
            "away_denominator": game.away_denominator,
            "start_time": game.start_time
        }
        for game in games
    ]

    _write_to_disk(dumps(output_json))
