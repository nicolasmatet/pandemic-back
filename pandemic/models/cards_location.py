import enum

from django.db import models


class CardPosition(enum.Enum):
    hand = 'hand'
    special = 'special'
    deck = 'deck'
    dump = 'dump'
    removed = 'removed'


class CardEvent(enum.Enum):
    pont = 'Pont Aérien'
    subvention = "Subvention Publique"
    nuit = "Nuit Tranquille"
    population = "Population Résiliente"
    prevision = "Prévision"


class CardType(enum.Enum):
    epidemic = 'epidemic'
    location = 'location'
    event = 'event'


class CardLocation(models.Model):
    playroom = models.ForeignKey('PlayRoom', related_name='playroom_card_locations', on_delete=models.CASCADE)
    card = models.ForeignKey('CardsLocationDeck', max_length=32, on_delete=models.CASCADE,
                                related_name="card_location")
    order = models.IntegerField(default=None)
    position = models.CharField(max_length=8, default=CardPosition.deck.value)
    player = models.ForeignKey('Player', related_name='hand', on_delete=models.CASCADE, null=True)

    class Meta:
        ordering = ['order']
