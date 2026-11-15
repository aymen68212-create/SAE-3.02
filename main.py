import threading
import time
import sys
from PyQt5.QtWidgets import QApplication
from parametres import PORT, VITESSE_AMBULANCE, FREQUENCE_POSITION, generer_trajet, generer_trajet_retour
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
    pas = VITESSE_AMBULANCE / FREQUENCE_POSITION
    trajet_aller = generer_trajet(pas)
    ambulance = Ambulance()
    ambulance.callback_position = carte.mettre_a_jour_ambulance
    ambulance.callback_onde = carte.ajouter_onde
    ambulance.connecter()
    carte.demarrer_circulation()
    ambulance.deplacer(trajet_aller)
    ambulance.signaler_arret()
    time.sleep(2)
    carte.embarquer_patient()
    ambulance.signaler_embarquement()
    ambulance.deplacer(generer_trajet_retour(pas))
    ambulance.terminer()
    carte.mission_terminee = True


def lancer_mission(carte, infrastructure_prete, verrou_mission):
    try:
        lancer_ambulance(carte, infrastructure_prete)
    finally:
        verrou_mission.release()


def demarrer_mission(carte, infrastructure_prete, verrou_mission, remettre_a_zero):
    if not verrou_mission.acquire(blocking=False):
        return False
    if remettre_a_zero:
        carte.reinitialiser()
    thread_ambulance = threading.Thread(target=lancer_mission, args=(carte, infrastructure_prete, verrou_mission), daemon=True)
    thread_ambulance.start()
    return True


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

    verrou_mission = threading.Lock()
    carte.callback_rejouer = lambda: demarrer_mission(carte, infrastructure_prete, verrou_mission, True)
    demarrer_mission(carte, infrastructure_prete, verrou_mission, False)

    sys.exit(app.exec_())