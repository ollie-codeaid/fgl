# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render


def index(request):
    user_season_list = []

    if request.user.is_authenticated():
        for season in request.user.seasons.all():
            user_season_list.append(season)
    
    context = {'season_list': user_season_list}
    return render(request, 'common/index.html', context)
