"""Véhicules de fond : suivi d'un trajet, arrêt aux feux rouges et distance de sécurité."""

import math
from gui.vehicules import dessiner_voiture_orientee

VITESSE_VOITURE = 90
VOISINAGE_ANGLE = 3
DEMI_LONGUEUR = 23
MARGE_ARRET = 4
DISTANCE_SECURITE = 60
ECART_LATERAL = 15


def trajet_depuis_morceaux(morceaux):
    """Assemble des morceaux de trajet en une seule liste de points.

    Args:
        morceaux: listes de points (lignes, arcs, courbes) à la suite.

    Returns:
        La liste des points sans doublon consécutif (le dernier point d'un morceau est aussi le premier du suivant).
    """
    trajet = []
    for morceau in morceaux:
        for point in morceau:
            if not trajet or trajet[-1] != point:
                trajet.append(point)
    return trajet


class Vehicule:
    """Véhicule qui suit un trajet à vitesse constante.

    Attributes:
        trajet: liste de points (x, y), un point par pixel parcouru.
        indice: position (flottante) sur le trajet.
        id_feu: feu à respecter, ou None.
        indice_ligne_arret: indice du point de la ligne d'arrêt, ou None.
        actif: le véhicule n'avance que s'il est actif.
    """
    def __init__(self, trajet, couleur, id_feu=None, indice_ligne_arret=None):
        """Crée un véhicule immobile au début de son trajet.

        Args:
            trajet: liste de points (x, y).
            couleur: `QColor` de la carrosserie.
            id_feu: identifiant du feu à respecter, ou None.
            indice_ligne_arret: indice du trajet où se trouve la ligne d'arrêt, ou None.
        """
        self.trajet = trajet
        self.indice = 0.0
        self.couleur = couleur
        self.id_feu = id_feu
        self.indice_ligne_arret = indice_ligne_arret
        self.actif = False
        self.visible = True

    def get_trajet(self):
        """Retourne le trajet."""
        return self.trajet

    def set_trajet(self, trajet):
        """Change le trajet.

        Args:
            trajet: liste de points (x, y).
        """
        self.trajet = trajet

    def get_indice(self):
        """Retourne l'indice courant sur le trajet."""
        return self.indice

    def set_indice(self, indice):
        """Change l'indice courant.

        Args:
            indice: nouvelle position sur le trajet.
        """
        self.indice = indice

    def get_couleur(self):
        """Retourne la couleur de la carrosserie."""
        return self.couleur

    def set_couleur(self, couleur):
        """Change la couleur.

        Args:
            couleur: `QColor`.
        """
        self.couleur = couleur

    def get_id_feu(self):
        """Retourne l'identifiant du feu respecté."""
        return self.id_feu

    def set_id_feu(self, id_feu):
        """Change le feu respecté.

        Args:
            id_feu: identifiant du feu, ou None.
        """
        self.id_feu = id_feu

    def get_indice_ligne_arret(self):
        """Retourne l'indice de la ligne d'arrêt."""
        return self.indice_ligne_arret

    def set_indice_ligne_arret(self, indice_ligne_arret):
        """Change l'indice de la ligne d'arrêt.

        Args:
            indice_ligne_arret: indice du trajet, ou None.
        """
        self.indice_ligne_arret = indice_ligne_arret

    def get_actif(self):
        """Indique si le véhicule est actif."""
        return self.actif

    def set_actif(self, actif):
        """Active ou désactive le véhicule.

        Args:
            actif: True pour le faire avancer.
        """
        self.actif = actif

    def get_visible(self):
        """Indique si le véhicule est dessiné."""
        return self.visible

    def set_visible(self, visible):
        """Affiche ou masque le véhicule.

        Args:
            visible: True pour le dessiner.
        """
        self.visible = visible

    def position(self):
        """Retourne la position (x, y) actuelle."""
        return self.trajet[int(self.indice)]

    def angle(self):
        """Calcule l'orientation en degrés à partir des points voisins du trajet (lisse les virages)."""
        i = int(self.indice)
        avant = self.trajet[min(i + VOISINAGE_ANGLE, len(self.trajet) - 1)]
        arriere = self.trajet[max(i - VOISINAGE_ANGLE, 0)]
        return math.degrees(math.atan2(avant[1] - arriere[1], avant[0] - arriere[0]))

    def termine(self):
        """Indique si le véhicule a atteint la fin de son trajet."""
        return self.indice >= len(self.trajet) - 1

    def indice_arret(self):
        """Calcule l'indice où le véhicule doit s'immobiliser devant sa ligne d'arrêt.

        On recule d'une demi-longueur de voiture plus une marge, pour que le pare-chocs reste avant la ligne.

        Returns:
            L'indice d'arrêt, ou None s'il n'y a pas de ligne d'arrêt.
        """
        if self.indice_ligne_arret is None:
            return None
        # On remonte le trajet depuis la ligne pour que le pare-chocs avant reste avant la ligne.
        reste = DEMI_LONGUEUR + MARGE_ARRET
        i = int(self.indice_ligne_arret)
        while i > 0 and reste > 0:
            reste -= math.dist(self.trajet[i], self.trajet[i - 1])
            i -= 1
        return i

    def doit_s_arreter_au_feu(self, feux):
        """Indique si le feu rouge impose l'arrêt.

        Args:
            feux: dictionnaire {identifiant: état} ou None.

        Returns:
            True si le feu est rouge et que le véhicule n'a pas encore dépassé son point d'arrêt.
        """
        arret = self.indice_arret()
        if arret is None or feux is None or feux.get(self.id_feu) != "rouge":
            return False
        return self.indice <= arret

    def obstacle_devant(self, obstacles):
        """Détecte un obstacle devant le véhicule.

        Un obstacle gêne s'il est dans le sens de la marche à moins de DISTANCE_SECURITE et à moins de
        ECART_LATERAL de l'axe du véhicule.

        Args:
            obstacles: liste de positions (x, y), ou None.

        Returns:
            True si un obstacle bloque le passage.
        """
        if not obstacles:
            return False
        x, y = self.position()
        angle = math.radians(self.angle())
        avant_x = math.cos(angle)
        avant_y = math.sin(angle)
        for ox, oy in obstacles:
            dx = ox - x
            dy = oy - y
            devant = dx * avant_x + dy * avant_y
            lateral = abs(dx * avant_y - dy * avant_x)
            if 0 < devant < DISTANCE_SECURITE and lateral < ECART_LATERAL:
                return True
        return False

    def avancer(self, dt, feux=None, obstacles=None):
        """Fait avancer le véhicule, sauf s'il est inactif, bloqué par un obstacle ou arrêté par un feu rouge.

        Args:
            dt: temps écoulé en secondes.
            feux: dictionnaire {identifiant: état} ou None.
            obstacles: liste de positions (x, y) ou None.
        """
        if not self.actif or self.obstacle_devant(obstacles):
            return
        suivant = self.indice + dt * VITESSE_VOITURE
        # Au rouge, on ne dépasse pas le point d'arrêt ; un véhicule déjà passé n'est pas concerné.
        if self.doit_s_arreter_au_feu(feux):
            suivant = min(suivant, self.indice_arret())
        self.indice = min(suivant, len(self.trajet) - 1)

    def dessiner(self, p):
        """Dessine le véhicule s'il est visible.

        Args:
            p: `QPainter`.
        """
        if not self.visible:
            return
        x, y = self.position()
        dessiner_voiture_orientee(p, x, y, self.angle(), self.couleur)
