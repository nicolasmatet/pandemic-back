import enum

from django.db import models


class PlayerRolesEnum(enum.Enum):
    medecin = "medecin"
    planificateur = "planificateur"
    repartiteuse = "repartiteuse"
    scientifique = "scientifique"
    expert = "expert"
    specialiste = "specialiste"
    chercheuse = "chercheuse"


class Player(models.Model):
    name = models.CharField(max_length=64)
    taken = models.BooleanField(default=True)
    ready = models.BooleanField(default=False)
    role = models.CharField(max_length=16, null=True)
    order = models.IntegerField(default=0)
    location = models.ForeignKey('MapLocation', related_name='map_states',
                                 on_delete=models.SET_DEFAULT, null=True,
                                 blank=True,
                                 default=None)
    playroom = models.ForeignKey('PlayRoom', related_name='players', on_delete=models.CASCADE)
