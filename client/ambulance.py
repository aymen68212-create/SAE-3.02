"""Client ambulance : suit un trajet, envoie sa position et ses ondes au serveur.

Les messages sont du JSON, un message par ligne (terminé par \n), envoyés sur une connexion TCP.
"""

import socket
import json
import time
import threading
from parametres import (HOTE, PORT, INTERVALLE_ONDE, FREQUENCE_POSITION, cap_depuis_deplacement,
                        message_serveur_injoignable)


class Ambulance:
    """Client TCP simulant l'ambulance.

    Attributes:
        position: dernière position (x, y) envoyée, ou None.
        cap: cap courant ("nord", "sud", "est" ou "ouest").
        callback_position: fonction appelée avec (x, y) à chaque pas, pour l'affichage.
        callback_onde: fonction appelée à chaque onde émise, pour l'affichage.
    """
    def __init__(self):
        """Crée la socket et initialise la position et le cap."""
        self.position = None
        self.cap = "nord"
        self.connexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.callback_position = None
        self.callback_onde = None
        self.verrou_envoi = threading.Lock()

    def get_position(self):
        """Retourne la dernière position (x, y) envoyée, ou None."""
        return self.position

    def set_position(self, position):
        """Mémorise la position courante.

        Args:
            position: tuple (x, y).
        """
        self.position = position

    def get_cap(self):
        """Retourne le cap courant."""
        return self.cap

    def set_cap(self, cap):
        """Mémorise le cap courant.

        Args:
            cap: "nord", "sud", "est" ou "ouest".
        """
        self.cap = cap

    def connecter(self):
        """Se connecte au serveur (adresse SAE_HOTE, port PORT).

        Raises:
            OSError: si le serveur est injoignable, après avoir affiché un message en français.
        """
        try:
            self.connexion.connect((HOTE, PORT))
        except OSError as erreur:
            print(message_serveur_injoignable(erreur))
            raise

    def envoyer(self, message):
        """Envoie un message JSON, une ligne par message.

        Le verrou évite que deux threads mélangent leurs octets sur la même socket.

        Args:
            message: dictionnaire sérialisable en JSON, avec une clé "type".
        """
        # Protocole : un message JSON par ligne, terminé par un retour à la ligne.
        with self.verrou_envoi:
            self.connexion.sendall((json.dumps(message) + "\n").encode())

    def envoyer_position(self, x, y):
        """Met à jour le cap puis envoie la position au serveur.

        Args:
            x: abscisse en pixels.
            y: ordonnée en pixels.
        """
        precedente = self.get_position()
        if precedente is not None and precedente != (x, y):
            self.set_cap(cap_depuis_deplacement(x - precedente[0], y - precedente[1]))
        self.set_position((x, y))
        self.envoyer({"type": "position_ambulance", "x": x, "y": y, "cap": self.get_cap()})

    def emettre_onde(self):
        """Envoie au serveur une onde sonore émise à la position courante."""
        x, y = self.get_position()
        self.envoyer({"type": "onde", "x": x, "y": y, "cap": self.get_cap()})

    def signaler_arret(self):
        """Signale au serveur que l'ambulance est arrêtée à sa position courante."""
        x, y = self.get_position()
        self.envoyer({"type": "arret", "x": x, "y": y})

    def signaler_embarquement(self):
        """Signale au serveur que le patient est embarqué."""
        self.envoyer({"type": "patient_embarque"})

    def deplacer(self, trajet):
        """Parcourt un trajet en envoyant la position à FREQUENCE_POSITION Hz et une onde toutes les INTERVALLE_ONDE secondes.

        Args:
            trajet: liste de points (x, y) à suivre.
        """
        derniere_onde = 0
        for x, y in trajet:
            self.envoyer_position(x, y)
            if self.callback_position:
                self.callback_position(x, y)
            maintenant = time.time()
            # Une onde est émise toutes les INTERVALLE_ONDE secondes, indépendamment du pas de position.
            if maintenant - derniere_onde >= INTERVALLE_ONDE:
                self.emettre_onde()
                if self.callback_onde:
                    self.callback_onde()
                derniere_onde = maintenant
            time.sleep(1 / FREQUENCE_POSITION)

    def terminer(self):
        """Signale la fin de mission (`arrivee`) puis ferme la connexion."""
        self.envoyer({"type": "arrivee"})
        self.connexion.close()


if __name__ == "__main__":
    from parametres import VITESSE_AMBULANCE, generer_trajet

    ambulance = Ambulance()
    ambulance.connecter()
    ambulance.deplacer(generer_trajet(VITESSE_AMBULANCE / FREQUENCE_POSITION))
    ambulance.terminer()