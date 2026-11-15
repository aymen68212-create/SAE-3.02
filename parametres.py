"""Constantes et fonctions partagées : réseau, vitesses, feux et trajectoires.

Les adresses réseau se règlent par variables d'environnement : SAE_HOTE (adresse du serveur pour les clients) et
SAE_ECOUTE (adresse d'écoute du serveur). Les trajectoires sont construites à partir de lignes droites et
d'arcs de cercle échantillonnés en points.
"""

import math
import os

HOTE = os.environ.get("SAE_HOTE", "localhost")
ECOUTE = os.environ.get("SAE_ECOUTE", "localhost")
PORT = 5050

LARGEUR = 1000
HAUTEUR = 700

VITESSE_AMBULANCE = 90
FREQUENCE_POSITION = 20
VITESSE_ONDE = 220
PORTEE_ONDE = 110
DELAI_CHANGEMENT_FEU = 2.0
INTERVALLE_ONDE = 0.7
POINT_ARRET = (885, 110)

VOIES = {
    "avenue_nord": 575,
    "avenue_sud_voiture": 425,
    "avenue_sud_ambulance": 475,
    "jardins_est": 345,
    "jardins_ouest": 295,
    "branche_nord": 885,
    "branche_sud": 835,
}

FEUX = {
    "sud_droite": {"x": 612, "y": 395, "approche": "nord"},
    "sud_gauche": {"x": 388, "y": 395, "approche": "nord"},
    "nord_droite": {"x": 612, "y": 245, "approche": "sud"},
    "nord_gauche": {"x": 388, "y": 245, "approche": "sud"},
}


PAIRE_AMBULANCE = ("sud_droite", "nord_gauche")
PAIRE_RETOUR = ("sud_gauche", "nord_droite")


def message_serveur_injoignable(erreur):
    """Construit le message affiché quand le serveur ne répond pas.

    Args:
        erreur: exception levée par la tentative de connexion.

    Returns:
        Un message en français indiquant l'adresse testée et les vérifications à faire.
    """
    return (f"Impossible de joindre le serveur {HOTE}:{PORT} ({erreur}). "
            "Vérifiez que le serveur est lancé (python -m server.server), que l'adresse donnée "
            "dans SAE_HOTE est correcte et que le port est ouvert.")


def etats_initiaux():
    """Donne l'état de repos des feux à l'aller.

    Returns:
        Un dictionnaire {identifiant du feu: "rouge" ou "vert"} : `PAIRE_AMBULANCE` au rouge, l'autre au vert.
    """
    return {id_feu: "rouge" if id_feu in PAIRE_AMBULANCE else "vert" for id_feu in FEUX}


def cap_depuis_deplacement(dx, dy):
    """Déduit le cap cardinal d'un déplacement.

    Args:
        dx: déplacement horizontal en pixels.
        dy: déplacement vertical en pixels (l'axe y est orienté vers le bas).

    Returns:
        "est", "ouest", "sud" ou "nord", selon l'axe dominant.
    """
    if abs(dx) >= abs(dy):
        return "est" if dx > 0 else "ouest"
    return "sud" if dy > 0 else "nord"


def points_ligne(depart, arrivee, pas):
    """Échantillonne un segment de droite.

    Args:
        depart: point (x, y) de départ.
        arrivee: point (x, y) d'arrivée.
        pas: distance approximative entre deux points, en pixels.

    Returns:
        La liste des points, départ et arrivée compris.
    """
    longueur = math.dist(depart, arrivee)
    # Nombre de segments pour obtenir un point tous les `pas` pixels environ.
    nombre = max(1, round(longueur / pas))
    return [
        (
            depart[0] + (arrivee[0] - depart[0]) * i / nombre,
            depart[1] + (arrivee[1] - depart[1]) * i / nombre,
        )
        for i in range(nombre + 1)
    ]


def points_arc(centre, rayon, angle_depart, angle_arrivee, pas):
    """Échantillonne un arc de cercle.

    Args:
        centre: centre (x, y) du cercle.
        rayon: rayon en pixels.
        angle_depart: angle de départ en degrés (0 = est, 90 = sud car y est vers le bas).
        angle_arrivee: angle d'arrivée en degrés.
        pas: longueur approximative entre deux points, en pixels.

    Returns:
        La liste des points de l'arc, extrémités comprises.
    """
    longueur = abs(math.radians(angle_arrivee - angle_depart)) * rayon
    nombre = max(1, round(longueur / pas))
    points = []
    for i in range(nombre + 1):
        # Interpolation linéaire de l'angle, puis passage en coordonnées cartésiennes (y vers le bas).
        angle = math.radians(angle_depart + (angle_arrivee - angle_depart) * i / nombre)
        points.append((centre[0] + rayon * math.cos(angle), centre[1] + rayon * math.sin(angle)))
    return points


def points_courbe(depart, controle, arrivee, pas):
    """Échantillonne une courbe de Bézier quadratique (raccord lisse entre deux directions).

    Args:
        depart: point de départ.
        controle: point de contrôle, à l'intersection des deux tangentes.
        arrivee: point d'arrivée.
        pas: longueur approximative entre deux points, en pixels.

    Returns:
        La liste des points de la courbe.
    """
    longueur = math.dist(depart, controle) + math.dist(controle, arrivee)
    nombre = max(1, round(longueur / pas))
    points = []
    for i in range(nombre + 1):
        # Bézier quadratique : B(t) = (1-t)^2 * depart + 2(1-t)t * controle + t^2 * arrivee.
        t = i / nombre
        points.append((
            (1 - t) ** 2 * depart[0] + 2 * (1 - t) * t * controle[0] + t ** 2 * arrivee[0],
            (1 - t) ** 2 * depart[1] + 2 * (1 - t) * t * controle[1] + t ** 2 * arrivee[1],
        ))
    return points


def generer_trajet(pas):
    """Génère le trajet aller de l'ambulance, de l'avenue d'Alsace au parking.

    Args:
        pas: distance en pixels parcourue entre deux positions envoyées.

    Returns:
        La liste des points (x, y) entiers, sans doublon consécutif.
    """
    morceaux = [
        points_ligne((VOIES["avenue_nord"], 690), (VOIES["avenue_nord"], 400), pas),
        points_arc((630, 400), 55, 180, 270, pas),
        points_ligne((630, VOIES["jardins_est"]), (830, VOIES["jardins_est"]), pas),
        points_arc((830, 290), 55, 90, 0, pas),
        points_ligne((VOIES["branche_nord"], 290), POINT_ARRET, pas),
    ]
    trajet = []
    for morceau in morceaux:
        for point in morceau:
            # Positions envoyées en pixels entiers ; on évite les doublons créés aux jonctions des morceaux.
            point_entier = (round(point[0]), round(point[1]))
            if not trajet or trajet[-1] != point_entier:
                trajet.append(point_entier)
    return trajet

def generer_trajet_retour(pas):
    """Génère le trajet retour : demi-tour au parking, Rue des Jardins puis avenue d'Alsace vers le sud.

    Args:
        pas: distance en pixels parcourue entre deux positions envoyées.

    Returns:
        La liste des points (x, y) entiers, sans doublon consécutif.
    """
    morceaux = [
        points_arc((860, 110), 25, 0, -180, pas),
        points_ligne((VOIES["branche_sud"], 110), (VOIES["branche_sud"], 235), pas),
        points_arc((775, 235), 60, 0, 90, pas),
        points_ligne((775, VOIES["jardins_ouest"]), (VOIES["avenue_nord"], VOIES["jardins_ouest"]), pas),
        points_arc((VOIES["avenue_nord"], 395), 100, -90, -180, pas),
        points_ligne((VOIES["avenue_sud_ambulance"], 395), (VOIES["avenue_sud_ambulance"], 730), pas),
    ]
    trajet = []
    for morceau in morceaux:
        for point in morceau:
            point_entier = (round(point[0]), round(point[1]))
            if not trajet or trajet[-1] != point_entier:
                trajet.append(point_entier)
    return trajet
