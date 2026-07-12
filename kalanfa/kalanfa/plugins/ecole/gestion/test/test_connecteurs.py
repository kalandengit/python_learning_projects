"""
Tests des connecteurs Slack et WhatsApp — API mockées.

Aucun service externe requis : requests.post est simulé. Vérifie la
configuration obligatoire, la normalisation des numéros, les payloads
Slack/Meta et le contrôle d'accès de l'endpoint WhatsApp.
"""
from unittest import mock

from django.urls import reverse
from rest_framework.test import APITestCase

from kalanfa.core.auth.models import Facility
from kalanfa.core.auth.models import FacilityUser
from kalanfa.core.auth.test.helpers import DUMMY_PASSWORD
from kalanfa.core.auth.test.helpers import provision_device

from ..connecteurs import ConnecteurError
from ..connecteurs import SlackConnector
from ..connecteurs import WhatsAppConnector
from ..connecteurs import _normaliser_numero


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text="ok"):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


class NumeroTestCase(APITestCase):
    def test_normalisation_numero_malien(self):
        self.assertEqual(_normaliser_numero("+223 76 00 00 00"), "22376000000")
        self.assertEqual(_normaliser_numero("223-76-00-00-00"), "22376000000")

    def test_numero_invalide(self):
        with self.assertRaises(ConnecteurError):
            _normaliser_numero("12")


class SlackConnectorTestCase(APITestCase):
    def test_configuration_absente(self):
        with mock.patch.dict("os.environ", {"KALANFA_SLACK_WEBHOOK_URL": ""}):
            with self.assertRaises(ConnecteurError):
                SlackConnector()

    @mock.patch("kalanfa.plugins.ecole.gestion.connecteurs.requests.post")
    def test_envoi(self, m_post):
        m_post.return_value = FakeResponse(200)
        connecteur = SlackConnector(webhook_url="https://hooks.slack.test/x")
        self.assertTrue(connecteur.envoyer("Bonjour l'école"))
        self.assertEqual(m_post.call_args[1]["json"], {"text": "Bonjour l'école"})

    @mock.patch("kalanfa.plugins.ecole.gestion.connecteurs.requests.post")
    def test_refus_slack(self, m_post):
        m_post.return_value = FakeResponse(404, text="no_service")
        connecteur = SlackConnector(webhook_url="https://hooks.slack.test/x")
        with self.assertRaises(ConnecteurError):
            connecteur.envoyer("x")


class WhatsAppConnectorTestCase(APITestCase):
    def test_configuration_absente(self):
        with mock.patch.dict(
            "os.environ",
            {"KALANFA_WHATSAPP_TOKEN": "", "KALANFA_WHATSAPP_PHONE_ID": ""},
        ):
            with self.assertRaises(ConnecteurError):
                WhatsAppConnector()

    @mock.patch("kalanfa.plugins.ecole.gestion.connecteurs.requests.post")
    def test_envoi_texte(self, m_post):
        m_post.return_value = FakeResponse(200, {"messages": [{"id": "wamid.1"}]})
        connecteur = WhatsAppConnector(token="t", phone_id="12345")
        resultat = connecteur.envoyer_texte("+223 76 00 00 00", "Rappel : réunion")
        self.assertEqual(resultat["messages"][0]["id"], "wamid.1")
        url = m_post.call_args[0][0]
        self.assertIn("/12345/messages", url)
        payload = m_post.call_args[1]["json"]
        self.assertEqual(payload["to"], "22376000000")
        self.assertEqual(payload["text"]["body"], "Rappel : réunion")

    @mock.patch("kalanfa.plugins.ecole.gestion.connecteurs.requests.post")
    def test_envoi_template(self, m_post):
        m_post.return_value = FakeResponse(200, {"messages": [{"id": "wamid.2"}]})
        connecteur = WhatsAppConnector(token="t", phone_id="12345")
        connecteur.envoyer_template(
            "22376000000", "rappel_frais", parametres=["Awa", "25000"]
        )
        payload = m_post.call_args[1]["json"]
        self.assertEqual(payload["type"], "template")
        self.assertEqual(payload["template"]["name"], "rappel_frais")
        self.assertEqual(payload["template"]["language"]["code"], "fr")
        parametres = payload["template"]["components"][0]["parameters"]
        self.assertEqual([p["text"] for p in parametres], ["Awa", "25000"])


class WhatsAppEndpointTestCase(APITestCase):
    databases = "__all__"

    @classmethod
    def setUpTestData(cls):
        provision_device()
        cls.ecole = Facility.objects.create(name="École MOUMA")
        cls.admin = FacilityUser.objects.create(username="admin", facility=cls.ecole)
        cls.admin.set_password(DUMMY_PASSWORD)
        cls.admin.save()
        cls.ecole.add_admin(cls.admin)
        cls.eleve = FacilityUser.objects.create(username="eleve", facility=cls.ecole)
        cls.eleve.set_password(DUMMY_PASSWORD)
        cls.eleve.save()
        cls.url = reverse("kalanfa:kalanfa.plugins.ecole:messagerie-whatsapp")

    def test_eleve_refuse(self):
        self.client.login(
            username="eleve", password=DUMMY_PASSWORD, facility=self.ecole
        )
        reponse = self.client.post(
            self.url, {"telephone": "22376000000", "texte": "x"}, format="json"
        )
        self.assertEqual(reponse.status_code, 403)

    def test_parametres_obligatoires(self):
        self.client.login(
            username="admin", password=DUMMY_PASSWORD, facility=self.ecole
        )
        reponse = self.client.post(self.url, {"telephone": ""}, format="json")
        self.assertEqual(reponse.status_code, 400)

    @mock.patch(
        "kalanfa.plugins.ecole.gestion.connecteurs.WhatsAppConnector.envoyer_texte"
    )
    @mock.patch(
        "kalanfa.plugins.ecole.gestion.connecteurs.WhatsAppConnector.__init__",
        return_value=None,
    )
    def test_admin_envoie_texte(self, m_init, m_envoyer):
        m_envoyer.return_value = {"messages": [{"id": "wamid.9"}]}
        self.client.login(
            username="admin", password=DUMMY_PASSWORD, facility=self.ecole
        )
        reponse = self.client.post(
            self.url,
            {"telephone": "+22376000000", "texte": "Réunion samedi 9h"},
            format="json",
        )
        self.assertEqual(reponse.status_code, 201)
        self.assertTrue(reponse.json()["envoye"])

    def test_non_configure_erreur_propre(self):
        self.client.login(
            username="admin", password=DUMMY_PASSWORD, facility=self.ecole
        )
        with mock.patch.dict(
            "os.environ",
            {"KALANFA_WHATSAPP_TOKEN": "", "KALANFA_WHATSAPP_PHONE_ID": ""},
        ):
            reponse = self.client.post(
                self.url,
                {"telephone": "22376000000", "texte": "x"},
                format="json",
            )
        self.assertEqual(reponse.status_code, 502)
