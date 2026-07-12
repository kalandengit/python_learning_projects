"""Routage de l'application core - PROJET_SCHOOL_MOUMA_BKO_2026."""
from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.tableau_de_bord, name="tableau_de_bord"),
]
