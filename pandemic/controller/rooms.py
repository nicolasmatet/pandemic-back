import secrets
from typing import List

from pandemic.games import AllGames
from pandemic.models import Player, PlayRoom, Map


def create_room():
    play_token = secrets.token_hex(8)
    default_map = Map.objects.get(name="default")
    playroom = PlayRoom.objects.create(name=play_token, map=default_map)
    return playroom


def start_game(playroom):
    return AllGames.start_game(playroom)


def get_player_status(player):
    if not player:
        return None
    return {
        'name': player.name,
        'taken': player.taken,
        'role': player.role,
        'is_ready': player.ready
    }


def get_playroom_state(playroom):
    players = get_all_players_status(playroom)
    has_started = playroom.has_started
    return {
        "players": players,
        "has_started": has_started
    }


def get_all_players_status(playroom):
    all_players: List[Player] = Player.objects.filter(playroom=playroom).all()
    all_players_status = []
    for player in all_players:
        player_status = get_player_status(player)
        if player_status:
            all_players_status.append(player_status)
    return all_players_status
