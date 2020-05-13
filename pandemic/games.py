from abc import abstractmethod
import copy
from typing import Union, Hashable, Set

import pandemic.game as game
import pandemic.controller as controller
from pandemic.controller.maplocations import get_location_graph, get_location_types
from pandemic.controller.utils import get_player_id
from pandemic import errors
from pandemic.game.rules import Rules
from pandemic.models import DiseaseStatus
from pandemic.models.cards_location import CardEvent
from pandemic.models.disease import DiseaseStatusEnum
from pandemic.models.player import PlayerRolesEnum
from pandemic.models.playroom import PlayPhases


class GameTools:
    @classmethod
    def backup_point(cls, func):
        def wrapper(*args):
            game = args[0]
            res = func(*args)
            game.do_backup()
            return res

        return wrapper

    @classmethod
    def require_phase(cls, phase):
        def decorator(func):
            def wrapper(*args):
                game = args[0]
                if not game.game_state.phase == phase:
                    raise errors.InvalidGamePhase
                return func(*args)

            return wrapper

        return decorator


class GameStateTools:
    @classmethod
    def check_endgame(cls, func):
        def wrapper(*args):
            try:
                return func(*args)
            except (errors.Victory, errors.Defeat):
                game_state = args[0]
                return game_state.serialize()

        return wrapper

    @classmethod
    def require_current_player(cls, func):
        def wrapper(*args):
            game_state = args[0]
            actiong_player = args[1]
            if actiong_player == game_state.current_player:
                return func(*args)
            raise errors.NotYourTurn

        return wrapper

    @classmethod
    def require_action(cls, func):
        def wrapper(*args):
            game_state = args[0]
            if game_state.player_actions < Rules.max_actions:
                dict_game_state_changes = func(*args)
                game.players.increment_plater_action(game_state)
                dict_game_state_changes['player_actions'] = game_state.player_actions
                return dict_game_state_changes
            raise errors.RequireAction

        return wrapper

    @classmethod
    def require_phase(cls, phase: Union[Hashable, Set]):
        def decorator(func):
            if isinstance(phase, set):
                test = lambda game_state: game_state.phase in phase
            else:
                test = lambda game_state: game_state.phase == phase

            def wrapper(*args):
                game_state = args[0]
                if not test(game_state):
                    raise errors.InvalidGamePhase
                return func(*args)

            return wrapper

        return decorator

    @classmethod
    def require_role(cls, role: Union[Hashable, Set]):
        def decorator(func):
            if isinstance(role, set):
                test = lambda game_state: game_state.player_roles[game_state.current_player] in role
            else:
                test = lambda game_state: game_state.player_roles[game_state.current_player] == role

            def wrapper(*args):
                game_state = args[0]
                if not test(game_state):
                    raise errors.InvalidPlayer
                return func(*args)

            return wrapper

        return decorator


class AllGames:
    dict_playroom_to_game = dict()

    @classmethod
    def register_game(cls, playroom):
        if playroom.name not in cls.dict_playroom_to_game:
            new_game = Game(playroom)
            cls.dict_playroom_to_game[playroom.name] = new_game
            return new_game
        else:
            return cls.dict_playroom_to_game[playroom.name]

    @classmethod
    def delete_game(cls, playroom):
        del cls.dict_playroom_to_game[playroom.name]

    @classmethod
    def get_game(cls, playroom) -> 'Game':
        return cls.dict_playroom_to_game.get(playroom.name)

    @classmethod
    def start_game(cls, playroom):
        game = cls.get_game(playroom)
        if not game:
            game = cls.register_game(playroom)
        return game.start_game()

    @classmethod
    def get_game_state(cls, playroom):
        game = cls.get_game(playroom)
        if not game and playroom.has_started:
            cls.start_game(playroom)
        if not game:
            return {}
        return cls.get_game(playroom).get_game_state()

    @classmethod
    def register_action(cls, playroom, player, game_action):
        game = cls.get_game(playroom)
        if not game:
            raise errors.GameHasNotStarted
        return game.register_action(player, game_action)

    @classmethod
    def get_next_infections(cls, playroom, player, n=6, need_card=True):
        game = cls.get_game(playroom)
        if not game:
            raise errors.GameHasNotStarted
        return game.get_next_infections(player, n, need_card)

    @classmethod
    def set_next_infections(cls, playroom, player, cards):
        game = cls.get_game(playroom)
        if not game:
            raise errors.GameHasNotStarted
        return game.set_next_infections(player, cards)

    @classmethod
    def cancel_last_action(cls, playroom, player):
        game = cls.get_game(playroom)
        return game.cancel_last_action(player)


class Game:
    move_event = {'player_locations'}
    heal_event = {'locations_disease_count', 'disease_status', 'phase'}
    infection_event = {'infection_deck_count', 'infection_dump', 'locations_disease_count', 'disease_status',
                       'outbreaks', 'epidemics', 'phase', 'current_player'}
    drawn_location_event = {'player_hands', 'location_deck_count', 'epidemics', 'phase'}
    dump_location_event = {'player_hands', 'location_dump', 'phase'}
    build_event = {'locations_research_center', 'phase'}
    cure_event = {'disease_status'}
    give_card_event = ['player_hands', 'phase']
    end_turn_event = {'player_actions', 'current_player', 'phase'}

    @staticmethod
    def events(*args):
        for event in args:
            for field in event:
                yield field

    def __init__(self, playroom):
        self.playroom = playroom
        self.game_state = GameState(playroom)
        self.backup_game_state = copy.copy(self.game_state)
        self.actions = []

    @GameTools.backup_point
    def start_game(self):
        if not self.playroom.has_started:
            self._initialize_game(self.playroom)
            self.playroom.has_started = True
            self.playroom.save()
        res_start = self.game_state.start_game()
        return res_start

    def _initialize_game(self, playroom):
        controller.cards.initial_location_cards_setup(playroom)
        controller.cards.initial_infection_cards_setup(playroom)
        controller.maplocations.initialize_map_states(playroom)
        controller.maplocations.initialize_infections(playroom)
        controller.players.initialize_player_location(playroom)
        controller.maplocations.initialize_research_centers(playroom)
        controller.players.initialize_player_order(playroom)
        controller.players.initialize_current_player(playroom)

    def register_action(self, player, game_action: 'GameAction'):
        dict_changes = self.apply_action(player, game_action)
        if game_action.cancellable:
            self.actions.append(game_action)
        else:
            self.actions = []
            self.do_backup()
        return dict_changes

    @GameTools.backup_point
    def get_next_infections(self, player, n, need_card):
        next_infections = self.game_state.get_next_infections(get_player_id(player), n, need_card)
        self.actions = []
        return next_infections

    @GameTools.backup_point
    def set_next_infections(self, player, cards):
        self.actions = []
        return self.game_state.set_next_infections(player, cards)

    def apply_action(self, player, game_action):
        dict_game_state_changes = game_action.apply_to_game_state(get_player_id(player), self.game_state)
        dict_game_state_changes['cancellable'] = game_action.cancellable
        return dict_game_state_changes

    @GameTools.require_phase(PlayPhases.player_action.value)
    def cancel_last_action(self, player):
        if player == self.game_state.current_player:
            raise errors.NotYourTurn
        if self.actions:
            self.actions.pop()
        self.reload_backup()
        for game_action in self.actions:
            self.apply_action(player, game_action)
        dict_state = self.game_state.serialize()
        dict_state['cancellable'] = self.actions and self.actions[0].cancellable
        return dict_state

    def get_game_state(self):
        return self.game_state.serialize()

    def do_backup(self):
        self.backup_game_state = copy.deepcopy(self.game_state)

    def reload_backup(self):
        self.game_state = copy.deepcopy(self.backup_game_state)


def disease_status_adapter(game_state):
    disease_count = game.diseases.get_disease_count(game_state)
    return [{'type': d_type, 'count': d_count, 'status': game_state.disease_status.get(d_type)}
            for d_type, d_count in disease_count.items()]


class GameState:

    def __init__(self, playroom):
        self.serialization_fields = ['player_roles', 'player_locations', 'player_hands', 'locations_disease_count',
                                     'locations_research_center', 'disease_status', 'location_deck_count',
                                     'infection_deck_count',
                                     'location_dump', 'infection_dump', 'epidemics', 'outbreaks',
                                     'outbreaks', 'phase',
                                     'epidemics_to_solve', 'player_actions', 'current_player', 'locations_types',
                                     'cancellable']
        self.serialization_adapters = {
            'location_deck_count': lambda game_state: len(game_state.location_deck),
            'infection_deck_count': lambda game_state: len(game_state.infection_deck),
            'locations_disease_count': lambda game_state: [{'location': location,
                                                            'diseases': [{'type': d_type, 'count': d_count}
                                                                         for d_type, d_count in diseases.items()]}
                                                           for location, diseases in
                                                           game_state.locations_disease_count.items()],
            'disease_status': disease_status_adapter
        }

        self.playroom = playroom
        self.players = []
        self.player_roles = dict()
        self.player_locations = dict()
        self.player_hands = dict()
        self.locations_disease_count = dict()
        self.locations_research_center = dict()
        self.disease_status = dict()
        self.location_deck = list()
        self.infection_deck = list()
        self.location_dump = list()
        self.infection_dump = list()
        self.epidemics = 0
        self.outbreaks = 0
        self.phase = PlayPhases.not_started.value
        self.phase_on_hold = None
        self.epidemics_to_solve = 0
        self.player_actions = 0
        self.location_network = None
        self.current_player = None
        self.locations_types = dict()
        self.cancellable = False
        self.nuit_tranquille = False

    def start_game(self):
        self.players = controller.players.get_players(self.playroom)
        self.player_roles = controller.players.get_player_roles(self.playroom)
        self.player_locations = controller.players.get_players_locations(self.playroom)
        self.player_hands = controller.cards.get_players_hands(self.playroom)
        self.locations_disease_count = controller.maplocations.get_disease_count(self.playroom)
        self.locations_research_center = controller.maplocations.get_research_center(self.playroom)
        self.disease_status = controller.maplocations.get_disease_status(self.playroom)
        self.location_deck = controller.cards.get_location_deck(self.playroom)
        self.infection_deck = controller.cards.get_infection_deck(self.playroom)
        self.location_dump = controller.cards.get_location_dump(self.playroom)
        self.infection_dump = controller.cards.get_infection_dump(self.playroom)
        self.epidemics = self.playroom.epidemics
        self.outbreaks = self.playroom.outbreaks
        self.phase = PlayPhases.player_action.value

        self.epidemics_to_solve = self.playroom.epidemics_to_solve
        self.player_actions = self.playroom.player_actions
        self.location_network = get_location_graph(self.playroom)
        self.locations_types = get_location_types(self.playroom)

        self.current_player = get_player_id(self.playroom.current_player)

        self.nuit_tranquille = self.playroom.nuit_tranquille
        return self.serialize()

    def serialize(self):
        return self.serialize_fields(self.serialization_fields)

    def serialize_fields(self, fields):
        return {
            field: getattr(self, field)
            if field not in self.serialization_adapters
            else self.serialization_adapters[field](self)
            for field in fields
        }

    def hold_phase(self, new_phase):
        self.phase_on_hold = self.phase
        self.phase = new_phase

    def resume_phase(self):
        if not self.phase_on_hold:
            self.phase = PlayPhases.player_action
        else:
            self.phase = self.phase_on_hold
            self.phase_on_hold = None
        return self.phase

    @GameStateTools.check_endgame
    @GameStateTools.require_current_player
    @GameStateTools.require_action
    @GameStateTools.require_phase(PlayPhases.player_action.value)
    def move(self, player, moving_player, to_location):
        is_repartiteuse = game.players.is_repartiteuse(self, player)
        if not (player == moving_player or is_repartiteuse):
            raise errors.CannotMoveOthers
        player_location = game.players.get_player_location(self, moving_player)
        if not game.locations.is_neighbor(self, player_location, to_location):
            players_at_to_location = list(
                filter(lambda location: location == to_location, self.player_locations.values()))
            if not (is_repartiteuse and players_at_to_location):
                raise errors.NotANeighbor
        return self._do_move(moving_player, to_location)

    def _do_move(self, moving_player, to_location):
        game.players.set_player_location(self, moving_player, to_location)
        if game.players.is_medecin(self, moving_player):
            game.diseases.auto_cure_diseases(self, to_location)
            return self.serialize_fields(Game.events(Game.move_event, Game.heal_event))
        return self.serialize_fields(Game.move_event)

    def pont_aerien(self, player, moving_player, location):
        game.cards.use_card(self, player, CardEvent.pont.value)
        dict_changes = self._do_move(moving_player, location)
        self.check_dump_phase()
        dict_change_hand = self.serialize_fields(Game.dump_location_event)
        dict_changes.update(dict_change_hand)
        return dict_changes

    def play_population_resiliente(self, player, infection_card):
        game.cards.use_card(self, player, CardEvent.population.value)
        try:
            self.infection_dump.remove(infection_card)
        except:
            raise errors.NoSuchCard
        self.check_dump_phase()
        return self.serialize_fields(Game.events(Game.infection_event, Game.dump_location_event))

    def get_next_infections(self, player, n, need_card):
        if need_card:
            game.cards.use_card(self, player, CardEvent.prevision.value)
            self.check_dump_phase()
        if self.phase == PlayPhases.solve_epidemic.value:
            game.infections.shuffle_infection_dump(self)

        next_infections = self.infection_deck[-n:]
        next_infections.reverse()
        return next_infections

    def set_next_infections(self, player, cards):
        max_cards = 6
        if len(cards) > max_cards:
            raise errors.TooManyCards

        set_top_deck = set(self.infection_deck[-len(cards):])
        for card in cards:
            if not card in set_top_deck:
                raise errors.InvalidCard
        self.infection_deck[-len(cards):] = cards[::-1]
        return self.serialize_fields(Game.events(Game.dump_location_event, Game.infection_event))

    def play_nuit_tranquille(self, player):
        game.cards.use_card(self, player, CardEvent.nuit.value)
        self.nuit_tranquille = True
        self.check_dump_phase()
        return self.serialize_fields(Game.dump_location_event)

    @GameStateTools.check_endgame
    @GameStateTools.require_current_player
    @GameStateTools.require_action
    @GameStateTools.require_phase(PlayPhases.player_action.value)
    def heal(self, player, disease_type=None):
        player_location = game.players.get_player_location(self, player)
        if not disease_type in self.disease_status:
            disease_type = game.diseases.get_disease_to_heal(self, player_location)
        number_of_disease_to_heal = game.diseases.get_number_of_disease_to_heal(self, player, player_location,
                                                                                disease_type)
        game.diseases.remove_disease_from_location(self, player_location, disease_type, number_of_disease_to_heal)
        return self.serialize_fields(Game.heal_event)

    @GameStateTools.require_phase(PlayPhases.dump_card.value)
    def dump_card(self, player, *cards):
        for card in cards:
            game.cards.dump_card(self, player, card)
            if not game.cards.player_hand_limit(self, player):
                break
        new_phase = self.check_dump_phase()
        dict_change = self.serialize_fields(Game.dump_location_event)
        if new_phase == PlayPhases.end_turn.value:
            dict_end_turn = self.end_turn(player)
            dict_change.update(dict_end_turn)
        return dict_change

    def check_dump_phase(self):
        if self.phase == PlayPhases.dump_card.value:
            if game.cards.any_player_hand_limit(self):
                self.phase = PlayPhases.dump_card.value
            else:
                return self.resume_phase()

    @GameStateTools.check_endgame
    @GameStateTools.require_current_player
    @GameStateTools.require_action
    @GameStateTools.require_phase(PlayPhases.player_action.value)
    def move_to_location(self, player, to_location, card_to_use):
        game.cards.use_card(self, player, card_to_use)
        game.players.set_player_location(self, player, to_location)
        dict_change = self._do_move(player, to_location)
        dict_change.update(self.serialize_fields(Game.dump_location_event))
        return dict_change

    @GameStateTools.require_role(PlayerRolesEnum.expert.value)
    def move_to_locationexpert(self, player, to_location, card_to_use):
        return self.move_to_location(player, to_location, card_to_use)

    @GameStateTools.check_endgame
    @GameStateTools.require_current_player
    @GameStateTools.require_action
    @GameStateTools.require_phase(PlayPhases.player_action.value)
    def move_from_location(self, player, to_location):
        player_location = game.players.get_player_location(self, player)
        game.cards.use_card(self, player, player_location)
        dict_change = self._do_move(player, to_location)
        dict_change.update(self.serialize_fields(Game.dump_location_event))
        return dict_change

    @GameStateTools.require_current_player
    @GameStateTools.require_action
    @GameStateTools.require_phase(PlayPhases.player_action.value)
    def build_research_center(self, player):
        player_location = game.players.get_player_location(self, player)
        game.locations.check_build_research_center(self, player_location)
        if not game.players.is_expert(self, player):
            game.cards.use_card(self, player, player_location)
        return self._do_build_research_center(player, player_location)

    def _do_build_research_center(self, player, player_location):
        game.locations.build_research_center(self, player, player_location)
        if len(self.locations_research_center) >= Rules.max_research_centers:
            self.hold_phase(PlayPhases.destroy_research_center.value)
        return self.serialize_fields(Game.events(Game.dump_location_event, Game.build_event))

    def subvention_publique(self, player, location):
        game.cards.use_card(self, player, CardEvent.subvention.value)
        self.check_dump_phase()
        return self._do_build_research_center(player, location)

    @GameStateTools.require_current_player
    @GameStateTools.require_phase(PlayPhases.destroy_research_center.value)
    def destroy_research_center(self, player, location):
        if self.locations_research_center.get(location):
            game.locations.destroy_research_center(self, location)
        if len(self.locations_research_center) >= Rules.max_research_centers:
            self.hold_phase(PlayPhases.destroy_research_center.value)
        else:
            self.resume_phase()
        return self.serialize_fields(Game.build_event)

    @GameStateTools.check_endgame
    @GameStateTools.require_current_player
    @GameStateTools.require_action
    @GameStateTools.require_phase(PlayPhases.player_action.value)
    def cure_disease(self, player, cards):
        game.diseases.cure_disease(self, player, cards)
        return self.serialize_fields(Game.events(Game.dump_location_event, Game.cure_event))

    @GameStateTools.require_action
    @GameStateTools.require_phase(PlayPhases.player_action.value)
    def give_card(self, player, player_from, player_to, card):
        if not (self.current_player == player_from or self.current_player == player_to):
            raise errors.InvalidPlayer
        game.cards.check_give_card(self, player_from, player_to, card)
        game.cards.give_card(self, player_from, player_to, card)
        if game.cards.player_hand_limit(self, player_to):
            self.hold_phase(PlayPhases.dump_card.value)
        return self.serialize_fields(Game.give_card_event)

    @GameStateTools.check_endgame
    @GameStateTools.require_current_player
    @GameStateTools.require_phase(
        {PlayPhases.player_action.value, PlayPhases.solve_epidemic.value, PlayPhases.end_turn.value})
    def end_turn(self, player):
        if self.phase == PlayPhases.player_action.value and self.player_actions < Rules.max_actions:
            raise errors.ActionRemainig
        if self.phase == PlayPhases.player_action.value:
            drawn_cards = game.cards._draw_locations_cards(self)
            epidemic_to_solve = game.cards.add_cards_to_hand_epidemic(self, player, drawn_cards)
            self.epidemics_to_solve = epidemic_to_solve
            self.epidemics += epidemic_to_solve
            self.phase = PlayPhases.end_turn.value

        if game.cards.player_hand_limit(self, player):
            self.hold_phase(PlayPhases.dump_card.value)
            return self.serialize_fields(Game.events(Game.end_turn_event, Game.drawn_location_event))

        if self.epidemics_to_solve:
            self.phase = PlayPhases.solve_epidemic.value
            game.infections.solve_epidemic(self)
            return self.serialize_fields(
                Game.events(Game.end_turn_event, Game.drawn_location_event, Game.infection_event))

        if self.phase == PlayPhases.solve_epidemic.value:
            game.infections.shuffle_infection_dump(self)

        if not self.nuit_tranquille:
            game.infections.infections(self)

        self.phase = PlayPhases.player_action.value
        self.nuit_tranquille = False
        self.current_player = game.players.next_player(self)
        self.player_actions = 0
        return self.serialize_fields(Game.events(Game.end_turn_event, Game.drawn_location_event, Game.infection_event))

    @GameStateTools.check_endgame
    @GameStateTools.require_current_player
    @GameStateTools.require_phase(PlayPhases.solve_epidemic.value)
    def trigger_infections(self, player):
        if self.epidemics_to_solve <= 0:
            self.epidemics_to_solve = 0
            game.infections.infections(self)
        else:
            game.infections.solve_epidemic(self)
        return self.serialize_fields(Game.infection_event)


class GameAction:
    def __init__(self):
        self.cancellable = []
        self.args = []

    @abstractmethod
    def apply_to_game_state(self, player, game_state):
        pass


class Move(GameAction):

    def __init__(self, *args):
        GameAction.__init__(self)
        self.args = args
        self.cancellable = True

    def apply_to_game_state(self, player, game_state):
        if len(self.args) == 1 or not self.args[1]:
            return game_state.move(player, player, self.args[0])
        return game_state.move(player, self.args[0], self.args[1])


class Heal(GameAction):

    def __init__(self, *args):
        GameAction.__init__(self)
        self.args = args
        self.cancellable = True

    def apply_to_game_state(self, player, game_state):
        return game_state.heal(player, self.args[0])


class EndTurn(GameAction):

    def __init__(self, *args):
        GameAction.__init__(self)
        self.cancellable = False

    def apply_to_game_state(self, player, game_state):
        return game_state.end_turn(player)


class DumpCard(GameAction):

    def __init__(self, *args):
        GameAction.__init__(self)
        self.args = args
        self.cancellable = True

    def apply_to_game_state(self, player, game_state):
        if len(self.args) == 1 or not self.args[1]:
            return game_state.dump_card(player, self.args[0])
        return game_state.dump_card(player, self.args[0], self.args[1])


class MoveToLocation(GameAction):

    def __init__(self, *args):
        GameAction.__init__(self)
        self.args = args
        self.cancellable = True

    def apply_to_game_state(self, player, game_state):
        if self.args:
            return game_state.move_to_location(player, self.args[0], self.args[0])
        raise errors.NoSuchCard


class MoveToLocationExpert(GameAction):

    def __init__(self, *args):
        GameAction.__init__(self)
        self.args = args
        self.cancellable = True

    def apply_to_game_state(self, player, game_state):
        if self.args and len(self.args) == 2:
            return game_state.move_to_locationexpert(player, self.args[0], self.args[1])
        raise errors.NoSuchCard


class MoveFromLocation(GameAction):

    def __init__(self, *args):
        GameAction.__init__(self)
        self.args = args
        self.cancellable = True

    def apply_to_game_state(self, player, game_state):
        if self.args:
            return game_state.move_from_location(player, self.args[0])
        raise errors.NoSuchCard


class BuildResearchCenter(GameAction):

    def __init__(self, *args):
        GameAction.__init__(self)
        self.args = args
        self.cancellable = True

    def apply_to_game_state(self, player, game_state):
        return game_state.build_research_center(player)


class DestroyResearchCenter(GameAction):

    def __init__(self, *args):
        GameAction.__init__(self)
        self.args = args
        self.cancellable = True

    def apply_to_game_state(self, player, game_state):
        if self.args:
            return game_state.destroy_research_center(player, self.args[0])
        raise errors.NoResearchCenterPresent


class CureDisease(GameAction):
    def __init__(self, *args):
        GameAction.__init__(self)
        self.args = args
        self.cancellable = True

    def apply_to_game_state(self, player, game_state):
        if self.args:
            return game_state.cure_disease(player, self.args)
        raise errors.NoDisease


class GiveCard(GameAction):
    def __init__(self, *args):
        GameAction.__init__(self)
        self.args = args
        self.cancellable = True

    def apply_to_game_state(self, player, game_state):
        if self.args and len(self.args) == 3:
            return game_state.give_card(player, *self.args)
        raise errors.CannotGiveCard


class Subvention(GameAction):
    def __init__(self, *args):
        GameAction.__init__(self)
        self.args = args
        self.cancellable = True

    def apply_to_game_state(self, player, game_state):
        if self.args:
            return game_state.subvention_publique(player, self.args[0])
        raise errors.NoSuchLocation


class PontAerien(GameAction):
    def __init__(self, *args):
        GameAction.__init__(self)
        self.args = args
        self.cancellable = True

    def apply_to_game_state(self, player, game_state):
        if self.args and len(self.args) == 2:
            return game_state.pont_aerien(player, self.args[1], self.args[0])
        raise errors.NoSuchLocation


class NuitTranquille(GameAction):
    def __init__(self, *args):
        GameAction.__init__(self)
        self.args = args
        self.cancellable = True

    def apply_to_game_state(self, player, game_state):
        return game_state.play_nuit_tranquille(player)


class PopulationResiliente(GameAction):
    def __init__(self, *args):
        GameAction.__init__(self)
        self.args = args
        self.cancellable = True

    def apply_to_game_state(self, player, game_state):
        if self.args:
            return game_state.play_population_resiliente(player, self.args[0])
        raise errors.NoSuchCard


EVENTS = {
    CardEvent.subvention.value: Subvention,
    CardEvent.pont.value: PontAerien,
    CardEvent.nuit.value: NuitTranquille,
    CardEvent.population.value: PopulationResiliente

}


def get_event_class(event_type):
    if event_type not in EVENTS:
        raise errors.NoSuchEvent
    return EVENTS[event_type]
