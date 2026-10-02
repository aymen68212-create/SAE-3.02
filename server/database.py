try:
    import mariadb
except ImportError:
    mariadb = None

DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "root"
DB_NAME = "sae302"

class Database:
    def __init__(self):
        self.connexion = None

    def connecter(self):
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
        curseur.execute("""
            CREATE TABLE IF NOT EXISTS evenements (
                id INT AUTO_INCREMENT PRIMARY KEY,
                type_evenement VARCHAR(50) NOT NULL,
                position_x INT,
                position_y INT,
                horodatage TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def inserer_evenement(self, type_evenement, x, y):
        if self.connexion is None:
            return
        try:
            curseur = self.connexion.cursor()
            curseur.execute(
                "INSERT INTO evenements (type_evenement, position_x, position_y) VALUES (?, ?, ?)",
                (type_evenement, x, y)
            )
            self.connexion.commit()
        except mariadb.Error as e:
            print(f"[DB] Erreur insertion : {e}")

    def fermer(self):
        if self.connexion:
            self.connexion.close()