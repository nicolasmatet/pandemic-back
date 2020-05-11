from django.db import models


class Map(models.Model):
    name = models.CharField(max_length=32)
    starting_location = models.ForeignKey('MapLocation', on_delete=models.SET_NULL, null=True,
                                          related_name='starting_map')
