import unittest
from parametres import FEUX, PAIRE_AMBULANCE, PAIRE_RETOUR
from server.server import Serveur


class TestFeux(unittest.TestCase):
    def setUp(self):
        self.serveur = Serveur(0)

    def tearDown(self):
        self.serveur.socket_serveur.close()

    def etats(self, trajet, phase):
        self.serveur.trajet = trajet
        self.serveur.phase = phase
        return {id_feu: self.serveur.etat_voulu(id_feu) for id_feu in FEUX}

    def attendus(self, paire, paire_verte):
        if paire_verte:
            return {id_feu: "vert" if id_feu in paire else "rouge" for id_feu in FEUX}
        return {id_feu: "rouge" if id_feu in paire else "vert" for id_feu in FEUX}

    def test_pas_de_connexion_base_au_constructeur(self):
        self.assertIsNone(self.serveur.db.connexion)

    def test_aller_attente(self):
        self.assertEqual(self.etats("aller", "attente"), self.attendus(PAIRE_AMBULANCE, False))

    def test_aller_passage(self):
        self.assertEqual(self.etats("aller", "passage"), self.attendus(PAIRE_AMBULANCE, True))

    def test_aller_apres(self):
        self.assertEqual(self.etats("aller", "apres"), self.attendus(PAIRE_AMBULANCE, False))

    def test_retour_attente(self):
        self.assertEqual(self.etats("retour", "attente"), self.attendus(PAIRE_RETOUR, False))

    def test_retour_passage(self):
        self.assertEqual(self.etats("retour", "passage"), self.attendus(PAIRE_RETOUR, True))

    def test_retour_apres(self):
        self.assertEqual(self.etats("retour", "apres"), self.attendus(PAIRE_RETOUR, False))

    def test_trajet_aller_au_depart(self):
        self.assertEqual(self.serveur.trajet, "aller")


if __name__ == "__main__":
    unittest.main()
