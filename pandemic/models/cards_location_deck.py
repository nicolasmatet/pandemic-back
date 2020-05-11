from django.db import models


class CardsLocationDeck(models.Model):
    name = models.CharField(max_length=32)
    type = models.CharField(max_length=16)
    location = models.ForeignKey('MapLocation', null=True, default=None, on_delete=models.CASCADE)
