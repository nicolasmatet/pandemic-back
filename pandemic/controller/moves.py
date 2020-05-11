from pandemic.controller import cards
from pandemic.errors import NeedAResarchCenter, NotANeighbor, NeedCurrentLocationCard, NeedLocationCard
from pandemic.models import MapState
from pandemic.models.cards_location import CardLocation, CardPosition


def set_player_location(playroom, player, to_location):
    if player.playroom == playroom:
        player.location = to_location
        player.save()


def dump_card_and_move(playroom, player, card, to_location):
    cards.dump_location_cards([card])
    set_player_location(playroom, player, to_location)


def move_to_neighbor(playroom, player, to_location):
    player_location = player.location
    if not to_location in player_location.neighbors.all():
        raise NotANeighbor
    set_player_location(playroom, player, to_location)
    return to_location


def move_to_research_center(playroom, player, to_location):
    map_state_from = MapState.objects.get(playroom=playroom, location=player.location)
    map_state_to = MapState.objects.get(playroom=playroom, location=to_location)
    if not map_state_from.research_center or not map_state_to.research_center:
        raise NeedAResarchCenter
    set_player_location(playroom, player, to_location)
    return to_location


def move_by_dumping_current_location(playroom, player, to_location):
    try:
        card_to_dump = CardLocation.objects.get(playroom=playroom,
                                                position=CardPosition.hand.value,
                                                player=player,
                                                card__location=player.location)
        dump_card_and_move(playroom, player, card_to_dump, to_location)
    except CardLocation.DoesNotExist:
        raise NeedCurrentLocationCard


def move_by_dumping_to_location(playroom, player, to_location):
    try:
        card_to_dump = CardLocation.objects.get(playroom=playroom,
                                                position=CardPosition.hand.value,
                                                player=player,
                                                card__location=to_location)
        dump_card_and_move(playroom, player, card_to_dump, to_location)
    except CardLocation.DoesNotExist:
        raise NeedCurrentLocationCard


def move_dumping_on_research_center(playroom, player, to_location, card_name):
    map_state_from = MapState.objects.get(playroom=playroom, location=player.location)
    if not map_state_from.research_center:
        raise NeedAResarchCenter
    try:
        card_to_dump = CardLocation.objects.get(playroom=playroom, position=CardPosition.hand.value,
                                                player=player, card__name=card_name)
        dump_card_and_move(playroom, player, card_to_dump, to_location)
    except:
        raise NeedLocationCard
    return to_location


def move_to_player(playroom, player, player_to):
    if player.playroom == playroom:
        set_player_location(playroom, player, player_to.location)
    return player_to.location
