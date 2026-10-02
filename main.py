import threading
from server.server import Serveur
from client.ambulance import Ambulance
from client.infrastructure import Infrastructure
from gui.carte import Carte
from PyQt5.QtWidgets import QApplication
import sys

PORT = 5050

def lancer_serveur():
    serveur = Serveur(PORT)
    serveur.demarrer()

def lancer_ambulance():
    trajet = [(100, 500), (200, 400), (300, 300), (400, 200)]
    ambulance = Ambulance(trajet)
    ambulance.connecter()
    ambulance.deplacer()

def lancer_infrastructure():
    infrastructure = Infrastructure()
    infrastructure.connecter()
    infrastructure.ecouter()

if __name__ == "__main__":

    thread_serveur = threading.Thread(target=lancer_serveur, daemon=True)
    thread_serveur.start()


    thread_infra = threading.Thread(target=lancer_infrastructure, daemon=True)
    thread_infra.start()


    thread_ambulance = threading.Thread(target=lancer_ambulance, daemon=True)
    thread_ambulance.start()


    app = QApplication(sys.argv)
    fenetre = Carte()
    fenetre.show()
    sys.exit(app.exec_())