"""Vues de l'application core - PROJET_SCHOOL_MOUMA_BKO_2026."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def tableau_de_bord(request):
    """Page d'accueil / tableau de bord après connexion.

    Les cartes des modules seront alimentées au fil des milestones
    (inscriptions, notes, Montessori, frais).
    """
    contexte = {
        "titre": "Tableau de bord",
        "modules": [
            {
                "nom": "Inscriptions",
                "description": "Fiches de renseignement des élèves.",
                "disponible": False,
            },
            {
                "nom": "Notes & bulletins",
                "description": "Saisie des notes et génération des bulletins.",
                "disponible": False,
            },
            {
                "nom": "Montessori",
                "description": "Observations et suivi des acquis.",
                "disponible": False,
            },
            {
                "nom": "Frais de scolarité",
                "description": "Échéanciers, reçus et impayés.",
                "disponible": False,
            },
        ],
    }
    return render(request, "core/tableau_de_bord.html", contexte)
