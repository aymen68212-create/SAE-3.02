import sys
import math
import time
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtGui import QPainter, QColor, QPen, QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from parametres import LARGEUR, HAUTEUR, VOIES, FEUX, VITESSE_ONDE, PORTEE_ONDE, etats_initiaux, points_ligne, points_arc
from gui.decor import (BATIMENTS, ARBRES, dessiner_batiment, dessiner_parking, dessiner_arbre,
                       dessiner_routes, dessiner_marquages, dessiner_passages, dessiner_noms)
from gui.vehicules import VOITURES_ARRETEES, dessiner_voiture, dessiner_voiture_orientee
from gui.lit import Lit
from gui.circulation import Vehicule, trajet_depuis_morceaux

DISTANCE_SUIVEUSE = 70

FOND = QColor(244, 239, 226)
COULEUR_BLEUE = QColor(60, 110, 200)
COULEUR_VIOLETTE = QColor(160, 90, 190)


def premier_indice(trajet, condition):
    return next(i for i, (x, y) in enumerate(trajet) if condition(x, y))


def trajet_violette():
    jardins = VOIES["jardins_ouest"]
    return trajet_depuis_morceaux([
        points_ligne((VOIES["branche_sud"], -30), (VOIES["branche_sud"], 235), 1),
        points_arc((775, 235), 60, 0, 90, 1),
        points_ligne((775, jardins), (400, jardins), 1),
        points_ligne((400, jardins), (-30, jardins + 215), 1),
    ])


def trajet_bleue():
    x = VOIES["avenue_sud_voiture"]
    return trajet_depuis_morceaux([points_ligne((x, -30), (x, 760), 1)])


class Carte(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulation Ambulance - IUT Colmar")
        self.setFixedSize(LARGEUR, HAUTEUR)
        self.verrou = threading.Lock()
        self.embarquement_fini = threading.Event()
        self.en_marche = threading.Event()
        self.callback_pause = None
        self.callback_reprise = None
        self.callback_rejouer = None
        self.bouton_pause = QPushButton("Pause", self)
        self.bouton_pause.setGeometry(12, HAUTEUR - 96, 110, 26)
        self.bouton_pause.clicked.connect(self.basculer_pause)
        self.bouton_rejouer = QPushButton("Rejouer", self)
        self.bouton_rejouer.setGeometry(128, HAUTEUR - 96, 110, 26)
        self.bouton_rejouer.clicked.connect(self.rejouer)
        self.reinitialiser()
        self.fond = QPixmap(LARGEUR, HAUTEUR)
        peintre = QPainter(self.fond)
        peintre.setRenderHint(QPainter.Antialiasing)
        self.dessiner_decor(peintre)
        peintre.end()
        self.timer = QTimer()
        self.timer.timeout.connect(self.avancer_circulation)
        self.timer.timeout.connect(self.avancer_lit)
        self.timer.timeout.connect(self.update)
        self.timer.start(25)

    def reinitialiser(self):
        self.ambulance_x = VOIES["avenue_nord"]
        self.ambulance_y = 690
        self.angle = -90
        self.feux = etats_initiaux()
        self.trace = [(VOIES["avenue_nord"], y) for y in range(690 + DISTANCE_SUIVEUSE + 10, 690, -1)] + [(VOIES["avenue_nord"], 690)]
        with self.verrou:
            self.ondes = []
        self.embarquement_fini.clear()
        self.portes_ouvertes = False
        self.lit = Lit(self.embarquement_fini)
        self.lit.visible = True
        self.lit.actif = False
        self.en_marche.set()
        self.duree_pause = 0.0
        self.debut_pause = None
        self.bouton_pause.setText("Pause")
        self.dernier_temps_lit = time.time()
        self.dernier_temps_circulation = time.time()
        self.vehicules = self.creer_circulation()

    def dessiner_decor(self, p):
        p.fillRect(0, 0, LARGEUR, HAUTEUR, FOND)
        for x, y, l, h, couleur in BATIMENTS:
            dessiner_batiment(p, x, y, l, h, couleur)
        dessiner_parking(p, 20, 20, 110, 250)
        dessiner_parking(p, 925, 30, 70, 160)
        dessiner_routes(p)
        dessiner_marquages(p)
        dessiner_passages(p)
        dessiner_noms(p)
        for x, y in ARBRES:
            dessiner_arbre(p, x, y)
        dessiner_voiture(p, 70, 60, 46, 22, QColor(250, 250, 250))
        dessiner_voiture(p, 70, 138, 46, 22, QColor(250, 250, 250))
        dessiner_voiture(p, 940, 58, 42, 20, QColor(250, 250, 250))
        dessiner_voiture(p, 940, 110, 42, 20, QColor(250, 250, 250))

    def creer_circulation(self):
        trajet = trajet_bleue()
        ligne = premier_indice(trajet, lambda x, y: y >= 250)
        bleue = Vehicule(trajet, COULEUR_BLEUE, "nord_gauche", ligne)
        trajet = trajet_violette()
        ligne = premier_indice(trajet, lambda x, y: x <= 624 and y == VOIES["jardins_ouest"])
        violette = Vehicule(trajet, COULEUR_VIOLETTE, "nord_droite", ligne)
        return [bleue, violette]

    def demarrer_circulation(self):
        self.dernier_temps_circulation = time.time()
        for vehicule in self.vehicules:
            vehicule.actif = True

    def avancer_circulation(self):
        maintenant = time.time()
        dt = maintenant - self.dernier_temps_circulation if self.en_marche.is_set() else 0
        self.dernier_temps_circulation = maintenant
        obstacles = [(self.ambulance_x, self.ambulance_y), self.pose_suiveuse()[:2]]
        for vehicule in self.vehicules:
            vehicule.avancer(dt, self.feux, obstacles)

    def avancer_lit(self):
        maintenant = time.time()
        duree = maintenant - self.dernier_temps_lit
        self.dernier_temps_lit = maintenant
        self.lit.avancer(duree if self.en_marche.is_set() else 0)

    def temps_simulation(self):
        maintenant = time.time()
        pause = self.duree_pause
        if self.debut_pause is not None:
            pause += maintenant - self.debut_pause
        return maintenant - pause

    def basculer_pause(self):
        if self.en_marche.is_set():
            self.debut_pause = time.time()
            self.en_marche.clear()
            self.bouton_pause.setText("Reprendre")
            if self.callback_pause:
                self.callback_pause()
        else:
            self.duree_pause += time.time() - self.debut_pause
            self.debut_pause = None
            self.en_marche.set()
            self.bouton_pause.setText("Pause")
            if self.callback_reprise:
                self.callback_reprise()

    def rejouer(self):
        if self.callback_rejouer:
            self.callback_rejouer()

    def jouer_embarquement(self):
        self.embarquement_fini.clear()
        self.dernier_temps_lit = time.time()
        self.lit.actif = True
        self.portes_ouvertes = True
        self.embarquement_fini.wait()
        self.portes_ouvertes = False

    def pose_suiveuse(self):
        trace = list(self.trace)
        parcouru = 0
        i = len(trace) - 1
        while i > 0 and parcouru < DISTANCE_SUIVEUSE:
            parcouru += math.dist(trace[i], trace[i - 1])
            i -= 1
        x, y = trace[i]
        suivant = trace[min(i + 5, len(trace) - 1)]
        angle = math.degrees(math.atan2(suivant[1] - y, suivant[0] - x))
        return x, y, angle

    def dessiner_suiveuse(self, p):
        x, y, angle = self.pose_suiveuse()
        dessiner_voiture_orientee(p, x, y, angle, QColor(90, 170, 90))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.drawPixmap(0, 0, self.fond)
        for id_feu in FEUX:
            self.dessiner_feu(p, id_feu)
        self.dessiner_ondes(p)
        for x, y, angle, couleur in VOITURES_ARRETEES:
            dessiner_voiture_orientee(p, x, y, angle, couleur)
        for vehicule in self.vehicules:
            vehicule.dessiner(p)
        self.dessiner_suiveuse(p)
        self.lit.dessiner(p)
        self.dessiner_ambulance(p)
        self.dessiner_legende(p)

    def dessiner_feu(self, p, id_feu):
        x = FEUX[id_feu]["x"]
        y = FEUX[id_feu]["y"]
        rouge = self.feux[id_feu] == "rouge"
        p.setPen(QPen(QColor(10, 10, 12), 1))
        p.setBrush(QColor(32, 32, 36))
        p.drawRoundedRect(QRectF(x - 9, y - 23, 18, 46), 5, 5)
        vert = not rouge
        lampes = [
            (y - 14, QColor(235, 45, 45) if rouge else QColor(85, 30, 30), rouge),
            (y, QColor(90, 80, 20), False),
            (y + 14, QColor(45, 210, 85) if vert else QColor(25, 70, 35), vert),
        ]
        for centre_y, couleur, allumee in lampes:
            p.setPen(Qt.NoPen)
            if allumee:
                p.setBrush(QColor(couleur.red(), couleur.green(), couleur.blue(), 70))
                p.drawEllipse(QPointF(x, centre_y), 11, 11)
            p.setBrush(couleur)
            p.drawEllipse(QPointF(x, centre_y), 6, 6)

    def dessiner_ondes(self, p):
        maintenant = self.temps_simulation()
        with self.verrou:
            ondes = list(self.ondes)
        p.setBrush(Qt.NoBrush)
        for debut in ondes:
            rayon = (maintenant - debut) * VITESSE_ONDE
            if 0 <= rayon <= PORTEE_ONDE:
                opacite = int(50 + 190 * (1 - rayon / PORTEE_ONDE))
                p.setPen(QPen(QColor(230, 30, 30, opacite), 3))
                p.drawEllipse(QPointF(self.ambulance_x, self.ambulance_y), rayon, rayon)

    def dessiner_ambulance(self, p):
        p.save()
        p.translate(self.ambulance_x, self.ambulance_y)
        p.rotate(self.angle)
        p.scale(1.3, 1.3)
        p.setPen(QPen(QColor(40, 40, 45), 1))
        p.setBrush(QColor(255, 255, 255))
        p.drawRoundedRect(QRectF(-22, -11, 44, 22), 4, 4)
        p.setBrush(QColor(170, 205, 235))
        p.drawRect(QRectF(11, -9, 7, 18))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(220, 30, 30))
        p.drawRect(QRectF(-16, -2.5, 13, 5))
        p.drawRect(QRectF(-12, -6.5, 5, 13))
        alternance = int(time.time() * 6) % 2 == 0
        p.setBrush(QColor(255, 40, 40) if alternance else QColor(50, 90, 255))
        p.drawRect(QRectF(4, -9, 4, 7))
        p.setBrush(QColor(50, 90, 255) if alternance else QColor(255, 40, 40))
        p.drawRect(QRectF(4, 2, 4, 7))
        if self.portes_ouvertes:
            p.setPen(QPen(QColor(40, 40, 45), 1))
            p.setBrush(QColor(235, 235, 235))
            p.drawRect(QRectF(-30, -11, 8, 3))
            p.drawRect(QRectF(-30, 8, 8, 3))
        p.restore()

    def dessiner_legende(self, p):
        p.setPen(QPen(QColor(150, 150, 150), 1))
        p.setBrush(QColor(255, 255, 255, 215))
        p.drawRoundedRect(QRectF(12, HAUTEUR - 62, 345, 50), 6, 6)
        p.setPen(QColor(30, 30, 30))
        p.setFont(QFont("Arial", 9))
        p.drawText(24, HAUTEUR - 41, "Cercles rouges : ondes sonores émises par l'ambulance")
        p.drawText(24, HAUTEUR - 22, "Feu rouge -> feu vert dès que l'onde la plus grande le touche")

    def mettre_a_jour_ambulance(self, x, y):
        dx = x - self.ambulance_x
        dy = y - self.ambulance_y
        if math.hypot(dx, dy) > 0.5:
            self.angle = math.degrees(math.atan2(dy, dx))
        self.ambulance_x = x
        self.ambulance_y = y
        self.trace.append((x, y))
        del self.trace[:-400]

    def ajouter_onde(self):
        maintenant = self.temps_simulation()
        with self.verrou:
            self.ondes = [t for t in self.ondes if (maintenant - t) * VITESSE_ONDE <= PORTEE_ONDE]
            self.ondes.append(maintenant)

    def mettre_a_jour_feu(self, id_feu, etat):
        self.feux[id_feu] = etat


if __name__ == "__main__":
    app = QApplication(sys.argv)
    fenetre = Carte()
    fenetre.show()
    sys.exit(app.exec_())