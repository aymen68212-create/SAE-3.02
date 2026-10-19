import math

HOTE = "localhost"
PORT = 5050

LARGEUR = 1000
HAUTEUR = 700

VITESSE_AMBULANCE = 90
FREQUENCE_POSITION = 20
VITESSE_ONDE = 220
PORTEE_ONDE = 280
INTERVALLE_ONDE = 0.7

FEUX = {
    "sud_droite": {"x": 612, "y": 395, "approche": "nord"},
    "sud_gauche": {"x": 388, "y": 395, "approche": "nord"},
    "nord_droite": {"x": 612, "y": 245, "approche": "sud"},
    "nord_gauche": {"x": 388, "y": 245, "approche": "sud"},
}


def cap_depuis_deplacement(dx, dy):
    if abs(dx) >= abs(dy):
        return "est" if dx > 0 else "ouest"
    return "sud" if dy > 0 else "nord"


def points_ligne(depart, arrivee, pas):
    longueur = math.dist(depart, arrivee)
    nombre = max(1, round(longueur / pas))
    return [
        (
            depart[0] + (arrivee[0] - depart[0]) * i / nombre,
            depart[1] + (arrivee[1] - depart[1]) * i / nombre,
        )
        for i in range(nombre + 1)
    ]


def points_arc(centre, rayon, angle_depart, angle_arrivee, pas):
    longueur = abs(math.radians(angle_arrivee - angle_depart)) * rayon
    nombre = max(1, round(longueur / pas))
    points = []
    for i in range(nombre + 1):
        angle = math.radians(angle_depart + (angle_arrivee - angle_depart) * i / nombre)
        points.append((centre[0] + rayon * math.cos(angle), centre[1] + rayon * math.sin(angle)))
    return points


def generer_trajet(pas):
    morceaux = [
        points_ligne((550, 690), (550, 400), pas),
        points_arc((605, 400), 55, 180, 270, pas),
        points_ligne((605, 345), (830, 345), pas),
        points_arc((830, 290), 55, 90, 0, pas),
        points_ligne((885, 290), (885, -30), pas),
    ]
    trajet = []
    for morceau in morceaux:
        for point in morceau:
            point_entier = (round(point[0]), round(point[1]))
            if not trajet or trajet[-1] != point_entier:
                trajet.append(point_entier)
    return trajet