import random

from pandemic import game
from pandemic.game import players, locations
from pandemic.game.cards import _drawn_infection_cards
from pandemic.game.diseases import check_too_many_outbreaks, disease_is_cured, auto_cure_diseases
from pandemic.game.locations import get_neighbors, get_location_type
from pandemic.game.rules import Rules
from pandemic.models.player import PlayerRolesEnum
from pandemic.models.playroom import PlayPhases


def solve_epidemic(game_state):
    if game_state.epidemics_to_solve > 0:
        location = game_state.infection_deck[0]
        infect_locations(game_state, [location], infection_number=3)
        game_state.infection_deck.pop(0)
        game_state.epidemics_to_solve -= 1
        game_state.infection_dump.append(location)


def shuffle_infection_dump(game_state):
    if game_state.infection_dump:
        random.shuffle(game_state.infection_dump)
        game_state.infection_deck.extend(game_state.infection_dump)
        game_state.infection_dump = []


def infections(game_state):
    number_of_infections = Rules.infections[game_state.epidemics]
    drawn_cards = _drawn_infection_cards(game_state, number_of_infections)

    protected = set()
    specialist_location = players.get_role_location(game_state, PlayerRolesEnum.specialiste.value)
    if specialist_location:
        protected = locations.get_all_neighbors(game_state, specialist_location)
    infect_locations(game_state, drawn_cards, visited=protected)
    medic_location = players.get_role_location(game_state, PlayerRolesEnum.medecin.value)
    if medic_location:
        auto_cure_diseases(game_state, medic_location)


def infect_locations(game_state, locations, infection_number=1, disease_type=None, visited=None):
    if visited is None:
        visited = set()
    for location in locations:
        infection_location(game_state, location, infection_number, visited, disease_type=disease_type)


def infection_location(game_state, location, infection_number, visited, disease_type=None):
    if location not in visited:
        disease_type = disease_type if disease_type is not None else get_location_type(game_state, location)
        if game.diseases.disease_is_eradicated(game_state, disease_type):
            return
        if game_state.locations_disease_count[location][disease_type] + infection_number < Rules.max_infections + 1:
            game_state.locations_disease_count[location][disease_type] += infection_number
        else:
            game_state.locations_disease_count[location][disease_type] = Rules.max_infections
            game_state.outbreaks += 1
            check_too_many_outbreaks(game_state)
            visited.add(location)
            neighbors = get_neighbors(game_state, location)
            infect_locations(game_state, neighbors, infection_number=1, disease_type=disease_type, visited=visited)
