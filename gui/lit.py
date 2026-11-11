import math
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtCore import Qt, QRectF, QPointF
from parametres import points_ligne, points_arc


def dessiner_lit(p, x, y, angle, avec_patient=True):
    p.save()
    p.translate(x, y)
    p.rotate(angle)
    p.setPen(QPen(QColor(70, 75, 85), 1))
    p.setBrush(QColor(170, 175, 180))
    p.drawRoundedRect(QRectF(-20, -8, 40, 16), 3, 3)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(225, 235, 245))
    p.drawRoundedRect(QRectF(-18, -6, 36, 12), 2, 2)
    p.setBrush(QColor(255, 255, 255))
    p.drawRoundedRect(QRectF(-17, -4.5, 8, 9), 2, 2)
    if avec_patient:
        p.setBrush(QColor(235, 190, 150))
        p.drawEllipse(QPointF(-12, 0), 5, 5)
        p.setBrush(QColor(120, 170, 210))
        p.drawRoundedRect(QRectF(-7, -4.5, 17, 9), 3, 3)
        p.setBrush(QColor(255, 255, 255))
        p.drawRect(QRectF(10, -2.5, 8, 5))
        p.setBrush(QColor(200, 40, 40))
        p.drawEllipse(QPointF(14, 0), 1.3, 1.3)
    p.setPen(QPen(QColor(120, 125, 135), 1.2))
    p.drawLine(QPointF(-16, -7), QPointF(16, -7))
    p.drawLine(QPointF(-16, 7), QPointF(16, 7))
    p.setPen(QPen(QColor(40, 40, 45), 1))
    p.setBrush(QColor(40, 40, 45))
    for cx, cy in ((-17, -8), (17, -8), (-17, 8), (17, 8)):
        p.drawEllipse(QPointF(cx, cy), 2.5, 2.5)
    p.restore()


class Lit:
    def __init__(self):
        self.x = 958
        self.y = 170
        self.angle = 180
        self.trajet = []
        self.indice = 0.0
        self.visible = True
        self.en_mouvement = False

    def get_position(self):
        return (self.x, self.y)

    def set_position(self, x, y):
        self.x = x
        self.y = y

    def get_angle(self):
        return self.angle

    def set_angle(self, angle):
        self.angle = angle

    def generer_trajet_lit(self):
        morceaux = (
            points_ligne((958, 170), (910, 170), 1)
            + points_arc((910, 145), 25, 90, 180, 1)
            + points_ligne((885, 145), (885, 110), 1)
        )
        points = []
        for point in morceaux:
            if not points or math.dist(points[-1], point) > 1e-6:
                points.append(point)
        return points

    def dessiner(self, p):
        if self.visible:
            dessiner_lit(p, self.x, self.y, self.angle)
