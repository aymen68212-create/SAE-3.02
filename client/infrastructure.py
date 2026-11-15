"""Client infrastructure : reçoit du serveur les ordres de feux tricolores."""

import socket
import json
from parametres import HOTE, PORT, message_serveur_injoignable


class Infrastructure:
    """Client TCP représentant les feux : il applique les ordres `feu` reçus.

    Attributes:
        etat_feu: dernier état connu de chaque feu.
        callback_feux: fonction appelée avec chaque message `feu` reçu.
    """
    def __init__(self):
        """Crée la socket et l'état vide des feux."""
        self.etat_feu = {}
        self.connexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.callback_feux = None

    def get_etat_feu(self):
        """Retourne le dictionnaire {identifiant du feu: état}."""
        return self.etat_feu

    def set_etat_feu(self, id_feu, etat):
        """Mémorise l'état d'un feu.

        Args:
            id_feu: identifiant du feu.
            etat: "rouge" ou "vert".
        """
        self.etat_feu[id_feu] = etat

    def connecter(self):
        """Se connecte au serveur et s'identifie avec le rôle `infrastructure`.

        Raises:
            OSError: si le serveur est injoignable, après avoir affiché un message en français.
        """
        try:
            self.connexion.connect((HOTE, PORT))
        except OSError as erreur:
            print(message_serveur_injoignable(erreur))
            raise
        identification = {"type": "identification", "role": "infrastructure"}
        self.connexion.sendall((json.dumps(identification) + "\n").encode())

    def ecouter(self):
        """Lit les messages du serveur (appel bloquant) jusqu'à la fermeture de la connexion."""
        # Les messages arrivent en flux : on découpe sur les retours à la ligne (un JSON par ligne).
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