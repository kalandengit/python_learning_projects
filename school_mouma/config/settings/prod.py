"""
Configuration de production - PROJET_SCHOOL_MOUMA_BKO_2026.

Sécurisé par défaut : HTTPS forcé, cookies sécurisés, PostgreSQL.
Toutes les valeurs sensibles proviennent des variables d'environnement.
"""
import os

import dj_database_url

from .base import *  # noqa: F401,F403

DEBUG = False

# En production, SECRET_KEY et ALLOWED_HOSTS sont obligatoires.
if SECRET_KEY == "insecure-dev-key-change-me":  # noqa: F405
    raise RuntimeError(
        "DJANGO_SECRET_KEY doit être définie en production."
    )
if not ALLOWED_HOSTS:  # noqa: F405
    raise RuntimeError(
        "DJANGO_ALLOWED_HOSTS doit être définie en production."
    )

# --- Base de données PostgreSQL --------------------------------------------
_database_url = os.environ.get("DATABASE_URL")
if not _database_url:
    raise RuntimeError("DATABASE_URL doit être définie en production.")
DATABASES = {
    "default": dj_database_url.parse(_database_url, conn_max_age=600)
}

# --- Durcissement de la sécurité -------------------------------------------
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 an
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

CSRF_TRUSTED_ORIGINS = [
    f"https://{h}" for h in ALLOWED_HOSTS  # noqa: F405
]

# --- Fichiers statiques (WhiteNoise, manifeste compressé) -------------------
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}
