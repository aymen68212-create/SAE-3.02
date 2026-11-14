import unittest
from PyQt5.QtGui import QColor
from gui.circulation import Vehicule, trajet_depuis_morceaux, VITESSE_VOITURE
from parametres import points_ligne


class TestVehicule(unittest.TestCase):
    def setUp(self):
        self.trajet = trajet_depuis_morceaux([points_ligne((0, 0), (200, 0), 1), points_ligne((200, 0), (200, 200), 1)])
        self.vehicule = Vehicule(self.trajet, QColor(10, 20, 30))

    def test_trajet_sans_doublons(self):
        self.assertEqual(len(self.trajet), len(set(self.trajet)))
        self.assertEqual(self.trajet[0], (0, 0))
        self.assertEqual(self.trajet[-1], (200, 200))

    def test_inactif_par_defaut(self):
        self.vehicule.avancer(1.0)
        self.assertEqual(self.vehicule.indice, 0.0)

    def test_vitesse_constante(self):
        self.vehicule.actif = True
        self.vehicule.avancer(0.5)
        self.assertAlmostEqual(self.vehicule.indice, 0.5 * VITESSE_VOITURE)

    def test_arrive_au_bout(self):
        self.vehicule.actif = True
        self.vehicule.avancer(100)
        self.assertEqual(self.vehicule.position(), (200, 200))
        self.assertTrue(self.vehicule.termine())

    def test_angle(self):
        self.vehicule.indice = 50
        self.assertAlmostEqual(self.vehicule.angle(), 0)
        self.vehicule.indice = 300
        self.assertAlmostEqual(self.vehicule.angle(), 90)

    def test_arret_au_feu_rouge(self):
        v = Vehicule(self.trajet, QColor(0, 0, 0), "f", 100)
        v.actif = True
        v.avancer(10, {"f": "rouge"})
        self.assertEqual(v.indice, 100)
        v.avancer(0.5, {"f": "vert"})
        self.assertAlmostEqual(v.indice, 145)

    def test_feu_rouge_apres_la_ligne_ignore(self):
        v = Vehicule(self.trajet, QColor(0, 0, 0), "f", 100)
        v.actif = True
        v.indice = 120
        v.avancer(0.5, {"f": "rouge"})
        self.assertAlmostEqual(v.indice, 165)


if __name__ == "__main__":
    unittest.main()
