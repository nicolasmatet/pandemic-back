import random
from collections import defaultdict
from typing import List, Dict

from pandemic.controller.utils import get_card_id, get_player_id
from pandemic.models import Player
from pandemic.models.cards_infection import CardInfection
from pandemic.models.cards_location import CardLocation, CardPosition, CardType
from pandemic.models.cards_location_deck import CardsLocationDeck
from pandemic.models.maplocation import MapLocation


def initial_location_cards_setup(playroom):
    CardLocation.objects.filter(playroom=playroom).delete()
    all_players = Player.objects.filter(playroom=playroom)
    all_location_cards = [card for card in
                          CardsLocationDeck.objects.filter(type=CardType.location.value).filter(
                              location__map=playroom.map)]
    all_events_cards = [card for card in CardsLocationDeck.objects.filter(type=CardType.event.value)]
    card_epidemic = CardsLocationDeck.objects.get(type=CardType.epidemic.value)
    all_deck_cards = [*all_events_cards, *all_location_cards]
    all_playroom_cards = []
    # shuffte the cards
    random.shuffle(all_deck_cards)

    # give cards to players
    player_count = all_players.count()
    card_per_player = 6 - player_count
    player_cards = all_deck_cards[0:player_count * card_per_player]
    for player_idx, player in enumerate(all_players):
        for card_idx in range(player_idx * card_per_player, (player_idx + 1) * card_per_player):
            card = player_cards[card_idx]
            all_playroom_cards.append(
                CardLocation(playroom=playroom, card=card, position=CardPosition.hand.value, player=player,
                             order=-1 - card_idx))

    deck_cards = all_deck_cards[player_count * card_per_player:]
    epidemic_number = 5
    subdeck_size = (53 - player_count * card_per_player) // epidemic_number
    list_int_epidemic_pos = [i * subdeck_size + random.randrange(0, subdeck_size) for i in range(0, epidemic_number)]
    list_int_epidemic_pos.reverse()
    order = 0
    for card in deck_cards:
        all_playroom_cards.append(CardLocation(playroom=playroom, card=card, order=order))
        if list_int_epidemic_pos and order == list_int_epidemic_pos[-1]:
            order += 1
            list_int_epidemic_pos.pop()
            all_playroom_cards.append(CardLocation(playroom=playroom, card=card_epidemic, order=order))
        order += 1
    CardLocation.objects.bulk_create(all_playroom_cards)


def initial_infection_cards_setup(playroom):
    CardInfection.objects.filter(playroom=playroom).delete()

    all_locations = [loc for loc in MapLocation.objects.filter(map=playroom.map)]
    random.shuffle(all_locations)
    all_playroom_infection = []
    for order, loc in enumerate(all_locations):
        all_playroom_infection.append(CardInfection(playroom=playroom, name=loc.name, location=loc, order=order))
    CardInfection.objects.bulk_create(all_playroom_infection)


def draw_infections(playroom, infection_number: int) -> List[CardInfection]:
    draw_cards = CardInfection.objects.filter(playroom=playroom, position=CardPosition.deck.value).all()[
                 :infection_number]
    for card in draw_cards:
        card.position = CardPosition.dump.value
    CardInfection.objects.bulk_update(draw_cards, ['position'])
    return draw_cards


def reload_infection_dump(playroom):
    dumped_cards = [c for c in CardInfection.objects.filter(playroom=playroom, position=CardPosition.dump.value).all()]
    random.shuffle(dumped_cards)
    for idx, card in enumerate(dumped_cards):
        card.position = CardPosition.deck.value
        card.order = idx
    CardInfection.objects.bulk_update(dumped_cards, ['order', 'position'])


def draw_locations(playroom, player, location_number=2) -> List[CardLocation]:
    draw_cards = CardLocation.objects.filter(playroom=playroom, position=CardPosition.deck.value).all() \
                     .prefetch_related('card')[:location_number]
    for card in draw_cards:
        card.position = CardPosition.dump.value if card.card.type == CardType.epidemic.value else CardPosition.hand.value
        card.player = player
    CardLocation.objects.bulk_update(draw_cards, ['position', 'player'])
    return draw_cards


def transfer_between_player(playroom, player_from, player_to, card_name):
    card = CardLocation.objects.get(playroom=playroom, position=CardPosition.hand.value, player=player_from,
                                    card__name=card_name)
    card.player = player_to
    return card


def _check_card_type(cards: List[CardLocation], target_type):
    for card in cards:
        if not card.card.location.location_type == target_type:
            return False
    return True


def dump_location(playroom, card_name: str) -> CardLocation:
    card = CardLocation.objects.get(playroom=playroom, position=CardPosition.hand.value, card__name=card_name)
    card.position = CardPosition.dump.value
    card.save()
    return card


def dump_location_cards(cards: List[CardLocation]):
    for card in cards:
        card.position = CardPosition.dump.value
    CardLocation.objects.bulk_update(cards)


def remove_location(playroom, card_name: str) -> CardLocation:
    card = CardLocation.objects.get(playroom=playroom, card__type=CardType.event.value,
                                    position=CardPosition.hand.value, card__name=card_name)
    card.position = CardPosition.removed.value
    card.save()
    return card


def remove_infection(playroom, card_name: str) -> CardLocation:
    card = CardInfection.objects.get(playroom=playroom, name=card_name)
    card.position = CardPosition.removed.value
    card.save()
    return card


def get_players_hands(playroom) -> Dict[str, List[str]]:
    hands = defaultdict(list)
    all_player = playroom.players.all()
    cards = CardLocation.objects.filter(position=CardPosition.hand.value, player__in=all_player) \
        .prefetch_related('player', 'card')
    for card in cards:
        hands[get_player_id(card.player)].append(get_card_id(card.card))
    return hands


def get_location_deck(playroom) -> List[str]:
    return list(
        CardLocation.objects.filter(playroom=playroom, position=CardPosition.deck.value).values_list('card__name',
                                                                                                     flat=True))


def get_infection_deck(playroom) -> List[str]:
    return list(CardInfection.objects.filter(playroom=playroom, position=CardPosition.deck.value).values_list('name',
                                                                                                              flat=True))


def get_location_dump(playroom) -> List[str]:
    return list(
        CardLocation.objects.filter(playroom=playroom, position=CardPosition.dump.value).values_list('card__name',
                                                                                                     flat=True))


def get_infection_dump(playroom) -> List[str]:
    return list(CardInfection.objects.filter(playroom=playroom, position=CardPosition.dump.value).values_list('name',
                                                                                                              flat=True))
