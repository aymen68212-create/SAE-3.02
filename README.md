# SAÉ 3.02 – Simulation d'une ambulance et de feux tricolores

**Groupe : L'Acquisition** – Aymen MRIZEL et Adam SEBAR

Simulation d'une ambulance qui traverse le carrefour **Av. d'Alsace × Rue des Jardins**, près de l'IUT de Colmar.
L'ambulance émet des ondes sonores ; lorsque l'onde touche un feu, le serveur commande le passage des feux :
l'axe de ce feu passe au vert, l'autre au rouge. Une fois l'ambulance éloignée, les feux reviennent à leur état
normal.

## Sommaire

1. [Structure du projet](#structure-du-projet)
2. [Installation sur Debian](#installation-sur-debian-12-ou-13)
3. [MariaDB (optionnel)](#mariadb-optionnel-côté-serveur)
4. [Lancement](#lancement)
5. [Scénario à deux machines](#scénario-à-deux-machines)
6. [Problèmes fréquents](#problèmes-fréquents)
7. [Fonctionnement](#fonctionnement)
8. [Protocole des messages](#protocole-des-messages)
9. [Base de données](#base-de-données)
10. [Tests](#tests)
11. [Documents du projet](#documents-du-projet)

## Structure du projet

```
.
├── main.py              # Point d'entrée : lance l'interface, le serveur et les deux clients
├── parametres.py        # Constantes partagées (réseau, vitesses, feux, trajets de l'ambulance)
├── requirements.txt     # Dépendances Python (PyQt5, mariadb)
├── server/
│   ├── server.py        # Serveur TCP : reçoit les messages, décide de l'état des feux
│   ├── database.py      # Enregistrement des événements dans MariaDB (optionnel)
│   └── consulter.py     # Affiche les derniers événements enregistrés
├── client/
│   ├── ambulance.py     # Client ambulance : envoie sa position et ses ondes
│   └── infrastructure.py# Client infrastructure : reçoit les ordres des feux
├── gui/
│   ├── carte.py         # Interface PyQt5 : carte du carrefour, ambulance, ondes, feux, bouton Rejouer
│   ├── circulation.py   # Véhicules de fond : trajets, arrêt aux feux, distance de sécurité
│   ├── decor.py         # Bâtiments, routes, marquages, terre-plein central et sens interdit de la diagonale
│   ├── lit.py           # Lit du patient, dessiné dans le parking jusqu'à l'embarquement
│   └── vehicules.py     # Dessin des voitures
└── tests/               # Tests unitaires (unittest)
```

## Installation sur Debian (12 ou 13)

Les commandes ci-dessous partent d'une Debian vierge avec un environnement graphique. Copiez-les dans l'ordre.

```
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip libgl1 libxkbcommon-x11-0 libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xfixes0 libxcb-xkb1
git clone https://github.com/aymen68212-create/SAE-3.02
cd SAE-3.02
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- Les paquets `lib...` sont les bibliothèques système dont Qt a besoin pour afficher une fenêtre.
- Le dossier `.venv` est un environnement Python isolé : il faut le réactiver dans chaque nouveau terminal avec
  `source .venv/bin/activate` (depuis le dossier `SAE-3.02`).
- Le paquet Python `mariadb` (version `2.0.0rc2` ou plus récente, écrit en Python) s'installe sans le connecteur C
  du système.

## MariaDB (optionnel, côté serveur)

**MariaDB est optionnel** : sans elle, la simulation fonctionne normalement et le serveur affiche simplement un
message `[DB]` (les événements ne sont pas enregistrés). Pour l'activer :

```
sudo apt install -y mariadb-server
sudo systemctl enable --now mariadb
sudo mariadb -e "CREATE DATABASE IF NOT EXISTS sae302; CREATE USER 'sae'@'localhost' IDENTIFIED BY 'sae'; GRANT ALL PRIVILEGES ON sae302.* TO 'sae'@'localhost';"
export SAE_DB_USER=sae SAE_DB_PASSWORD=sae
```

Le couple `root` / `root`, utilisé par défaut dans le code, **ne fonctionne pas sur Debian** : l'utilisateur
`root` de MariaDB s'y authentifie par socket Unix (il faut être `root` du système, via `sudo`) et n'a pas de mot
de passe. C'est pourquoi on crée un utilisateur dédié `sae`, puis on indique ses identifiants par les variables
d'environnement `SAE_DB_USER` et `SAE_DB_PASSWORD`. Ces variables doivent être définies dans le terminal qui lance
le serveur (le `export` ci-dessus ne vaut que pour le terminal courant). La base `sae302` et ses tables sont
créées automatiquement au démarrage du serveur.

## Lancement

Dans le dossier `SAE-3.02`, avec l'environnement virtuel activé :

```
python main.py
```

Une fenêtre « Simulation Ambulance - IUT Colmar » s'ouvre et la simulation démarre automatiquement : `main.py`
lance le serveur, le client infrastructure, le client ambulance et l'interface dans le même programme. Le bouton
**Rejouer** est grisé tant que la mission n'est pas terminée ; il devient actif quand l'ambulance est arrivée et
relance alors une mission complète.

Autres commandes utiles :

```
python -m unittest
QT_QPA_PLATFORM=offscreen python -m unittest
python -m server.consulter
python -m server.server
```

- `python -m unittest` lance tous les tests. Avec `QT_QPA_PLATFORM=offscreen`, Qt n'a pas besoin d'écran
  (serveur sans interface graphique, intégration continue).
- `python -m server.consulter` affiche les 20 derniers événements enregistrés en base.
- `python -m server.server` lance le serveur seul (voir le scénario à deux machines).

Les adresses réseau se règlent avec deux variables d'environnement :

| Variable | Rôle | Valeur par défaut |
|---|---|---|
| `SAE_HOTE` | Adresse du serveur, utilisée par les clients (ambulance et infrastructure) | `localhost` |
| `SAE_ECOUTE` | Adresse sur laquelle le serveur écoute (`0.0.0.0` : toutes les interfaces réseau) | `localhost` |

## Scénario à deux machines

Exemple avec deux machines virtuelles Debian sur le même réseau, chacune installée comme décrit plus haut.

**VM serveur** (avec MariaDB si on veut enregistrer les événements) :

```
cd SAE-3.02
source .venv/bin/activate
export SAE_DB_USER=sae SAE_DB_PASSWORD=sae
SAE_ECOUTE=0.0.0.0 python -m server.server
```

Pour connaître l'adresse IP de la VM serveur, lancez `ip a` et repérez la ligne `inet` de l'interface réseau
(par exemple `192.168.1.20`).

**VM client** (interface graphique, ambulance et infrastructure) :

```
sudo apt install -y netcat-openbsd
nc -vz <IP de la VM serveur> 5050
cd SAE-3.02
source .venv/bin/activate
SAE_HOTE=<IP de la VM serveur> python main.py --sans-serveur
```

- `nc -vz <IP> 5050` teste la connexion au port du serveur ; la réponse doit contenir `succeeded` (ou `open`).
- L'option `--sans-serveur` lance seulement l'interface et les deux clients, qui se connectent au serveur
  désigné par `SAE_HOTE`. Sans cette option, `python main.py` lance tout sur la même machine.
- Démarrez toujours le serveur avant le client. Si le serveur est injoignable, le client affiche un message en
  français et s'arrête.

## Problèmes fréquents

**`error: externally-managed-environment` pendant `pip install`.** Debian interdit d'installer des paquets Python
dans le système. Utilisez l'environnement virtuel : `python3 -m venv .venv`, puis `source .venv/bin/activate`,
puis `pip install -r requirements.txt`.

**`Could not load the Qt platform plugin "xcb"` au lancement.** Il manque une bibliothèque système. Pour
identifier laquelle (depuis le dossier du projet, environnement virtuel activé) :

```
ldd .venv/lib/python3*/site-packages/PyQt5/Qt5/plugins/platforms/libqxcb.so | grep "not found"
```

Chaque ligne `not found` désigne une bibliothèque absente ; installez le paquet Debian correspondant avec
`sudo apt install -y <paquet>` (la liste de l'installation ci-dessus couvre les cas courants). Vérifiez aussi
qu'une session graphique est ouverte (variable `DISPLAY` définie) ; sans écran, utilisez
`QT_QPA_PLATFORM=offscreen`.

**`OSError: [Errno 98] Address already in use` (port 5050 occupé).** Un autre serveur tourne déjà (souvent une
simulation précédente restée ouverte). Identifiez-le avec `ss -ltnp | grep 5050`, puis fermez-le
(`kill <PID>`) avant de relancer.

**Message `[DB]` au démarrage du serveur.** MariaDB est absente, arrêtée ou refuse les identifiants : la
simulation fonctionne, mais rien n'est enregistré. Pour l'activer, suivez la section MariaDB ; en cas de
`Access denied`, vérifiez `SAE_DB_USER` et `SAE_DB_PASSWORD` dans le terminal qui lance le serveur.

**`Impossible de joindre le serveur ...`.** Le serveur n'est pas lancé, `SAE_HOTE` est incorrecte ou le port 5050
est bloqué (testez avec `nc -vz <IP> 5050`).

## Fonctionnement

- **Serveur TCP** (`server/server.py`) : écoute sur `SAE_ECOUTE` (par défaut `localhost`), port **5050**. Les
  messages sont échangés en JSON, un message par ligne. Un thread par client gère les connexions, et un thread
  de supervision met à jour l'état des feux environ toutes les 30 ms.
- **Client ambulance** (`client/ambulance.py`) : suit un trajet prédéfini (`generer_trajet` dans `parametres.py`).
  À chaque pas, il envoie sa position et son cap (`position_ambulance`) ; toutes les 0,7 s il émet une onde
  (`onde`). Une fois arrêtée dans le parking, l'ambulance attend 2 secondes pendant que le patient est embarqué
  (le lit disparaît), puis repart. À la fin du trajet, le client envoie `arrivee` : le serveur prépare la mission
  suivante (position, ondes, trajet `aller`, axe actif) **sans modifier les feux**, qui gardent leur état de fin
  de mission jusqu'au premier tick de la mission suivante.
- **Client infrastructure** (`client/infrastructure.py`) : s'identifie auprès du serveur avec le rôle
  `infrastructure`, puis reçoit les ordres `feu` (identifiant du feu et état `rouge` ou `vert`) et les
  transmet à l'interface.
- **Logique des feux** : un feu est « touché » quand la distance ambulance-feu est inférieure ou égale au
  rayon de la plus grande onde vivante. Au repos, `PAIRE_AMBULANCE` (sud_droite / nord_gauche) est rouge et
  `PAIRE_RETOUR` (sud_gauche / nord_droite) est verte à l'aller ; c'est l'inverse au retour. Dès qu'un feu est
  touché, son axe passe au vert et l'autre au rouge. L'axe reste vert tant que l'ambulance est à moins de
  `PORTEE_ONDE` (110 pixels) d'au moins un de ses feux ; une fois sortie de portée, il reste vert encore
  `DELAI_CHANGEMENT_FEU` (2 secondes), sauf si un de ses feux est de nouveau touché, puis les feux reviennent au
  repos. Au premier tick d'une nouvelle mission, le serveur renvoie les quatre feux pour resynchroniser la carte.
- **Interface PyQt5** (`gui/carte.py`) : dessine le carrefour, l'ambulance, les ondes (cercles rouges fins), les
  quatre feux et quelques autres véhicules. La diagonale (Rue Schickelé) est une seule voie de 50 px, à sens
  unique vers le carrefour, avec un panneau de sens interdit sur le trottoir nord à son entrée. L'Av. d'Alsace
  a un terre-plein central végétalisé. Les véhicules de fond (voiture bleue, taxi, voiture verte derrière
  l'ambulance) s'arrêtent aux feux rouges et derrière tout véhicule devant eux. L'interface est mise à jour par
  les callbacks de l'ambulance et de l'infrastructure.
- **Base de données** (`server/database.py`) : si MariaDB est disponible, les événements sont insérés dans la
  table `evenements` (type, position x/y, horodatage) : positions de l'ambulance (une sur dix),
  ondes émises (`onde_ambulance`), arrêt dans le parking (`arret_ambulance`), embarquement du patient
  (`patient_embarque`) et changements d'état des feux (`feu_vert:<id>` ou `feu_rouge:<id>`).

## Protocole des messages

Les clients et le serveur échangent des messages JSON sur une connexion TCP : un message JSON par ligne,
chaque message étant terminé par un retour à la ligne (`\n`). Chaque message contient un champ `type`.

| Type | Envoyé par | Reçu par | Champs | Effet côté serveur |
|---|---|---|---|---|
| `identification` | infrastructure | serveur | `role` (`"infrastructure"`) | Le client est ajouté à la liste des infrastructures qui recevront les ordres `feu`. |
| `position_ambulance` | ambulance | serveur | `x`, `y`, `cap` | Mémorise la dernière position et le cap ; la première position d'une mission ouvre une mission en base ; une position sur dix est enregistrée. |
| `onde` | ambulance | serveur | `x`, `y`, `cap` | Démarre une onde dont le rayon grandit ; enregistrée comme `onde_ambulance`. |
| `arret` | ambulance | serveur | `x`, `y` | Enregistré comme `arret_ambulance`, affiche « Ambulance arrêtée ». |
| `patient_embarque` | ambulance | serveur | aucun | Enregistré avec la dernière position connue, affiche « Patient embarqué » et passe au trajet retour (état de repos inversé). |
| `arrivee` | ambulance | serveur | aucun | Ferme la mission en base et prépare la suivante : position, cap, ondes, compteur, trajet `aller`, axe actif et délai remis à zéro. Les feux ne sont pas modifiés et aucun message `feu` n'est envoyé. |
| `feu` | serveur | infrastructure | `id` (identifiant du feu), `etat` (`"rouge"` ou `"vert"`) | Envoyé à chaque changement d'état d'un feu, et pour les quatre feux au premier tick d'une mission ; l'infrastructure le transmet à l'interface. |

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

Sur Debian, ces valeurs par défaut ne fonctionnent pas (voir la section MariaDB : créez l'utilisateur `sae` et
définissez `SAE_DB_USER` et `SAE_DB_PASSWORD`).

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

Sur une machine sans écran, ajoutez `QT_QPA_PLATFORM=offscreen` devant la commande.

- `tests/test_trajets.py` : départ et arrivée des trajets aller et retour, pas de point répété et pas plus de
  10 pixels entre deux points consécutifs.
- `tests/test_carte.py` : trajets des véhicules de fond (voiture verte, taxi sur l'axe de la diagonale puis vers l'avenue),
  lit, bouton Rejouer grisé jusqu'à la fin de la mission.
- `tests/test_ondes.py` : axe actif obtenu en rejouant les trajets aller et retour à 20 Hz (`time.time`
  patché) : le feu d'approche est vert avant y=421 à l'aller (sud_droite) et x=653 au retour (nord_droite) ;
  `arrivee` ne touche pas aux feux et le premier tick de la mission suivante les resynchronise.
- `tests/test_circulation.py` : arrêt aux feux et distance de sécurité des véhicules.
- `tests/test_feux.py` : état voulu de chaque feu au repos et selon l'axe actif, à l'aller et au retour ;
  activation de l'axe par un feu touché, délai de 2 secondes et libération hors de portée ; le serveur ne se
  connecte pas à la base avant `demarrer()`.
- `tests/test_reseau.py` : variables `SAE_HOTE` et `SAE_ECOUTE`, option `--sans-serveur` et message d'erreur
  quand le serveur est injoignable.

## Documents du projet

Cette section listera les documents rendus avec le projet (à venir) :

- `Bilan_Projet.pdf`
- `IAGraphie.pdf`
