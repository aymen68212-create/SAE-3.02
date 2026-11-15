"""Serveur TCP : reçoit l'ambulance, décide de l'état des feux et les envoie à l'infrastructure.

Protocole : des messages JSON, un par ligne, avec une clé "type" (identification, position_ambulance, onde,
arret, patient_embarque, arrivee, feu). Règle des feux : voir `Serveur.mettre_a_jour_feux`.
"""

import socket
import json
import threading
import time
import math
from server.database import Database
from parametres import ECOUTE, PORT, FEUX, PAIRE_AMBULANCE, PAIRE_RETOUR, VITESSE_ONDE, PORTEE_ONDE, DELAI_CHANGEMENT_FEU, etats_initiaux


class Serveur:
    """Serveur de simulation.

    Un thread accepte les connexions, un thread par client lit ses messages et un thread de supervision
    recalcule les feux. Tout l'état partagé est protégé par `verrou`.

    Attributes:
        etat_feux: état courant de chaque feu ("rouge" ou "vert").
        axe_actif: paire de feux verte à cause d'une onde, ou None au repos.
        sortie_portee: instant où l'ambulance est sortie de portée de l'axe actif, ou None.
        trajet: "aller" ou "retour" (détermine l'état de repos).
    """
    def __init__(self, port):
        """Prépare la socket d'écoute et l'état de la simulation.

        Args:
            port: port TCP d'écoute (0 pour laisser le système choisir, utile aux tests).
        """
        self.port = port
        self.socket_serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_serveur.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = []
        self.infrastructures = []
        self.db = Database()
        self.pret = threading.Event()
        # Protège l'état partagé entre le thread de supervision et les threads clients.
        self.verrou = threading.Lock()
        self.position_ambulance = None
        self.cap_ambulance = None
        self.ondes = []
        self.etat_feux = etats_initiaux()
        self.axe_actif = None
        self.sortie_portee = None
        self.resynchroniser = True
        self.trajet = "aller"
        self.compteur_positions = 0

    def get_port(self):
        """Retourne le port d'écoute."""
        return self.port

    def set_port(self, port):
        """Change le port d'écoute (avant `demarrer`).

        Args:
            port: numéro de port TCP.
        """
        self.port = port

    def demarrer(self):
        """Connecte la base, écoute sur ECOUTE:port et accepte les clients (appel bloquant)."""
        self.db.connecter()
        self.socket_serveur.bind((ECOUTE, self.get_port()))
        self.socket_serveur.listen()
        print(f"Serveur en attente de connexions sur {ECOUTE}:{self.get_port()}...")
        thread_supervision = threading.Thread(target=self.superviser, daemon=True)
        thread_supervision.start()
        self.pret.set()
        while True:
            connexion, adresse = self.socket_serveur.accept()
            print("Client connecté :", adresse)
            with self.verrou:
                self.clients.append(connexion)
            # Un thread par client : un client lent ne bloque pas les autres.
            thread_client = threading.Thread(target=self.gerer_client, args=(connexion, adresse), daemon=True)
            thread_client.start()

    def lire_messages(self, connexion):
        """Lit une connexion et produit les messages JSON reçus.

        Args:
            connexion: socket du client.

        Yields:
            Chaque message décodé (dictionnaire), jusqu'à la fermeture de la connexion.
        """
        # Protocole : un message JSON par ligne ; on accumule les octets reçus jusqu'au retour à la ligne.
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
        """Traite tous les messages d'un client puis nettoie à sa déconnexion.

        Args:
            connexion: socket du client.
            adresse: adresse du client, pour les messages de journal.
        """
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
        """Applique l'effet d'un message reçu.

        Args:
            connexion: socket de l'expéditeur.
            message: dictionnaire décodé, dont la clé "type" désigne l'action.
        """
        type_message = message.get("type")
        if type_message == "identification":
            if message.get("role") == "infrastructure":
                with self.verrou:
                    self.infrastructures.append(connexion)
        elif type_message == "position_ambulance":
            x = message.get("x")
            y = message.get("y")
            with self.verrou:
                nouvelle_mission = self.position_ambulance is None
                self.position_ambulance = (x, y)
                self.cap_ambulance = message.get("cap")
                self.compteur_positions += 1
                enregistrer = self.compteur_positions % 10 == 1
            if nouvelle_mission:
                self.db.debut_mission()
            if enregistrer:
                self.db.inserer_evenement("position_ambulance", x, y)
        elif type_message == "onde":
            with self.verrou:
                self.ondes.append(time.time())
            self.db.inserer_evenement("onde_ambulance", message.get("x"), message.get("y"))
        elif type_message == "arret":
            self.db.inserer_evenement("arret_ambulance", message.get("x"), message.get("y"))
            print("Ambulance arrêtée")
        elif type_message == "patient_embarque":
            with self.verrou:
                position = self.position_ambulance
            if position is None:
                position = (0, 0)
            self.db.inserer_evenement("patient_embarque", position[0], position[1])
            print("Patient embarqué")
            self.demarrer_retour()
        elif type_message == "arrivee":
            self.db.fin_mission()
            self.reinitialiser()

    def superviser(self):
        """Recalcule les feux environ toutes les 30 ms (boucle infinie, thread dédié)."""
        while True:
            time.sleep(0.03)
            self.mettre_a_jour_feux()

    def mettre_a_jour_feux(self):
        """Applique la règle des feux et envoie les changements aux infrastructures.

        Un feu est « touché » quand la distance ambulance-feu est inférieure ou égale au rayon de l'onde la plus
        ancienne encore vivante. L'axe du feu touché passe au vert et l'autre au rouge. Cet axe reste vert tant que
        l'ambulance est à moins de PORTEE_ONDE d'un de ses feux, puis encore DELAI_CHANGEMENT_FEU secondes, avant
        le retour à l'état de repos.
        """
        changements = []
        renvois = []
        with self.verrou:
            maintenant = time.time()
            self.ondes = [t for t in self.ondes if (maintenant - t) * VITESSE_ONDE <= PORTEE_ONDE]
            position = self.position_ambulance
            if position is None:
                return
            # Rayon de l'onde la plus ancienne encore vivante, donc la plus grande.
            rayon = (maintenant - self.ondes[0]) * VITESSE_ONDE if self.ondes else 0
            # Axe actif : il reste vert tant que l'ambulance est à portée d'un de ses feux,
            # puis encore DELAI_CHANGEMENT_FEU secondes après sa sortie de portée.
            if self.axe_actif is not None:
                if self.a_portee(position, self.axe_actif):
                    self.sortie_portee = None
                elif self.sortie_portee is None:
                    self.sortie_portee = maintenant
                elif maintenant - self.sortie_portee >= DELAI_CHANGEMENT_FEU:
                    self.axe_actif = None
                    self.sortie_portee = None
            # Un feu est touché quand sa distance à l'ambulance est <= au rayon de l'onde :
            # son axe devient l'axe actif (vert), l'autre axe passe au rouge.
            if self.axe_actif is None and self.ondes:
                for id_feu in FEUX:
                    if self.distance(position, FEUX[id_feu]) <= rayon:
                        self.axe_actif = self.axe_de(id_feu)
                        break
            # Au premier tick d'une mission, les feux inchangés sont aussi renvoyés
            # pour que la carte et le serveur repartent du même état.
            resynchroniser = self.resynchroniser
            self.resynchroniser = False
            for id_feu in FEUX:
                actuel = self.etat_feux[id_feu]
                nouveau = self.etat_voulu(id_feu)
                if nouveau != actuel:
                    self.etat_feux[id_feu] = nouveau
                    changements.append((id_feu, nouveau, position))
                elif resynchroniser:
                    renvois.append((id_feu, nouveau))
        # Les envois se font hors du verrou pour ne pas bloquer les autres threads.
        for id_feu, etat, position in changements:
            self.signaler_feu(id_feu, etat, position)
        for id_feu, etat in renvois:
            self.envoyer_aux_infrastructures({"type": "feu", "id": id_feu, "etat": etat})

    def a_portee(self, position, axe):
        """Indique si l'ambulance est à moins de PORTEE_ONDE d'au moins un feu de l'axe.

        Args:
            position: position (x, y) de l'ambulance.
            axe: paire d'identifiants de feux.

        Returns:
            True si un feu de l'axe est à portée.
        """
        return any(self.distance(position, FEUX[id_feu]) < PORTEE_ONDE for id_feu in axe)

    def axe_de(self, id_feu):
        """Retourne l'axe (paire de feux opposés) auquel appartient un feu.

        Args:
            id_feu: identifiant du feu.
        """
        return PAIRE_AMBULANCE if id_feu in PAIRE_AMBULANCE else PAIRE_RETOUR

    def paire_repos(self):
        """Retourne la paire de feux rouge au repos : `PAIRE_AMBULANCE` à l'aller, `PAIRE_RETOUR` au retour."""
        return PAIRE_RETOUR if self.trajet == "retour" else PAIRE_AMBULANCE

    def etat_voulu(self, id_feu):
        """Calcule l'état que doit avoir un feu.

        Args:
            id_feu: identifiant du feu.

        Returns:
            "vert" ou "rouge", selon l'axe actif ou, à défaut, l'état de repos.
        """
        if self.axe_actif is None:
            return "rouge" if id_feu in self.paire_repos() else "vert"
        return "vert" if id_feu in self.axe_actif else "rouge"

    def distance(self, position, feu):
        """Calcule la distance entre l'ambulance et un feu.

        Args:
            position: position (x, y) de l'ambulance.
            feu: dictionnaire du feu, avec les clés "x" et "y".

        Returns:
            La distance en pixels.
        """
        return math.hypot(position[0] - feu["x"], position[1] - feu["y"])

    def signaler_feu(self, id_feu, etat, position):
        """Journalise un changement de feu, l'enregistre en base et l'envoie aux infrastructures.

        Args:
            id_feu: identifiant du feu.
            etat: nouvel état.
            position: position de l'ambulance au moment du changement.
        """
        print(f"Feu {id_feu} -> {etat}")
        self.db.inserer_evenement(f"feu_{etat}:{id_feu}", position[0], position[1])
        self.envoyer_aux_infrastructures({"type": "feu", "id": id_feu, "etat": etat})

    def envoyer_aux_infrastructures(self, message):
        """Envoie un message JSON à tous les clients infrastructure.

        Args:
            message: dictionnaire à envoyer ; les erreurs d'envoi sont ignorées.
        """
        ligne = (json.dumps(message) + "\n").encode()
        with self.verrou:
            cibles = list(self.infrastructures)
        for cible in cibles:
            try:
                cible.sendall(ligne)
            except OSError:
                pass

    def demarrer_retour(self):
        """Passe au trajet retour : l'état de repos s'inverse et l'axe actif est oublié."""
        with self.verrou:
            self.trajet = "retour"
            self.axe_actif = None
            self.sortie_portee = None
            changements = []
            for id_feu in FEUX:
                nouveau = self.etat_voulu(id_feu)
                if nouveau != self.etat_feux[id_feu]:
                    self.etat_feux[id_feu] = nouveau
                    changements.append((id_feu, nouveau))
            position = self.position_ambulance or (0, 0)
        for id_feu, etat in changements:
            self.signaler_feu(id_feu, etat, position)

    def reinitialiser(self):
        """Prépare la mission suivante (position, ondes, trajet, axe et délai).

        Les feux ne sont pas modifiés : ils gardent l'état de fin de mission jusqu'au premier tick de la mission
        suivante, qui renvoie alors l'état de repos de l'aller aux infrastructures.
        """
        with self.verrou:
            self.trajet = "aller"
            self.position_ambulance = None
            self.cap_ambulance = None
            self.ondes = []
            self.compteur_positions = 0
            self.axe_actif = None
            self.sortie_portee = None
            self.resynchroniser = True


if __name__ == "__main__":
    serveur = Serveur(PORT)
    serveur.demarrer()