import math
import unittest
from parametres import generer_trajet, generer_trajet_retour, POINT_ARRET

PAS = 4.5


class TestTrajets(unittest.TestCase):
    def setUp(self):
        self.aller = generer_trajet(PAS)
        self.retour = generer_trajet_retour(PAS)

    def test_aller_depart_et_arrivee(self):
        self.assertEqual(self.aller[0], (550, 690))
        self.assertEqual(self.aller[-1], POINT_ARRET)

    def test_retour_depart_et_arrivee(self):
        self.assertLessEqual(math.dist(self.retour[0], POINT_ARRET), 5)
        self.assertEqual(self.retour[-1][0], 450)
        self.assertGreaterEqual(self.retour[-1][1], 700)

    def verifier_continuite(self, trajet):
        for precedent, suivant in zip(trajet, trajet[1:]):
            self.assertNotEqual(precedent, suivant)
            self.assertLessEqual(math.dist(precedent, suivant), 10)

    def test_aller_continu(self):
        self.verifier_continuite(self.aller)

    def test_retour_continu(self):
        self.verifier_continuite(self.retour)


if __name__ == "__main__":
    unittest.main()
