from django.urls import path

from . import views

urlpatterns = [
    path(
        "gameweek/<int:gameweek_id>/create_longterm/",
        views.create_longterm,
        name="create-longterm",
    ),
    path(
        "longterms/<int:longspecial_id>/update/",
        views.update_longterm,
        name="update-longterm",
    ),
    path(
        "gameweek/<int:gameweek_id>/manage-bets/",
        views.BetContainerCreateView.as_view(),
        name="manage-bet-container",
    ),
    path(
        "bets/<int:pk>/update-bets/",
        views.BetContainerDetailView.as_view(),
        name="update-bet-container",
    ),
    path(
        "bets/<int:bet_container_id>/add-bet/",
        views.AccumulatorCreateView.as_view(),
        name="add-bet"
    ),
    path(
        "bets/<int:pk>/update-bet/",
        views.AccumulatorUpdateView.as_view(),
        name="update-bet"
    ),
    path(
        "bets/<int:pk>/delete-bet/",
        views.AccumulatorDeleteView.as_view(),
        name="delete-bet",
    ),
    path(
        "longterms/<int:bet_container_id>/<int:longspecial_id>/manage_bet/",
        views.manage_longterm_bet,
        name="manage-longterm-bet",
    ),
]
