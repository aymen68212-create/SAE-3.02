# SAÉ 3.02 – Simulation d'une ambulance et de feux tricolores

Simulation d'une ambulance qui traverse le carrefour **Av. d'Alsace × Rue des Jardins**, près de l'IUT de Colmar.
L'ambulance émet des ondes sonores ; lorsque l'onde atteint le feu qui la concerne, le serveur commande le passage
des feux : le sens de l'ambulance passe au vert, les autres au rouge. Une fois l'ambulance éloignée, les feux
reviennent à leur état normal.

Projet réalisé en binôme par **Aymen MRIZEL** et **Adam SEBAR** (SAÉ 3.02).

## Structure du projet

```
.
├── main.py              # Point d'entrée : lance l'interface, le serveur et les deux clients
├── parametres.py        # Constantes partagées (port, vitesses, feux, trajet de l'ambulance)
├── requirements.txt     # Dépendances Python (PyQt5, mariadb)
├── server/
│   ├── server.py        # Serveur TCP : reçoit les messages, décide de l'état des feux
│   └── database.py      # Enregistrement des événements dans MariaDB (optionnel)
├── client/
│   ├── ambulance.py     # Client ambulance : envoie sa position et ses ondes
│   └── infrastructure.py# Client infrastructure : reçoit les ordres des feux
└── gui/
    └── carte.py         # Interface PyQt5 : carte du carrefour, ambulance, ondes, feux
```

## Installation

Python 3 est requis. Depuis la racine du projet :

```
pip install -r requirements.txt
```

**MariaDB est optionnel** : l'application fonctionne sans. Si le module `mariadb` est absent ou si le serveur
de base de données est inaccessible, le serveur affiche un message `[DB]` et les événements ne sont simplement
pas enregistrés.

Pour activer l'enregistrement, il faut un serveur MariaDB sur `localhost:3306` accessible avec l'utilisateur
`root` / mot de passe `root` (valeurs définies dans `server/database.py`). La base `sae302` et la table
`evenements` sont créées automatiquement au démarrage.

## Lancement

Depuis la racine du projet :

```
python main.py
```

Une fenêtre « Simulation Ambulance - IUT Colmar » s'ouvre et la simulation démarre automatiquement.

## Fonctionnement

- **Serveur TCP** (`server/server.py`) : écoute sur `localhost`, port **5050**. Les messages sont échangés en
  JSON, un message par ligne. Un thread par client gère les connexions, et un thread de supervision met à jour
  l'état des feux environ toutes les 30 ms.
- **Client ambulance** (`client/ambulance.py`) : suit un trajet prédéfini (`generer_trajet` dans `parametres.py`).
  À chaque pas, il envoie sa position et son cap (`position_ambulance`) ; toutes les 0,7 s il émet une onde
  (`onde`). À la fin du trajet, il envoie `arrivee`, ce qui réinitialise le serveur et remet les feux dans leur
  état initial.
- **Client infrastructure** (`client/infrastructure.py`) : s'identifie auprès du serveur avec le rôle
  `infrastructure`, puis reçoit les ordres `feu` (identifiant du feu et état `rouge` ou `vert`) et les
  transmet à l'interface.
- **Logique des feux** : au départ, la paire de feux de l'ambulance est rouge et les deux autres sont vertes.
  Dès que le rayon de l'onde atteint le feu de l'ambulance, la paire de l'ambulance passe au vert et les
  autres au rouge. Quand l'ambulance s'éloigne au-delà de la portée de l'onde, les feux reviennent à
  la situation de départ.
- **Interface PyQt5** (`gui/carte.py`) : dessine le carrefour, l'ambulance, les ondes (cercles rouges), les
  quatre feux et quelques autres véhicules. Elle est mise à jour par les callbacks de l'ambulance et de
  l'infrastructure.
- **Base de données** (`server/database.py`) : si MariaDB est disponible, les événements sont insérés dans la
  table `evenements` (type, position x/y, horodatage) : positions de l'ambulance (une sur dix), ondes émises
  et changements d'état des feux.
