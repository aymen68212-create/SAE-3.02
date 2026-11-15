"""Tests de l'état voulu des feux, de l'activation des axes et du délai de 2 secondes."""

import unittest
import unittest.mock
from parametres import FEUX, PAIRE_AMBULANCE, PAIRE_RETOUR, DELAI_CHANGEMENT_FEU
from server.server import Serveur


class TestFeux(unittest.TestCase):
    """Tests de la logique des feux du serveur (sans réseau ni base de données)."""
    def setUp(self):
        """Crée un serveur non démarré."""
        self.serveur = Serveur(0)

    def tearDown(self):
        """Ferme la socket du serveur."""
        self.serveur.socket_serveur.close()

    def etats(self, trajet, axe_actif):
        """Calcule les états voulus pour un trajet et un axe actif donnés.

        Args:
            trajet: "aller" ou "retour".
            axe_actif: paire de feux verte, ou None.

        Returns:
            Un dictionnaire {identifiant du feu: état}.
        """
        self.serveur.trajet = trajet
        self.serveur.axe_actif = axe_actif
        return {id_feu: self.serveur.etat_voulu(id_feu) for id_feu in FEUX}

    def attendus(self, paire_rouge):
        """Construit les états attendus pour une paire rouge.

        Args:
            paire_rouge: feux au rouge ; les autres sont verts.

        Returns:
            Un dictionnaire {identifiant du feu: état}.
        """
        return {id_feu: "rouge" if id_feu in paire_rouge else "vert" for id_feu in FEUX}

    def test_pas_de_connexion_base_au_constructeur(self):
        """Le serveur ne se connecte pas à la base avant `demarrer`."""
        self.assertIsNone(self.serveur.db.connexion)

    def test_repos_a_l_aller(self):
        """Au repos à l'aller, `PAIRE_AMBULANCE` est rouge."""
        self.assertEqual(self.etats("aller", None), self.attendus(PAIRE_AMBULANCE))

    def test_repos_au_retour(self):
        """Au repos au retour, `PAIRE_RETOUR` est rouge."""
        self.assertEqual(self.etats("retour", None), self.attendus(PAIRE_RETOUR))

    def test_axe_ambulance_vert_a_l_aller(self):
        """L'axe de l'ambulance actif met `PAIRE_AMBULANCE` au vert."""
        self.assertEqual(self.etats("aller", PAIRE_AMBULANCE), self.attendus(PAIRE_RETOUR))

    def test_axe_retour_vert_au_retour(self):
        """L'axe du retour actif met `PAIRE_RETOUR` au vert."""
        self.assertEqual(self.etats("retour", PAIRE_RETOUR), self.attendus(PAIRE_AMBULANCE))

    def test_trajet_aller_au_depart(self):
        """Le serveur démarre à l'aller sans axe actif."""
        self.assertEqual(self.serveur.trajet, "aller")
        self.assertIsNone(self.serveur.axe_actif)

    def test_feu_touche_active_son_axe(self):
        """Un feu touché par l'onde active son axe."""
        self.serveur.position_ambulance = (575, 400)
        self.serveur.ondes = [100.0]
        with unittest.mock.patch("server.server.time.time", return_value=100.4):
            self.serveur.mettre_a_jour_feux()
        self.assertEqual(self.serveur.axe_actif, PAIRE_AMBULANCE)

    def test_onde_trop_courte_ne_touche_pas(self):
        """Une onde qui n'atteint pas le feu n'active aucun axe."""
        self.serveur.position_ambulance = (575, 600)
        self.serveur.ondes = [100.0]
        with unittest.mock.patch("server.server.time.time", return_value=100.4):
            self.serveur.mettre_a_jour_feux()
        self.assertIsNone(self.serveur.axe_actif)

    def mettre_a_jour(self, position, instant):
        """Positionne l'ambulance et recalcule les feux à un instant donné.

        Args:
            position: position (x, y) de l'ambulance.
            instant: valeur simulée de `time.time`.
        """
        self.serveur.position_ambulance = position
        with unittest.mock.patch("server.server.time.time", return_value=instant):
            self.serveur.mettre_a_jour_feux()

    def test_delai_de_changement_defini(self):
        """Le délai de changement vaut 2 secondes."""
        self.assertEqual(DELAI_CHANGEMENT_FEU, 2.0)

    def test_axe_reste_vert_1_9_s_apres_la_sortie_de_portee(self):
        """L'axe reste vert 1,9 s après la sortie de portée."""
        self.serveur.axe_actif = PAIRE_AMBULANCE
        self.mettre_a_jour((900, 600), 100.0)
        self.mettre_a_jour((900, 600), 101.9)
        self.assertEqual(self.serveur.axe_actif, PAIRE_AMBULANCE)
        self.assertEqual(self.serveur.etat_feux["sud_droite"], "vert")

    def test_axe_repasse_au_repos_apres_2_s(self):
        """L'axe repasse au repos 2,0 s après la sortie de portée."""
        self.serveur.axe_actif = PAIRE_AMBULANCE
        self.mettre_a_jour((900, 600), 100.0)
        self.mettre_a_jour((900, 600), 102.0)
        self.assertIsNone(self.serveur.axe_actif)
        self.assertIsNone(self.serveur.sortie_portee)
        self.assertEqual(self.serveur.etat_feux, self.attendus(PAIRE_AMBULANCE))

    def test_retour_en_portee_annule_le_compte_a_rebours(self):
        """Un retour en portée annule le compte à rebours."""
        self.serveur.axe_actif = PAIRE_AMBULANCE
        self.mettre_a_jour((900, 600), 100.0)
        self.mettre_a_jour((575, 400), 101.0)
        self.assertIsNone(self.serveur.sortie_portee)
        self.mettre_a_jour((900, 600), 101.5)
        self.mettre_a_jour((900, 600), 103.4)
        self.assertEqual(self.serveur.axe_actif, PAIRE_AMBULANCE)
        self.mettre_a_jour((900, 600), 103.5)
        self.assertIsNone(self.serveur.axe_actif)

    def test_remise_a_zero_du_delai(self):
        """`demarrer_retour` et `reinitialiser` remettent le délai à zéro."""
        self.serveur.sortie_portee = 5.0
        self.serveur.demarrer_retour()
        self.assertIsNone(self.serveur.sortie_portee)
        self.serveur.sortie_portee = 5.0
        self.serveur.reinitialiser()
        self.assertIsNone(self.serveur.sortie_portee)

    def test_retour_remet_le_repos_inverse(self):
        """`demarrer_retour` applique l'état de repos du retour."""
        self.serveur.axe_actif = PAIRE_AMBULANCE
        self.serveur.demarrer_retour()
        self.assertIsNone(self.serveur.axe_actif)
        self.assertEqual(self.serveur.etat_feux, self.attendus(PAIRE_RETOUR))


if __name__ == "__main__":
    unittest.main()
