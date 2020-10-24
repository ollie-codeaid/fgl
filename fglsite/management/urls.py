from django.urls import path

from . import views

urlpatterns = [
    path(
        '<int:season_id>/join_season/',
        views.join_season,
        name='join-season'
    ),
    path(
        '<int:season_id>/manage_joinrequests/',
        views.manage_joinrequests,
        name='manage-requests'
    ),
    path(
        '<int:joinrequest_id>/accept/',
        views.accept_joinrequest,
        name='accept-request'
    ),
    path(
        '<int:joinrequest_id>/reject/',
        views.reject_joinrequest,
        name='reject-request'
    ),
]
