from _ast import Set

import networkx as nx

from pandemic import errors
from pandemic.errors import NoResearchCenterPresent
from pandemic.game import cards, players


def get_location_type(game_state, location):
    return game_state.locations_types[location]


def get_neighbors(game_state, location):
    return nx.neighbors(game_state.location_network, location)


def is_neighbor(game_state, location1, location2):
    return (game_state.location_network.has_edge(location1, location2)
            or game_state.location_network.has_edge(location1, location2)) \
           or (has_research_center(game_state, location1) and has_research_center(game_state, location2))


def has_research_center(game_state, location):
    return location in game_state.locations_research_center


def build_research_center(game_state, player, location):
    game_state.locations_research_center[location] = True


def check_build_research_center(game_state, location):
    if has_research_center(game_state, location):
        raise errors.ResearchCenterAlreadyPresent


def destroy_research_center(game_state, location):
    if location not in game_state.locations_research_center:
        raise NoResearchCenterPresent
    del game_state.locations_research_center[location]


def get_all_neighbors(game_state, location, include_start=True) -> Set:
    location_network = game_state.location_network
    if not location in location_network:
        raise errors.NoSuchLocation
    neighbors = nx.neighbors(game_state.location_network, location)
    if include_start:
        return {location, *neighbors}
    return {*neighbors}
