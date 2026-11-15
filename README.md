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
    ├── carte.py         # Interface PyQt5 : carte du carrefour, ambulance, ondes, feux, bouton Rejouer
    ├── circulation.py   # Véhicules de fond : trajets, arrêt aux feux, distance de sécurité
    ├── decor.py         # Bâtiments, routes, marquages, terre-plein central et sens interdit de la diagonale
    ├── lit.py           # Lit du patient, dessiné dans le parking jusqu'à l'embarquement
    └── vehicules.py     # Dessin des voitures
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
Le bouton **Pause** fige tout (ambulance, véhicules, ondes, feux) jusqu'à **Reprendre**. Le bouton **Rejouer** est grisé tant que la mission n'est pas terminée ; il devient actif quand l'ambulance
est arrivée et relance alors une mission complète.

## Fonctionnement

- **Serveur TCP** (`server/server.py`) : écoute sur `localhost`, port **5050**. Les messages sont échangés en
  JSON, un message par ligne. Un thread par client gère les connexions, et un thread de supervision met à jour
  l'état des feux environ toutes les 30 ms.
- **Client ambulance** (`client/ambulance.py`) : suit un trajet prédéfini (`generer_trajet` dans `parametres.py`).
  À chaque pas, il envoie sa position et son cap (`position_ambulance`) ; toutes les 0,7 s il émet une onde
  (`onde`). Une fois arrêtée dans le parking, elle attend 2 secondes pendant que le patient est embarqué
  (le lit disparaît), puis repart. À la fin du trajet, il envoie `arrivee`, ce qui réinitialise le serveur et remet les feux dans leur
  état initial.
- **Client infrastructure** (`client/infrastructure.py`) : s'identifie auprès du serveur avec le rôle
  `infrastructure`, puis reçoit les ordres `feu` (identifiant du feu et état `rouge` ou `vert`) et les
  transmet à l'interface.
- **Logique des feux** : un feu est « touché » quand la distance ambulance-feu est inférieure ou égale au
  rayon de la plus grande onde vivante. Au repos, `PAIRE_AMBULANCE` (sud_droite / nord_gauche) est rouge et
  `PAIRE_RETOUR` (sud_gauche / nord_droite) est verte à l'aller ; c'est l'inverse au retour. Dès qu'un feu est
  touché, son axe passe au vert et l'autre au rouge. L'axe reste vert tant que l'ambulance est à moins de
  `PORTEE_ONDE` (110 pixels) d'au moins un de ses feux, puis les feux reviennent au repos.
- **Interface PyQt5** (`gui/carte.py`) : dessine le carrefour, l'ambulance, les ondes (cercles rouges fins), les
  quatre feux et quelques autres véhicules. La diagonale (Rue Schickelé) est une seule voie de 50 px, à sens
  unique vers le carrefour, avec un panneau de sens interdit sur le trottoir nord à son entrée. L'Av. d'Alsace
  a un terre-plein central végétalisé. Les véhicules de fond (bleue, taxi, voiture verte derrière
  l'ambulance) s'arrêtent aux feux rouges et derrière tout véhicule devant eux. L'interface est mise à jour par les callbacks de l'ambulance et de
  l'infrastructure.
- **Base de données** (`server/database.py`) : si MariaDB est disponible, les événements sont insérés dans la
  table `evenements` (type, position x/y, horodatage) : positions de l'ambulance (une sur dix), ondes émises
  et changements d'état des feux.

## Protocole des messages

Les clients et le serveur échangent des messages JSON sur une connexion TCP : un message JSON par ligne,
chaque message étant terminé par un retour à la ligne (`\n`). Chaque message contient un champ `type`.

| Type | Envoyé par | Reçu par | Champs | Effet côté serveur |
|---|---|---|---|---|
| `identification` | infrastructure | serveur | `role` (`"infrastructure"`) | Le client est ajouté à la liste des infrastructures qui recevront les ordres `feu`. |
| `position_ambulance` | ambulance | serveur | `x`, `y`, `cap` | Mémorise la dernière position et le cap ; la première position d'une mission ouvre une mission en base ; une position sur dix est enregistrée. |
| `onde` | ambulance | serveur | `x`, `y`, `cap` | Démarre une onde dont le rayon grandit ; enregistrée comme `onde_ambulance`. |
| `pause` | ambulance | serveur | aucun | Mémorise l'instant de la pause : les ondes et les feux sont figés (bouton Pause de l'interface). |
| `reprise` | ambulance | serveur | aucun | Décale les ondes de la durée de la pause pour qu'elles reprennent à leur rayon d'avant. |
| `arret` | ambulance | serveur | `x`, `y` | Enregistré comme `arret_ambulance`, affiche « Ambulance arrêtée ». |
| `patient_embarque` | ambulance | serveur | aucun | Enregistré avec la dernière position connue, affiche « Patient embarqué » et passe au trajet retour (état de repos inversé). |
| `arrivee` | ambulance | serveur | aucun | Ferme la mission en base et réinitialise le serveur : trajet `aller`, aucun axe actif, feux dans leur état initial. |
| `feu` | serveur | infrastructure | `id` (identifiant du feu), `etat` (`"rouge"` ou `"vert"`) | Envoyé à chaque changement d'état d'un feu ; l'infrastructure le transmet à l'interface. |

## Base de données

La base est **optionnelle** : sans le module `mariadb` ou sans serveur MariaDB joignable, l'application
fonctionne normalement et affiche simplement un message `[DB]` ; rien n'est enregistré.

Au démarrage du serveur, la base et ses tables sont créées si elles n'existent pas :

- **`evenements`** : `id` (INT, clé primaire auto-incrémentée), `type_evenement` (VARCHAR(50)),
  `position_x` (INT), `position_y` (INT), `horodatage` (TIMESTAMP, date courante par défaut).
- **`missions`** : `id` (INT, clé primaire auto-incrémentée), `debut` (TIMESTAMP, date courante par défaut),
  `fin` (TIMESTAMP, vide tant que la mission n'est pas terminée). Une ligne est créée à la première position
  reçue d'une mission, et `fin` est renseignée à la réception de `arrivee`.

Les identifiants de connexion se règlent avec des variables d'environnement (le port reste 3306) :

| Variable | Valeur par défaut |
|---|---|
| `SAE_DB_HOST` | `localhost` |
| `SAE_DB_USER` | `root` |
| `SAE_DB_PASSWORD` | `root` |
| `SAE_DB_NAME` | `sae302` |

Pour afficher les 20 derniers événements enregistrés, depuis la racine du projet :

```
python -m server.consulter
```

Sans connexion à la base, le script affiche un message d'explication et s'arrête sans erreur.

## Tests

Les tests unitaires (dossier `tests/`) utilisent `unittest` et se lancent depuis la racine du projet :

```
python -m unittest
```

- `tests/test_trajets.py` : départ et arrivée des trajets aller et retour, pas de point répété et pas plus de
  10 pixels entre deux points consécutifs.
- `tests/test_carte.py` : trajets des véhicules de fond (voiture verte, taxi sur l'axe de la diagonale puis vers l'avenue),
  lit, bouton Rejouer grisé jusqu'à la fin de la mission.
- `tests/test_ondes.py` : axe actif obtenu en rejouant les trajets aller et retour à 20 Hz (`time.time`
  patché) : le feu d'approche est vert avant y=421 à l'aller (sud_droite) et x=653 au retour (nord_droite).
- `tests/test_pause.py` : décalage des ondes de la durée de la pause, reprise sans pause, double pause.
- `tests/test_circulation.py` : arrêt aux feux et distance de sécurité des véhicules.
- `tests/test_feux.py` : état voulu de chaque feu au repos et selon l'axe actif, à l'aller et au retour ;
  activation de l'axe par un feu touché et libération hors de portée ; le serveur ne se connecte pas à la base avant `demarrer()`.
