import socket
import json
import time
import threading

HOTE = "localhost"
PORT = 5050

class Ambulance:
    def __init__(self, trajet):
        self.trajet = trajet
        self.position = None
        self.connexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def get_position(self):
        return self.position

    def set_position(self, position):
        self.position = position

    def connecter(self):
        self.connexion.connect((HOTE, PORT))

    def envoyer_position(self, x, y):
        self.set_position((x, y))
        message = json.dumps({"type": "position_ambulance", "x": x, "y": y})
        self.connexion.send(message.encode())
        print("Position envoyée :", self.get_position())

    def deplacer(self):
        for x, y in self.trajet:
            self.envoyer_position(x, y)
            time.sleep(1)
        self.connexion.close()

if __name__ == "__main__":
    trajet = [(100, 500), (200, 400), (300, 300), (400, 200)]
    ambulance = Ambulance(trajet)
    ambulance.connecter()
    thread_deplacement = threading.Thread(target=ambulance.deplacer)
    thread_deplacement.start()
    thread_deplacement.join()