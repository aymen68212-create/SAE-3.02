import unittest
import unittest.mock
from parametres import FEUX, PAIRE_AMBULANCE, PAIRE_RETOUR
from server.server import Serveur


class TestFeux(unittest.TestCase):
    def setUp(self):
        self.serveur = Serveur(0)

    def tearDown(self):
        self.serveur.socket_serveur.close()

    def etats(self, trajet, axe_actif):
        self.serveur.trajet = trajet
        self.serveur.axe_actif = axe_actif
        return {id_feu: self.serveur.etat_voulu(id_feu) for id_feu in FEUX}

    def attendus(self, paire_rouge):
        return {id_feu: "rouge" if id_feu in paire_rouge else "vert" for id_feu in FEUX}

    def test_pas_de_connexion_base_au_constructeur(self):
        self.assertIsNone(self.serveur.db.connexion)

    def test_repos_a_l_aller(self):
        self.assertEqual(self.etats("aller", None), self.attendus(PAIRE_AMBULANCE))

    def test_repos_au_retour(self):
        self.assertEqual(self.etats("retour", None), self.attendus(PAIRE_RETOUR))

    def test_axe_ambulance_vert_a_l_aller(self):
        self.assertEqual(self.etats("aller", PAIRE_AMBULANCE), self.attendus(PAIRE_RETOUR))

    def test_axe_retour_vert_au_retour(self):
        self.assertEqual(self.etats("retour", PAIRE_RETOUR), self.attendus(PAIRE_AMBULANCE))

    def test_trajet_aller_au_depart(self):
        self.assertEqual(self.serveur.trajet, "aller")
        self.assertIsNone(self.serveur.axe_actif)

    def test_feu_touche_active_son_axe(self):
        self.serveur.position_ambulance = (575, 400)
        self.serveur.ondes = [100.0]
        with unittest.mock.patch("server.server.time.time", return_value=100.4):
            self.serveur.mettre_a_jour_feux()
        self.assertEqual(self.serveur.axe_actif, PAIRE_AMBULANCE)

    def test_onde_trop_courte_ne_touche_pas(self):
        self.serveur.position_ambulance = (575, 600)
        self.serveur.ondes = [100.0]
        with unittest.mock.patch("server.server.time.time", return_value=100.4):
            self.serveur.mettre_a_jour_feux()
        self.assertIsNone(self.serveur.axe_actif)

    def test_axe_libere_hors_de_portee(self):
        self.serveur.position_ambulance = (900, 600)
        self.serveur.axe_actif = PAIRE_AMBULANCE
        with unittest.mock.patch("server.server.time.time", return_value=100.0):
            self.serveur.mettre_a_jour_feux()
        self.assertIsNone(self.serveur.axe_actif)

    def test_retour_remet_le_repos_inverse(self):
        self.serveur.axe_actif = PAIRE_AMBULANCE
        self.serveur.demarrer_retour()
        self.assertIsNone(self.serveur.axe_actif)
        self.assertEqual(self.serveur.etat_feux, self.attendus(PAIRE_RETOUR))


if __name__ == "__main__":
    unittest.main()
