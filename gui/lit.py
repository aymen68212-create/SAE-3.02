from PyQt5.QtGui import QColor, QPen
from PyQt5.QtCore import Qt, QRectF, QPointF


def dessiner_lit(p, x, y, angle):
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
    p.setPen(QPen(QColor(120, 125, 135), 1.2))
    p.drawLine(QPointF(-16, -7), QPointF(16, -7))
    p.drawLine(QPointF(-16, 7), QPointF(16, 7))
    p.setPen(QPen(QColor(40, 40, 45), 1))
    p.setBrush(QColor(40, 40, 45))
    for cx, cy in ((-17, -8), (17, -8), (-17, 8), (17, 8)):
        p.drawEllipse(QPointF(cx, cy), 2.5, 2.5)
    p.restore()
