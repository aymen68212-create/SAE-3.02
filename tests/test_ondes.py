import unittest
from unittest.mock import patch
from parametres import (FEUX, PAIRE_AMBULANCE, PAIRE_RETOUR, INTERVALLE_ONDE, PORTEE_ONDE,
                        VITESSE_AMBULANCE, FREQUENCE_POSITION, generer_trajet, generer_trajet_retour)
from server.server import Serveur

PAS = VITESSE_AMBULANCE / FREQUENCE_POSITION


class TestOndes(unittest.TestCase):
    def setUp(self):
        self.serveur = Serveur(0)
        self.serveur.signaler_feu = lambda id_feu, etat, position: None

    def tearDown(self):
        self.serveur.socket_serveur.close()

    def rouler(self, trajet, decalage=0.0):
        maintenant = 1000.0
        derniere_onde = maintenant - INTERVALLE_ONDE + decalage
        axes = []
        for x, y in trajet:
            self.serveur.position_ambulance = (x, y)
            if maintenant - derniere_onde >= INTERVALLE_ONDE - 1e-9:
                self.serveur.ondes.append(maintenant)
                derniere_onde = maintenant
            with patch("server.server.time.time", return_value=maintenant):
                self.serveur.mettre_a_jour_feux()
            yield x, y, self.serveur.etat_feux.copy()
            if not axes or axes[-1] != self.serveur.axe_actif:
                axes.append(self.serveur.axe_actif)
            maintenant += 1 / FREQUENCE_POSITION
        self.axes = axes

    def parcourir(self, trajet, decalage=0.0):
        return list(self.rouler(trajet, decalage))

    def verifier_feu_vert_avant(self, trajet, feu, atteint):
        for decalage in (0.0, 0.2, 0.4, 0.6):
            self.setUp()
            for x, y, etats in self.parcourir(trajet, decalage):
                if atteint(x, y):
                    self.assertEqual(etats[feu], "vert", (decalage, x, y))
                    break
            self.tearDown()
        self.setUp()

    def test_aller_feu_d_approche_vert_avant_y_421(self):
        self.verifier_feu_vert_avant(generer_trajet(PAS), "sud_droite", lambda x, y: y <= 421)

    def test_retour_feu_d_approche_vert_avant_x_653(self):
        self.serveur.demarrer_retour()
        self.verifier_feu_vert_avant(generer_trajet_retour(PAS), "nord_droite", lambda x, y: y == 295 and x <= 653)

    def test_aller_axe_ambulance_puis_repos(self):
        self.parcourir(generer_trajet(PAS))
        self.assertEqual(self.axes, [None, PAIRE_AMBULANCE, None])

    def test_retour_axe_retour_puis_repos(self):
        self.serveur.demarrer_retour()
        self.parcourir(generer_trajet_retour(PAS))
        self.assertEqual(set(self.axes), {None, PAIRE_RETOUR})
        self.assertEqual(self.axes[:2], [None, PAIRE_RETOUR])
        self.assertIsNone(self.axes[-1])

    def test_axe_actif_vert_et_autre_axe_rouge_pendant_le_passage(self):
        for x, y, etats in self.parcourir(generer_trajet(PAS)):
            if (x, y) == (575, 421):
                for id_feu in FEUX:
                    self.assertEqual(etats[id_feu], "vert" if id_feu in PAIRE_AMBULANCE else "rouge")

    def test_ondes_anciennes_supprimees(self):
        self.serveur.position_ambulance = (0, 0)
        self.serveur.ondes = [0.0]
        with patch("server.server.time.time", return_value=10.0):
            self.serveur.mettre_a_jour_feux()
        self.assertEqual(self.serveur.ondes, [])

    def test_portee(self):
        self.assertEqual(PORTEE_ONDE, 110)


if __name__ == "__main__":
    unittest.main()
