"""Point d'entrée de la simulation : interface, serveur et clients.

Lance par défaut le serveur, le client infrastructure, le client ambulance et la fenêtre Qt dans le même
processus (un thread par composant). Avec l'option --sans-serveur, seul le côté client est lancé et il se
connecte au serveur désigné par la variable d'environnement SAE_HOTE.
"""

import argparse
import socket
import threading
import time
import sys
from PyQt5.QtWidgets import QApplication
from parametres import (HOTE, PORT, VITESSE_AMBULANCE, FREQUENCE_POSITION, generer_trajet, generer_trajet_retour,
                        message_serveur_injoignable)
from server.server import Serveur
from client.ambulance import Ambulance
from client.infrastructure import Infrastructure
from gui.carte import Carte


def lancer_serveur(serveur):
    """Démarre le serveur TCP (appel bloquant, à exécuter dans un thread).

    Args:
        serveur: instance de `Serveur` à démarrer.
    """
    serveur.demarrer()


def lancer_infrastructure(carte, infrastructure_prete):
    """Connecte le client infrastructure et relaie les ordres de feux à la carte.

    Args:
        carte: fenêtre `Carte` dont les feux sont mis à jour.
        infrastructure_prete: événement positionné une fois la connexion établie.
    """
    infrastructure = Infrastructure()
    infrastructure.callback_feux = lambda message: carte.mettre_a_jour_feu(message["id"], message["etat"])
    infrastructure.connecter()
    infrastructure_prete.set()
    infrastructure.ecouter()


def lancer_ambulance(carte, infrastructure_prete):
    """Déroule une mission complète de l'ambulance (aller, embarquement, retour).

    Args:
        carte: fenêtre `Carte` qui affiche l'ambulance et les ondes.
        infrastructure_prete: événement signalant que l'infrastructure est connectée.
    """
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
    """Exécute une mission et libère le verrou de mission, même en cas d'erreur.

    Args:
        carte: fenêtre `Carte`.
        infrastructure_prete: événement signalant que l'infrastructure est connectée.
        verrou_mission: verrou pris par `demarrer_mission`, relâché à la fin.
    """
    try:
        lancer_ambulance(carte, infrastructure_prete)
    finally:
        verrou_mission.release()


def demarrer_mission(carte, infrastructure_prete, verrou_mission, remettre_a_zero):
    """Démarre une mission dans un nouveau thread si aucune n'est en cours.

    Args:
        carte: fenêtre `Carte`.
        infrastructure_prete: événement signalant que l'infrastructure est connectée.
        verrou_mission: verrou empêchant deux missions simultanées.
        remettre_a_zero: si vrai, la carte est réinitialisée avant le départ (rejeu).

    Returns:
        True si la mission a démarré, False si une mission était déjà en cours.
    """
    if not verrou_mission.acquire(blocking=False):
        return False
    if remettre_a_zero:
        carte.reinitialiser()
    thread_ambulance = threading.Thread(target=lancer_mission, args=(carte, infrastructure_prete, verrou_mission), daemon=True)
    thread_ambulance.start()
    return True


def serveur_joignable():
    """Teste si le serveur répond à l'adresse SAE_HOTE:PORT.

    Returns:
        True si la connexion réussit, sinon False après avoir affiché un message d'erreur en français.
    """
    try:
        socket.create_connection((HOTE, PORT), timeout=3).close()
    except OSError as erreur:
        print(message_serveur_injoignable(erreur))
        return False
    return True


def lire_options():
    """Analyse la ligne de commande.

    Returns:
        Un tuple (options, arguments restants) ; les arguments inconnus sont transmis à Qt.
    """
    analyseur = argparse.ArgumentParser(description="Simulation d'une ambulance et de feux tricolores")
    analyseur.add_argument("--sans-serveur", action="store_true",
                           help="ne lance pas le serveur : se connecte à celui de SAE_HOTE")
    return analyseur.parse_known_args()


if __name__ == "__main__":
    options, arguments_qt = lire_options()
    if options.sans_serveur and not serveur_joignable():
        sys.exit(1)
    app = QApplication([sys.argv[0]] + arguments_qt)
    carte = Carte()
    carte.show()

    if not options.sans_serveur:
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