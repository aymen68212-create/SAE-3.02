import socket
import json
import threading
import time
import math
from server.database import Database
from parametres import HOTE, PORT, FEUX, FEU_AMBULANCE, PAIRE_AMBULANCE,VITESSE_ONDE, PORTEE_ONDE, etats_initiaux


class Serveur:
    def __init__(self, port):
        self.port = port
        self.socket_serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_serveur.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = []
        self.infrastructures = []
        self.db = Database()
        self.pret = threading.Event()
        self.verrou = threading.Lock()
        self.position_ambulance = None
        self.cap_ambulance = None
        self.ondes = []
        self.etat_feux = etats_initiaux()
        self.phase = "attente"
        self.compteur_positions = 0

    def get_port(self):
        return self.port

    def set_port(self, port):
        self.port = port

    def demarrer(self):
        self.db.connecter()
        self.socket_serveur.bind((HOTE, self.get_port()))
        self.socket_serveur.listen()
        print("Serveur en attente de connexions...")
        thread_supervision = threading.Thread(target=self.superviser, daemon=True)
        thread_supervision.start()
        self.pret.set()
        while True:
            connexion, adresse = self.socket_serveur.accept()
            print("Client connecté :", adresse)
            with self.verrou:
                self.clients.append(connexion)
            thread_client = threading.Thread(target=self.gerer_client, args=(connexion, adresse), daemon=True)
            thread_client.start()

    def lire_messages(self, connexion):
        tampon = ""
        while True:
            try:
                donnees = connexion.recv(4096)
            except OSError:
                return
            if not donnees:
                return
            tampon += donnees.decode()
            while "\n" in tampon:
                ligne, tampon = tampon.split("\n", 1)
                if ligne.strip():
                    yield json.loads(ligne)

    def gerer_client(self, connexion, adresse):
        for message in self.lire_messages(connexion):
            self.traiter_message(connexion, message)
        connexion.close()
        with self.verrou:
            if connexion in self.clients:
                self.clients.remove(connexion)
            if connexion in self.infrastructures:
                self.infrastructures.remove(connexion)
        print("Client déconnecté :", adresse)

    def traiter_message(self, connexion, message):
        type_message = message.get("type")
        if type_message == "identification":
            if message.get("role") == "infrastructure":
                with self.verrou:
                    self.infrastructures.append(connexion)
        elif type_message == "position_ambulance":
            x = message.get("x")
            y = message.get("y")
            with self.verrou:
                self.position_ambulance = (x, y)
                self.cap_ambulance = message.get("cap")
                self.compteur_positions += 1
                enregistrer = self.compteur_positions % 10 == 1
            if enregistrer:
                self.db.inserer_evenement("position_ambulance", x, y)
        elif type_message == "onde":
            with self.verrou:
                self.ondes.append(time.time())
            self.db.inserer_evenement("onde_ambulance", message.get("x"), message.get("y"))
        elif type_message == "arrivee":
            self.reinitialiser()

    def superviser(self):
        while True:
            time.sleep(0.03)
            self.mettre_a_jour_feux()

    def mettre_a_jour_feux(self):
        maintenant = time.time()
        changements = []
        with self.verrou:
            self.ondes = [t for t in self.ondes if (maintenant - t) * VITESSE_ONDE <= PORTEE_ONDE]
            position = self.position_ambulance
            cap = self.cap_ambulance
            if position is None:
                return
            rayon = (maintenant - self.ondes[0]) * VITESSE_ONDE if self.ondes else 0
            distance = self.distance(position, FEUX[FEU_AMBULANCE])
            if self.phase == "attente" and distance <= rayon:
                self.phase = "passage"
            elif self.phase == "passage" and distance > PORTEE_ONDE:
                self.phase = "apres"
            for id_feu in FEUX:
                actuel = self.etat_feux[id_feu]
                if id_feu in PAIRE_AMBULANCE:
                    nouveau = "vert" if self.phase == "passage" else "rouge"
                else:
                    nouveau = "rouge" if self.phase == "passage" else "vert"
                if nouveau != actuel:
                    self.etat_feux[id_feu] = nouveau
                    changements.append((id_feu, nouveau, position))
        for id_feu, etat, position in changements:
            self.signaler_feu(id_feu, etat, position)

    def distance(self, position, feu):
        return math.hypot(position[0] - feu["x"], position[1] - feu["y"])

    def signaler_feu(self, id_feu, etat, position):
        print(f"Feu {id_feu} -> {etat}")
        self.db.inserer_evenement(f"feu_{etat}:{id_feu}", position[0], position[1])
        self.envoyer_aux_infrastructures({"type": "feu", "id": id_feu, "etat": etat})

    def envoyer_aux_infrastructures(self, message):
        ligne = (json.dumps(message) + "\n").encode()
        with self.verrou:
            cibles = list(self.infrastructures)
        for cible in cibles:
            try:
                cible.sendall(ligne)
            except OSError:
                pass

    def reinitialiser(self):
        with self.verrou:
            self.position_ambulance = None
            self.cap_ambulance = None
            self.ondes = []
            self.compteur_positions = 0
            self.phase = "attente"
            initiaux = etats_initiaux()
            a_remettre = [id_feu for id_feu, etat in self.etat_feux.items() if etat != initiaux[id_feu]]
            for id_feu in a_remettre:
                self.etat_feux[id_feu] = initiaux[id_feu]
        for id_feu in a_remettre:
            print(f"Feu {id_feu} -> {initiaux[id_feu]}")
            self.envoyer_aux_infrastructures({"type": "feu", "id": id_feu, "etat": initiaux[id_feu]})


if __name__ == "__main__":
    serveur = Serveur(PORT)
    serveur.demarrer()