"""
Configuration Django commune - PROJET_SCHOOL_MOUMA_BKO_2026.

Les réglages spécifiques à l'environnement sont dans dev.py et prod.py.
Aucun secret n'est stocké ici : tout provient des variables d'environnement.
"""
from pathlib import Path
import os

# school_mouma/config/settings/base.py -> remonte à school_mouma/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# --- Sécurité ---------------------------------------------------------------
# La clé secrète DOIT être fournie par l'environnement en production.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "insecure-dev-key-change-me")

# Surchargé dans dev.py / prod.py
DEBUG = False

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
    if h.strip()
]

# --- Applications -----------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

# Applications métier (ajoutées au fil des milestones)
LOCAL_APPS = [
    "apps.core",
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.ecole",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- Base de données (surchargée par environnement) -------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# --- Validation des mots de passe -------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalisation (français, Bamako) --------------------------------
LANGUAGE_CODE = os.environ.get("DJANGO_LANGUAGE_CODE", "fr")
TIME_ZONE = os.environ.get("DJANGO_TIME_ZONE", "Africa/Bamako")
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / "locale"]

# --- Fichiers statiques -----------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
# Le stockage manifeste compressé (WhiteNoise) est activé uniquement en
# production (prod.py) car il exige un `collectstatic` préalable.

# --- Divers -----------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_REDIRECT_URL = "core:tableau_de_bord"
LOGIN_URL = "login"
LOGOUT_REDIRECT_URL = "login"

# --- Identité de l'établissement (affichée sur les documents) ---------------
ECOLE = {
    "nom": os.environ.get("ECOLE_NOM", "École MOUMA"),
    "ville": os.environ.get("ECOLE_VILLE", "Bamako"),
    "annee": os.environ.get("ECOLE_ANNEE", "2026"),
    "devise": os.environ.get("ECOLE_DEVISE", "XOF"),
}

# --- Journalisation ---------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        }
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}
