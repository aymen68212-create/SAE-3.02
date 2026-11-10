from PyQt5.QtGui import QColor, QPen
from PyQt5.QtCore import Qt, QPointF, QRectF

MARQUAGE = QColor(245, 245, 245)
PARKING = QColor(156, 156, 161)

BATIMENTS = [
    (240, 30, 120, 90, QColor(196, 130, 106)),
    (150, 150, 200, 100, QColor(164, 90, 74)),
    (640, 20, 150, 170, QColor(201, 176, 144)),
    (260, 480, 110, 70, QColor(184, 111, 92)),
    (180, 600, 170, 100, QColor(201, 176, 144)),
    (20, 610, 130, 90, QColor(164, 90, 74)),
    (640, 440, 140, 90, QColor(184, 111, 92)),
    (820, 470, 150, 120, QColor(164, 90, 74)),
    (700, 600, 200, 80, QColor(201, 176, 144)),
]

ARBRES = [
    (140, 30), (370, 60), (370, 140), (60, 300), (120, 335), (200, 300), (300, 275),
    (60, 580), (375, 440), (160, 520), (230, 570),
    (630, 215), (710, 225), (775, 215),
    (950, 230), (960, 300), (950, 400),
    (655, 412), (800, 420), (790, 560), (640, 570), (630, 650), (930, 640), (965, 610), (985, 440),
]


def dessiner_batiment(p, x, y, l, h, couleur):
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0, 0, 0, 40))
    p.drawRect(x + 8, y + 8, l, h)
    p.setPen(QPen(couleur.darker(130), 2))
    p.setBrush(couleur)
    p.drawRect(x, y, l, h)
    p.setPen(Qt.NoPen)
    p.setBrush(couleur.darker(112))
    p.drawRect(x + 12, y + 12, l - 24, h - 24)
    p.setBrush(couleur.darker(135))
    for i in range(3):
        p.drawRect(x + 22 + i * 36, y + 22, 18, 18)


def dessiner_parking(p, x, y, l, h):
    p.setPen(QPen(QColor(120, 120, 125), 2))
    p.setBrush(PARKING)
    p.drawRect(x, y, l, h)
    p.setPen(QPen(MARQUAGE, 2))
    ligne = y + 26
    while ligne < y + h - 10:
        p.drawLine(x + l - 62, ligne, x + l, ligne)
        ligne += 26


def dessiner_arbre(p, x, y):
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0, 0, 0, 45))
    p.drawEllipse(QPointF(x + 3, y + 5), 12, 10)
    p.setPen(QPen(QColor(60, 100, 48), 1))
    p.setBrush(QColor(82, 127, 63))
    p.drawRoundedRect(QRectF(x - 11, y - 11, 22, 22), 8, 8)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(105, 150, 80))
    p.drawEllipse(QPointF(x - 3, y - 3), 5, 5)
