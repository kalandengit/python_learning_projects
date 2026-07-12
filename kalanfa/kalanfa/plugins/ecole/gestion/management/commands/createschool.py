"""
Commande d'intégration SaaS : créer un nouvel établissement (tenant).

Crée une Facility avec le préréglage choisi et son administrateur, en une
seule commande — c'est la porte d'entrée multi-établissements de Kalanfa.

Exemple :
    kalanfa manage createschool --nom "École MOUMA" --admin admin.mouma \
        --motdepasse "..." --preset formal
"""
import logging

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import transaction

from kalanfa.core.auth.constants.facility_presets import default
from kalanfa.core.auth.constants.facility_presets import presets
from kalanfa.core.auth.models import Facility
from kalanfa.core.auth.models import FacilityUser

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Crée un nouvel établissement (tenant SaaS) avec son administrateur."

    def add_arguments(self, parser):
        parser.add_argument(
            "--nom", required=True, help="Nom de l'établissement (ex. École MOUMA)"
        )
        parser.add_argument(
            "--admin", required=True, help="Nom d'utilisateur de l'admin d'école"
        )
        parser.add_argument(
            "--motdepasse", required=True, help="Mot de passe de l'admin d'école"
        )
        parser.add_argument(
            "--preset",
            default=default,
            choices=list(presets.keys()),
            help="Préréglage de l'établissement (formal = école classique)",
        )

    def handle(self, *args, **options):
        nom = options["nom"].strip()
        if not nom:
            raise CommandError("Le nom de l'établissement ne peut pas être vide.")
        if Facility.objects.filter(name=nom).exists():
            raise CommandError(f"Un établissement nommé « {nom} » existe déjà.")
        if len(options["motdepasse"]) < 8:
            raise CommandError("Le mot de passe doit contenir au moins 8 caractères.")

        with transaction.atomic():
            facility = Facility.objects.create(name=nom)
            facility.dataset.preset = options["preset"]
            facility.dataset.save()

            if FacilityUser.objects.filter(
                username__iexact=options["admin"], facility=facility
            ).exists():
                raise CommandError(
                    f"L'utilisateur « {options['admin']} » existe déjà dans cet établissement."
                )
            admin = FacilityUser.objects.create_user(
                username=options["admin"],
                password=options["motdepasse"],
                facility=facility,
            )
            facility.add_admin(admin)

        logger.info(
            "Établissement « %s » créé (preset %s) avec l'admin « %s ».",
            nom,
            options["preset"],
            options["admin"],
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Établissement « {nom} » créé. Admin : {options['admin']} "
                f"(id facility : {facility.id})"
            )
        )
