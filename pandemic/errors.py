class Error(Exception):
    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg

    def __str__(self):
        return self.msg


class PlayerAlreadyExists(Error):
    def __init__(self):
        Error.__init__(self, 'Player already exists !')


class TooManyPlayers(Error):
    def __init__(self):
        Error.__init__(self, 'Too many players in this room (max. 4)')


class PlayerIsTaken(Error):
    def __init__(self):
        Error.__init__(self, 'Player is already taken !')


class ResearchCenterAlreadyPresent(Error):
    def __init__(self):
        Error.__init__(self, 'A research center is already build here.')


class ResearchCenterLimit(Error):
    def __init__(self):
        Error.__init__(self, 'Too many research centers (max. 6). You may destroy any for free.')


class NoResearchCenterPresent(Error):
    def __init__(self):
        Error.__init__(self, 'No research center here.')


class NoDiseaseToCure(Error):
    def __init__(self):
        Error.__init__(self, 'No disease of this type to cure.')


class NoDisease(Error):
    def __init__(self):
        Error.__init__(self, 'Vous devez indiquer une maladie.')


class DiseaseAlreadyCured(Error):
    def __init__(self):
        Error.__init__(self, 'Disease is already cured.')


class LocationCardsNotMatching(Error):
    def __init__(self):
        Error.__init__(self, 'You need 5 locations cards of the same type.')


class LocationCardsAreMissing(Error):
    def __init__(self):
        Error.__init__(self, 'You need 5 locations cards of the same type.')


class NeedAResarchCenter(Error):
    def __init__(self):
        Error.__init__(self, 'You need a research center at origin and destination.')


class NotANeighbor(Error):
    def __init__(self):
        Error.__init__(self, 'You can only move to a neighbor.')


class NeedCurrentLocationCard(Error):
    def __init__(self):
        Error.__init__(self, 'You need a card of the current location for this action.')


class NeedLocationCard(Error):
    def __init__(self):
        Error.__init__(self, 'You need to dump a location card for this action.')


class RequireAction(Error):
    def __init__(self):
        Error.__init__(self, "You have spend all action points")


class CannotMoveOthers(Error):
    def __init__(self):
        Error.__init__(self, "You cannot move other players")


class NotYourTurn(Error):
    def __init__(self):
        Error.__init__(self, "You need to wait your turn")


class PlayerHasNoRole(Error):
    def __init__(self):
        Error.__init__(self, "You must first choose a role")


class RoleAlreadyTaken(Error):
    def __init__(self):
        Error.__init__(self, "Role is already taken")


class RoleDoesNotExists(Error):
    def __init__(self):
        Error.__init__(self, "Role does not exists")


class PlayerUnready(Error):
    def __init__(self):
        Error.__init__(self, "A player is not ready")


class GameHasStarted(Error):
    def __init__(self):
        Error.__init__(self, "Game has Already Started")


class GameHasNotStarted(Error):
    def __init__(self):
        Error.__init__(self, "Game has not begun ! All players must be ready.")


class Defeat(Error):
    def __init__(self):
        Error.__init__(self, "THE PANDEMIC HAS WON !")


class Victory(Error):
    def __init__(self):
        Error.__init__(self, "THE PANDEMIC WAS DEFEATED !")


class ActionRemainig(Error):
    def __init__(self):
        Error.__init__(self, "Vous devez utiliser touts vos points d'action !")


class InvalidGamePhase(Error):
    def __init__(self):
        Error.__init__(self, "Vous ne pouvez pas faire ça maintenant :")


class CannotDumpCard(Error):
    def __init__(self):
        Error.__init__(self, "Vous ne pouvez pas jeter de carte maintenant !")


class NoSuchCard(Error):
    def __init__(self):
        Error.__init__(self, "Vous n'avez pas cette carte...")


class NoSuchLocation(Error):
    def __init__(self):
        Error.__init__(self, "Cet emplacement n'existe pas...")


class CannotGiveCard(Error):
    def __init__(self):
        Error.__init__(self, "Impossible de donner cette carte !")


class InvalidPlayer(Error):
    def __init__(self):
        Error.__init__(self, "Impossible de faire ça avec ce joueur !")


class NoInTheRightPlace(Error):
    def __init__(self):
        Error.__init__(self, "Vous n'êtes pas au bon endroit !")


class NotInTheSamePlace(Error):
    def __init__(self):
        Error.__init__(self, "Vous devez être au même endroit !")


class NotALocationCard(Error):
    def __init__(self):
        Error.__init__(self, "Vous ne pouvez pas donner d'évènements !")


class NoSuchEvent(Error):
    def __init__(self):
        Error.__init__(self, "Cet évènement n'existe pas !")


class InvalidSecret(Error):
    def __init__(self):
        Error.__init__(self, "Vous n'êtes pas le bon joueur !")


class InvalidCard(Error):
    def __init__(self):
        Error.__init__(self, "Pas les bonnes cartes !")


class TooManyCards(Error):
    def __init__(self):
        Error.__init__(self, "Trop de cartes !")
