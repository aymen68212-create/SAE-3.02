"""Tests de bout en bout de la logique des feux : trajets rejoués à 20 Hz avec un temps simulé."""

import unittest
from unittest.mock import patch
from parametres import (FEUX, PAIRE_AMBULANCE, PAIRE_RETOUR, INTERVALLE_ONDE, PORTEE_ONDE,
                        VITESSE_AMBULANCE, FREQUENCE_POSITION, generer_trajet, generer_trajet_retour)
from server.server import Serveur

PAS = VITESSE_AMBULANCE / FREQUENCE_POSITION


class TestOndes(unittest.TestCase):
    """Rejoue les trajets de l'ambulance contre le serveur, en patchant `time.time`."""
    def setUp(self):
        """Crée un serveur non démarré dont `signaler_feu` est neutralisé."""
        self.serveur = Serveur(0)
        self.serveur.signaler_feu = lambda id_feu, etat, position: None

    def tearDown(self):
        """Ferme la socket du serveur."""
        self.serveur.socket_serveur.close()

    def rouler(self, trajet, decalage=0.0):
        """Fait rouler l'ambulance sur un trajet, avec une onde toutes les INTERVALLE_ONDE secondes.

        Args:
            trajet: liste de points (x, y).
            decalage: décalage de l'émission de la première onde, en secondes.

        Yields:
            (x, y, états des feux) après chaque mise à jour du serveur.
        """
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
        """Parcourt un trajet complet et retourne tous les pas.

        Args:
            trajet: liste de points (x, y).
            decalage: décalage de la première onde.

        Returns:
            La liste des (x, y, états des feux).
        """
        return list(self.rouler(trajet, decalage))

    def verifier_feu_vert_avant(self, trajet, feu, atteint):
        """Vérifie qu'un feu est vert avant que l'ambulance atteigne une position, pour plusieurs décalages d'onde.

        Args:
            trajet: trajet à rejouer.
            feu: identifiant du feu d'approche.
            atteint: fonction (x, y) -> bool, vraie quand la ligne d'arrêt est atteinte.
        """
        for decalage in (0.0, 0.2, 0.4, 0.6):
            self.setUp()
            for x, y, etats in self.parcourir(trajet, decalage):
                if atteint(x, y):
                    self.assertEqual(etats[feu], "vert", (decalage, x, y))
                    break
            self.tearDown()
        self.setUp()

    def test_aller_feu_d_approche_vert_avant_y_421(self):
        """À l'aller, `sud_droite` est vert avant que l'ambulance atteigne y=421."""
        self.verifier_feu_vert_avant(generer_trajet(PAS), "sud_droite", lambda x, y: y <= 421)

    def test_retour_feu_d_approche_vert_avant_x_653(self):
        """Au retour, `nord_droite` est vert avant que l'ambulance atteigne x=653."""
        self.serveur.demarrer_retour()
        self.verifier_feu_vert_avant(generer_trajet_retour(PAS), "nord_droite", lambda x, y: y == 295 and x <= 653)

    def test_aller_axe_ambulance_puis_repos(self):
        """À l'aller, l'axe de l'ambulance est activé puis relâché."""
        self.parcourir(generer_trajet(PAS))
        self.assertEqual(self.axes, [None, PAIRE_AMBULANCE, None])

    def test_retour_axe_retour_puis_repos(self):
        """Au retour, l'axe du retour est activé puis relâché sans clignotement."""
        self.serveur.demarrer_retour()
        self.parcourir(generer_trajet_retour(PAS))
        self.assertEqual(self.axes, [None, PAIRE_RETOUR, None])

    def test_axe_actif_vert_et_autre_axe_rouge_pendant_le_passage(self):
        """Pendant le passage, l'axe actif est vert et l'autre rouge."""
        for x, y, etats in self.parcourir(generer_trajet(PAS)):
            if (x, y) == (575, 421):
                for id_feu in FEUX:
                    self.assertEqual(etats[id_feu], "vert" if id_feu in PAIRE_AMBULANCE else "rouge")

    def fin_de_mission(self):
        """Rejoue une mission complète puis envoie `arrivee`, en enregistrant les messages envoyés aux infrastructures."""
        self.envois = []
        self.serveur.envoyer_aux_infrastructures = self.envois.append
        self.parcourir(generer_trajet(PAS))
        self.serveur.demarrer_retour()
        self.serveur.ondes = []
        self.parcourir(generer_trajet_retour(PAS))
        self.serveur.traiter_message(None, {"type": "arrivee"})

    def etats_attendus(self, paire_rouge):
        """Construit les états attendus pour une paire rouge.

        Args:
            paire_rouge: feux au rouge ; les autres sont verts.

        Returns:
            Un dictionnaire {identifiant du feu: état}.
        """
        return {id_feu: "rouge" if id_feu in paire_rouge else "vert" for id_feu in FEUX}

    def test_arrivee_ne_touche_pas_aux_feux(self):
        """`arrivee` ne change pas les feux et n'envoie aucun message."""
        self.fin_de_mission()
        self.envois.clear()
        self.serveur.traiter_message(None, {"type": "arrivee"})
        self.assertEqual(self.serveur.etat_feux, self.etats_attendus(PAIRE_RETOUR))
        self.assertEqual(self.envois, [])

    def test_arrivee_remet_le_reste_a_zero(self):
        """`arrivee` remet à zéro position, cap, ondes, compteur, trajet, axe et délai."""
        self.fin_de_mission()
        self.assertEqual(self.serveur.trajet, "aller")
        self.assertIsNone(self.serveur.position_ambulance)
        self.assertIsNone(self.serveur.cap_ambulance)
        self.assertEqual(self.serveur.ondes, [])
        self.assertEqual(self.serveur.compteur_positions, 0)
        self.assertIsNone(self.serveur.axe_actif)
        self.assertIsNone(self.serveur.sortie_portee)

    def test_aucune_mise_a_jour_entre_deux_missions(self):
        """Entre deux missions, les feux ne changent pas."""
        self.fin_de_mission()
        self.envois.clear()
        with patch("server.server.time.time", return_value=5000.0):
            self.serveur.mettre_a_jour_feux()
        self.assertEqual(self.serveur.etat_feux, self.etats_attendus(PAIRE_RETOUR))
        self.assertEqual(self.envois, [])

    def test_premier_tick_de_la_mission_suivante_remet_le_repos_de_l_aller(self):
        """Au premier tick de la mission suivante, l'état de repos de l'aller est envoyé pour les 4 feux."""
        self.fin_de_mission()
        self.envois.clear()
        del self.serveur.signaler_feu
        self.serveur.position_ambulance = (575, 690)
        with patch("server.server.time.time", return_value=5000.0):
            self.serveur.mettre_a_jour_feux()
        self.assertEqual(self.serveur.etat_feux, self.etats_attendus(PAIRE_AMBULANCE))
        envoyes = {m["id"]: m["etat"] for m in self.envois}
        self.assertEqual(envoyes, self.etats_attendus(PAIRE_AMBULANCE))

    def test_premier_tick_renvoie_les_4_feux_meme_sans_difference(self):
        """Le premier tick renvoie les 4 feux même s'ils n'ont pas changé."""
        self.envois = []
        self.serveur.envoyer_aux_infrastructures = self.envois.append
        self.serveur.position_ambulance = (575, 690)
        with patch("server.server.time.time", return_value=5000.0):
            self.serveur.mettre_a_jour_feux()
            self.serveur.mettre_a_jour_feux()
        self.assertEqual(len(self.envois), 4)

    def test_ondes_anciennes_supprimees(self):
        """Les ondes qui ont dépassé la portée sont supprimées."""
        self.serveur.position_ambulance = (0, 0)
        self.serveur.ondes = [0.0]
        with patch("server.server.time.time", return_value=10.0):
            self.serveur.mettre_a_jour_feux()
        self.assertEqual(self.serveur.ondes, [])

    def test_portee(self):
        """La portée des ondes vaut 110 pixels."""
        self.assertEqual(PORTEE_ONDE, 110)


if __name__ == "__main__":
    unittest.main()
