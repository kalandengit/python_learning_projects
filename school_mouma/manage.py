#!/usr/bin/env python
"""Utilitaire en ligne de commande de Django pour PROJET_SCHOOL_MOUMA_BKO_2026."""
import os
import sys

from dotenv import load_dotenv


def main() -> None:
    """Point d'entrée des commandes d'administration."""
    # Charge les variables de .env avant toute configuration Django.
    load_dotenv()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "Django est introuvable. Avez-vous activé l'environnement virtuel "
            "et installé les dépendances (pip install -r requirements.txt) ?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
