import socket
import json
import threading

HOTE = "localhost"
PORT = 5050  # 5000 est pris par AirPlay Receiver sur macOS, on évite


class Serveur:
    def __init__(self, port):
        self.port = port
        self.socket_serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []

    def get_port(self):
        return self.port

    def set_port(self, port):
        self.port = port

    def demarrer(self):
        self.socket_serveur.bind((HOTE, self.get_port()))
        self.socket_serveur.listen()
        print("Serveur en attente de connexions...")

        while True:
            connexion, adresse = self.socket_serveur.accept()
            print("Client connecté :", adresse)
            self.clients.append(connexion)
            thread_client = threading.Thread(target=self.gerer_client, args=(connexion, adresse))
            thread_client.start()

    def gerer_client(self, connexion, adresse):
        while True:
            donnees = connexion.recv(1024)
            if not donnees:
                break
            message = json.loads(donnees.decode())
            print(f"Message de {adresse} :", message)
        connexion.close()
        self.clients.remove(connexion)
        print("Client déconnecté :", adresse)


if __name__ == "__main__":
    serveur = Serveur(PORT)
    serveur.demarrer()
    serveur
