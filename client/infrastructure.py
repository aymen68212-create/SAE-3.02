import socket
import json
from parametres import HOTE, PORT


class Infrastructure:
    def __init__(self):
        self.etat_feu = {}
        self.connexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.callback_feux = None

    def get_etat_feu(self):
        return self.etat_feu

    def set_etat_feu(self, id_feu, etat):
        self.etat_feu[id_feu] = etat

    def connecter(self):
        self.connexion.connect((HOTE, PORT))
        identification = {"type": "identification", "role": "infrastructure"}
        self.connexion.sendall((json.dumps(identification) + "\n").encode())

    def ecouter(self):
        tampon = ""
        try:
            while True:
                donnees = self.connexion.recv(4096)
                if not donnees:
                    break
                tampon += donnees.decode()
                while "\n" in tampon:
                    ligne, tampon = tampon.split("\n", 1)
                    if not ligne.strip():
                        continue
                    message = json.loads(ligne)
                    if message.get("type") == "feu":
                        self.set_etat_feu(message["id"], message["etat"])
                        print("Ordre reçu du serveur :", message)
                        if self.callback_feux:
                            self.callback_feux(message)
        except OSError:
            pass
        self.connexion.close()


if __name__ == "__main__":
    infrastructure = Infrastructure()
    infrastructure.connecter()
    infrastructure.ecouter()