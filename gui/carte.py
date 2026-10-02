import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
from PyQt5.QtCore import Qt, QTimer

class Carte(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulation Ambulance - IUT Colmar")
        self.setFixedSize(900, 650)
        self.ambulance_x = 100
        self.ambulance_y = 500
        self.feux = {"nord": False, "sud": False, "est": False, "ouest": False}
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(100)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(0, 0, 900, 650, QColor(180, 210, 180))
        painter.setBrush(QBrush(QColor(80, 80, 80)))
        painter.setPen(Qt.NoPen)
        painter.drawRect(400, 0, 100, 650)
        painter.drawRect(0, 200, 500, 80)
        painter.drawRect(400, 450, 500, 80)
        painter.setPen(QPen(QColor(255, 255, 255), 2, Qt.DashLine))
        painter.drawLine(450, 0, 450, 200)
        painter.drawLine(0, 240, 400, 240)
        painter.drawLine(450, 450, 450, 650)
        painter.drawLine(500, 490, 900, 490)
        self.dessiner_feu(painter, 385, 185, "nord")
        self.dessiner_feu(painter, 515, 185, "est")
        self.dessiner_feu(painter, 385, 295, "sud")
        self.dessiner_feu(painter, 515, 295, "ouest")
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.drawRect(self.ambulance_x - 15, self.ambulance_y - 10, 30, 20)
        painter.setPen(QPen(QColor(255, 0, 0), 3))
        painter.drawLine(self.ambulance_x, self.ambulance_y - 7, self.ambulance_x, self.ambulance_y + 7)
        painter.drawLine(self.ambulance_x - 7, self.ambulance_y, self.ambulance_x + 7, self.ambulance_y)
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.drawText(10, 635, "Rouge = feu rouge  |  Vert = feu vert  |  Blanc/Croix = Ambulance")

    def dessiner_feu(self, painter, x, y, direction):
        couleur = QColor(0, 200, 0) if self.feux[direction] else QColor(200, 0, 0)
        painter.setBrush(QBrush(couleur))
        painter.setPen(QPen(Qt.black, 1))
        painter.drawEllipse(x, y, 20, 20)

    def mettre_a_jour_ambulance(self, x, y):
        self.ambulance_x = x
        self.ambulance_y = y

    def mettre_a_jour_feux(self, etat_feux):
        self.feux = etat_feux

if __name__ == "__main__":
    app = QApplication(sys.argv)
    fenetre = Carte()
    fenetre.show()
    sys.exit(app.exec_())