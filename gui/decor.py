from PyQt5.QtGui import QColor, QPen, QPainterPath, QFont
from PyQt5.QtCore import Qt, QPointF, QRectF
from parametres import HAUTEUR

ROUTE = QColor(76, 78, 84)
TROTTOIR = QColor(196, 196, 199)
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


def chaussees():
    chemin = QPainterPath()
    chemin.setFillRule(Qt.WindingFill)
    chemin.addRect(400, 0, 200, HAUTEUR)
    chemin.addRect(600, 270, 310, 100)
    chemin.addRect(810, 0, 100, 370)
    diagonale = QPainterPath()
    diagonale.moveTo(400, 270)
    diagonale.lineTo(400, 370)
    diagonale.lineTo(0, 570)
    diagonale.lineTo(0, 470)
    diagonale.closeSubpath()
    chemin.addPath(diagonale)
    return chemin.simplified()


def dessiner_routes(p):
    route = chaussees()
    p.strokePath(route, QPen(TROTTOIR, 22, Qt.SolidLine, Qt.FlatCap, Qt.MiterJoin))
    p.fillPath(route, ROUTE)


def dessiner_marquages(p):
    pointillees = QPen(MARQUAGE, 2)
    pointillees.setDashPattern([7, 9])
    p.setPen(pointillees)
    for x in (450, 500, 550):
        p.drawLine(x, 0, x, 248)
        p.drawLine(x, 394, x, HAUTEUR)
    p.drawLine(388, 322, 0, 516)
    p.drawLine(622, 320, 860, 320)
    p.drawLine(860, 320, 860, 0)


def dessiner_passages(p):
    p.setPen(Qt.NoPen)
    p.setBrush(MARQUAGE)
    for x in range(410, 592, 18):
        p.drawRect(x, 250, 10, 18)
        p.drawRect(x, 374, 10, 18)
    for y in range(280, 362, 16):
        p.drawRect(402, y, 18, 9)
        p.drawRect(606, y, 18, 9)


def dessiner_noms(p):
    p.setPen(QColor(255, 255, 255))
    p.setFont(QFont("Arial", 13, QFont.Bold))
    p.save()
    p.translate(582, 90)
    p.rotate(90)
    p.drawText(0, 0, "Av. d'Alsace")
    p.restore()
    p.setFont(QFont("Arial", 11, QFont.Bold))
    p.drawText(660, 306, "Rue des Jardins")
    p.save()
    p.translate(842, 230)
    p.rotate(-90)
    p.drawText(0, 0, "Rue des Jardins")
    p.restore()
    p.setPen(QPen(QColor(120, 100, 0), 1))
    p.setBrush(QColor(250, 205, 20))
    p.drawRoundedRect(QRectF(455, 60, 42, 20), 4, 4)
    p.setPen(QColor(30, 30, 30))
    p.setFont(QFont("Arial", 9, QFont.Bold))
    p.drawText(QRectF(455, 60, 42, 20), Qt.AlignCenter, "D201")
