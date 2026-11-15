"""Tests des trajets des véhicules de fond, du lit et du bouton Rejouer (Qt en mode offscreen)."""

import math
import os
import unittest
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt5.QtWidgets import QApplication
from gui.carte import Carte, trajet_taxi, trajet_verte
from gui.lit import Lit
from parametres import VOIES

app = QApplication.instance() or QApplication([])


class TestTrajetsVehicules(unittest.TestCase):
    """Vérifie la géométrie des trajets du taxi et de la voiture verte."""
    def test_taxi_roule_sur_l_axe_de_la_diagonale(self):
        """Le taxi suit l'axe de la diagonale."""
        for x, y in trajet_taxi():
            if x <= 350:
                self.assertAlmostEqual(y, 542 - x / 2, delta=0.01)

    def test_taxi_va_tout_droit_puis_monte_sur_l_avenue(self):
        """Le taxi va tout droit, tourne sur un arc de rayon 50 puis monte sur x=525."""
        trajet = trajet_taxi()
        self.assertIn((400, VOIES["jardins_est"]), trajet)
        self.assertIn((475, VOIES["jardins_est"]), trajet)
        self.assertIn((525, 295), trajet)
        self.assertEqual(trajet[-1], (525, -30))
        for x, y in trajet:
            if 400 <= x <= 475:
                self.assertEqual(y, VOIES["jardins_est"])
            if 475 < x < 525 and 295 < y < 345:
                self.assertAlmostEqual(math.dist((x, y), (475, 295)), 50, delta=0.01)
            if y < 295:
                self.assertEqual(x, 525)

    def test_taxi_continu(self):
        """Le trajet du taxi n'a pas de saut."""
        trajet = trajet_taxi()
        for precedent, suivant in zip(trajet, trajet[1:]):
            self.assertLessEqual(math.dist(precedent, suivant), 2)

    def test_verte_tout_droit_vers_le_nord(self):
        """La voiture verte reste sur x=575 de (575,760) à (575,-30)."""
        trajet = trajet_verte()
        self.assertEqual(trajet[0], (VOIES["avenue_nord"], 760))
        self.assertEqual(trajet[-1], (VOIES["avenue_nord"], -30))
        for x, y in trajet:
            self.assertEqual(x, VOIES["avenue_nord"])


class TestLit(unittest.TestCase):
    """Vérifie l'état du lit."""
    def test_visible_au_depart(self):
        """Le lit est visible au départ."""
        self.assertTrue(Lit().get_visible())

    def test_masquer(self):
        """Le lit peut être masqué."""
        lit = Lit()
        lit.set_visible(False)
        self.assertFalse(lit.visible)


class TestCarte(unittest.TestCase):
    """Vérifie le comportement de la fenêtre."""
    def setUp(self):
        """Crée une carte."""
        self.carte = Carte()

    def tearDown(self):
        """Arrête le timer de la carte."""
        self.carte.timer.stop()

    def test_rejouer_grise_tant_que_la_mission_n_est_pas_terminee(self):
        """Rejouer est grisé pendant la mission."""
        self.carte.mettre_a_jour_bouton()
        self.assertFalse(self.carte.bouton_rejouer.isEnabled())

    def test_rejouer_actif_une_fois_la_mission_terminee(self):
        """Rejouer devient actif à la fin de la mission."""
        self.carte.mission_terminee = True
        self.carte.mettre_a_jour_bouton()
        self.assertTrue(self.carte.bouton_rejouer.isEnabled())

    def test_reinitialiser_regrise_le_bouton(self):
        """La réinitialisation grise de nouveau Rejouer."""
        self.carte.mission_terminee = True
        self.carte.reinitialiser()
        self.carte.mettre_a_jour_bouton()
        self.assertFalse(self.carte.bouton_rejouer.isEnabled())

    def test_embarquer_patient_masque_le_lit(self):
        """L'embarquement masque le lit et la réinitialisation le réaffiche."""
        self.carte.embarquer_patient()
        self.assertFalse(self.carte.lit.visible)
        self.carte.reinitialiser()
        self.assertTrue(self.carte.lit.visible)


if __name__ == "__main__":
    unittest.main()
