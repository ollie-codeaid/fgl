from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?P<season_id>[0-9]+)/$', views.season, name='season'),
    url(r'^(?P<season_id>[0-9]+)/create_gameweek/$', views.create_gameweek, name='create-gameweek'),
    url(r'^gameweek/(?P<gameweek_id>[0-9]+)/$', views.gameweek, name='gameweek'),
    url(r'^gameweek/(?P<gameweek_id>[0-9]+)/update/$', views.update_gameweek, name='update-gameweek'),
    url(r'^gameweek/(?P<gameweek_id>[0-9]+)/add_results/$', views.add_gameweek_results, name='add-gameweek-results'),
]
