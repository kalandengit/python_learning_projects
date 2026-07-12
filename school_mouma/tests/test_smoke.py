"""Tests de fumée du Milestone 1 - PROJET_SCHOOL_MOUMA_BKO_2026."""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


@pytest.mark.django_db
def test_tableau_de_bord_exige_connexion(client):
    """Un visiteur anonyme est redirigé vers la page de connexion."""
    url = reverse("core:tableau_de_bord")
    reponse = client.get(url)
    assert reponse.status_code == 302
    assert reverse("login") in reponse.url


@pytest.mark.django_db
def test_tableau_de_bord_accessible_apres_connexion(client):
    """Un utilisateur connecté voit le tableau de bord."""
    User = get_user_model()
    User.objects.create_user(username="agent", password="motdepasse-solide-1")
    client.login(username="agent", password="motdepasse-solide-1")
    reponse = client.get(reverse("core:tableau_de_bord"))
    assert reponse.status_code == 200
    assert b"Tableau de bord" in reponse.content


def test_page_connexion_accessible(client):
    """La page de connexion répond sans authentification."""
    reponse = client.get(reverse("login"))
    assert reponse.status_code == 200
