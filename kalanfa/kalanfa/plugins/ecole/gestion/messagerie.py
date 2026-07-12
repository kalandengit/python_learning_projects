"""
Intégration de la messagerie instantanée (Mattermost) — plugin ecole.

Kalanfa s'appuie sur Mattermost Team Edition (licence MIT, binaire unique +
PostgreSQL, ~2 Go de RAM pour ~1000 utilisateurs) comme messagerie de type
Slack, auto-hébergeable sur le serveur local de l'école.

Principe multi-tenant : une équipe (« team ») Mattermost par établissement
(facility). Les canaux par défaut (annonces, enseignants, direction) sont
créés à l'initialisation, et les utilisateurs Kalanfa de l'établissement y
sont provisionnés.

Configuration par variables d'environnement (jamais dans le dépôt) :
  KALANFA_MATTERMOST_URL    ex. https://chat.ecole-mouma.ml
  KALANFA_MATTERMOST_TOKEN  jeton d'un compte administrateur système
"""
import logging
import os
import re
import secrets
import unicodedata

import requests

logger = logging.getLogger(__name__)

CANAUX_PAR_DEFAUT = (
    ("annonces", "Annonces"),
    ("enseignants", "Enseignants"),
    ("direction", "Direction"),
)


class MessagerieError(Exception):
    """Erreur d'intégration avec le serveur de messagerie."""


def _slug(texte, longueur_max=60):
    """Slug ASCII minuscule accepté par Mattermost (noms d'équipe/canal)."""
    texte = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()
    texte = re.sub(r"[^a-z0-9]+", "-", texte.lower()).strip("-")
    return texte[:longueur_max] or "ecole"


class MattermostClient:
    """Client minimal de l'API REST v4 de Mattermost."""

    @classmethod
    def est_configure(cls):
        return bool(
            os.environ.get("KALANFA_MATTERMOST_URL")
            and os.environ.get("KALANFA_MATTERMOST_TOKEN")
        )

    def __init__(self, base_url=None, token=None, timeout=10):
        self.base_url = (
            base_url or os.environ.get("KALANFA_MATTERMOST_URL", "")
        ).rstrip("/")
        self.token = token or os.environ.get("KALANFA_MATTERMOST_TOKEN", "")
        self.timeout = timeout
        if not self.base_url or not self.token:
            raise MessagerieError(
                "KALANFA_MATTERMOST_URL et KALANFA_MATTERMOST_TOKEN doivent "
                "être définies pour activer la messagerie."
            )

    # -- transport -----------------------------------------------------------
    def _request(self, method, path, **kwargs):
        url = f"{self.base_url}/api/v4{path}"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            reponse = requests.request(
                method, url, headers=headers, timeout=self.timeout, **kwargs
            )
        except requests.RequestException as exc:
            raise MessagerieError(f"Messagerie injoignable : {exc}") from exc
        if reponse.status_code >= 400:
            raise MessagerieError(
                f"{method} {path} -> {reponse.status_code}: {reponse.text[:200]}"
            )
        return reponse.json() if reponse.text else None

    def _get_or_none(self, path):
        try:
            return self._request("GET", path)
        except MessagerieError:
            return None

    # -- équipes (1 équipe = 1 établissement) --------------------------------
    def ensure_team(self, facility):
        """Retourne l'équipe de l'établissement, en la créant au besoin."""
        nom = _slug(facility.name)
        equipe = self._get_or_none(f"/teams/name/{nom}")
        if equipe:
            return equipe
        equipe = self._request(
            "POST",
            "/teams",
            json={
                "name": nom,
                "display_name": facility.name[:64],
                # invite seulement : l'isolement entre écoles est impératif
                "type": "I",
            },
        )
        logger.info("Équipe de messagerie créée : %s", nom)
        return equipe

    # -- canaux ---------------------------------------------------------------
    def ensure_channel(self, team_id, nom, nom_affiche, prive=False):
        canal = self._get_or_none(f"/teams/{team_id}/channels/name/{_slug(nom)}")
        if canal:
            return canal
        canal = self._request(
            "POST",
            "/channels",
            json={
                "team_id": team_id,
                "name": _slug(nom),
                "display_name": nom_affiche[:64],
                "type": "P" if prive else "O",
            },
        )
        logger.info("Canal créé : %s", nom)
        return canal

    def ensure_default_channels(self, team_id):
        return [
            self.ensure_channel(team_id, nom, affiche, prive=(nom != "annonces"))
            for nom, affiche in CANAUX_PAR_DEFAUT
        ]

    # -- utilisateurs ----------------------------------------------------------
    def ensure_user(self, facility_user, facility):
        """
        Provisionne l'utilisateur Kalanfa dans Mattermost et l'ajoute à
        l'équipe de son établissement. Retourne (user, mot_de_passe_initial) ;
        le mot de passe n'est renvoyé qu'à la création (sinon None).
        """
        username = _slug(facility_user.username, longueur_max=22)
        existant = self._get_or_none(f"/users/username/{username}")
        mot_de_passe = None
        if existant:
            utilisateur = existant
        else:
            # FacilityUser n'a pas d'email : adresse synthétique locale.
            email = f"{username}@{_slug(facility.name)}.kalanfa.local"
            mot_de_passe = secrets.token_urlsafe(12)
            utilisateur = self._request(
                "POST",
                "/users",
                json={
                    "username": username,
                    "email": email,
                    "password": mot_de_passe,
                    "first_name": (facility_user.full_name or "")[:64],
                },
            )
            logger.info("Utilisateur de messagerie créé : %s", username)
        equipe = self.ensure_team(facility)
        self._request(
            "POST",
            f"/teams/{equipe['id']}/members",
            json={"team_id": equipe["id"], "user_id": utilisateur["id"]},
        )
        return utilisateur, mot_de_passe

    # -- messages ---------------------------------------------------------------
    def post_message(self, channel_id, texte):
        return self._request(
            "POST", "/posts", json={"channel_id": channel_id, "message": texte}
        )

    def annoncer(self, facility, texte):
        """Publie une annonce dans le canal « annonces » de l'établissement."""
        equipe = self.ensure_team(facility)
        canal = self.ensure_channel(equipe["id"], "annonces", "Annonces")
        return self.post_message(canal["id"], texte)
