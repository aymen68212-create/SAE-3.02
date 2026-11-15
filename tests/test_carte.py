import math
import os
import unittest
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt5.QtWidgets import QApplication
from gui.carte import Carte, trajet_violette, trajet_taxi
from gui.lit import Lit
from parametres import VOIES

app = QApplication.instance() or QApplication([])


class TestTrajetsVehicules(unittest.TestCase):
    def test_violette_tourne_a_droite_vers_le_nord(self):
        trajet = trajet_violette()
        self.assertIn((600, 295), trajet)
        self.assertIn((575, 270), trajet)
        self.assertEqual(trajet[-1], (575, -30))
        for x, y in trajet:
            self.assertFalse(x < 575 and y > 280)

    def test_violette_arc_de_rayon_25(self):
        for x, y in trajet_violette():
            if 575 < x < 600 and 270 < y < 295:
                self.assertAlmostEqual(math.dist((x, y), (600, 270)), 25, delta=0.01)

    def test_taxi_roule_sur_l_axe_de_la_diagonale(self):
        for x, y in trajet_taxi():
            if x <= 300:
                self.assertAlmostEqual(y, 520 - x / 2, delta=0.01)

    def test_taxi_rejoint_la_voie_est(self):
        trajet = trajet_taxi()
        self.assertIn((400, VOIES["jardins_est"]), trajet)
        for precedent, suivant in zip(trajet, trajet[1:]):
            self.assertLessEqual(math.dist(precedent, suivant), 2)


class TestLit(unittest.TestCase):
    def test_visible_au_depart(self):
        self.assertTrue(Lit().get_visible())

    def test_masquer(self):
        lit = Lit()
        lit.set_visible(False)
        self.assertFalse(lit.visible)


class TestCarte(unittest.TestCase):
    def setUp(self):
        self.carte = Carte()

    def tearDown(self):
        self.carte.timer.stop()

    def test_rejouer_grise_tant_que_la_mission_n_est_pas_terminee(self):
        self.carte.mettre_a_jour_bouton()
        self.assertFalse(self.carte.bouton_rejouer.isEnabled())

    def test_rejouer_actif_une_fois_la_mission_terminee(self):
        self.carte.mission_terminee = True
        self.carte.mettre_a_jour_bouton()
        self.assertTrue(self.carte.bouton_rejouer.isEnabled())

    def test_reinitialiser_regrise_le_bouton(self):
        self.carte.mission_terminee = True
        self.carte.reinitialiser()
        self.carte.mettre_a_jour_bouton()
        self.assertFalse(self.carte.bouton_rejouer.isEnabled())

    def test_embarquer_patient_masque_le_lit(self):
        self.carte.embarquer_patient()
        self.assertFalse(self.carte.lit.visible)
        self.carte.reinitialiser()
        self.assertTrue(self.carte.lit.visible)


if __name__ == "__main__":
    unittest.main()
