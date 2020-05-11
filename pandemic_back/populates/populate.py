import csv

from pandemic.models.cards_location import CardType, CardEvent
from pandemic.models.maplocation import LocationType


def load_locations(apps, schema_editor):
    print("*** creating locations...")

    Map = apps.get_model('pandemic', 'Map')
    default_map, _ = Map.objects.get_or_create(name="default")
    MapLocation = apps.get_model('pandemic', 'MapLocation')
    all_locations = []
    with open('pandemic_back/populates/locations.csv', newline='') as csvfile:
        locations = csv.reader(csvfile, delimiter=',', quotechar='|')
        for name, loc_type, x, y, population in locations:
            all_locations.append(
                MapLocation(name=name, map=default_map, location_type=LocationType.__members__[loc_type].value,
                            x=float(x), y=float(y), population=population))
    MapLocation.objects.bulk_create(all_locations)


def set_starting_location(apps, schema_editor):
    Map = apps.get_model('pandemic', 'Map')
    MapLocation = apps.get_model('pandemic', 'MapLocation')
    default_map = Map.objects.get(name="default")
    starting_location = MapLocation.objects.get(name__iexact='atlanta')
    default_map.starting_location = starting_location
    default_map.save()


def load_connections(apps, schema_editor):
    print("*** creating links...")
    Map = apps.get_model('pandemic', 'Map')
    default_map = Map.objects.get(name="default")
    MapLocation = apps.get_model('pandemic', 'MapLocation')
    with open('pandemic_back/populates/connections.csv', newline='') as csvfile:
        connections = csv.reader(csvfile, delimiter=',', quotechar='|')
        for loc_from_name, loc_to_name in connections:
            loc_from = MapLocation.objects.get(name=loc_from_name, map=default_map)
            loc_to = MapLocation.objects.get(name=loc_to_name, map=default_map)
            loc_from.neighbors.add(loc_to)
            loc_from.save()


def load_cards_locations_deck(apps, schema_editor):
    print("*** creating cards...")

    Deck = apps.get_model('pandemic', 'CardsLocationDeck')
    MapLocation = apps.get_model('pandemic', 'MapLocation')
    all_locations = MapLocation.objects.all()
    all_deck = []
    for location in all_locations:
        all_deck.append(Deck(name=location.name, location=location, type=CardType.location.value))
    for name in CardEvent:
        all_deck.append(Deck(name=name.value, location=None, type=CardType.event.value))
    all_deck.append(Deck(name='épidémie', location=None, type=CardType.epidemic.value))
    Deck.objects.bulk_create(all_deck)
