import threading
import time
import sys
from server.server import Serveur
from client.ambulance import Ambulance
from client.infrastructure import Infrastructure
from gui.carte import Carte
from PyQt5.QtWidgets import QApplication

PORT = 5050

def lancer_serveur():
    serveur = Serveur(PORT)
    serveur.demarrer()

def lancer_infrastructure(carte):
    time.sleep(1)
    infrastructure = Infrastructure()
    infrastructure.callback_feux = lambda msg: carte.mettre_a_jour_feux({
        "nord": msg.get("nord", False),
        "sud": msg.get("sud", False),
        "est": msg.get("est", False),
        "ouest": msg.get("ouest", False)
    })
    infrastructure.connecter()
    infrastructure.ecouter()

def lancer_ambulance(carte):
    time.sleep(1)
    trajet = [(100, 500), (200, 430), (300, 360), (400, 290), (450, 240), (450, 180)]
    ambulance = Ambulance(trajet)
    ambulance.connecter()
    for x, y in trajet:
        ambulance.envoyer_position(x, y)
        carte.mettre_a_jour_ambulance(x, y)
        time.sleep(1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    carte = Carte()
    carte.show()

    thread_serveur = threading.Thread(target=lancer_serveur, daemon=True)
    thread_serveur.start()

    thread_infra = threading.Thread(target=lancer_infrastructure, args=(carte,), daemon=True)
    thread_infra.start()

    thread_ambulance = threading.Thread(target=lancer_ambulance, args=(carte,), daemon=True)
    thread_ambulance.start()

    sys.exit(app.exec_())