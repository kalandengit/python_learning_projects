"""
Tests de l'intégration messagerie (Mattermost) — API mockée.

Le serveur Mattermost n'est pas requis : chaque appel HTTP est simulé.
Vérifie l'idempotence du provisionnement, le slug des équipes, l'exigence
de configuration et le contrôle d'accès de l'endpoint d'annonce.
"""
from unittest import mock

from django.urls import reverse
from rest_framework.test import APITestCase

from kalanfa.core.auth.models import Facility
from kalanfa.core.auth.models import FacilityUser
from kalanfa.core.auth.test.helpers import DUMMY_PASSWORD
from kalanfa.core.auth.test.helpers import provision_device

from ..messagerie import MattermostClient
from ..messagerie import MessagerieError
from ..messagerie import _slug


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = "x" if payload is not None else ""

    def json(self):
        return self._payload


def _client():
    return MattermostClient(base_url="http://mm.test", token="jeton-test")


class SlugTestCase(APITestCase):
    def test_slug_ecole_accentuee(self):
        self.assertEqual(_slug("École MOUMA"), "ecole-mouma")
        self.assertEqual(_slug("Trimestre 1 / 2026"), "trimestre-1-2026")


class ClientMessagerieTestCase(APITestCase):
    databases = "__all__"

    def test_configuration_absente_refusee(self):
        with mock.patch.dict(
            "os.environ",
            {"KALANFA_MATTERMOST_URL": "", "KALANFA_MATTERMOST_TOKEN": ""},
        ):
            with self.assertRaises(MessagerieError):
                MattermostClient()

    @mock.patch("kalanfa.plugins.ecole.gestion.messagerie.requests.request")
    def test_ensure_team_existante_sans_creation(self, m_request):
        facility = mock.Mock()
        facility.name = "École MOUMA"
        m_request.return_value = FakeResponse(200, {"id": "t1", "name": "cole-mouma"})
        equipe = _client().ensure_team(facility)
        self.assertEqual(equipe["id"], "t1")
        # Un seul appel : le GET a suffi, aucun POST de création
        self.assertEqual(m_request.call_count, 1)
        self.assertEqual(m_request.call_args[0][0], "GET")

    @mock.patch("kalanfa.plugins.ecole.gestion.messagerie.requests.request")
    def test_ensure_team_creee_si_absente(self, m_request):
        facility = mock.Mock()
        facility.name = "École MOUMA"
        m_request.side_effect = [
            FakeResponse(404, {}),  # GET introuvable
            FakeResponse(201, {"id": "t2", "name": "cole-mouma"}),  # POST création
        ]
        equipe = _client().ensure_team(facility)
        self.assertEqual(equipe["id"], "t2")
        self.assertEqual(m_request.call_count, 2)
        methode, = m_request.call_args_list[1][0][:1]
        self.assertEqual(methode, "POST")
        # L'équipe créée est sur invitation (isolement inter-écoles)
        self.assertEqual(m_request.call_args_list[1][1]["json"]["type"], "I")

    @mock.patch("kalanfa.plugins.ecole.gestion.messagerie.requests.request")
    def test_annoncer_publie_dans_le_canal(self, m_request):
        facility = mock.Mock()
        facility.name = "École MOUMA"
        m_request.side_effect = [
            FakeResponse(200, {"id": "t1"}),          # GET team
            FakeResponse(200, {"id": "c1"}),          # GET canal annonces
            FakeResponse(201, {"id": "p1"}),          # POST message
        ]
        poste = _client().annoncer(facility, "Rentrée le 1er octobre")
        self.assertEqual(poste["id"], "p1")
        self.assertEqual(
            m_request.call_args_list[2][1]["json"]["message"],
            "Rentrée le 1er octobre",
        )


class AnnonceEndpointTestCase(APITestCase):
    databases = "__all__"

    @classmethod
    def setUpTestData(cls):
        provision_device()
        cls.ecole = Facility.objects.create(name="École MOUMA")
        cls.admin = FacilityUser.objects.create(
            username="admin", facility=cls.ecole
        )
        cls.admin.set_password(DUMMY_PASSWORD)
        cls.admin.save()
        cls.ecole.add_admin(cls.admin)
        cls.eleve = FacilityUser.objects.create(
            username="eleve", facility=cls.ecole
        )
        cls.eleve.set_password(DUMMY_PASSWORD)
        cls.eleve.save()
        cls.url = reverse("kalanfa:kalanfa.plugins.ecole:messagerie-annonce")

    def test_anonyme_refuse(self):
        reponse = self.client.post(self.url, {"texte": "x"}, format="json")
        self.assertEqual(reponse.status_code, 403)

    def test_eleve_refuse(self):
        self.client.login(
            username="eleve", password=DUMMY_PASSWORD, facility=self.ecole
        )
        reponse = self.client.post(self.url, {"texte": "x"}, format="json")
        self.assertEqual(reponse.status_code, 403)

    def test_texte_obligatoire(self):
        self.client.login(
            username="admin", password=DUMMY_PASSWORD, facility=self.ecole
        )
        reponse = self.client.post(self.url, {"texte": "  "}, format="json")
        self.assertEqual(reponse.status_code, 400)

    @mock.patch(
        "kalanfa.plugins.ecole.gestion.messagerie.MattermostClient.annoncer"
    )
    @mock.patch(
        "kalanfa.plugins.ecole.gestion.messagerie.MattermostClient.__init__",
        return_value=None,
    )
    @mock.patch(
        "kalanfa.plugins.ecole.gestion.messagerie.MattermostClient.est_configure",
        return_value=True,
    )
    def test_admin_publie(self, m_conf, m_init, m_annoncer):
        m_annoncer.return_value = {"id": "p42"}
        self.client.login(
            username="admin", password=DUMMY_PASSWORD, facility=self.ecole
        )
        reponse = self.client.post(
            self.url, {"texte": "Réunion des parents samedi"}, format="json"
        )
        self.assertEqual(reponse.status_code, 201)
        self.assertEqual(reponse.json()["canaux"], ["mattermost"])

    def test_messagerie_non_configuree_erreur_propre(self):
        self.client.login(
            username="admin", password=DUMMY_PASSWORD, facility=self.ecole
        )
        with mock.patch.dict(
            "os.environ",
            {"KALANFA_MATTERMOST_URL": "", "KALANFA_MATTERMOST_TOKEN": ""},
        ):
            reponse = self.client.post(
                self.url, {"texte": "Annonce"}, format="json"
            )
        self.assertEqual(reponse.status_code, 502)
