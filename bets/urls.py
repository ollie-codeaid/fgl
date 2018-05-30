from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^create_season/$', views.create_season, name='create-season'),
    url(r'^find_season/', views.find_season, name='find-season'),
    url(r'^(?P<season_id>[0-9]+)/$', views.season, name='season'),
    url(r'^(?P<season_id>[0-9]+)/join_season/$', views.join_season, name='join-season'),
    url(r'^(?P<season_id>[0-9]+)/manage_join_requests/$', views.manage_joinrequests, name='manage-requests'),
    url(r'^(?P<joinrequest_id>[0-9]+)/accept/$', views.accept_joinrequest, name='accept-request'),
    url(r'^(?P<joinrequest_id>[0-9]+)/reject/$', views.reject_joinrequest, name='reject-request'),
    url(r'^(?P<season_id>[0-9]+)/create_gameweek/$', views.create_gameweek, name='create-gameweek'),
    url(r'^gameweek/(?P<gameweek_id>[0-9]+)/$', views.gameweek, name='gameweek'),
    url(r'^gameweek/(?P<gameweek_id>[0-9]+)/update/$', views.update_gameweek, name='update-gameweek'),
    url(r'^gameweek/(?P<gameweek_id>[0-9]+)/add_results/$', views.add_gameweek_results, name='add-gameweek-results'),
    url(r'^gameweek/(?P<gameweek_id>[0-9]+)/manage_bet_container/$', views.manage_bet_container, name='manage-bet-container'),
    url(r'^bets/(?P<bet_container_id>[0-9]+)/my_bets/$', views.bet_container, name='bet-container'),
    url(r'^bets/(?P<bet_container_id>[0-9]+)/add_bet/$', views.add_bet, name='add-bet'),
    url(r'^bets/(?P<accumulator_id>[0-9]+)/update_bet/$', views.update_bet, name='update-bet'),
    url(r'^bets/(?P<bet_container_id>[0-9]+)/(?P<accumulator_id>[0-9]+)/delete_bet/$', views.delete_bet, name='delete-bet'),
]
