from pandemic import errors
from pandemic.models.player import PlayerRolesEnum


def is_repartiteuse(game_state, player):
    return get_player_role(game_state, player) == PlayerRolesEnum.repartiteuse.value


def is_medecin(game_state, player):
    return get_player_role(game_state, player) == PlayerRolesEnum.medecin.value


def is_expert(game_state, player):
    return get_player_role(game_state, player) == PlayerRolesEnum.expert.value


def is_role(game_state, player, role):
    return get_player_role(game_state, player) == role


def get_player_role(game_state, player):
    return game_state.player_roles.get(player)


def get_player_location(game_state, player):
    return game_state.player_locations[player]


def set_player_location(game_state, player, to_location):
    if not to_location in game_state.locations_types:
        raise errors.NoSuchLocation
    game_state.player_locations[player] = to_location


def increment_plater_action(game_state):
    game_state.player_actions += 1


def next_player(game_state):
    idx_player = game_state.players.index(game_state.current_player)
    return game_state.players[(idx_player + 1) % len(game_state.players)]


def get_specialist_location(game_state):
    for player, location in game_state.player_locations.items():
        if is_role(game_state, player, PlayerRolesEnum.specialiste.value):
            return location
    return None
