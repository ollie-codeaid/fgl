from django.contrib import messages
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, render, redirect, reverse

from .models import JoinRequest
from fglsite.bets.models import Season


def join_season(request, season_id):
    season = get_object_or_404(Season, pk=season_id)

    if not request.user.is_authenticated:
        messages.error(request, 'Must be logged in to join season')
    elif request.user in season.players.all():
        messages.error(request, 'Already joined season')
    elif len(season.joinrequest_set.filter(player=request.user)) == 1:
        messages.error(request, 'Join request already sent to commissioner')
    elif season.public:
        season.players.add(request.user)
        season.save()
        messages.success(request, 'Added to season.')
    else:
        join_request = JoinRequest(season=season, player=request.user)
        join_request.save()
        messages.success(request, 'Join request sent to commissioner')
    return redirect('season', season_id=season.id)


def manage_joinrequests(request, season_id):
    season = get_object_or_404(Season, pk=season_id)
    return render(request, 'bets/manage_requests.html', {'season': season})


def _manage_joinrequest(request, joinrequest_id, accept):
    joinrequest = get_object_or_404(JoinRequest, pk=joinrequest_id)
    season = joinrequest.season
    if request.user != season.commissioner:
        messages.error(request,
                       'Only season Commissioner can approve/reject requests')
        return redirect(reverse('manage-requests', args=(season.id,)))

    player = joinrequest.player
    action = 'accept' if accept else 'reject'

    try:
        with transaction.atomic():
            if accept:
                season.players.add(player)
                season.save()
            joinrequest.delete()
    except IntegrityError as err:
        messages.error(request, 'Error {0}ing request'.format(action))
        messages.error(request, err)
        return redirect(reverse('manage-requests', args=(season.id,)))

    messages.success(
        request,
        '{0}\'s request {1}ed'.format(player.username, action))
    return redirect(reverse('manage-requests', args=(season.id,)))


def accept_joinrequest(request, joinrequest_id):
    return _manage_joinrequest(request, joinrequest_id, True)


def reject_joinrequest(request, joinrequest_id):
    return _manage_joinrequest(request, joinrequest_id, False)
