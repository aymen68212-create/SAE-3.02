from PyQt5.QtGui import QColor, QPen
from PyQt5.QtCore import Qt, QRectF

VOITURES_ARRETEES = [
    (450, 200, 90, QColor(60, 110, 200)),
    (340, 350, -26.6, QColor(220, 170, 40)),
]


def dessiner_voiture(p, x, y, l, h, couleur):
    p.setPen(QPen(QColor(150, 150, 150), 1))
    p.setBrush(couleur)
    p.drawRoundedRect(QRectF(x, y, l, h), 6, 6)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(40, 50, 70))
    p.drawRoundedRect(QRectF(x + l * 0.3, y + 3, l * 0.38, h - 6), 3, 3)


def dessiner_voiture_orientee(p, x, y, angle, couleur):
    p.save()
    p.translate(x, y)
    p.rotate(angle)
    dessiner_voiture(p, -23, -11, 46, 22, couleur)
    p.restore()
