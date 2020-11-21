from django.urls import path

from . import views

urlpatterns = [
    path("create_season/", views.SeasonCreateView.as_view(), name="create-season"),
    path("find_season/", views.find_season, name="find-season"),
    path("<int:pk>/", views.SeasonDetailView.as_view(), name="season"),
    path(
        "<int:season_id>/create_gameweek/",
        views.GameweekCreateView.as_view(),
        name="create-gameweek",
    ),
    path("gameweek/<int:pk>/", views.GameweekDetailView.as_view(), name="gameweek"),
    path(
        "gameweek/<int:pk>/update/",
        views.GameweekUpdateView.as_view(),
        name="update-gameweek",
    ),
    path(
        "gameweek/<int:gameweek_id>/add_results/",
        views.ResultsFormView.as_view(),
        name="add-gameweek-results",
    ),
]
