from pandemic import errors, game
from pandemic.game.rules import Rules
from pandemic.models.player import PlayerRolesEnum


def check_not_enough_cards(game_state):
    if len(game_state.location_deck) <= 0:
        raise errors.Defeat


def is_epidemic(card):
    return card == "épidémie"


def _drawn_infection_cards(game_state, card_number):
    drawn_cards = game_state.infection_deck[-card_number:]
    game_state.infection_deck = game_state.infection_deck[:-card_number]

    game_state.infection_dump.extend(drawn_cards)
    return drawn_cards


def _draw_locations_cards(game_state, card_number=2):
    if len(game_state.location_deck) < card_number:
        return game_state.defeat()
    drawn_cards = game_state.location_deck[-card_number:]
    game_state.location_deck = game_state.location_deck[:-card_number]
    return drawn_cards


def add_cards_to_hand_epidemic(game_state, player, drawn_cards) -> int:
    epidemic_to_solve = 0
    for card in drawn_cards:
        if not is_epidemic(card):
            game_state.player_hands[player].append(card)
        else:
            epidemic_to_solve += 1
    return epidemic_to_solve


# def player_has(game_state, player, card):
#     return card in game_state.player_hands[player]


def player_hand_limit(game_state, player):
    return len(game_state.player_hands[player]) > Rules.max_hand_cards


def any_player_hand_limit(game_state):
    for player, hand in game_state.player_hands.items():
        if len(hand) > Rules.max_hand_cards:
            return True
    return False


def dump_card(game_state, player, card):
    hand = game_state.player_hands.get(player, [])
    if len(hand) < Rules.max_hand_cards:
        raise errors.CannotDumpCard
    try:
        hand.remove(card)
    except ValueError:
        raise errors.NoSuchCard

    game_state.location_dump.append(card)


def use_card(game_state, player, card):
    hand = game_state.player_hands.get(player, [])
    try:
        hand.remove(card)
    except ValueError:
        raise errors.NoSuchCard
    game_state.location_dump.append(card)


def use_cards(game_state, player, cards):
    hand = game_state.player_hands.get(player, [])
    try:
        for card in cards:
            hand.remove(card)
    except ValueError:
        raise errors.NoSuchCard
    game_state.location_dump.extend(cards)


def check_give_card(game_state, player_from, player_to, card):
    if not card in game_state.locations_types:
        raise errors.NotALocationCard
    player_from_location = game.players.get_player_location(game_state, player_from)
    player_to_location = game.players.get_player_location(game_state, player_to)
    if not (player_from_location == player_to_location):
        raise errors.NotInTheSamePlace
    is_chercheuse = game.players.is_role(game_state, player_from, PlayerRolesEnum.chercheuse.value)
    if not (is_chercheuse or player_from_location == card):
        raise errors.NoInTheRightPlace
    return True


def give_card(game_state, player_from, player_to, card):
    hand_from = game_state.player_hands.get(player_from, [])
    hand_to = game_state.player_hands.get(player_to, [])
    try:
        hand_from.remove(card)
        hand_to.append(card)
    except ValueError:
        raise errors.NoSuchCard
