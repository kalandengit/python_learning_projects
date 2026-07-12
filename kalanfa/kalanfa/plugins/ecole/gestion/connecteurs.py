"""
Connecteurs de notification externes — plugin ecole.

En complément de la messagerie interne (Mattermost, voir messagerie.py),
Kalanfa peut relayer annonces et alertes vers :

- **Slack** : via un « incoming webhook » d'un espace de travail Slack
  (aucune app OAuth requise). Configuration :
      KALANFA_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../...

- **WhatsApp** : via l'API Cloud WhatsApp Business (Meta Graph API), pour
  joindre les parents là où ils sont déjà — canal dominant à Bamako.
  Configuration :
      KALANFA_WHATSAPP_TOKEN=<jeton d'accès système Meta>
      KALANFA_WHATSAPP_PHONE_ID=<identifiant du numéro d'expéditeur>

  Contrainte Meta : hors fenêtre de 24 h après le dernier message du
  destinataire, seuls des messages « template » pré-approuvés peuvent
  être envoyés ; envoyer_texte() sert aux réponses dans la fenêtre,
  envoyer_template() aux notifications sortantes (rappels d'impayés...).

Aucun secret dans le dépôt : tout vient des variables d'environnement.
"""
import logging
import os
import re

import requests

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v20.0"


class ConnecteurError(Exception):
    """Erreur d'un connecteur de notification externe."""


def _normaliser_numero(numero):
    """Format international sans « + » (attendu par l'API WhatsApp).

    Exemple : « +223 76 00 00 00 » -> « 22376000000 ».
    """
    chiffres = re.sub(r"[^\d]", "", numero or "")
    if len(chiffres) < 8:
        raise ConnecteurError(f"Numéro de téléphone invalide : {numero!r}")
    return chiffres


class SlackConnector:
    """Publication vers un canal Slack via incoming webhook."""

    def __init__(self, webhook_url=None, timeout=10):
        self.webhook_url = webhook_url or os.environ.get(
            "KALANFA_SLACK_WEBHOOK_URL", ""
        )
        self.timeout = timeout
        if not self.webhook_url:
            raise ConnecteurError(
                "KALANFA_SLACK_WEBHOOK_URL doit être définie pour le connecteur Slack."
            )

    @classmethod
    def est_configure(cls):
        return bool(os.environ.get("KALANFA_SLACK_WEBHOOK_URL"))

    def envoyer(self, texte):
        """Envoie un message texte au canal associé au webhook."""
        if not (texte or "").strip():
            raise ConnecteurError("Le texte du message est vide.")
        try:
            reponse = requests.post(
                self.webhook_url, json={"text": texte}, timeout=self.timeout
            )
        except requests.RequestException as exc:
            raise ConnecteurError(f"Slack injoignable : {exc}") from exc
        # Les webhooks Slack répondent 200 + corps "ok"
        if reponse.status_code >= 400:
            raise ConnecteurError(
                f"Slack a refusé le message : {reponse.status_code} "
                f"{reponse.text[:200]}"
            )
        return True


class WhatsAppConnector:
    """Envoi de messages via l'API Cloud WhatsApp Business (Meta)."""

    def __init__(self, token=None, phone_id=None, timeout=10):
        self.token = token or os.environ.get("KALANFA_WHATSAPP_TOKEN", "")
        self.phone_id = phone_id or os.environ.get("KALANFA_WHATSAPP_PHONE_ID", "")
        self.timeout = timeout
        if not self.token or not self.phone_id:
            raise ConnecteurError(
                "KALANFA_WHATSAPP_TOKEN et KALANFA_WHATSAPP_PHONE_ID doivent "
                "être définies pour le connecteur WhatsApp."
            )

    @classmethod
    def est_configure(cls):
        return bool(
            os.environ.get("KALANFA_WHATSAPP_TOKEN")
            and os.environ.get("KALANFA_WHATSAPP_PHONE_ID")
        )

    def _envoyer(self, payload):
        url = f"{GRAPH_API_BASE}/{self.phone_id}/messages"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            reponse = requests.post(
                url, json=payload, headers=headers, timeout=self.timeout
            )
        except requests.RequestException as exc:
            raise ConnecteurError(f"WhatsApp injoignable : {exc}") from exc
        if reponse.status_code >= 400:
            raise ConnecteurError(
                f"WhatsApp a refusé le message : {reponse.status_code} "
                f"{reponse.text[:200]}"
            )
        return reponse.json()

    def envoyer_texte(self, numero, texte):
        """Message texte libre (fenêtre de 24 h après contact entrant)."""
        if not (texte or "").strip():
            raise ConnecteurError("Le texte du message est vide.")
        return self._envoyer(
            {
                "messaging_product": "whatsapp",
                "to": _normaliser_numero(numero),
                "type": "text",
                "text": {"body": texte},
            }
        )

    def envoyer_template(self, numero, nom_template, langue="fr", parametres=None):
        """Message template pré-approuvé (notifications sortantes)."""
        composants = []
        if parametres:
            composants.append(
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(p)} for p in parametres
                    ],
                }
            )
        return self._envoyer(
            {
                "messaging_product": "whatsapp",
                "to": _normaliser_numero(numero),
                "type": "template",
                "template": {
                    "name": nom_template,
                    "language": {"code": langue},
                    "components": composants,
                },
            }
        )
