import unittest
from unittest.mock import patch
from server.server import Serveur


class TestPause(unittest.TestCase):
    def setUp(self):
        self.serveur = Serveur(0)

    def tearDown(self):
        self.serveur.socket_serveur.close()

    def test_ondes_decalees_de_la_duree_de_pause(self):
        self.serveur.ondes = [100.0, 102.5]
        with patch("server.server.time.time", return_value=110.0):
            self.serveur.traiter_message(None, {"type": "pause"})
        with patch("server.server.time.time", return_value=117.0):
            self.serveur.traiter_message(None, {"type": "reprise"})
        self.assertEqual(self.serveur.ondes, [107.0, 109.5])
        self.assertIsNone(self.serveur.debut_pause)

    def test_age_des_ondes_identique_apres_pause(self):
        self.serveur.ondes = [100.0]
        with patch("server.server.time.time", return_value=101.0):
            avant = 101.0 - self.serveur.ondes[0]
            self.serveur.traiter_message(None, {"type": "pause"})
        with patch("server.server.time.time", return_value=161.0):
            self.serveur.traiter_message(None, {"type": "reprise"})
            apres = 161.0 - self.serveur.ondes[0]
        self.assertEqual(avant, apres)

    def test_reprise_sans_pause_ne_change_rien(self):
        self.serveur.ondes = [100.0]
        self.serveur.traiter_message(None, {"type": "reprise"})
        self.assertEqual(self.serveur.ondes, [100.0])

    def test_double_pause_garde_le_premier_debut(self):
        with patch("server.server.time.time", return_value=10.0):
            self.serveur.traiter_message(None, {"type": "pause"})
        with patch("server.server.time.time", return_value=20.0):
            self.serveur.traiter_message(None, {"type": "pause"})
        self.assertEqual(self.serveur.debut_pause, 10.0)


if __name__ == "__main__":
    unittest.main()
