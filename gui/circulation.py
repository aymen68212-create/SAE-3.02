import math
from gui.vehicules import dessiner_voiture_orientee

VITESSE_VOITURE = 90
VOISINAGE_ANGLE = 3


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

    def avancer(self, dt, feux=None):
        if not self.actif:
            return
        suivant = self.indice + dt * VITESSE_VOITURE
        arret = self.indice_ligne_arret
        if arret is not None and feux is not None and feux.get(self.id_feu) == "rouge" and self.indice <= arret:
            suivant = min(suivant, arret)
        self.indice = min(suivant, len(self.trajet) - 1)

    def dessiner(self, p):
        if not self.visible:
            return
        x, y = self.position()
        dessiner_voiture_orientee(p, x, y, self.angle(), self.couleur)
