"""Configuration de développement - PROJET_SCHOOL_MOUMA_BKO_2026."""
from .base import *  # noqa: F401,F403

DEBUG = True

# En dev on accepte les hôtes locaux même si la variable n'est pas définie.
ALLOWED_HOSTS = ALLOWED_HOSTS or ["localhost", "127.0.0.1", "[::1]"]  # noqa: F405

# Base SQLite locale (déjà définie dans base.py, rappelée ici pour clarté).
# Aucune configuration de sécurité renforcée en dev.
