"""Tests des trajets aller et retour de l'ambulance."""

import math
import unittest
from parametres import generer_trajet, generer_trajet_retour, POINT_ARRET, VOIES

PAS = 4.5


class TestTrajets(unittest.TestCase):
    """Vérifie départ, arrivée, voies empruntées et continuité des trajets."""
    def setUp(self):
        """Génère les deux trajets avec un pas de 4,5 pixels."""
        self.aller = generer_trajet(PAS)
        self.retour = generer_trajet_retour(PAS)

    def test_aller_depart_et_arrivee(self):
        """L'aller part de l'avenue d'Alsace et finit au point d'arrêt."""
        self.assertEqual(self.aller[0], (VOIES["avenue_nord"], 690))
        self.assertEqual(self.aller[-1], POINT_ARRET)

    def test_retour_depart_et_arrivee(self):
        """Le retour part du point d'arrêt et finit au sud de l'écran sur la voie de l'ambulance."""
        self.assertLessEqual(math.dist(self.retour[0], POINT_ARRET), 5)
        self.assertEqual(self.retour[-1][0], VOIES["avenue_sud_ambulance"])
        self.assertGreaterEqual(self.retour[-1][1], 700)

    def test_aller_roule_a_droite(self):
        """L'aller reste sur les bonnes voies (avenue, Rue des Jardins est, branche nord)."""
        for x, y in self.aller:
            if y > 400:
                self.assertEqual(x, VOIES["avenue_nord"])
            if 630 <= x <= 830:
                self.assertEqual(y, VOIES["jardins_est"])
            if y < 290 and x > 830:
                self.assertEqual(x, VOIES["branche_nord"])

    def test_retour_roule_a_droite(self):
        """Le retour reste sur les bonnes voies."""
        for x, y in self.retour:
            if 110 < y < 235 and x > 800:
                self.assertEqual(x, VOIES["branche_sud"])
            if 775 <= x <= VOIES["avenue_nord"] and 290 <= y <= 300:
                self.assertEqual(y, VOIES["jardins_ouest"])
            if y > 395:
                self.assertEqual(x, VOIES["avenue_sud_ambulance"])

    def verifier_continuite(self, trajet):
        """Vérifie qu'un trajet n'a ni doublon ni saut de plus de 10 pixels.

        Args:
            trajet: liste de points à contrôler.
        """
        for precedent, suivant in zip(trajet, trajet[1:]):
            self.assertNotEqual(precedent, suivant)
            self.assertLessEqual(math.dist(precedent, suivant), 10)

    def test_aller_continu(self):
        """L'aller est continu."""
        self.verifier_continuite(self.aller)

    def test_retour_continu(self):
        """Le retour est continu."""
        self.verifier_continuite(self.retour)


if __name__ == "__main__":
    unittest.main()
