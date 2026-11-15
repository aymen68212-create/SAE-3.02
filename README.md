# SAÉ 3.02 – Simulation d'une ambulance et de feux tricolores

**Groupe : L'Acquisition**
Étudiants : Aymen MRIZEL et Adam SEBAR (BUT Réseaux & Télécommunications, 2e année, IUT de Colmar)

## 1. De quoi s'agit-il ?

Une ambulance traverse un carrefour réel de Colmar (Av. d'Alsace × Rue des Jardins). Elle émet des « ondes sonores », dessinées comme des cercles rouges. Quand une onde touche un feu, le serveur passe ce feu au vert pour l'ambulance et au rouge pour les autres voitures. Quand l'ambulance s'éloigne, les feux reviennent à la normale. L'ambulance va jusqu'à un parking, embarque un patient, puis refait le chemin dans l'autre sens.

Le programme est fait de plusieurs morceaux qui se parlent par le réseau : un **serveur** (il décide), une **ambulance** (elle envoie sa position), une **infrastructure** (les feux, qui obéissent au serveur) et une **fenêtre** qui dessine le tout.

## 2. Comment lire ce guide

- Les étapes numérotées sont à suivre dans l'ordre, sans rien sauter. Chaque étape te dit **quoi taper**, puis **ce que tu dois voir**.
- Une commande se copie telle quelle (sans les trois apostrophes inversées), puis on appuie sur la touche **Entrée**.
- Les encadrés « 🔧 Pour les plus avancés » sont facultatifs : on peut les ignorer.
- Le **terminal** est la fenêtre où l'on tape des commandes. Pour l'ouvrir : menu Applications, puis « Terminal » (ou touches Ctrl + Alt + T).

## 3. Une machine ou deux ?

| | Option A : une seule VM | Option B : deux VM |
|---|---|---|
| Principe | tout tourne sur la même machine | une VM « serveur » (avec la base de données) et une VM « client » (avec l'interface) |
| Difficulté | facile | un peu plus longue |
| À choisir | pour commencer et pour tester | pour montrer le fonctionnement en réseau |

**Si tu débutes : fais l'Option A d'abord.**

## 4. Option A : installation sur une seule VM

**Étape 1 – Ouvre un terminal** (voir plus haut).

**Étape 2 – Mets à jour la liste des logiciels.**
```
sudo apt update
```
Le système demande ton mot de passe : tape-le puis Entrée. **Rien ne s'affiche pendant que tu tapes, c'est normal.** Tu dois voir défiler des lignes, puis le terminal te rend la main.

**Étape 3 – Installe les outils nécessaires** (une seule ligne, à copier en entier).
```
sudo apt install -y git python3 python3-venv python3-pip libgl1 libxkbcommon-x11-0 libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xfixes0 libxcb-xkb1
```
Tu dois voir des paquets s'installer. Cela peut prendre une minute.

> 🔧 **Pour les plus avancés** : `git` sert à télécharger le projet, `python3-venv` à créer un environnement Python isolé, et les paquets `libxcb…` / `libgl1` sont des bibliothèques dont la fenêtre graphique (PyQt5) a besoin.

**Étape 4 – Télécharge le projet.**
```
git clone https://github.com/aymen68212-create/SAE-3.02
cd SAE-3.02
```
Tu dois voir « Cloning into 'SAE-3.02' ». La deuxième commande te place dans le dossier du projet : **toutes les commandes suivantes se tapent dans ce dossier.**

**Étape 5 – Crée l'environnement Python du projet.**
```
python3 -m venv .venv
source .venv/bin/activate
```
Tu dois voir **(.venv)** apparaître au début de la ligne du terminal. Si tu fermes le terminal, il faudra retaper `cd SAE-3.02` puis `source .venv/bin/activate` avant de relancer le projet.

> 🔧 **Pour les plus avancés** : un « venv » est un dossier qui contient une copie de Python avec ses propres bibliothèques. Il évite de toucher au Python du système, ce que Debian 12 et 13 interdisent (erreur `externally-managed-environment`).

**Étape 6 – Installe les bibliothèques Python.**
```
pip install -r requirements.txt
```
Tu dois voir « Successfully installed … » à la fin.

**Étape 7 – Lance la simulation.**
```
python main.py
```
Une fenêtre « Simulation Ambulance - IUT Colmar » s'ouvre et la simulation démarre toute seule. Dans le terminal, tu vois « Serveur en attente de connexions… » puis des lignes « Feu … -> vert/rouge ».
Pour arrêter : ferme la fenêtre.

**Étape 8 – Vérifie que tout fonctionne (facultatif, conseillé).**
```
python -m unittest
```
Tu dois voir « OK » à la fin.

**Étape 9 – La base de données (facultatif).** Sans elle, le programme fonctionne normalement, mais n'enregistre rien. Pour l'activer :
```
sudo apt install -y mariadb-server
sudo systemctl enable --now mariadb
sudo mariadb -e "CREATE DATABASE IF NOT EXISTS sae302; CREATE USER IF NOT EXISTS 'sae'@'localhost' IDENTIFIED BY 'sae'; GRANT ALL PRIVILEGES ON sae302.* TO 'sae'@'localhost'; FLUSH PRIVILEGES;"
export SAE_DB_USER=sae
export SAE_DB_PASSWORD=sae
python main.py
```
Dans le terminal, tu dois voir « [DB] Connexion réussie. ». Pour afficher les derniers événements enregistrés (dans le même terminal, après une simulation) :
```
python -m server.consulter
```
Les deux lignes `export` ne valent que pour le terminal où tu les tapes : si tu en ouvres un autre, retape-les.

> 🔧 **Pour les plus avancés** : sur Debian, l'utilisateur `root` de MariaDB se connecte par le socket système, donc `root/root` ne fonctionne pas en TCP. On crée un utilisateur dédié `sae` et le programme lit ses identifiants dans les variables d'environnement `SAE_DB_HOST`, `SAE_DB_USER`, `SAE_DB_PASSWORD` et `SAE_DB_NAME`.

## 5. Option B : installation sur deux VM

Tu as besoin de l'adresse réseau (IP) de la VM serveur. L'Option A te sert de référence : les étapes sont les mêmes.

### B1. Sur la VM « serveur » (elle porte la base de données)

1. Ouvre un terminal, puis installe les outils (pas besoin des bibliothèques graphiques) :
```
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip mariadb-server
```
2. Télécharge le projet et prépare Python :
```
git clone https://github.com/aymen68212-create/SAE-3.02
cd SAE-3.02
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
3. Prépare la base de données :
```
sudo systemctl enable --now mariadb
sudo mariadb -e "CREATE DATABASE IF NOT EXISTS sae302; CREATE USER IF NOT EXISTS 'sae'@'localhost' IDENTIFIED BY 'sae'; GRANT ALL PRIVILEGES ON sae302.* TO 'sae'@'localhost'; FLUSH PRIVILEGES;"
export SAE_DB_USER=sae
export SAE_DB_PASSWORD=sae
```
4. Note l'adresse IP de cette VM :
```
ip a
```
Cherche la ligne qui commence par `inet` suivie de quelque chose comme `192.168.1.25/24` : l'IP est la partie avant le `/`.
5. Lance le serveur et **laisse ce terminal ouvert** :
```
SAE_ECOUTE=0.0.0.0 python -m server.server
```
Tu dois voir « Serveur en attente de connexions… » et « [DB] Connexion réussie. ».

> 🔧 **Pour les plus avancés** : `SAE_ECOUTE=0.0.0.0` fait écouter le serveur sur toutes les interfaces réseau, sinon il n'accepte que les connexions de sa propre machine.

### B2. Sur la VM « client » (elle affiche la fenêtre, un bureau graphique est nécessaire)

1. Ouvre un terminal et installe les outils (avec les bibliothèques graphiques) :
```
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip libgl1 libxkbcommon-x11-0 libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xfixes0 libxcb-xkb1
```
2. Télécharge le projet et prépare Python :
```
git clone https://github.com/aymen68212-create/SAE-3.02
cd SAE-3.02
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
3. Vérifie que la VM client voit le serveur (remplace `192.168.1.25` par l'IP notée à l'étape B1.4) :
```
python3 -c "import socket; socket.create_connection(('192.168.1.25', 5050), 3); print('Connexion OK')"
```
Tu dois voir « Connexion OK ». Sinon, regarde la section « Problèmes fréquents ».
4. Lance la simulation (toujours avec ton IP) :
```
SAE_HOTE=192.168.1.25 python main.py --sans-serveur
```
La fenêtre s'ouvre ; c'est le serveur de l'autre VM qui commande les feux.

### B3. Vérifier la base de données

Sur la VM serveur, dans **un deuxième terminal**, depuis le dossier du projet :
```
source .venv/bin/activate
export SAE_DB_USER=sae
export SAE_DB_PASSWORD=sae
python -m server.consulter
```
Tu dois voir un tableau avec les événements de la mission.

## 6. Ce que tu vois à l'écran

- L'ambulance (blanche avec une croix rouge) arrive par le sud. Les **cercles rouges** sont ses ondes sonores.
- Le feu touché par une onde passe au **vert** : l'ambulance passe. Les autres véhicules attendent au rouge.
- L'ambulance s'arrête au parking à droite, le lit disparaît (le patient est embarqué), puis elle repart par l'autre route.
- Le bouton **Rejouer** est grisé pendant la mission et devient utilisable à la fin pour recommencer.

## 7. Problèmes fréquents

| Ce que tu vois | Ce qu'il faut faire |
|---|---|
| `sudo : commande introuvable` (selon la façon dont la VM a été installée) | Tape `su -` (mot de passe root), puis `apt install -y sudo`, puis `usermod -aG sudo TON_NOM_D_UTILISATEUR`, puis `exit`, déconnecte-toi et reconnecte-toi. |
| `error: externally-managed-environment` | Tu n'es pas dans le venv. Tape `cd SAE-3.02` puis `source .venv/bin/activate`, et vérifie que `(.venv)` s'affiche. |
| `ModuleNotFoundError: No module named 'PyQt5'` | Même cause : active le venv, puis refais `pip install -r requirements.txt`. |
| `Could not load the Qt platform plugin "xcb"` | Il manque des bibliothèques ou il n'y a pas de bureau graphique. Teste : `ldd .venv/lib/python3*/site-packages/PyQt5/Qt5/plugins/platforms/libqxcb.so \| grep "not found"` puis installe les paquets signalés avec `sudo apt install`. La VM doit avoir un bureau graphique. |
| `Address already in use` (port 5050) | Une ancienne simulation tourne encore. Ferme sa fenêtre, ou tape `pkill -f main.py`, puis relance. |
| `[DB] Module mariadb absent…` ou `[DB] Erreur…` | Normal sans MariaDB : la simulation fonctionne, rien n'est enregistré. Pour l'activer, voir l'étape 9. |
| Connexion refusée entre les deux VM | Sur la VM serveur : vérifie que le serveur tourne et écoute (`ss -ltn \| grep 5050`), qu'il a été lancé avec `SAE_ECOUTE=0.0.0.0`, et qu'aucun pare-feu ne bloque (`sudo ufw status`). Vérifie que l'IP est la bonne. |

---

# Documentation technique (pour les plus avancés)

## Structure du projet

```
.
├── main.py              # Point d'entrée : lance l'interface, le serveur et les deux clients
├── parametres.py        # Constantes partagées (réseau, vitesses, feux, trajets de l'ambulance)
├── requirements.txt     # Dépendances Python (PyQt5, mariadb>=2.0.0rc2)
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

## Lancement et réglages réseau

| Commande | Effet |
|---|---|
| `python main.py` | Lance tout : serveur, infrastructure, ambulance et fenêtre, sur la même machine. |
| `python main.py --sans-serveur` | Lance seulement la fenêtre, le client ambulance et le client infrastructure, qui se connectent au serveur désigné par `SAE_HOTE`. Si le serveur est injoignable, un message en français est affiché et le programme s'arrête. |
| `python -m server.server` | Lance le serveur seul. |
| `python -m server.consulter` | Affiche les 20 derniers événements enregistrés en base. |
| `python -m unittest` | Lance les tests (ajouter `QT_QPA_PLATFORM=offscreen` sur une machine sans écran). |

| Variable | Rôle | Valeur par défaut |
|---|---|---|
| `SAE_HOTE` | Adresse du serveur, utilisée par les clients (ambulance et infrastructure) | `localhost` |
| `SAE_ECOUTE` | Adresse sur laquelle le serveur écoute (`0.0.0.0` : toutes les interfaces réseau) | `localhost` |

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

Sur Debian, ces valeurs par défaut ne fonctionnent pas : créer l'utilisateur `sae` (étape 9 du guide) et définir
`SAE_DB_USER` et `SAE_DB_PASSWORD`.

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
