from django.db import models

from pandemic.models.cards_location import CardPosition


class CardInfection(models.Model):
    playroom = models.ForeignKey('PlayRoom', related_name='card_infections', on_delete=models.CASCADE)
    name = models.CharField(max_length=32)
    location = models.ForeignKey('MapLocation', null=True, default=None, on_delete=models.CASCADE,
                                    related_name='location_card_infections')
    order = models.IntegerField()
    position = models.CharField(max_length=8, default=CardPosition.deck.value)

    class Meta:
        ordering = ['order']
