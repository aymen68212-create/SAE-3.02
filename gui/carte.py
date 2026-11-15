import sys
import math
import time
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtGui import QPainter, QColor, QPen, QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from parametres import (LARGEUR, HAUTEUR, VOIES, FEUX, VITESSE_ONDE, PORTEE_ONDE, etats_initiaux,
                        points_ligne, points_arc, points_courbe)
from gui.decor import (BATIMENTS, ARBRES, dessiner_batiment, dessiner_parking, dessiner_arbre,
                       dessiner_routes, dessiner_marquages, dessiner_terre_plein, dessiner_sens_interdit,
                       dessiner_passages, dessiner_noms)
from gui.vehicules import dessiner_voiture
from gui.lit import Lit
from gui.circulation import Vehicule, trajet_depuis_morceaux

FOND = QColor(244, 239, 226)
COULEUR_BLEUE = QColor(60, 110, 200)
COULEUR_VIOLETTE = QColor(160, 90, 190)
COULEUR_TAXI = QColor(220, 170, 40)
COULEUR_VERTE = QColor(90, 170, 90)


def premier_indice(trajet, condition):
    return next(i for i, (x, y) in enumerate(trajet) if condition(x, y))


def trajet_violette():
    jardins = VOIES["jardins_ouest"]
    return trajet_depuis_morceaux([
        points_ligne((VOIES["branche_sud"], -30), (VOIES["branche_sud"], 235), 1),
        points_arc((775, 235), 60, 0, 90, 1),
        points_ligne((775, jardins), (600, jardins), 1),
        points_arc((600, 270), 25, 90, 180, 1),
        points_ligne((575, 270), (575, -30), 1),
    ])


def trajet_taxi():
    jardins = VOIES["jardins_est"]
    return trajet_depuis_morceaux([
        points_ligne((-30, 557), (350, 367), 1),
        points_courbe((350, 367), (394, jardins), (400, jardins), 1),
        points_ligne((400, jardins), (475, jardins), 1),
        points_arc((475, 295), 50, 90, 0, 1),
        points_ligne((525, 295), (525, -30), 1),
    ])


def trajet_verte():
    x = VOIES["avenue_nord"]
    return trajet_depuis_morceaux([points_ligne((x, 760), (x, -30), 1)])


def trajet_bleue():
    x = VOIES["avenue_sud_voiture"]
    return trajet_depuis_morceaux([points_ligne((x, -30), (x, 760), 1)])


class Carte(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulation Ambulance - IUT Colmar")
        self.setFixedSize(LARGEUR, HAUTEUR)
        self.verrou = threading.Lock()
        self.en_marche = threading.Event()
        self.callback_pause = None
        self.callback_reprise = None
        self.callback_rejouer = None
        self.mission_terminee = False
        self.bouton_pause = QPushButton("Pause", self)
        self.bouton_pause.setGeometry(12, HAUTEUR - 96, 110, 26)
        self.bouton_pause.clicked.connect(self.basculer_pause)
        self.bouton_rejouer = QPushButton("Rejouer", self)
        self.bouton_rejouer.setGeometry(128, HAUTEUR - 96, 110, 26)
        self.bouton_rejouer.setEnabled(False)
        self.bouton_rejouer.clicked.connect(self.rejouer)
        self.reinitialiser()
        self.fond = QPixmap(LARGEUR, HAUTEUR)
        peintre = QPainter(self.fond)
        peintre.setRenderHint(QPainter.Antialiasing)
        self.dessiner_decor(peintre)
        peintre.end()
        self.timer = QTimer()
        self.timer.timeout.connect(self.avancer_circulation)
        self.timer.timeout.connect(self.mettre_a_jour_bouton)
        self.timer.timeout.connect(self.update)
        self.timer.start(25)

    def reinitialiser(self):
        self.ambulance_x = VOIES["avenue_nord"]
        self.ambulance_y = 690
        self.angle = -90
        self.feux = etats_initiaux()
        with self.verrou:
            self.ondes = []
        self.lit = Lit()
        self.mission_terminee = False
        self.en_marche.set()
        self.duree_pause = 0.0
        self.debut_pause = None
        self.bouton_pause.setText("Pause")
        self.dernier_temps_circulation = time.time()
        self.vehicules = self.creer_circulation()

    def dessiner_decor(self, p):
        p.fillRect(0, 0, LARGEUR, HAUTEUR, FOND)
        for x, y, l, h, couleur in BATIMENTS:
            dessiner_batiment(p, x, y, l, h, couleur)
        dessiner_parking(p, 925, 30, 70, 160)
        dessiner_routes(p)
        dessiner_marquages(p)
        dessiner_terre_plein(p)
        dessiner_sens_interdit(p, 352, 328)
        dessiner_passages(p)
        dessiner_noms(p)
        for x, y in ARBRES:
            dessiner_arbre(p, x, y)
        dessiner_voiture(p, 940, 58, 42, 20, QColor(250, 250, 250))
        dessiner_voiture(p, 940, 110, 42, 20, QColor(250, 250, 250))

    def creer_circulation(self):
        trajet = trajet_bleue()
        ligne = premier_indice(trajet, lambda x, y: y >= 250)
        bleue = Vehicule(trajet, COULEUR_BLEUE, "nord_gauche", ligne)
        trajet = trajet_violette()
        ligne = premier_indice(trajet, lambda x, y: x <= 624 and y == VOIES["jardins_ouest"])
        violette = Vehicule(trajet, COULEUR_VIOLETTE, "nord_droite", ligne)
        trajet = trajet_taxi()
        ligne = premier_indice(trajet, lambda x, y: x >= 402)
        taxi = Vehicule(trajet, COULEUR_TAXI, "sud_gauche", ligne)
        trajet = trajet_verte()
        ligne = premier_indice(trajet, lambda x, y: y <= 392)
        verte = Vehicule(trajet, COULEUR_VERTE, "sud_droite", ligne)
        return [bleue, violette, taxi, verte]

    def demarrer_circulation(self):
        self.dernier_temps_circulation = time.time()
        for vehicule in self.vehicules:
            vehicule.actif = True

    def avancer_circulation(self):
        maintenant = time.time()
        dt = maintenant - self.dernier_temps_circulation if self.en_marche.is_set() else 0
        self.dernier_temps_circulation = maintenant
        for vehicule in self.vehicules:
            obstacles = [(self.ambulance_x, self.ambulance_y)]
            obstacles += [autre.position() for autre in self.vehicules if autre is not vehicule and not autre.termine()]
            vehicule.avancer(dt, self.feux, obstacles)

    def mettre_a_jour_bouton(self):
        self.bouton_rejouer.setEnabled(self.mission_terminee)
        self.bouton_pause.setEnabled(not self.mission_terminee)

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

    def embarquer_patient(self):
        self.lit.set_visible(False)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.drawPixmap(0, 0, self.fond)
        for id_feu in FEUX:
            self.dessiner_feu(p, id_feu)
        self.dessiner_ondes(p)
        for vehicule in self.vehicules:
            vehicule.dessiner(p)
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
                p.setPen(QPen(QColor(230, 30, 30, 200), 2))
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
        alternance = int(self.temps_simulation() * 6) % 2 == 0
        p.setBrush(QColor(255, 40, 40) if alternance else QColor(50, 90, 255))
        p.drawRect(QRectF(4, -9, 4, 7))
        p.setBrush(QColor(50, 90, 255) if alternance else QColor(255, 40, 40))
        p.drawRect(QRectF(4, 2, 4, 7))
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