"""
Tests du plugin ecole : isolement multi-tenant et logique métier.

Vérifie qu'un membre d'un établissement ne voit jamais les données d'un
autre établissement, que l'écriture est réservée au staff, et que le
bulletin calcule moyennes et rang correctement.
"""
from django.urls import reverse
from rest_framework.test import APITestCase

from kalanfa.core.auth.models import Facility
from kalanfa.core.auth.models import FacilityUser
from kalanfa.core.auth.test.helpers import DUMMY_PASSWORD
from kalanfa.core.auth.test.helpers import provision_device

from ..models import DossierEleve
from ..models import Note
from ..models import Periode


def _make_facility(name, admin_username, learner_username):
    facility = Facility.objects.create(name=name)
    admin = FacilityUser.objects.create(username=admin_username, facility=facility)
    admin.set_password(DUMMY_PASSWORD)
    admin.save()
    facility.add_admin(admin)
    learner = FacilityUser.objects.create(username=learner_username, facility=facility)
    learner.set_password(DUMMY_PASSWORD)
    learner.save()
    return facility, admin, learner


class IsolementMultiTenantTestCase(APITestCase):
    databases = "__all__"

    @classmethod
    def setUpTestData(cls):
        provision_device()
        cls.ecole_a, cls.admin_a, cls.eleve_a = _make_facility(
            "École MOUMA", "admin_a", "eleve_a"
        )
        cls.ecole_b, cls.admin_b, cls.eleve_b = _make_facility(
            "École Autre", "admin_b", "eleve_b"
        )
        cls.dossier_a = DossierEleve.objects.create(
            facility=cls.ecole_a, eleve=cls.eleve_a, lieu_naissance="Bamako"
        )
        cls.dossier_b = DossierEleve.objects.create(
            facility=cls.ecole_b, eleve=cls.eleve_b, lieu_naissance="Kayes"
        )
        cls.url_dossiers = reverse("kalanfa:kalanfa.plugins.ecole:dossiereleve-list")

    def _login(self, user, facility):
        self.client.login(
            username=user.username, password=DUMMY_PASSWORD, facility=facility
        )

    def test_anonyme_refuse(self):
        reponse = self.client.get(self.url_dossiers)
        self.assertEqual(reponse.status_code, 403)

    def test_admin_ne_voit_que_son_ecole(self):
        self._login(self.admin_a, self.ecole_a)
        reponse = self.client.get(self.url_dossiers)
        self.assertEqual(reponse.status_code, 200)
        ids = {row["id"] for row in reponse.json()}
        self.assertIn(str(self.dossier_a.id), ids)
        self.assertNotIn(str(self.dossier_b.id), ids)

    def test_acces_direct_dossier_autre_ecole_refuse(self):
        self._login(self.admin_a, self.ecole_a)
        url = reverse(
            "kalanfa:kalanfa.plugins.ecole:dossiereleve-detail", kwargs={"pk": self.dossier_b.id}
        )
        reponse = self.client.get(url)
        self.assertEqual(reponse.status_code, 404)

    def test_eleve_ne_peut_pas_ecrire(self):
        self._login(self.eleve_a, self.ecole_a)
        reponse = self.client.post(
            self.url_dossiers, {"eleve": self.eleve_a.id}, format="json"
        )
        self.assertEqual(reponse.status_code, 403)

    def test_creation_assigne_la_facility_du_demandeur(self):
        self._login(self.admin_a, self.ecole_a)
        nouveau = FacilityUser.objects.create(
            username="eleve_a2", facility=self.ecole_a
        )
        reponse = self.client.post(
            self.url_dossiers, {"eleve": nouveau.id}, format="json"
        )
        self.assertEqual(reponse.status_code, 201)
        dossier = DossierEleve.objects.get(eleve=nouveau)
        self.assertEqual(dossier.facility_id, self.ecole_a.id)


class BulletinTestCase(APITestCase):
    databases = "__all__"

    @classmethod
    def setUpTestData(cls):
        provision_device()
        cls.ecole, cls.admin, cls.eleve1 = _make_facility(
            "École MOUMA", "admin", "eleve1"
        )
        cls.eleve2 = FacilityUser.objects.create(
            username="eleve2", facility=cls.ecole
        )
        cls.periode = Periode.objects.create(
            facility=cls.ecole, annee_scolaire="2026-2027", nom="Trimestre 1", ordre=1
        )
        # eleve1 : Maths 15 (coef 3), Français 12 (coef 2) -> moyenne 13.8
        Note.objects.create(
            facility=cls.ecole, eleve=cls.eleve1, periode=cls.periode,
            matiere="Mathématiques", valeur=15, coefficient=3,
        )
        Note.objects.create(
            facility=cls.ecole, eleve=cls.eleve1, periode=cls.periode,
            matiere="Français", valeur=12, coefficient=2,
        )
        # eleve2 : meilleur -> rang 1
        Note.objects.create(
            facility=cls.ecole, eleve=cls.eleve2, periode=cls.periode,
            matiere="Mathématiques", valeur=18, coefficient=3,
        )
        Note.objects.create(
            facility=cls.ecole, eleve=cls.eleve2, periode=cls.periode,
            matiere="Français", valeur=16, coefficient=2,
        )

    def test_bulletin_moyenne_et_rang(self):
        self.client.login(
            username="admin", password=DUMMY_PASSWORD, facility=self.ecole
        )
        url = reverse("kalanfa:kalanfa.plugins.ecole:note-bulletin")
        reponse = self.client.get(
            url, {"eleve": self.eleve1.id, "periode": str(self.periode.id)}
        )
        self.assertEqual(reponse.status_code, 200)
        data = reponse.json()
        self.assertEqual(data["moyenne_generale"], 13.8)
        self.assertEqual(data["rang"], 2)
        self.assertEqual(data["effectif"], 2)
        self.assertEqual(len(data["matieres"]), 2)

    def test_bulletin_parametres_manquants(self):
        self.client.login(
            username="admin", password=DUMMY_PASSWORD, facility=self.ecole
        )
        url = reverse("kalanfa:kalanfa.plugins.ecole:note-bulletin")
        reponse = self.client.get(url)
        self.assertEqual(reponse.status_code, 400)
