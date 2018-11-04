from django.contrib.auth.models import User
from django.db import models

from fglsite.bets.models import Season


class JoinRequest(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    player = models.ForeignKey(User, on_delete=models.CASCADE)

