import unittest
from unittest.mock import patch
from parametres import (FEUX, FEU_AMBULANCE, FEU_RETOUR, PAIRE_AMBULANCE, PAIRE_RETOUR, INTERVALLE_ONDE,
                        PORTEE_ONDE, VITESSE_AMBULANCE, FREQUENCE_POSITION, generer_trajet, generer_trajet_retour)
from server.server import Serveur

PAS = VITESSE_AMBULANCE / FREQUENCE_POSITION


class TestOndes(unittest.TestCase):
    def setUp(self):
        self.serveur = Serveur(0)
        self.serveur.signaler_feu = lambda id_feu, etat, position: None

    def tearDown(self):
        self.serveur.socket_serveur.close()

    def rouler(self, trajet, feu, paire):
        maintenant = 1000.0
        derniere_onde = -1.0
        phases = []
        distances_au_passage = []
        for x, y in trajet:
            self.serveur.position_ambulance = (x, y)
            if maintenant - derniere_onde >= INTERVALLE_ONDE:
                self.serveur.ondes.append(maintenant)
                derniere_onde = maintenant
            with patch("server.server.time.time", return_value=maintenant):
                self.serveur.mettre_a_jour_feux()
            if not phases or phases[-1] != self.serveur.phase:
                phases.append(self.serveur.phase)
            if self.serveur.phase == "passage":
                distances_au_passage.append(self.serveur.distance((x, y), FEUX[feu]))
            maintenant += 1 / FREQUENCE_POSITION
        return phases, distances_au_passage

    def test_aller_attente_passage_apres(self):
        phases, distances = self.rouler(generer_trajet(PAS), FEU_AMBULANCE, PAIRE_AMBULANCE)
        self.assertEqual(phases, ["attente", "passage", "apres"])
        self.assertLessEqual(max(distances), PORTEE_ONDE)

    def test_retour_attente_passage_apres(self):
        self.serveur.demarrer_retour()
        phases, distances = self.rouler(generer_trajet_retour(PAS), FEU_RETOUR, PAIRE_RETOUR)
        self.assertEqual(phases, ["attente", "passage", "apres"])
        self.assertLessEqual(max(distances), PORTEE_ONDE)

    def test_feux_verts_pendant_le_passage_de_l_aller(self):
        self.rouler(generer_trajet(PAS), FEU_AMBULANCE, PAIRE_AMBULANCE)
        self.assertEqual(self.serveur.etat_feux[FEU_AMBULANCE], "rouge")

    def test_ondes_anciennes_supprimees(self):
        self.serveur.position_ambulance = (0, 0)
        self.serveur.ondes = [0.0]
        with patch("server.server.time.time", return_value=10.0):
            self.serveur.mettre_a_jour_feux()
        self.assertEqual(self.serveur.ondes, [])


if __name__ == "__main__":
    unittest.main()
