from django.test import TestCase

from bets.models import Season, Gameweek, Game, BetContainer, Balance, Accumulator
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
    def test_update_no_bet_users(self, set_balance_method, prev_gameweek_method, users_method):
        user_one = Mock(spec=User)
        user_two = Mock(spec=User)
        
        user_one_balance = Mock(spec=Balance)
        user_one_balance.user = user_one
        user_two_balance = Mock(spec=Balance)
        user_two_balance.user = user_two
        user_two_balance.week = 50.0
        
        prev_gameweek = Mock()
        prev_gameweek.balance_set.all.return_value = { user_one_balance, user_two_balance }
        
        users_method.return_value = [ user_one ]
        prev_gameweek_method.return_value = prev_gameweek
        
        season = _create_test_season()
        gameweek_one = _create_test_gameweek(season)
        gameweek_two = _create_test_gameweek(season)
        
        gameweek_two.update_no_bet_users()
        
        self.assertEqual(1, set_balance_method.call_count)
        set_balance_method.assert_any_call(
            user=user_two, 
            week_winnings=float(-100.0), 
            week_unused=float(50.0))
        
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
    @patch('bets.models.Gameweek.user_has_balance', Mock(return_value=False))
    def test__set_balance_by_user(self, balance):
        
        season = _create_test_season()
        gameweek = _create_test_gameweek(season)
        
        user = Mock()
        gameweek.set_balance_by_user(user, 123.0, 50.0)
        
        balance.assert_any_call(
            gameweek=gameweek, 
            user=user, 
            week=123.0, 
            provisional=173.0, 
            banked=50.0)
        
    def test__get_balance_by_user(self):
        season = _create_test_season()
        gameweek = _create_test_gameweek(season)
        user_one = User.objects.create_user('user_one')
        user_one.save()
        user_two = User.objects.create_user('user_two')
        user_two.save()

        balance = Balance(
                gameweek=gameweek,
                user=user_one,
                week=123.0,
                provisional=1234.0,
                banked=10.0)
        balance.save()

        result_balance = gameweek._get_balance_by_user(user_one)

        self.assertEquals( balance, result_balance )
        self.assertIsNone( gameweek._get_balance_by_user(user_two) )

    def test_has_bets(self):
        season = _create_test_season()
        gameweek = _create_test_gameweek(season)

        user_one = User.objects.create_user('user_one')
        user_one.save()
        
        self.assertFalse( gameweek.has_bets() )

        bet_container = BetContainer( owner=user_one, gameweek=gameweek )
        bet_container.save()
        self.assertTrue( gameweek.has_bets() )

    def test_deadline_passed(self):
        season = _create_test_season()
        gameweek = _create_test_gameweek(season)

        self.assertTrue( gameweek.deadline_passed() )

    @patch('bets.models.Gameweek.get_rollable_allowances')
    def test__get_allowance_by_user(self, rollables ):
        season = _create_test_season()
        gameweek = _create_test_gameweek(season)
        user_one = User.objects.create_user('user_one')
        user_one.save()
        user_two = User.objects.create_user('user_two')
        user_two.save()
        rollables.return_value = { user_one: 123.0 }

        self.assertEquals( 223.0, gameweek._get_allowance_by_user( user_one ) )
        self.assertEquals( 100.0, gameweek._get_allowance_by_user( user_two ) )

    def test_get_rollable_allowances(self):
        season = _create_test_season()
        gameweek_one = _create_test_gameweek(season)
        gameweek_two = _create_test_gameweek(season)
        user_one = User.objects.create_user('user_one')
        user_one.save()

        gameweek_one.set_balance_by_user( user_one, 199.0, 29.9 )

        allowances = gameweek_two.get_rollable_allowances()

        self.assertIsNone( gameweek_one.get_rollable_allowances() )
        # will have to leave this for the time being - errors locally but seemingly for no reason
        self.assertEquals( 1, len(allowances) )
        self.assertIn( user_one, allowances )
        self.assertEquals( 199.0, allowances[user_one] )

    def test_get_ordered_results(self):
        season = _create_test_season()
        gameweek_one = _create_test_gameweek(season)
        gameweek_two = _create_test_gameweek(season)
        user_one = User.objects.create_user('user_one')
        user_one.save()
        user_two = User.objects.create_user('user_two')
        user_two.save()

        gameweek_one.set_balance_by_user( user_one, 1000.0, 0.0 )
        gameweek_one.set_balance_by_user( user_two, 500.0, 0.0 )

        gameweek_two.set_balance_by_user( user_one, -100.0, 0.0 )
        gameweek_two.set_balance_by_user( user_two, -100.0, 500.0 )

        results_one = gameweek_one.get_ordered_results()
        results_two = gameweek_two.get_ordered_results()

        self.assertEquals( 2, len(results_one) )
        self.assertEquals( [user_one, 1000.0, 1000.0, 0.0, '-'], results_one[0] )
        self.assertEquals( [user_two, 500.0, 500.0, 0.0, '-'], results_one[1] )

        self.assertEquals( 2, len(results_two) )
        self.assertEquals( [user_two, -100.0, 400.0, 400.0, '/\\'], results_two[0] )
        self.assertEquals( [user_one, -100.0, -100.0, -100.0, '\\/'], results_two[1] )

    def test__get_users_with_ready_bets_as_string(self):
        season = _create_test_season()
        gameweek = _create_test_gameweek(season)

        user_one = User.objects.create_user('user_one')
        user_one.save()
        user_two = User.objects.create_user('user_two')
        user_two.save()

        bet_container = BetContainer(owner = user_one, gameweek=gameweek)
        bet_container.save()
        accumulator = Accumulator(bet_container=bet_container, stake=100.0)
        accumulator.save()
        
        users_with_ready_bets = gameweek.get_users_with_ready_bets_as_string()

        self.assertIn(user_one.username, users_with_ready_bets)
        self.assertNotIn(user_two.username, users_with_ready_bets)

class BalanceTest(TestCase):

    def test__str__(self):
        season = _create_test_season()
        gameweek = _create_test_gameweek(season)
        user_one = User.objects.create_user('user_one')
        user_one.save()
        balance = Balance(gameweek=gameweek, user=user_one, week=100.0, provisional=100.0, banked=100.0)
        
        self.assertIn(str(gameweek), str(balance))
        self.assertIn(user_one.username, str(balance))

class GameTest(TestCase):

    def test_get_numerator(self):
        season = _create_test_season()
        gameweek = _create_test_gameweek(season)
        game = _create_test_game(gameweek)

        self.assertEquals(1, game.get_numerator('H'))
        self.assertEquals(1, game.get_numerator('D'))
        self.assertEquals(100, game.get_numerator('A'))

    def test_get_denominator(self):
        season = _create_test_season()
        gameweek = _create_test_gameweek(season)
        game = _create_test_game(gameweek)

        self.assertEquals(50, game.get_denominator('H'))
        self.assertEquals(20, game.get_denominator('D'))
        self.assertEquals(1, game.get_denominator('A'))
