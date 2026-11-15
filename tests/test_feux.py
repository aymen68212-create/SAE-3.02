import unittest
import unittest.mock
from parametres import FEUX, PAIRE_AMBULANCE, PAIRE_RETOUR, DELAI_CHANGEMENT_FEU
from server.server import Serveur


class TestFeux(unittest.TestCase):
    def setUp(self):
        self.serveur = Serveur(0)

    def tearDown(self):
        self.serveur.socket_serveur.close()

    def etats(self, trajet, axe_actif):
        self.serveur.trajet = trajet
        self.serveur.axe_actif = axe_actif
        return {id_feu: self.serveur.etat_voulu(id_feu) for id_feu in FEUX}

    def attendus(self, paire_rouge):
        return {id_feu: "rouge" if id_feu in paire_rouge else "vert" for id_feu in FEUX}

    def test_pas_de_connexion_base_au_constructeur(self):
        self.assertIsNone(self.serveur.db.connexion)

    def test_repos_a_l_aller(self):
        self.assertEqual(self.etats("aller", None), self.attendus(PAIRE_AMBULANCE))

    def test_repos_au_retour(self):
        self.assertEqual(self.etats("retour", None), self.attendus(PAIRE_RETOUR))

    def test_axe_ambulance_vert_a_l_aller(self):
        self.assertEqual(self.etats("aller", PAIRE_AMBULANCE), self.attendus(PAIRE_RETOUR))

    def test_axe_retour_vert_au_retour(self):
        self.assertEqual(self.etats("retour", PAIRE_RETOUR), self.attendus(PAIRE_AMBULANCE))

    def test_trajet_aller_au_depart(self):
        self.assertEqual(self.serveur.trajet, "aller")
        self.assertIsNone(self.serveur.axe_actif)

    def test_feu_touche_active_son_axe(self):
        self.serveur.position_ambulance = (575, 400)
        self.serveur.ondes = [100.0]
        with unittest.mock.patch("server.server.time.time", return_value=100.4):
            self.serveur.mettre_a_jour_feux()
        self.assertEqual(self.serveur.axe_actif, PAIRE_AMBULANCE)

    def test_onde_trop_courte_ne_touche_pas(self):
        self.serveur.position_ambulance = (575, 600)
        self.serveur.ondes = [100.0]
        with unittest.mock.patch("server.server.time.time", return_value=100.4):
            self.serveur.mettre_a_jour_feux()
        self.assertIsNone(self.serveur.axe_actif)

    def mettre_a_jour(self, position, instant):
        self.serveur.position_ambulance = position
        with unittest.mock.patch("server.server.time.time", return_value=instant):
            self.serveur.mettre_a_jour_feux()

    def test_delai_de_changement_defini(self):
        self.assertEqual(DELAI_CHANGEMENT_FEU, 2.0)

    def test_axe_reste_vert_1_9_s_apres_la_sortie_de_portee(self):
        self.serveur.axe_actif = PAIRE_AMBULANCE
        self.mettre_a_jour((900, 600), 100.0)
        self.mettre_a_jour((900, 600), 101.9)
        self.assertEqual(self.serveur.axe_actif, PAIRE_AMBULANCE)
        self.assertEqual(self.serveur.etat_feux["sud_droite"], "vert")

    def test_axe_repasse_au_repos_apres_2_s(self):
        self.serveur.axe_actif = PAIRE_AMBULANCE
        self.mettre_a_jour((900, 600), 100.0)
        self.mettre_a_jour((900, 600), 102.0)
        self.assertIsNone(self.serveur.axe_actif)
        self.assertIsNone(self.serveur.sortie_portee)
        self.assertEqual(self.serveur.etat_feux, self.attendus(PAIRE_AMBULANCE))

    def test_retour_en_portee_annule_le_compte_a_rebours(self):
        self.serveur.axe_actif = PAIRE_AMBULANCE
        self.mettre_a_jour((900, 600), 100.0)
        self.mettre_a_jour((575, 400), 101.0)
        self.assertIsNone(self.serveur.sortie_portee)
        self.mettre_a_jour((900, 600), 101.5)
        self.mettre_a_jour((900, 600), 103.4)
        self.assertEqual(self.serveur.axe_actif, PAIRE_AMBULANCE)
        self.mettre_a_jour((900, 600), 103.5)
        self.assertIsNone(self.serveur.axe_actif)

    def test_remise_a_zero_du_delai(self):
        self.serveur.sortie_portee = 5.0
        self.serveur.demarrer_retour()
        self.assertIsNone(self.serveur.sortie_portee)
        self.serveur.sortie_portee = 5.0
        self.serveur.reinitialiser()
        self.assertIsNone(self.serveur.sortie_portee)

    def test_retour_remet_le_repos_inverse(self):
        self.serveur.axe_actif = PAIRE_AMBULANCE
        self.serveur.demarrer_retour()
        self.assertIsNone(self.serveur.axe_actif)
        self.assertEqual(self.serveur.etat_feux, self.attendus(PAIRE_RETOUR))


if __name__ == "__main__":
    unittest.main()
