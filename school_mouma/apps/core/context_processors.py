"""Processeurs de contexte - PROJET_SCHOOL_MOUMA_BKO_2026."""
from django.conf import settings


def ecole(request):
    """Expose l'identité de l'établissement à tous les gabarits."""
    return {"ECOLE": settings.ECOLE}
