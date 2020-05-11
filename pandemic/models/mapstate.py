from django.db import models


class MapState(models.Model):
    playroom = models.ForeignKey('PlayRoom', related_name='mapstates', on_delete=models.CASCADE)
    location = models.ForeignKey('MapLocation', on_delete=models.CASCADE, related_name='location_map_state')
    research_center = models.BooleanField(default=False)
