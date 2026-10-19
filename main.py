import threading
import time
import sys
from PyQt5.QtWidgets import QApplication
from parametres import PORT, VITESSE_AMBULANCE, FREQUENCE_POSITION, generer_trajet
from server.server import Serveur
from client.ambulance import Ambulance
from client.infrastructure import Infrastructure
from gui.carte import Carte


def lancer_serveur(serveur):
    serveur.demarrer()


def lancer_infrastructure(carte, infrastructure_prete):
    infrastructure = Infrastructure()
    infrastructure.callback_feux = lambda message: carte.mettre_a_jour_feu(message["id"], message["etat"])
    infrastructure.connecter()
    infrastructure_prete.set()
    infrastructure.ecouter()


def lancer_ambulance(carte, infrastructure_prete):
    infrastructure_prete.wait()
    time.sleep(1)
    trajet = generer_trajet(VITESSE_AMBULANCE / FREQUENCE_POSITION)
    ambulance = Ambulance(trajet)
    ambulance.callback_position = carte.mettre_a_jour_ambulance
    ambulance.callback_onde = carte.ajouter_onde
    ambulance.connecter()
    ambulance.deplacer()
    ambulance.terminer()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    carte = Carte()
    carte.show()

    serveur = Serveur(PORT)
    thread_serveur = threading.Thread(target=lancer_serveur, args=(serveur,), daemon=True)
    thread_serveur.start()
    serveur.pret.wait()

    infrastructure_prete = threading.Event()

    thread_infrastructure = threading.Thread(target=lancer_infrastructure, args=(carte, infrastructure_prete), daemon=True)
    thread_infrastructure.start()

    thread_ambulance = threading.Thread(target=lancer_ambulance, args=(carte, infrastructure_prete), daemon=True)
    thread_ambulance.start()

    sys.exit(app.exec_())