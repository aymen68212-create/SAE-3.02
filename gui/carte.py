import sys
import math
import time
import threading
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from parametres import LARGEUR, HAUTEUR, FEUX, VITESSE_ONDE, PORTEE_ONDE, etats_initiaux, points_ligne, points_arc
from gui.decor import (BATIMENTS, ARBRES, dessiner_batiment, dessiner_parking, dessiner_arbre,
                       dessiner_routes, dessiner_marquages, dessiner_passages, dessiner_noms)
from gui.vehicules import VOITURES_ARRETEES, dessiner_voiture, dessiner_voiture_orientee

DISTANCE_SUIVEUSE = 70
VITESSE_VOITURE = 90
LIGNE_ARRET_OPPOSEE = 665

FOND = QColor(244, 239, 226)


class Carte(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulation Ambulance - IUT Colmar")
        self.setFixedSize(LARGEUR, HAUTEUR)
        self.ambulance_x = 550
        self.ambulance_y = 690
        self.angle = -90
        self.feux = etats_initiaux()
        self.trace = [(550, y) for y in range(690 + DISTANCE_SUIVEUSE + 10, 690, -1)] + [(550, 690)]
        self.ondes = []
        self.verrou = threading.Lock()
        self.fond = QPixmap(LARGEUR, HAUTEUR)
        peintre = QPainter(self.fond)
        peintre.setRenderHint(QPainter.Antialiasing)
        self.dessiner_decor(peintre)
        peintre.end()
        self.timer = QTimer()
        self.timer.timeout.connect(self.avancer_opposee)
        self.timer.timeout.connect(self.update)
        self.timer.start(25)
        self.trajet_oppose = self.generer_trajet_oppose()
        self.indice_oppose = 0.0
        self.dernier_temps = time.time()

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

    def generer_trajet_oppose(self):
        trajet = []
        morceaux = [
            points_ligne((910, 295), (550, 295), 1),
            points_arc((550, 395), 100, -90, -180, 1),
            points_ligne((450, 395), (450, 760), 1),
        ]
        for morceau in morceaux:
            for point in morceau:
                if not trajet or trajet[-1] != point:
                    trajet.append(point)
        return trajet

    def avancer_opposee(self):
        maintenant = time.time()
        pas = (maintenant - self.dernier_temps) * VITESSE_VOITURE
        self.dernier_temps = maintenant
        suivant = self.indice_oppose + pas
        x = self.trajet_oppose[int(self.indice_oppose)][0]
        y = self.trajet_oppose[int(self.indice_oppose)][1]
        avant_ligne = y == 295 and x > LIGNE_ARRET_OPPOSEE
        if avant_ligne and self.feux["nord_droite"] == "rouge":
            suivant = min(suivant, self.indice_ligne_arret())
        self.indice_oppose = min(suivant, len(self.trajet_oppose) - 1)

    def indice_ligne_arret(self):
        return next(i for i, (x, y) in enumerate(self.trajet_oppose) if x <= LIGNE_ARRET_OPPOSEE)

    def dessiner_opposee(self, p):
        i = int(self.indice_oppose)
        x, y = self.trajet_oppose[i]
        avant = self.trajet_oppose[min(i + 3, len(self.trajet_oppose) - 1)]
        arriere = self.trajet_oppose[max(i - 3, 0)]
        angle = math.degrees(math.atan2(avant[1] - arriere[1], avant[0] - arriere[0]))
        dessiner_voiture_orientee(p, x, y, angle, QColor(160, 90, 190))

    def dessiner_suiveuse(self, p):
        trace = list(self.trace)
        parcouru = 0
        i = len(trace) - 1
        while i > 0 and parcouru < DISTANCE_SUIVEUSE:
            parcouru += math.dist(trace[i], trace[i - 1])
            i -= 1
        x, y = trace[i]
        suivant = trace[min(i + 5, len(trace) - 1)]
        angle = math.degrees(math.atan2(suivant[1] - y, suivant[0] - x))
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
        self.dessiner_suiveuse(p)
        self.dessiner_opposee(p)
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
        maintenant = time.time()
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
        maintenant = time.time()
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