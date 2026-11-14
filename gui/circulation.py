import math
from gui.vehicules import dessiner_voiture_orientee

VITESSE_VOITURE = 90
VOISINAGE_ANGLE = 3
DEMI_LONGUEUR = 23
MARGE_ARRET = 4
DISTANCE_SECURITE = 60
ECART_LATERAL = 15


def trajet_depuis_morceaux(morceaux):
    trajet = []
    for morceau in morceaux:
        for point in morceau:
            if not trajet or trajet[-1] != point:
                trajet.append(point)
    return trajet


class Vehicule:
    def __init__(self, trajet, couleur, id_feu=None, indice_ligne_arret=None):
        self.trajet = trajet
        self.indice = 0.0
        self.couleur = couleur
        self.id_feu = id_feu
        self.indice_ligne_arret = indice_ligne_arret
        self.actif = False
        self.visible = True

    def get_trajet(self):
        return self.trajet

    def set_trajet(self, trajet):
        self.trajet = trajet

    def get_indice(self):
        return self.indice

    def set_indice(self, indice):
        self.indice = indice

    def get_couleur(self):
        return self.couleur

    def set_couleur(self, couleur):
        self.couleur = couleur

    def get_id_feu(self):
        return self.id_feu

    def set_id_feu(self, id_feu):
        self.id_feu = id_feu

    def get_indice_ligne_arret(self):
        return self.indice_ligne_arret

    def set_indice_ligne_arret(self, indice_ligne_arret):
        self.indice_ligne_arret = indice_ligne_arret

    def get_actif(self):
        return self.actif

    def set_actif(self, actif):
        self.actif = actif

    def get_visible(self):
        return self.visible

    def set_visible(self, visible):
        self.visible = visible

    def position(self):
        return self.trajet[int(self.indice)]

    def angle(self):
        i = int(self.indice)
        avant = self.trajet[min(i + VOISINAGE_ANGLE, len(self.trajet) - 1)]
        arriere = self.trajet[max(i - VOISINAGE_ANGLE, 0)]
        return math.degrees(math.atan2(avant[1] - arriere[1], avant[0] - arriere[0]))

    def termine(self):
        return self.indice >= len(self.trajet) - 1

    def indice_arret(self):
        if self.indice_ligne_arret is None:
            return None
        reste = DEMI_LONGUEUR + MARGE_ARRET
        i = int(self.indice_ligne_arret)
        while i > 0 and reste > 0:
            reste -= math.dist(self.trajet[i], self.trajet[i - 1])
            i -= 1
        return i

    def doit_s_arreter_au_feu(self, feux):
        arret = self.indice_arret()
        if arret is None or feux is None or feux.get(self.id_feu) != "rouge":
            return False
        return self.indice <= arret

    def obstacle_devant(self, obstacles):
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
        if not self.actif or self.obstacle_devant(obstacles):
            return
        suivant = self.indice + dt * VITESSE_VOITURE
        if self.doit_s_arreter_au_feu(feux):
            suivant = min(suivant, self.indice_arret())
        self.indice = min(suivant, len(self.trajet) - 1)

    def dessiner(self, p):
        if not self.visible:
            return
        x, y = self.position()
        dessiner_voiture_orientee(p, x, y, self.angle(), self.couleur)
