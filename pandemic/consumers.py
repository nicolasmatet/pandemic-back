import secrets

from asgiref.sync import async_to_sync
import json

from pandemic import errors
from pandemic.controller import maplocations, rooms
from pandemic.controller.players import create_player, take_player, free_player, rename_player, \
    ready_player, check_start_game, choose_role, unready_player
from pandemic.controller.rooms import create_room, start_game, get_player_status
from pandemic.errors import TooManyPlayers, PlayerAlreadyExists, Error
from pandemic.games import AllGames, Move, EndTurn, DumpCard, Heal, MoveToLocation, MoveFromLocation, \
    BuildResearchCenter, CureDisease, DestroyResearchCenter, GiveCard, MoveToLocationExpert, \
    get_event_class
from pandemic.models import PlayRoom, Player
from pandemic_back import settings

from channels.generic.websocket import WebsocketConsumer
import re

regex_command = re.compile("/([a-z]+)([^|]*)\|?(.*)")


def game_action(func):
    def wrapper(*args):
        consumer = args[0]
        if consumer.player:
            try:
                res = func(*args)
                consumer.send_message_to_group('game_state', json.dumps(res))
            except Error as e:
                consumer.send_message_to_socket('error', str(e))

    return wrapper


def require_player(func):
    def wrapper(*args):
        consumer = args[0]
        if consumer.player:
            try:
                return func(*args)
            except Error as e:
                consumer.send_message_to_socket('error', str(e))

    return wrapper


def parse_command(str_input):
    r = re.search(regex_command, str_input)
    if not r:
        return None, ()
    return r.group(1), (r.group(2).strip(), r.group(3).strip())


class JoinConsumer(WebsocketConsumer):

    def connect(self):
        self.accept()
        self.send(text_data=json.dumps({
            "type": "info",
            "message": "Welcome ! Create a room with: /new"
        }))

    def receive(self, text_data):
        command, args = parse_command(json.loads(text_data))
        if command == "new":
            playroom = create_room()
            self.send(text_data=json.dumps({
                "type": "url",
                "message": "/pandemic/{:}".format(playroom.name)
            }))

    def disconnect(self, close_code):
        # Leave room group
        pass


class PlayConsumer(WebsocketConsumer):

    def connect(self):
        self.secret = secrets.token_hex(4)
        self.username = None
        self.player = None
        self.playroom_id = None
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'pandemic_%s' % self.room_name
        if not PlayRoom.objects.filter(name=self.room_name).exists():
            return
        self.username = "Anonymous"
        self.playroom_id = PlayRoom.objects.get(name=self.room_name).id

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()
        self.send(text_data=json.dumps(
            {
                "type": "info",
                "message": "Welcome {:} to room {:}".format(self.username, self.room_name)
            }
        ))

    def receive(self, text_data):
        print("in::", text_data)
        command, args = parse_command(json.loads(text_data))
        print("cmd::", command, args)

        if command:
            method = getattr(self, 'handle_' + command, None)
            if method:
                method(*args)

    def send_message_to_group(self, msg_type, message, **kwargs):
        # Send message to room group
        # print(msg)
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': msg_type,
                'message': message,
                **kwargs
            }
        )

    def send_message_to_socket(self, msg_type, message):
        msg = {
            'type': msg_type,
            'message': message
        }
        print(msg)
        self.send(json.dumps({
            'type': msg_type,
            'message': message
        }))

    def disconnect(self, close_code):
        # Leave room group
        if self.player:
            playroom = self.get_playroom()
            free_player(playroom, self.player.name)
            self.send_message_to_group("info", "Player {:} has left".format(self.player.name))
            self.handle_playroomstate()
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def get_playroom(self):
        return PlayRoom.objects.get(id=self.playroom_id)

    ### solve actions
    def handle_join(self, arg1=None, arg2=None):
        playername = arg1
        if not playername:
            return
        self.username = playername
        playroom = self.get_playroom()

        try:
            if self.player:
                free_player(playroom, self.player.name)
            self.player = take_player(playername, playroom)
            self.send_message_to_socket('info', "You joined the game as {:}".format(self.player.name))
            self.send_message_to_group('info', "Player {:} joined the game".format(self.player.name))
            self.handle_playroomstate()
            if playroom.has_started:
                self.handle_gamestate()

        except Player.DoesNotExist:
            if not playroom.has_started:
                self._handle_add_player()
                self.handle_playroomstate()
        except Error as e:
            self.send_message_to_socket('error', str(e))

    def _handle_add_player(self):
        try:
            playroom = self.get_playroom()
            self.player = create_player(self.username, playroom)
            self.send_message_to_socket('info', "You joined the game as {:}".format(self.player.name))
            self.send_message_to_group('info', "Player {:} joined the game".format(self.player.name))
        except (TooManyPlayers, PlayerAlreadyExists) as e:
            self.send_message_to_socket('error', str(e))

    def handle_kick(self, arg1=None, arg2=None):
        player_name = arg1
        if player_name:
            try:
                playroom = self.get_playroom()
                free_player(playroom, player_name)
                self.send_message_to_socket('info', "You kicked the game as {:}".format(player_name))
                self.send_message_to_group('player_kicked', "Player {:} was kicked".format(player_name),
                                           playername=player_name)
                self.handle_playroomstate()
            except Player.DoesNotExist as e:
                self.send_message_to_socket("error", str(e))

    def handle_rename(self, *args):
        if self.player:
            old_player_name = self.username
            self.send_message_to_socket('info', 'Your username was changed to {:}'.format(self.username))
            try:
                playroom = self.get_playroom()
                rename_player(self.player, self.username, playroom)
                self.username = args[0] if args[0] else 'Anonymous'
                self.send_message_to_group('info',
                                           "Player {:} was renamed to {:}".format(old_player_name, self.player.name))
            except Error as e:
                self.send_message_to_socket('error', str(e))
        else:
            self.username = args[0] if args[0] else 'Anonymous'

    def handle_playroomstate(self, *args):
        playroom = self.get_playroom()
        playroom_state = rooms.get_playroom_state(playroom)
        self.send_message_to_group('playroomstate', playroom_state)

    def handle_gamesetup(self, *args):
        playroom = self.get_playroom()
        dict_all_locations = maplocations.get_all_locations(playroom)
        self.send_message_to_socket('game_setup', json.dumps({
            "locations": dict_all_locations,
        }))

    # def handle_locations_network(self, *args):
    #     all_locations = maplocations.get_locations_network(self.playroom_id)
    #     self.send_message_to_socket('game_setup', json.dumps(all_locations))

    def handle_gamestate(self, *args):
        playroom = self.get_playroom()
        game_state = AllGames.get_game_state(playroom)
        self.send_message_to_group('game_state', json.dumps(game_state))

    @require_player
    def handle_role(self, *args):
        choose_role(self.player, args[0])
        self.handle_playroomstate()
        self.send_message_to_group('info', "Player {:} is now {:}".format(self.player.name, self.player.role))

    @require_player
    def handle_ready(self, *args):
        ready_player(self.player)
        self.handle_playroomstate()
        self.send_message_to_group('info', "Player {:} is ready.".format(self.player.name))

    @require_player
    def handle_unready(self, *args):
        unready_player(self.player)
        self.handle_playroomstate()
        self.send_message_to_group('info', "Player {:} not ready.".format(self.player.name))

    @require_player
    def handle_start(self, *args):
        playroom = self.get_playroom()
        check_start_game(playroom)
        self.send_message_to_group('info', "THE PANDEMIC HAS STARTED !")
        game_state = start_game(playroom)
        self.handle_playroomstate()
        self.send_message_to_group('game_state', json.dumps(game_state))

    @game_action
    def handle_cancel(self, *args):
        print("handle_cancel", args)
        playroom = self.get_playroom()
        return AllGames.cancel_last_action(playroom, self.player)

    @game_action
    def handle_move(self, *args):
        print("handle_move", args)
        playroom = self.get_playroom()
        return AllGames.register_action(playroom, self.player, Move(*args))

    @game_action
    def handle_heal(self, *args):
        print("handle_move", args)
        playroom = self.get_playroom()
        return AllGames.register_action(playroom, self.player, Heal(*args))

    @game_action
    def handle_end(self, *args):
        print("handle_end", args)
        playroom = self.get_playroom()
        return AllGames.register_action(playroom, self.player, EndTurn(*args))

    @game_action
    def handle_dump(self, *args):
        print("handle_dump", args)
        playroom = self.get_playroom()
        return AllGames.register_action(playroom, self.player, DumpCard(*args))

    @game_action
    def handle_moveto(self, *args):
        print("handle_moveto", args)
        playroom = self.get_playroom()
        return AllGames.register_action(playroom, self.player, MoveToLocation(*args))

    @game_action
    def handle_movefrom(self, *args):
        print("handle_movefrom", args)
        playroom = self.get_playroom()
        return AllGames.register_action(playroom, self.player, MoveFromLocation(*args))

    @game_action
    def handle_build(self, *args):
        print("handle_build", args)
        playroom = self.get_playroom()
        return AllGames.register_action(playroom, self.player, BuildResearchCenter(*args))

    @game_action
    def handle_destroy(self, *args):
        print("handle_build", args)
        playroom = self.get_playroom()
        return AllGames.register_action(playroom, self.player, DestroyResearchCenter(*args))

    @game_action
    def handle_cure(self, *args):
        print("handle_cure", args)
        playroom = self.get_playroom()
        args = str(args[0]).split('&')
        return AllGames.register_action(playroom, self.player, CureDisease(*args))

    @game_action
    def handle_give(self, *args):
        print("handle_give", args)
        playroom = self.get_playroom()
        args = str(args[0]).split('&')
        return AllGames.register_action(playroom, self.player, GiveCard(*args))

    @game_action
    def handle_movetoexpert(self, *args):
        print("handle_movetoexpert", args)
        playroom = self.get_playroom()
        return AllGames.register_action(playroom, self.player, MoveToLocationExpert(*args))

    @game_action
    def handle_playevent(self, *args):
        print("handle_playevent", args)
        playroom = self.get_playroom()
        event_type = args[0]
        event_class = get_event_class(event_type)
        event_args = str(args[1]).split("&")
        return AllGames.register_action(playroom, self.player, event_class(*event_args))

    def handle_seenextinfections(self, *args):
        print("handle_seenextinfections", args)
        playroom = self.get_playroom()
        try:
            nextinfections = AllGames.get_next_infections(playroom, self.player, n=6)
            self.send_message_to_group('cardList', {
                "type": "infections",
                "cards": nextinfections,
            }, playername=self.player.name)
        except Error as e:
            self.send_message_to_socket('error', str(e))

    def handle_setnextinfections(self, *args):
        print("handle_setnextinfections", args)
        playroom = self.get_playroom()
        secret = args[0]
        cards = args[1].split('&')

        try:
            self.check_secret(secret)
            dict_change = AllGames.set_next_infections(playroom, self.player, cards)
            self.send_message_to_group('cardList', {
                "type": "infections",
                "cards": cards,
            }, playername=None)
            self.send_message_to_group('game_state', json.dumps(dict_change))
        except Error as e:
            self.send_message_to_socket('error', str(e))
        except AttributeError as e:
            self.send_message_to_socket('error', 'cartes invalides')

    def new_secret(self):
        self.secret = secrets.token_hex(4)
        return self.secret

    def check_secret(self, secret):
        if secret == self.secret:
            self.new_secret()
            return True
        raise errors.InvalidSecret

    ## receiver for group messages

    def error(self, event):
        self.send_message_to_socket('error', event['message'])

    def info(self, event):
        self.send_message_to_socket('info', event['message'])

    def playroomstate(self, event):
        message = event['message']
        selfplayer_status = get_player_status(self.player)
        message["player"] = selfplayer_status
        self.send_message_to_socket('playroomstate', json.dumps(message))

    def game_state(self, event):
        self.send_message_to_socket('game_state', event['message'])

    def game_setup(self, event):
        self.send_message_to_socket('game_setup', event['message'])

    def player_kicked(self, event):
        playername = event.get('playername')
        if self.player and self.player.name == playername:
            self.player = None
            self.send_message_to_socket("info", "You were kicked out.")
        else:
            return self.send_message_to_socket('info', event['message'])

    def cardList(self, event):
        playername = event.get('playername')
        msg = event['message']
        if self.player and self.player.name == playername:
            msg['secret'] = self.new_secret()
        self.send_message_to_socket("cardList", json.dumps(msg))
