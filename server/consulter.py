from server.database import Database


def afficher_evenements(limite=20):
    db = Database()
    db.connecter()
    if db.connexion is None:
        print("Impossible de consulter la base : MariaDB n'est pas lancé ou le module mariadb n'est pas installé.")
        return
    evenements = db.derniers_evenements(limite)
    if not evenements:
        print("Aucun événement enregistré.")
    else:
        print(f"{'id':>5}  {'type':<25} {'x':>5} {'y':>5}  horodatage")
        for id_evenement, type_evenement, x, y, horodatage in evenements:
            print(f"{id_evenement:>5}  {type_evenement:<25} {str(x):>5} {str(y):>5}  {horodatage}")
    db.fermer()


if __name__ == "__main__":
    afficher_evenements()
