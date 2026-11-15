"""Accès optionnel à MariaDB : enregistrement des événements et des missions.

Sans le module `mariadb` ou sans serveur joignable, les méthodes ne font rien et la simulation continue.
Les paramètres de connexion se règlent par les variables SAE_DB_HOST, SAE_DB_USER, SAE_DB_PASSWORD et SAE_DB_NAME.
"""

import os
import threading

try:
    import mariadb
except ImportError:
    mariadb = None

DB_HOST = os.environ.get("SAE_DB_HOST", "localhost")
DB_PORT = 3306
DB_USER = os.environ.get("SAE_DB_USER", "root")
DB_PASSWORD = os.environ.get("SAE_DB_PASSWORD", "root")
DB_NAME = os.environ.get("SAE_DB_NAME", "sae302")


class Database:
    """Connexion à la base `sae302`.

    Attributes:
        connexion: connexion MariaDB, ou None si la base est indisponible.
        mission_en_cours: identifiant de la mission ouverte, ou None.
    """
    def __init__(self):
        """Prépare l'objet sans se connecter à la base."""
        self.connexion = None
        self.verrou = threading.Lock()
        self.mission_en_cours = None

    def connecter(self):
        """Se connecte, crée la base et les tables si besoin ; affiche un message [DB] en cas d'échec."""
        if mariadb is None:
            print("[DB] Module mariadb absent, les evenements ne seront pas enregistres.")
            return
        try:
            self.connexion = mariadb.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD
            )
            curseur = self.connexion.cursor()
            curseur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            curseur.execute(f"USE {DB_NAME}")
            self.creer_tables(curseur)
            self.connexion.commit()
            print("[DB] Connexion réussie.")
        except mariadb.Error as e:
            print(f"[DB] Erreur, les evenements ne seront pas enregistres : {e}")
            self.connexion = None

    def creer_tables(self, curseur):
        """Crée les tables `evenements` et `missions` si elles n'existent pas.

        Args:
            curseur: curseur MariaDB ouvert.
        """
        curseur.execute("""
            CREATE TABLE IF NOT EXISTS evenements (
                id INT AUTO_INCREMENT PRIMARY KEY,
                type_evenement VARCHAR(50) NOT NULL,
                position_x INT,
                position_y INT,
                horodatage TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        curseur.execute("""
            CREATE TABLE IF NOT EXISTS missions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                debut TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fin TIMESTAMP NULL
            )
        """)

    def inserer_evenement(self, type_evenement, x, y):
        """Enregistre un événement.

        Args:
            type_evenement: nom de l'événement (position_ambulance, onde_ambulance, feu_vert:id, ...).
            x: abscisse associée.
            y: ordonnée associée.
        """
        if self.connexion is None:
            return
        with self.verrou:
            try:
                curseur = self.connexion.cursor()
                curseur.execute(
                    "INSERT INTO evenements (type_evenement, position_x, position_y) VALUES (?, ?, ?)",
                    (type_evenement, x, y)
                )
                self.connexion.commit()
            except mariadb.Error as e:
                print(f"[DB] Erreur insertion : {e}")

    def debut_mission(self):
        """Ouvre une ligne dans `missions` et mémorise son identifiant."""
        if self.connexion is None:
            return
        with self.verrou:
            try:
                curseur = self.connexion.cursor()
                curseur.execute("INSERT INTO missions () VALUES ()")
                self.connexion.commit()
                self.mission_en_cours = curseur.lastrowid
            except mariadb.Error as e:
                print(f"[DB] Erreur début de mission : {e}")

    def fin_mission(self):
        """Renseigne la date de fin de la mission en cours."""
        if self.connexion is None:
            return
        with self.verrou:
            if self.mission_en_cours is None:
                return
            try:
                curseur = self.connexion.cursor()
                curseur.execute("UPDATE missions SET fin = NOW() WHERE id = ?", (self.mission_en_cours,))
                self.connexion.commit()
                self.mission_en_cours = None
            except mariadb.Error as e:
                print(f"[DB] Erreur fin de mission : {e}")

    def derniers_evenements(self, limite):
        """Lit les derniers événements enregistrés.

        Args:
            limite: nombre maximal de lignes.

        Returns:
            La liste des lignes (id, type, x, y, horodatage), les plus récentes d'abord ; vide si la base est absente.
        """
        if self.connexion is None:
            return []
        with self.verrou:
            try:
                curseur = self.connexion.cursor()
                curseur.execute(
                    "SELECT id, type_evenement, position_x, position_y, horodatage FROM evenements ORDER BY id DESC LIMIT ?",
                    (limite,)
                )
                return curseur.fetchall()
            except mariadb.Error as e:
                print(f"[DB] Erreur lecture : {e}")
                return []

    def fermer(self):
        """Ferme la connexion à la base si elle est ouverte."""
        if self.connexion:
            self.connexion.close()