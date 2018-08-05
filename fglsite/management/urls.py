from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^(?P<season_id>[0-9]+)/join_season/$',
        views.join_season,
        name='join-season'
    ),
    url(
        r'^(?P<season_id>[0-9]+)/manage_joinrequests/$',
        views.manage_joinrequests,
        name='manage-requests'
    ),
    url(
        r'^(?P<joinrequest_id>[0-9]+)/accept/$',
        views.accept_joinrequest,
        name='accept-request'
    ),
    url(
        r'^(?P<joinrequest_id>[0-9]+)/reject/$',
        views.reject_joinrequest,
        name='reject-request'
    ),
]
