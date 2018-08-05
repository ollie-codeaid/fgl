from django.contrib.auth.models import User
from django.db import models
from wagtail.wagtailsnippets.models import register_snippet

from fglsite.bets.models import Season


@register_snippet
class JoinRequest(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    player = models.ForeignKey(User, on_delete=models.CASCADE)

