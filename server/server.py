import socket
import json
import threading
from server.database import Database

HOTE = "localhost"
PORT = 5050

class Serveur:
    def __init__(self, port):
        self.port = port
        self.socket_serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_serveur.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = []
        self.db = Database()
        self.pret = threading.Event()

    def get_port(self):
        return self.port

    def set_port(self, port):
        self.port = port

    def demarrer(self):
        self.db.connecter()
        self.socket_serveur.bind((HOTE, self.get_port()))
        self.socket_serveur.listen()
        print("Serveur en attente de connexions...")
        self.pret.set()
        while True:
            connexion, adresse = self.socket_serveur.accept()
            print("Client connecté :", adresse)
            self.clients.append(connexion)
            thread_client = threading.Thread(target=self.gerer_client, args=(connexion, adresse))
            thread_client.start()

    def gerer_client(self, connexion, adresse):
        while True:
            try:
                donnees = connexion.recv(1024)
            except OSError:
                break
            if not donnees:
                break
            message = json.loads(donnees.decode())
            print(f"Message de {adresse} :", message)
            if message.get("type") == "position_ambulance":
                x = message.get("x")
                y = message.get("y")
                self.db.inserer_evenement("position_ambulance", x, y)
                if self.ambulance_proche_carrefour(x, y):
                    self.db.inserer_evenement("feux_vert", x, y)
                    ordre = json.dumps({"type": "feux_vert", "nord": True, "sud": True, "est": True, "ouest": True})
                    for client in self.clients:
                        try:
                            client.send(ordre.encode())
                        except:
                            pass
        connexion.close()
        self.clients.remove(connexion)
        print("Client déconnecté :", adresse)

    def ambulance_proche_carrefour(self, x, y):
        carrefour_x = 450
        carrefour_y = 240
        distance = ((x - carrefour_x) ** 2 + (y - carrefour_y) ** 2) ** 0.5
        return distance < 100

if __name__ == "__main__":
    serveur = Serveur(PORT)
    serveur.demarrer()