from django.apps import AppConfig


class GestionConfig(AppConfig):
    name = "kalanfa.plugins.ecole.gestion"
    label = "ecole_gestion"
    verbose_name = "Gestion scolaire"
    default_auto_field = "django.db.models.BigAutoField"
