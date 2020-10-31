from django.urls import path

from . import views

urlpatterns = [
    path('create_season/', views.SeasonCreateView.as_view(), name='create-season'),
    path('find_season/', views.find_season, name='find-season'),
    path('<int:pk>/', views.SeasonDetailView.as_view(), name='season'),

    path('<int:season_id>/create_gameweek/', views.create_gameweek, name='create-gameweek'),
    path('gameweek/<int:gameweek_id>/', views.gameweek, name='gameweek'),
    path('gameweek/<int:gameweek_id>/update/', views.update_gameweek, name='update-gameweek'),
    path('gameweek/<int:gameweek_id>/add_results/', views.add_gameweek_results, name='add-gameweek-results'),
]
