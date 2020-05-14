from collections import defaultdict

from pandemic import errors, game
from pandemic.game import players, endgame
from pandemic.game.rules import Rules
from pandemic.models.disease import DiseaseStatusEnum
from pandemic.models.player import PlayerRolesEnum


def cure_disease(game_state, player, cards):
    n_cards_required = get_n_cards_to_cure(game_state, player)
    if not cards or len(cards) < n_cards_required:
        raise errors.LocationCardsAreMissing
    disease_type = game_state.locations_types.get(cards[0])
    if disease_is_cured(game_state, disease_type):
        raise errors.DiseaseAlreadyCured
    for card in cards:
        card_type = game_state.locations_types.get(card)
        if card_type != disease_type:
            raise errors.LocationCardsNotMatching
    game.cards.use_cards(game_state, player, cards)
    set_disease_as_cured(game_state, disease_type)
    if players.is_medecin(game_state, player):
        auto_cure_diseases(game_state, players.get_player_location(game_state, player))
    if check_eradication(game_state, disease_type):
        set_disease_as_eradicated(game_state, disease_type)
    check_all_diseases_cured(game_state)


def get_n_cards_to_cure(game_state, player):
    if players.is_role(game_state, player, PlayerRolesEnum.scientifique.value):
        return Rules.cards_to_cure - 1
    return Rules.cards_to_cure


def auto_cure_diseases(game_state, location):
    diseases_count = game_state.locations_disease_count[location]
    for disease_type, count in diseases_count.items():
        if disease_is_cured(game_state, disease_type) and count:
            remove_disease_from_location(game_state, location, disease_type, number_to_heal=count)


def remove_disease_from_location(game_state, location, disease_type, number_to_heal=None):
    number_of_disease = game_state.locations_disease_count[location][disease_type]
    if number_to_heal is None:
        number_to_heal = number_of_disease
    game_state.locations_disease_count[location][disease_type] = max(0, number_of_disease - number_to_heal)
    if check_eradication(game_state, disease_type):
        set_disease_as_eradicated(game_state, disease_type)


def check_all_diseases_cured(game_state):
    for status in game_state.disease_status.items():
        if not (status == DiseaseStatusEnum.cured.value or status == DiseaseStatusEnum.cured.value):
            return False
    endgame.victory(game_state)


def disease_is_cured(game_state, disease_type):
    return game_state.disease_status.get(
        disease_type) == DiseaseStatusEnum.cured.value or game_state.disease_status.get(
        disease_type) == DiseaseStatusEnum.eradicated.value

def set_disease_as_cured(game_state, disease_type):
    game_state.disease_status[disease_type] = DiseaseStatusEnum.cured.value


def disease_is_eradicated(game_state, disease_type):
    return game_state.disease_status.get(disease_type) == DiseaseStatusEnum.eradicated.value


def check_eradication(game_state, disease_type):
    return (disease_is_cured(game_state, disease_type) and no_disease_left(game_state, disease_type))


def set_disease_as_eradicated(game_state, disease_type):
    game_state.disease_status[disease_type] = DiseaseStatusEnum.eradicated.value
    check_all_diseases_cured(game_state)


def no_disease_left(game_state, disease_type):
    count = 0
    for loc, dict_disease in game_state.locations_disease_count.items():
        count += dict_disease.get(disease_type, 0)
    return count == 0


def get_disease_to_heal(game_state, location):
    if location not in game_state.locations_disease_count:
        raise errors.NoDiseaseToCure
    disease_count = game_state.locations_disease_count[location]
    location_type = game_state.locations_types[location]
    if location_type in disease_count and disease_count[location_type] > 0:
        return location_type
    for disease_type, disease_count in disease_count.items():
        if disease_count > 0:
            return disease_type
    raise errors.NoDiseaseToCure


def get_number_of_disease_to_heal(game_state, player, location, disease_type):
    if players.is_medecin(game_state, player):
        return game_state.locations_disease_count[location][disease_type]
    if disease_is_cured(game_state, disease_type):
        return game_state.locations_disease_count[location][disease_type]
    return 1


def get_disease_count(game_state):
    disease_count = defaultdict(lambda: 0)
    for dict_diseases_count in game_state.locations_disease_count.values():
        for disease, count in dict_diseases_count.items():
            disease_count[disease] += count
    check_too_many_disease(disease_count)
    return disease_count


def check_too_many_outbreaks(game_state):
    if game_state.outbreaks > Rules.max_outbreaks:
        raise errors.Defeat


def check_too_many_disease(disease_count):
    for disease, count in disease_count.items():
        if count > Rules.max_diseases:
            raise errors.Defeat
