"""Tests du déplacement des véhicules : vitesse, arrêt aux feux et distance de sécurité."""

import unittest
from PyQt5.QtGui import QColor
from gui.circulation import Vehicule, trajet_depuis_morceaux, VITESSE_VOITURE, DEMI_LONGUEUR
from parametres import points_ligne


class TestVehicule(unittest.TestCase):
    """Tests de la classe `Vehicule` sur un trajet en L (200 pixels à l'est puis 200 au sud)."""
    def setUp(self):
        """Crée le trajet en L et un véhicule sans feu."""
        self.trajet = trajet_depuis_morceaux([points_ligne((0, 0), (200, 0), 1), points_ligne((200, 0), (200, 200), 1)])
        self.vehicule = Vehicule(self.trajet, QColor(10, 20, 30))

    def test_trajet_sans_doublons(self):
        """Le trajet assemblé n'a pas de point répété."""
        self.assertEqual(len(self.trajet), len(set(self.trajet)))
        self.assertEqual(self.trajet[0], (0, 0))
        self.assertEqual(self.trajet[-1], (200, 200))

    def test_inactif_par_defaut(self):
        """Un véhicule inactif n'avance pas."""
        self.vehicule.avancer(1.0)
        self.assertEqual(self.vehicule.indice, 0.0)

    def test_vitesse_constante(self):
        """Un véhicule actif avance de VITESSE_VOITURE points par seconde."""
        self.vehicule.actif = True
        self.vehicule.avancer(0.5)
        self.assertAlmostEqual(self.vehicule.indice, 0.5 * VITESSE_VOITURE)

    def test_arrive_au_bout(self):
        """Le véhicule s'arrête à la fin du trajet."""
        self.vehicule.actif = True
        self.vehicule.avancer(100)
        self.assertEqual(self.vehicule.position(), (200, 200))
        self.assertTrue(self.vehicule.termine())

    def test_angle(self):
        """L'angle vaut 0 sur la partie est et 90 sur la partie sud."""
        self.vehicule.indice = 50
        self.assertAlmostEqual(self.vehicule.angle(), 0)
        self.vehicule.indice = 300
        self.assertAlmostEqual(self.vehicule.angle(), 90)

    def test_arret_au_feu_rouge(self):
        """Au rouge, le véhicule s'arrête avant sa ligne puis repart au vert."""
        v = Vehicule(self.trajet, QColor(0, 0, 0), "f", 100)
        v.actif = True
        v.avancer(10, {"f": "rouge"})
        self.assertEqual(v.indice, 73)
        v.avancer(0.5, {"f": "vert"})
        self.assertAlmostEqual(v.indice, 118)

    def test_pare_choc_avant_la_ligne(self):
        """Le pare-chocs avant reste en deçà de la ligne d'arrêt."""
        v = Vehicule(self.trajet, QColor(0, 0, 0), "f", 100)
        v.actif = True
        v.avancer(10, {"f": "rouge"})
        x_avant = v.position()[0] + DEMI_LONGUEUR
        self.assertLess(x_avant, 100)

    def test_arret_sans_ligne_ne_bloque_pas(self):
        """Sans ligne d'arrêt, un feu rouge ne bloque pas."""
        v = Vehicule(self.trajet, QColor(0, 0, 0), "f")
        v.actif = True
        v.avancer(0.5, {"f": "rouge"})
        self.assertAlmostEqual(v.indice, 45)

    def test_feu_d_une_autre_voie_ignore(self):
        """Le feu d'une autre voie est ignoré."""
        v = Vehicule(self.trajet, QColor(0, 0, 0), "f", 100)
        v.actif = True
        v.avancer(0.5, {"g": "rouge"})
        self.assertAlmostEqual(v.indice, 45)

    def test_feu_rouge_apres_la_ligne_ignore(self):
        """Un feu qui passe au rouge après la ligne ne bloque plus le véhicule."""
        v = Vehicule(self.trajet, QColor(0, 0, 0), "f", 100)
        v.actif = True
        v.indice = 80
        v.avancer(0.5, {"f": "rouge"})
        self.assertAlmostEqual(v.indice, 125)

    def test_obstacle_proche_devant_bloque(self):
        """Un obstacle proche devant bloque le véhicule."""
        self.vehicule.actif = True
        self.vehicule.indice = 50
        self.vehicule.avancer(0.5, None, [(100, 0)])
        self.assertEqual(self.vehicule.indice, 50)

    def test_obstacle_loin_ne_bloque_pas(self):
        """Un obstacle au-delà de la distance de sécurité ne bloque pas."""
        self.vehicule.actif = True
        self.vehicule.indice = 50
        self.vehicule.avancer(0.5, None, [(130, 0)])
        self.assertAlmostEqual(self.vehicule.indice, 95)

    def test_obstacle_derriere_ne_bloque_pas(self):
        """Un obstacle derrière ne bloque pas."""
        self.vehicule.actif = True
        self.vehicule.indice = 50
        self.vehicule.avancer(0.5, None, [(20, 0)])
        self.assertAlmostEqual(self.vehicule.indice, 95)

    def test_obstacle_dans_une_autre_voie_ne_bloque_pas(self):
        """Un obstacle dans une voie voisine ne bloque pas."""
        self.vehicule.actif = True
        self.vehicule.indice = 50
        self.vehicule.avancer(0.5, None, [(100, 20)])
        self.assertAlmostEqual(self.vehicule.indice, 95)

    def test_obstacle_dans_la_voie_decalee_bloque(self):
        """Un obstacle légèrement décalé mais dans la voie bloque."""
        self.vehicule.actif = True
        self.vehicule.indice = 50
        self.vehicule.avancer(0.5, None, [(100, 10)])
        self.assertEqual(self.vehicule.indice, 50)

    def test_reprend_quand_l_obstacle_s_eloigne(self):
        """Le véhicule repart quand l'obstacle s'éloigne."""
        self.vehicule.actif = True
        self.vehicule.indice = 50
        self.vehicule.avancer(0.5, None, [(100, 0)])
        self.vehicule.avancer(0.5, None, [(150, 0)])
        self.assertAlmostEqual(self.vehicule.indice, 95)

    def test_obstacle_dans_le_virage(self):
        """Un obstacle est détecté dans le sens de la marche après un virage."""
        self.vehicule.actif = True
        self.vehicule.indice = 250
        x, y = self.vehicule.position()
        self.vehicule.avancer(0.5, None, [(x, y + 40)])
        self.assertEqual(self.vehicule.indice, 250)


if __name__ == "__main__":
    unittest.main()
