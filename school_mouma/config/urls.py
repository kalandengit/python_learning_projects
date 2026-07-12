"""Routage racine - PROJET_SCHOOL_MOUMA_BKO_2026."""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "connexion/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("apps.core.urls")),
]

# Personnalisation de l'en-tête de l'admin Django.
admin.site.site_header = "Administration — École MOUMA (BKO 2026)"
admin.site.site_title = "École MOUMA"
admin.site.index_title = "Gestion de l'établissement"
