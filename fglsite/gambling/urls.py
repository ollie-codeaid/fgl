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
        "gameweek/<int:gameweek_id>/manage_bet_container/",
        views.manage_bet_container,
        name="manage-bet-container",
    ),
    path(
        "bets/<int:bet_container_id>/my_bets/",
        views.bet_container,
        name="bet-container",
    ),
    path("bets/<int:bet_container_id>/add_bet/", views.add_bet, name="add-bet"),
    path("bets/<int:accumulator_id>/update_bet/", views.update_bet, name="update-bet"),
    path(
        "bets/<int:bet_container_id>/<int:accumulator_id>/delete_bet/",
        views.delete_bet,
        name="delete-bet",
    ),
    path(
        "longterms/<int:bet_container_id>/<int:longspecial_id>/manage_bet/",
        views.manage_longterm_bet,
        name="manage-longterm-bet",
    ),
]
