import math

HOTE = "localhost"
PORT = 5050

LARGEUR = 1000
HAUTEUR = 700

VITESSE_AMBULANCE = 90
FREQUENCE_POSITION = 20
VITESSE_ONDE = 220
PORTEE_ONDE = 160
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


FEU_AMBULANCE = "sud_droite"
PAIRE_AMBULANCE = ("sud_droite", "nord_gauche")
FEU_RETOUR = "sud_gauche"
PAIRE_RETOUR = ("sud_gauche", "nord_droite")


def etats_initiaux():
    return {id_feu: "rouge" if id_feu in PAIRE_AMBULANCE else "vert" for id_feu in FEUX}


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


def points_courbe(depart, controle, arrivee, pas):
    longueur = math.dist(depart, controle) + math.dist(controle, arrivee)
    nombre = max(1, round(longueur / pas))
    points = []
    for i in range(nombre + 1):
        t = i / nombre
        points.append((
            (1 - t) ** 2 * depart[0] + 2 * (1 - t) * t * controle[0] + t ** 2 * arrivee[0],
            (1 - t) ** 2 * depart[1] + 2 * (1 - t) * t * controle[1] + t ** 2 * arrivee[1],
        ))
    return points


def generer_trajet(pas):
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
            point_entier = (round(point[0]), round(point[1]))
            if not trajet or trajet[-1] != point_entier:
                trajet.append(point_entier)
    return trajet

def generer_trajet_retour(pas):
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
