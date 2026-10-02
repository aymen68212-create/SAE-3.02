import socket
import json
import threading

HOTE = "localhost"
PORT = 5050

class Infrastructure:
    def __init__(self):
        self.etat_feu = None
        self.connexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def get_etat_feu(self):
        return self.etat_feu

    def set_etat_feu(self, etat):
        self.etat_feu = etat

    def connecter(self):
        self.connexion.connect((HOTE, PORT))

    def ecouter(self):
        while True:
            donnees = self.connexion.recv(1024)
            if not donnees:
                break
            message = json.loads(donnees.decode())
            self.set_etat_feu(message)
            print("Ordre reçu du serveur :", self.get_etat_feu())
        self.connexion.close()


if __name__ == "__main__":
    infrastructure = Infrastructure()
    infrastructure.connecter()

    thread_ecoute = threading.Thread(target=infrastructure.ecouter)
    thread_ecoute.start()
    thread_ecoute.join()
