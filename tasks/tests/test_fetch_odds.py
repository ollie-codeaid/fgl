from json import dumps
from unittest import TestCase
from unittest.mock import Mock, patch

from tasks.fetch_odds_task import run_task
from tasks.tests.fixtures.fixtures import odds_json_fixture, output_json_fixture


class FetchOddsTest(TestCase):
    @patch("tasks.fetch_odds.writer._write_to_disk")
    @patch("tasks.fetch_odds.client.requests")
    def test_fetch_odds_end_to_end(self, mock_requests, mock_write):
        mock_response = Mock()
        mock_response.json.return_value = odds_json_fixture()
        mock_requests.get.return_value = mock_response

        run_task()

        mock_write.assert_called_once_with(dumps(output_json_fixture()))
