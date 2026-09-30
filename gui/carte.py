import sys
from PyQt5.QtWidgets import QApplication, QWidget


class Carte(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Carte")
        self.setFixedSize(900, 650)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    fenetre = Carte()
    fenetre.show()
    sys.exit(app.exec_())
