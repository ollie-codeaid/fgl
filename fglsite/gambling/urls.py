from django.urls import path

from . import views

urlpatterns = [
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
        name="add-bet",
    ),
    path(
        "bets/<int:pk>/update-bet/",
        views.AccumulatorUpdateView.as_view(),
        name="update-bet",
    ),
    path(
        "bets/<int:pk>/delete-bet/",
        views.AccumulatorDeleteView.as_view(),
        name="delete-bet",
    ),
    path(
        "gameweek/<int:gameweek_id>/create-longterm/",
        views.LongSpecialCreateView.as_view(),
        name="create-longterm",
    ),
    path(
        "longterms/<int:pk>/update/",
        views.LongSpecialUpdateView.as_view(),
        name="update-longterm",
    ),
    path(
        "bets/<int:bet_container_id>/longterms/<int:long_special_container_id>/add-bet/",
        views.LongSpecialBetCreateView.as_view(),
        name="create-longterm-bet",
    ),
    path(
        "bets/longterms/<int:pk>/update-bet/",
        views.LongSpecialBetUpdateView.as_view(),
        name="update-longterm-bet",
    ),
    path(
        "gameweek/<int:gameweek_id>/create-longterm/",
        views.LongSpecialCreateView.as_view(),
        name="add-longterm-results",
    ),
]
