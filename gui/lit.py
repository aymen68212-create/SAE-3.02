"""Lit du patient : dessin et état (position, angle, visibilité)."""

from PyQt5.QtGui import QColor, QPen
from PyQt5.QtCore import Qt, QRectF, QPointF


def dessiner_lit(p, x, y, angle, avec_patient=True):
    """Dessine un lit médicalisé orienté.

    Args:
        p: `QPainter`.
        x: abscisse du centre.
        y: ordonnée du centre.
        angle: orientation en degrés.
        avec_patient: si vrai, dessine aussi le patient allongé.
    """
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
    """Lit posé dans le parking jusqu'à l'embarquement.

    Attributes:
        x: abscisse.
        y: ordonnée.
        angle: orientation en degrés.
        visible: False une fois le patient embarqué.
    """
    def __init__(self):
        """Place le lit visible dans le parking."""
        self.x = 958
        self.y = 170
        self.angle = 180
        self.visible = True

    def get_position(self):
        """Retourne la position (x, y)."""
        return (self.x, self.y)

    def set_position(self, x, y):
        """Déplace le lit.

        Args:
            x: nouvelle abscisse.
            y: nouvelle ordonnée.
        """
        self.x = x
        self.y = y

    def get_angle(self):
        """Retourne l'orientation en degrés."""
        return self.angle

    def set_angle(self, angle):
        """Change l'orientation.

        Args:
            angle: angle en degrés.
        """
        self.angle = angle

    def get_visible(self):
        """Indique si le lit est dessiné."""
        return self.visible

    def set_visible(self, visible):
        """Affiche ou masque le lit.

        Args:
            visible: True pour le dessiner.
        """
        self.visible = visible

    def dessiner(self, p):
        """Dessine le lit s'il est visible.

        Args:
            p: `QPainter`.
        """
        if self.visible:
            dessiner_lit(p, self.x, self.y, self.angle)
