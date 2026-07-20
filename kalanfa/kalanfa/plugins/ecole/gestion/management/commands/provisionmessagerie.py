"""
Provisionne la messagerie (Mattermost) pour un établissement.

Crée l'équipe de l'école, les canaux par défaut (annonces, enseignants,
direction) et les comptes de messagerie de tous les utilisateurs actifs de
l'établissement. Idempotent : ré-exécutable sans doublons.

Exemple :
    KALANFA_MATTERMOST_URL=https://chat.exemple.ml \
    KALANFA_MATTERMOST_TOKEN=... \
    kalanfa manage provisionmessagerie --etablissement "École MOUMA"
"""
import logging

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from kalanfa.core.auth.models import Facility
from kalanfa.core.auth.models import FacilityUser

from ...messagerie import MattermostClient
from ...messagerie import MessagerieError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Provisionne l'équipe Mattermost, les canaux par défaut et les "
        "comptes de messagerie d'un établissement."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--etablissement", required=True, help="Nom exact de l'établissement"
        )
        parser.add_argument(
            "--url", default=None, help="URL Mattermost (défaut : env)"
        )
        parser.add_argument(
            "--token", default=None, help="Jeton admin Mattermost (défaut : env)"
        )

    def handle(self, *args, **options):
        try:
            facility = Facility.objects.get(name=options["etablissement"])
        except Facility.DoesNotExist:
            raise CommandError(
                f"Établissement introuvable : {options['etablissement']}"
            )

        try:
            client = MattermostClient(
                base_url=options["url"], token=options["token"]
            )
            equipe = client.ensure_team(facility)
            client.ensure_default_channels(equipe["id"])

            crees, existants = 0, 0
            nouveaux_mots_de_passe = []
            utilisateurs = FacilityUser.objects.filter(facility=facility)
            for utilisateur in utilisateurs:
                _, mot_de_passe = client.ensure_user(utilisateur, facility)
                if mot_de_passe:
                    crees += 1
                    nouveaux_mots_de_passe.append(
                        (utilisateur.username, mot_de_passe)
                    )
                else:
                    existants += 1
        except MessagerieError as exc:
            raise CommandError(str(exc))

        self.stdout.write(
            self.style.SUCCESS(
                f"Messagerie provisionnée pour « {facility.name} » : "
                f"{crees} compte(s) créé(s), {existants} existant(s)."
            )
        )
        if nouveaux_mots_de_passe:
            self.stdout.write(
                "Mots de passe initiaux (à remettre en main propre, "
                "changement obligatoire à la première connexion) :"
            )
            for username, mdp in nouveaux_mots_de_passe:
                self.stdout.write(f"  {username}: {mdp}")
