from django.test import TestCase

from bets.models import Season
import mock

class SeasonTest(TestCase):

    def test_get_next_gameweek_id(self):
        season = Season(name='test', weekly_allowance=100.0)
        
        id = season.get_next_gameweek_id()
        self.assertEqual(1, id)
        
        mockGameweekSet = mock.Mock()
        mockGameweekSet.all.return_value = [1,2]
        
        with mock.patch('bets.models.Season.gameweek_set', mockGameweekSet):
            id = season.get_next_gameweek_id()
            self.assertEqual(3, id)