import random
from typing import Dict, List

from django.db.models import Max

from pandemic.controller import maplocations
from pandemic.controller.utils import get_location_id, get_player_id
from pandemic.errors import TooManyPlayers, PlayerIsTaken, PlayerAlreadyExists, PlayerHasNoRole, RoleDoesNotExists, \
    RoleAlreadyTaken, PlayerUnready, GameHasStarted
from pandemic.models import Player, PlayRoom
from pandemic.models.cards_location import CardLocation
from pandemic.models.cards_location_deck import CardsLocationDeck
from pandemic.models.player import PlayerRolesEnum


def initialize_player_location(playroom):
    all_players = Player.objects.filter(playroom=playroom).all()
    location_init = maplocations.get_starting_location(playroom)
    for player in all_players:
        print("*************** player.name -> int location", location_init)
        player.location = location_init
        player.save()


def initialize_player_order(playroom):
    all_players = Player.objects.filter(playroom=playroom) \
        .annotate(max_population=Max('hand__card__location__population')) \
        .order_by('max_population')
    all_players.reverse()
    for idx, player in enumerate(all_players):
        player.order = idx


def initialize_current_player(playroom):
    starting_player = Player.objects.filter(playroom=playroom).order_by('order')[0]
    playroom.current_player = starting_player
    playroom.save()


def rename_player(player, new_name, playroom):
    if playroom.has_started:
        raise GameHasStarted
    if Player.objects.filter(name=new_name, playroom=playroom).exists():
        raise PlayerAlreadyExists
    player.name = new_name
    player.save()


def free_player(playroom, player_name):
    if Player.objects.filter(name=player_name, playroom=playroom).exists():
        player = Player.objects.get(name=player_name, playroom=playroom)
        if not playroom.has_started:
            player.delete()
        else:
            player.taken = False
            player.ready = False
            player.save()


def check_start_game(playroom) -> bool:
    all_ready = Player.objects.filter(playroom=playroom).values_list("ready", flat=True)
    for is_ready in all_ready:
        if not is_ready:
            raise PlayerUnready
    return True


def choose_role(player, role_name):
    if not role_name in PlayerRolesEnum.__members__:
        raise RoleDoesNotExists

    role = PlayerRolesEnum.__members__[role_name]
    if player.role == role.value:
        return
    playroom = PlayRoom.objects.get(id=player.playroom.id)
    if playroom.has_started:
        raise GameHasStarted
    if Player.objects.filter(playroom=player.playroom, role=role.value).count():
        raise RoleAlreadyTaken
    player.role = role.value
    player.save()


def ready_player(player: Player):
    if player.role is None:
        raise PlayerHasNoRole
    player.ready = True
    player.save()


def unready_player(player: Player):
    playroom = PlayRoom.objects.get(id=player.playroom.id)
    if playroom.has_started:
        raise GameHasStarted
    player.ready = False
    player.save()


def take_player(playername, playroom) -> Player:
    player = Player.objects.get(name=playername, playroom=playroom)
    if player.taken:
        raise PlayerIsTaken
    player.taken = True

    player.save()
    return player


def create_player(playername, playroom) -> Player:
    current_player_count = Player.objects.filter(playroom=playroom).count()
    if current_player_count >= 4:
        raise TooManyPlayers
    if Player.objects.filter(name=playername, playroom=playroom).exists():
        raise PlayerAlreadyExists
    player = Player.objects.create(name=playername, playroom=playroom, taken=True)
    return player


def get_players_locations(playroom) -> Dict[str, str]:
    all_players = Player.objects.filter(playroom=playroom).prefetch_related('location')
    return {get_player_id(player): get_location_id(player.location) for player in all_players}


def get_player_roles(playroom) -> Dict[str, int]:
    all_players = Player.objects.filter(playroom=playroom)
    return {get_player_id(player): player.role for player in all_players}


def get_players(playroom) -> List:
    all_players = Player.objects.filter(playroom=playroom).order_by('order')
    return [get_player_id(player) for player in all_players]
