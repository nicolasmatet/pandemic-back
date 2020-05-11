import enum

from django.db import models


class LocationType(enum.Enum):
    black = "black"
    blue = "blue"
    red = "red"
    yellow = "yellow"


class LocationLinkTypes(enum.Enum):
    neighbor = 0
    research_center = 1


serialization_fields = ["name", "location_type", "population", "x", "y"]


class MapLocation(models.Model):
    name = models.CharField(max_length=32)
    location_type = models.CharField(max_length=8)
    population = models.IntegerField()
    neighbors = models.ManyToManyField('MapLocation', related_name='rel_neighbors')
    map = models.ForeignKey('Map', related_name='maplocations', on_delete=models.CASCADE)
    x = models.FloatField()
    y = models.FloatField()

    def serialize(self):
        dict_location = {field: getattr(self, field) for field in serialization_fields}
        dict_location['neighbors'] = list(self.neighbors.all().values_list('name', flat=True))
        return dict_location

