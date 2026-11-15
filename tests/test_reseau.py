"""Tests des variables SAE_HOTE et SAE_ECOUTE et du mode --sans-serveur."""

import os
import socket
import subprocess
import sys
import unittest
from unittest.mock import patch
import main
import parametres
from server import server

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def lire_parametres(environnement):
    """Importe `parametres` dans un processus neuf avec l'environnement donné.

    Args:
        environnement: variables d'environnement à ajouter (ou à retirer si la valeur est None).

    Returns:
        Un tuple (HOTE, ECOUTE) tel que lu par le module `parametres`.
    """
    variables = dict(os.environ)
    for nom in ("SAE_HOTE", "SAE_ECOUTE"):
        variables.pop(nom, None)
    for nom, valeur in environnement.items():
        if valeur is not None:
            variables[nom] = valeur
    sortie = subprocess.run(
        [sys.executable, "-c", "import parametres; print(parametres.HOTE, parametres.ECOUTE)"],
        cwd=RACINE, env=variables, capture_output=True, text=True, check=True,
    ).stdout.split()
    return tuple(sortie)


class TestVariablesReseau(unittest.TestCase):
    """Vérifie la lecture des variables d'environnement SAE_HOTE et SAE_ECOUTE."""

    def test_valeurs_par_defaut(self):
        """Sans variable, clients et serveur utilisent localhost."""
        self.assertEqual(lire_parametres({}), ("localhost", "localhost"))

    def test_sae_hote_pour_les_clients(self):
        """SAE_HOTE change l'adresse des clients sans toucher à celle d'écoute."""
        self.assertEqual(lire_parametres({"SAE_HOTE": "192.168.1.20"}), ("192.168.1.20", "localhost"))

    def test_sae_ecoute_pour_le_serveur(self):
        """SAE_ECOUTE change l'adresse d'écoute sans toucher à celle des clients."""
        self.assertEqual(lire_parametres({"SAE_ECOUTE": "0.0.0.0"}), ("localhost", "0.0.0.0"))

    def test_le_serveur_ecoute_sur_l_adresse_configuree(self):
        """Le serveur utilise la constante ECOUTE pour son bind."""
        self.assertIs(server.ECOUTE, parametres.ECOUTE)
        self.assertFalse(hasattr(server, "HOTE"))


class TestModeSansServeur(unittest.TestCase):
    """Vérifie l'option --sans-serveur et le message d'erreur en français."""

    def test_option_absente_par_defaut(self):
        """Sans option, le serveur est lancé comme avant."""
        with patch.object(sys, "argv", ["main.py"]):
            options, restants = main.lire_options()
        self.assertFalse(options.sans_serveur)
        self.assertEqual(restants, [])

    def test_option_sans_serveur(self):
        """L'option --sans-serveur est reconnue et les autres arguments sont conservés."""
        with patch.object(sys, "argv", ["main.py", "--sans-serveur", "-style", "fusion"]):
            options, restants = main.lire_options()
        self.assertTrue(options.sans_serveur)
        self.assertEqual(restants, ["-style", "fusion"])

    def test_serveur_injoignable_affiche_un_message_clair(self):
        """Un serveur absent donne False et un message en français mentionnant SAE_HOTE."""
        with socket.socket() as libre:
            libre.bind(("localhost", 0))
            port = libre.getsockname()[1]
        with patch.object(main, "PORT", port), patch("builtins.print") as affichage:
            self.assertFalse(main.serveur_joignable())
        message = affichage.call_args[0][0]
        self.assertIn("Impossible de joindre le serveur", message)
        self.assertIn("SAE_HOTE", message)

    def test_serveur_joignable(self):
        """Un serveur à l'écoute est détecté."""
        with socket.socket() as ecoute:
            ecoute.bind(("localhost", 0))
            ecoute.listen()
            with patch.object(main, "PORT", ecoute.getsockname()[1]):
                self.assertTrue(main.serveur_joignable())


if __name__ == "__main__":
    unittest.main()
