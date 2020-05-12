class Error(Exception):
    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg

    def __str__(self):
        return self.msg


class PlayerAlreadyExists(Error):
    def __init__(self):
        Error.__init__(self, 'Le joueur existe déjà !')


class TooManyPlayers(Error):
    def __init__(self):
        Error.__init__(self, 'Trop de joueurs dans cette salle (max. 4)')


class PlayerIsTaken(Error):
    def __init__(self):
        Error.__init__(self, 'Le joueur est déjà pris !')


class ResearchCenterAlreadyPresent(Error):
    def __init__(self):
        Error.__init__(self, 'Un centre de recherche a déjà été construit ici.')


class ResearchCenterLimit(Error):
    def __init__(self):
        Error.__init__(self, 'Trop de centres de recherche (max. 6)! Vous devez en détruire un.')


class NoResearchCenterPresent(Error):
    def __init__(self):
        Error.__init__(self, 'Pas de centre de recherche ici.')


class NoDiseaseToCure(Error):
    def __init__(self):
        Error.__init__(self, 'Pas de maladie de ce type à soigner.')


class NoDisease(Error):
    def __init__(self):
        Error.__init__(self, 'Vous devez indiquer une maladie.')


class DiseaseAlreadyCured(Error):
    def __init__(self):
        Error.__init__(self, 'Un remède à déjà été trouvé.')


class LocationCardsNotMatching(Error):
    def __init__(self):
        Error.__init__(self, 'Il vous faut 5 cartes villes du même type.')


class LocationCardsAreMissing(Error):
    def __init__(self):
        Error.__init__(self, 'Il vous faut 5 cartes villes du même type.')


class NeedAResarchCenter(Error):
    def __init__(self):
        Error.__init__(self, 'Il faut un centre de recherche au départ et à l\'arrivée.')


class NotANeighbor(Error):
    def __init__(self):
        Error.__init__(self, 'Pas de connection vers cette ville !')


class NeedCurrentLocationCard(Error):
    def __init__(self):
        Error.__init__(self, 'Il vous manque la carte de la ville actuelle !')


class NeedLocationCard(Error):
    def __init__(self):
        Error.__init__(self, 'Vous devez sélectionner une carte ville pour cette action.')


class RequireAction(Error):
    def __init__(self):
        Error.__init__(self, "Vous avez utilisé tous vos points d'action")


class CannotMoveOthers(Error):
    def __init__(self):
        Error.__init__(self, "Vous ne pouvez pas déplacer un autre joueur.")


class NotYourTurn(Error):
    def __init__(self):
        Error.__init__(self, "Ce n'est pas votre tour !")


class PlayerHasNoRole(Error):
    def __init__(self):
        Error.__init__(self, "Vous devez choisir un rôle !")


class RoleAlreadyTaken(Error):
    def __init__(self):
        Error.__init__(self, "Ce rôle est déjà pris.")


class RoleDoesNotExists(Error):
    def __init__(self):
        Error.__init__(self, "Ce rôle n'existe pas...")


class PlayerUnready(Error):
    def __init__(self):
        Error.__init__(self, "Un joueur n'est pas encore prêt !")


class GameHasStarted(Error):
    def __init__(self):
        Error.__init__(self, "La partie a déjà commencée !")


class GameHasNotStarted(Error):
    def __init__(self):
        Error.__init__(self, "La partie n'a pas commencée ! Tous les joueurs doivent être prêts.")


class Defeat(Error):
    def __init__(self):
        Error.__init__(self, "LA PANDEMIE A GAGNÉ !")


class Victory(Error):
    def __init__(self):
        Error.__init__(self, "LA PANDÉMIE A ÉTÉ VAICUE !")


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
