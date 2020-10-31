import json
import os

FIXTURES_DIR = os.path.dirname(__file__)


def odds_json_fixture():
    with open(os.path.join(FIXTURES_DIR, "odds.json")) as odds_json:
        return json.load(odds_json)


def output_json_fixture():
    with open(os.path.join(FIXTURES_DIR, "output.json")) as output_json:
        return json.load(output_json)
