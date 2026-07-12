"""
Modèles de base réutilisables - PROJET_SCHOOL_MOUMA_BKO_2026.

Ces classes abstraites servent de fondation aux modèles métier
ajoutés lors des prochains milestones (élèves, notes, frais...).
"""
from django.db import models


class HorodatageMixin(models.Model):
    """Ajoute des dates de création et de modification automatiques."""

    cree_le = models.DateTimeField("Créé le", auto_now_add=True)
    modifie_le = models.DateTimeField("Modifié le", auto_now=True)

    class Meta:
        abstract = True


class ModeleBase(HorodatageMixin):
    """Modèle de base commun à toutes les entités métier."""

    actif = models.BooleanField("Actif", default=True)

    class Meta:
        abstract = True
