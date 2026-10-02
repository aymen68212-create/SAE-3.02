import mariadb
import sys

DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "root"
DB_NAME = "sae302"

class Database:
    def __init__(self):
        self.connexion = None

    def connecter(self):
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
            print("[DB] Connexion réussie et base initialisée.")
        except mariadb.Error as e:
            print(f"[DB] Erreur de connexion : {e}")
            sys.exit(1)

    def creer_tables(self, curseur):
        curseur.execute("""
            CREATE TABLE IF NOT EXISTS evenements (
                id INT AUTO_INCREMENT PRIMARY KEY,
                type_evenement VARCHAR(50) NOT NULL,
                position_x INT,
                position_y INT,
                horodatage TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("[DB] Table 'evenements' prête.")

    def inserer_evenement(self, type_evenement, x, y):
        try:
            curseur = self.connexion.cursor()
            curseur.execute(
                "INSERT INTO evenements (type_evenement, position_x, position_y) VALUES (?, ?, ?)",
                (type_evenement, x, y)
            )
            self.connexion.commit()
            print(f"[DB] Événement enregistré : {type_evenement} à ({x}, {y})")
        except mariadb.Error as e:
            print(f"[DB] Erreur insertion : {e}")

    def fermer(self):
        if self.connexion:
            self.connexion.close()
            print("[DB] Connexion fermée.")