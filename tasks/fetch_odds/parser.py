from fractions import Fraction
from typing import List, Tuple

from tasks.fetch_odds.client import GameData, OddsAPIResponse


# No dataclass yet because pythonanywhere only goes up to 3.6
class Game:
    def __init__(
        self,
        home_team: str,
        away_team: str,
        home_numerator: int,
        home_denominator: int,
        draw_numerator: int,
        draw_denominator: int,
        away_numerator: int,
        away_denominator: int,
        start_time: int,
    ):
        self.home_team = home_team
        self.away_team = away_team
        self.home_numerator = home_numerator
        self.home_denominator = home_denominator
        self.draw_numerator = draw_numerator
        self.draw_denominator = draw_denominator
        self.away_numerator = away_numerator
        self.away_denominator = away_denominator
        self.start_time = start_time


def get_start_time(game_data: GameData) -> int:
    return game_data["commence_time"]


def get_best_odds(game_data: GameData) -> Tuple[float, float, float]:
    team_one = 0.0
    team_two = 0.0
    draw = 0.0

    for site in game_data.get("sites", []):
        odds = site.get("odds", {}).get("h2h", None)

        if not odds:
            continue

        team_one = max(odds[0], team_one)
        team_two = max(odds[1], team_two)
        draw = max(odds[2], draw)

    return team_one, team_two, draw


def decimal_to_fraction(decimal: float) -> Fraction:
    return Fraction(decimal).limit_denominator(10)


def build_game(game_data: GameData) -> Game:
    home_team = game_data["home_team"]
    teams = game_data["teams"]
    home_first = teams[0] == home_team
    away_team = teams[1] if home_first else teams[0]

    best_odds = get_best_odds(game_data)

    # Odds are listed in same order as teams
    home_odd = best_odds[0] if home_first else best_odds[1]
    away_odd = best_odds[1] if home_first else best_odds[0]

    # Subtract 1 before converting to fraction to match UK bookmaker style
    home_fraction = decimal_to_fraction(home_odd - 1)
    away_fraction = decimal_to_fraction(away_odd - 1)
    draw_fraction = decimal_to_fraction(best_odds[2] - 1)

    return Game(
        home_team=home_team,
        away_team=away_team,
        home_numerator=home_fraction.numerator,
        home_denominator=home_fraction.denominator,
        away_numerator=away_fraction.numerator,
        away_denominator=away_fraction.denominator,
        draw_numerator=draw_fraction.numerator,
        draw_denominator=draw_fraction.denominator,
        start_time=get_start_time(game_data),
    )


def parse_odds(odds_response: OddsAPIResponse) -> List[Game]:

    data = odds_response.get("data", [])
    # Only worry about the next 10 games
    sorted_data = sorted(data, key=get_start_time)[0:10]

    result = []

    for game_data in sorted_data:
        result.append(build_game(game_data))

    return result
