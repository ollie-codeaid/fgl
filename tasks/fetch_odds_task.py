from tasks.fetch_odds.client import fetch_odds
from tasks.fetch_odds.parser import parse_odds
from tasks.fetch_odds.writer import write_odds_to_disk


def run_task():
    odds_response = fetch_odds()
    parsed_odds = parse_odds(odds_response)
    write_odds_to_disk(parsed_odds)


if __name__ == "__main__":
    run_task()
