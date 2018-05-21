from django.test import TestCase

from bets.models import Season, Gameweek, Game, BetContainer, Balance
from django.contrib.auth.models import User
from mock import Mock, patch
from datetime import date, time
from bets.views import gameweek

def _create_test_season():
    season = Season(name='test', 
                    weekly_allowance=100.0)
    season.save()
    return season

def _create_test_gameweek(season):
    gameweek = Gameweek(season=season, 
                        number=season.get_next_gameweek_id(), 
                        deadline_date=date(2017, 11, 1), 
                        deadline_time=time(12, 00), 
                        spiel='')
    gameweek.save()
    return gameweek

def _create_test_game(gameweek):
    game = Game(gameweek=gameweek,
                hometeam='Chelsea',
                awayteam='Liverpool',
                homenumerator=1, homedenominator=50,
                drawnumerator=1, drawdenominator=20,
                awaynumerator=100, awaydenominator=1)
    game.save()
    return game
    
def _create_test_bet_container(gameweek, user):
    betcontainer = BetContainer(gameweek=gameweek,
                                owner=user)
    betcontainer.save()
    return betcontainer
    
def _create_mock_user(username):
    # might have to be clever later on with user name
    return Mock(spec=User)

class SeasonTest(TestCase):

    def test__str__(self):
        season = _create_test_season()

        self.assertIn('test', str(season))

    def test_get_next_gameweek_id(self):
        season = _create_test_season()
        
        number = season.get_next_gameweek_id()
        self.assertEqual(1, number)
        
        _create_test_gameweek(season)
        _create_test_gameweek(season)
        
        number = season.get_next_gameweek_id()
        self.assertEqual(3, number)
            
    def test_balances_available(self):
        season = _create_test_season()
        
        mockGameweekSet = Mock()
        
        with patch('bets.models.Season.gameweek_set', mockGameweekSet):
            
            # Make sure len returns 0
            mockGameweekSet.all.return_value = []
            self.assertFalse(season.balances_available())
            
            # Make sure len returns 2
            mockGameweekSet.all.return_value = [1,2]
            self.assertTrue(season.balances_available())
            
            # Make sure len returns 1
            mockGameweek = Mock()
            mockGameweek.results_complete.return_value = True
            mockGameweekSet.all.return_value = [1,]
            mockGameweekSet.filter.return_value = [mockGameweek]
            self.assertTrue(season.balances_available())
            
    def test_get_latest_complete_gameweek(self):
        season = _create_test_season()
        mockGameweekLatest = Mock()
        
        with patch('bets.models.Season._get_latest_gameweek', return_value=mockGameweekLatest):
            mockGameweekLatest.results_complete.return_value = True
            result = season.get_latest_complete_gameweek()
            
            self.assertEqual(mockGameweekLatest, result)
            
            mockGameweekLatest.number = 2
            mockOtherGameweek = Mock()
            mockGameweekSet = Mock()
            mockGameweekSet.filter.return_value = [mockOtherGameweek]
            
            with patch('bets.models.Season.gameweek_set', mockGameweekSet):
                mockGameweekLatest.results_complete.return_value = False
                result = season.get_latest_complete_gameweek()
                
                self.assertEqual(mockOtherGameweek, result)
                # For good measure
                self.assertNotEqual(mockOtherGameweek, mockGameweekLatest)
            
    def test__get_latest_gameweek(self):
        season = _create_test_season()
        gameweek1 = _create_test_gameweek(season)
        gameweek2 = _create_test_gameweek(season)
        
        result = season._get_latest_gameweek()
        
        self.assertEqual(gameweek2, result)
        
    def test_can_create_gameweek(self):
        season = _create_test_season()
        self.assertTrue(season.can_create_gameweek())
        
        gameweek = _create_test_gameweek(season)
        _create_test_game(gameweek)
        self.assertFalse(season.can_create_gameweek())
        
class GameweekTest(TestCase):

    def test__str__(self):
        season = _create_test_season()
        gameweek = _create_test_gameweek(season)

        self.assertIn('test', str(gameweek))
        self.assertIn('1', str(gameweek))

    def test_is_first_gameweek(self):
        season = _create_test_season()
        gameweek_one = _create_test_gameweek(season)
        gameweek_two = _create_test_gameweek(season)

        self.assertTrue( gameweek_one.is_first_gameweek() )
        self.assertFalse( gameweek_two.is_first_gameweek() )

    def test_get_prev_gameweek(self):
        season = _create_test_season()
        gameweek_one = _create_test_gameweek(season)
        gameweek_two = _create_test_gameweek(season)
    
        self.assertEquals( gameweek_one, gameweek_two.get_prev_gameweek() )

        with self.assertRaises(Exception) as context:
            gameweek_one.get_prev_gameweek()

        self.assertIn( 'Called get_prev_gameweek on first gameweek', context.exception.message )

    def test_get_next_gameweek(self):
        season = _create_test_season()
        gameweek_one = _create_test_gameweek(season)
        gameweek_two = _create_test_gameweek(season)
    
        self.assertEquals( gameweek_two, gameweek_one.get_next_gameweek() )

        with self.assertRaises(Exception) as context:
            gameweek_two.get_next_gameweek()

        self.assertIn( 'Called get_next_gameweek on latest gameweek', context.exception.message )


    @patch('bets.models.Gameweek._get_users_with_bets')
    @patch('bets.models.Gameweek.get_prev_gameweek')
    @patch('bets.models.Gameweek.set_balance_by_user')
    def test_update_no_bet_users(self, setBalanceMethod, lastGameweekMethod, usersMethod):
        ollie = Mock(spec=User)
        liam = Mock(spec=User)
        
        ollieBalance = Mock(spec=Balance)
        ollieBalance.user = ollie
        liamBalance = Mock(spec=Balance)
        liamBalance.user = liam
        liamBalance.week = 50.0
        
        lastGameweek = Mock()
        lastGameweek._get_balance_set.return_value = [ ollieBalance, liamBalance ]
        
        usersMethod.return_value = [ ollie ]
        lastGameweekMethod.return_value = lastGameweek
        
        season = _create_test_season()
        gameweekOne = _create_test_gameweek(season)
        gameweekTwo = _create_test_gameweek(season)
        
        gameweekTwo.update_no_bet_users()
        
        self.assertEqual(1, setBalanceMethod.call_count)
        setBalanceMethod.assert_any_call(
            user=liam, 
            week_winnings=float(-100.0), 
            week_unused=float(50.0))
        
    def test__get_balance_map(self):
        season = _create_test_season()
        gameweek = _create_test_gameweek(season)
        
        self.assertEqual(0, len(gameweek.balancemap_set.all()))
        
        balancemap = gameweek._get_balancemap()
        self.assertEqual(1, len(gameweek.balancemap_set.all()))
        
        self.assertEqual(balancemap, gameweek._get_balancemap())
        
    def test__calc_enforce_banked(self):
        season = _create_test_season()
        gameweek = _create_test_gameweek(season)
        
        self.assertEqual(0.0, gameweek._calc_enforce_banked(10.0))
        self.assertEqual(-10.0, gameweek._calc_enforce_banked(-10.0))
        
    @patch('bets.models.Gameweek._get_balance_by_user')
    def test__get_last_banked(self, getBalanceMethod):
        season = _create_test_season()
        gameweek_one = _create_test_gameweek(season)
        gameweek_two = _create_test_gameweek(season)

        balance = Mock()
        balance.banked = 100.0
        getBalanceMethod.return_value = balance
        
        user = Mock()
        
        self.assertEqual(0.0, gameweek_one._get_prev_banked(user))
        self.assertEqual(100.0, gameweek_two._get_prev_banked(user))
        getBalanceMethod.assert_any_call(user)
        
    @patch('bets.models.Balance')
    @patch('bets.models.BalanceMap.user_has_balance', Mock(return_value=False))
    def test__set_balance_by_user(self, balance):
        
        season = _create_test_season()
        gameweek1 = _create_test_gameweek(season)
        balancemap = gameweek1._get_balancemap()
        
        user = Mock()
        gameweek1.set_balance_by_user(user, 123.0, 50.0)
        
        balance.assert_any_call(
            balancemap=balancemap, 
            user=user, 
            week=123.0, 
            provisional=173.0, 
            banked=50.0)
        
        
