import enum

from django.db import models


class PlayPhases(enum.Enum):
    end_turn = "end_turn"
    not_started = "not_started"
    player_action = "player_action"
    dump_card = "dump_card"
    solve_epidemic = "solve_epidemic"
    defeat = "defeat"
    victory = "victory"
    destroy_research_center = 'destroy'


class PlayRoom(models.Model):
    name = models.CharField(max_length=16)
    has_started = models.BooleanField(default=False)
    map = models.ForeignKey('Map', on_delete=models.CASCADE)
    outbreaks = models.IntegerField(default=0)
    epidemics = models.IntegerField(default=0)
    phase = models.CharField(max_length=16, default=PlayPhases.not_started.value)
    epidemics_to_solve = models.IntegerField(default=0)
    player_actions = models.IntegerField(default=0)
    current_player = models.ForeignKey('Player', null=True, default=None, on_delete=models.SET_DEFAULT,
                                       related_name="current_player")
    nuit_tranquille = models.BooleanField(default=False)

    def get_infections_number(self):
        infections = [2, 2, 3, 3, 3, 4, 4]
        return infections[self.epidemics]
