import enum

from django.db import models


class DiseaseStatusEnum(enum.Enum):
    ongoing = "ongoing"
    cured = "cured"
    eradicated = "eradicated"


class DiseaseStatus(models.Model):
    playroom = models.ForeignKey('PlayRoom', on_delete=models.CASCADE)
    disease_type = models.CharField(max_length=6, null=False)
    disease_status = models.CharField(max_length=10, default=DiseaseStatusEnum.ongoing.value)


class Disease(models.Model):
    map_state = models.ForeignKey('MapState', on_delete=models.CASCADE, null=False)
    disease_type = models.CharField(max_length=6, null=False)
    disease_count = models.IntegerField(default=0)
