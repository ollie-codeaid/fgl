from django.urls import path

from . import views

urlpatterns = [
    path('create_season/', views.create_season, name='create-season'),
    path('find_season/', views.find_season, name='find-season'),
    path('<int:season_id>/', views.season, name='season'),

    path('<int:season_id>/create_gameweek/', views.create_gameweek, name='create-gameweek'),
    path('gameweek/<int:gameweek_id>/', views.gameweek, name='gameweek'),
    path('gameweek/<int:gameweek_id>/update/', views.update_gameweek, name='update-gameweek'),
    path('gameweek/<int:gameweek_id>/add_results/', views.add_gameweek_results, name='add-gameweek-results'),
]
