"""Dessin des voitures vues de dessus."""

from PyQt5.QtGui import QColor, QPen
from PyQt5.QtCore import Qt, QRectF


def dessiner_voiture(p, x, y, l, h, couleur):
    """Dessine une voiture horizontale avec son pare-brise.

    Args:
        p: `QPainter`.
        x: abscisse du coin supérieur gauche.
        y: ordonnée du coin supérieur gauche.
        l: longueur.
        h: largeur.
        couleur: `QColor` de la carrosserie.
    """
    p.setPen(QPen(QColor(150, 150, 150), 1))
    p.setBrush(couleur)
    p.drawRoundedRect(QRectF(x, y, l, h), 6, 6)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(40, 50, 70))
    p.drawRoundedRect(QRectF(x + l * 0.3, y + 3, l * 0.38, h - 6), 3, 3)


def dessiner_voiture_orientee(p, x, y, angle, couleur):
    """Dessine une voiture de 46 x 22 pixels centrée en (x, y) et tournée de `angle` degrés.

    Args:
        p: `QPainter`.
        x: abscisse du centre.
        y: ordonnée du centre.
        angle: orientation en degrés.
        couleur: `QColor` de la carrosserie.
    """
    p.save()
    p.translate(x, y)
    p.rotate(angle)
    dessiner_voiture(p, -23, -11, 46, 22, couleur)
    p.restore()
