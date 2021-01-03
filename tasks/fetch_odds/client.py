import os
from typing import List

import requests

SPORT_KEY = "soccer_epl"
API_KEY = os.environ["ODDS_API_KEY"]
BETS_URL = f"https://api.the-odds-api.com/v3/odds/?sport={SPORT_KEY}&region=uk&apiKey={API_KEY}"


class Odds:
    h2h: List[float]


class Site:
    odds: Odds


class GameData:
    commence_time: int
    teams: List[str]
    home_team: str
    sites: List[Site]


class OddsAPIResponse:
    data: List[GameData]


def fetch_odds() -> OddsAPIResponse:
    return requests.get(BETS_URL).json()
