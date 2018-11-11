from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^gameweek/(?P<gameweek_id>[0-9]+)/create_longterm/$', views.create_longterm, name='create-longterm'),
    url(r'^longterms/(?P<longspecial_id>[0-9]+)/update/$', views.update_longterm, name='update-longterm'),

    url(r'^gameweek/(?P<gameweek_id>[0-9]+)/manage_bet_container/$', views.manage_bet_container, name='manage-bet-container'),
    url(r'^bets/(?P<bet_container_id>[0-9]+)/my_bets/$', views.bet_container, name='bet-container'),

    url(r'^bets/(?P<bet_container_id>[0-9]+)/add_bet/$', views.add_bet, name='add-bet'),
    url(r'^bets/(?P<accumulator_id>[0-9]+)/update_bet/$', views.update_bet, name='update-bet'),
    url(r'^bets/(?P<bet_container_id>[0-9]+)/(?P<accumulator_id>[0-9]+)/delete_bet/$', views.delete_bet, name='delete-bet'),

    url(r'^longterms/(?P<bet_container_id>[0-9]+)/(?P<longspecial_id>[0-9]+)/manage_bet/$', views.manage_longterm_bet, name='manage-longterm-bet'),
]
