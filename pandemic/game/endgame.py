from pandemic import errors
from pandemic.models.playroom import PlayPhases


def defeat(game_state):
    game_state.phase = PlayPhases.defeat.value
    raise errors.Defeat


def victory(game_state):
    game_state.phase = PlayPhases.victory.value
    raise errors.Victory
