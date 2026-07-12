"""Configuration de l'application core - PROJET_SCHOOL_MOUMA_BKO_2026."""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Base commune"
