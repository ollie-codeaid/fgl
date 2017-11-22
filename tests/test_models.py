from django.test import TestCase

from bets.models import Season
import mock

class SeasonTest(TestCase):

    def test_get_next_gameweek_id(self):
        season = Season(name='test', weekly_allowance=100.0)
        
        number = season.get_next_gameweek_id()
        self.assertEqual(1, number)
        
        mockGameweekSet = mock.Mock()
        # Make sure len returns 2
        mockGameweekSet.all.return_value = [1,2]
        
        with mock.patch('bets.models.Season.gameweek_set', mockGameweekSet):
            number = season.get_next_gameweek_id()
            self.assertEqual(3, number)
            
    def test_balances_available(self):
        season = Season(name='test', weekly_allowance=100.0)
        
        mockGameweekSet = mock.Mock()
        
        with mock.patch('bets.models.Season.gameweek_set', mockGameweekSet):
            
            # Make sure len returns 0
            mockGameweekSet.all.return_value = []
            self.assertFalse(season.balances_available())
            
            # Make sure len returns 2
            mockGameweekSet.all.return_value = [1,2]
            self.assertTrue(season.balances_available())
            
            # Make sure len returns 1
            mockGameweek = mock.Mock()
            mockGameweek.results_complete.return_value = True
            mockGameweekSet.all.return_value = [1,]
            mockGameweekSet.filter.return_value = [mockGameweek]
            self.assertTrue(season.balances_available())
            
    def test_get_latest_complete_gameweek(self):
        season = Season(name='test', weekly_allowance=100.0)
        mockGameweekLatest = mock.Mock()
        
        with mock.patch('bets.models.Season.get_latest_gameweek', return_value=mockGameweekLatest):
            mockGameweekLatest.results_complete.return_value = True
            result = season.get_latest_complete_gameweek()
            
            self.assertEqual(mockGameweekLatest, result)
            
            mockGameweekLatest.number = 2
            mockOtherGameweek = mock.Mock()
            mockGameweekSet = mock.Mock()
            mockGameweekSet.filter.return_value = [mockOtherGameweek]
            
            with mock.patch('bets.models.Season.gameweek_set', mockGameweekSet):
                mockGameweekLatest.results_complete.return_value = False
                result = season.get_latest_complete_gameweek()
                
                self.assertEqual(mockOtherGameweek, result)
                # For good measure
                self.assertNotEqual(mockOtherGameweek, mockGameweekLatest)
            
            