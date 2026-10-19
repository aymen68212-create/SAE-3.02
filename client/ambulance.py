import socket
import json
import time
from parametres import HOTE, PORT, INTERVALLE_ONDE, FREQUENCE_POSITION, cap_depuis_deplacement


class Ambulance:
    def __init__(self, trajet):
        self.trajet = trajet
        self.position = None
        self.cap = "nord"
        self.connexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.callback_position = None
        self.callback_onde = None

    def get_position(self):
        return self.position

    def set_position(self, position):
        self.position = position

    def get_cap(self):
        return self.cap

    def set_cap(self, cap):
        self.cap = cap

    def connecter(self):
        self.connexion.connect((HOTE, PORT))

    def envoyer(self, message):
        self.connexion.sendall((json.dumps(message) + "\n").encode())

    def envoyer_position(self, x, y):
        precedente = self.get_position()
        if precedente is not None and precedente != (x, y):
            self.set_cap(cap_depuis_deplacement(x - precedente[0], y - precedente[1]))
        self.set_position((x, y))
        self.envoyer({"type": "position_ambulance", "x": x, "y": y, "cap": self.get_cap()})

    def emettre_onde(self):
        x, y = self.get_position()
        self.envoyer({"type": "onde", "x": x, "y": y, "cap": self.get_cap()})

    def deplacer(self):
        derniere_onde = 0
        for x, y in self.trajet:
            self.envoyer_position(x, y)
            if self.callback_position:
                self.callback_position(x, y)
            maintenant = time.time()
            if maintenant - derniere_onde >= INTERVALLE_ONDE:
                self.emettre_onde()
                if self.callback_onde:
                    self.callback_onde()
                derniere_onde = maintenant
            time.sleep(1 / FREQUENCE_POSITION)

    def terminer(self):
        self.envoyer({"type": "arrivee"})
        self.connexion.close()


if __name__ == "__main__":
    from parametres import VITESSE_AMBULANCE, generer_trajet

    ambulance = Ambulance(generer_trajet(VITESSE_AMBULANCE / FREQUENCE_POSITION))
    ambulance.connecter()
    ambulance.deplacer()
    ambulance.terminer()