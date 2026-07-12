"""Point d'entrée WSGI - PROJET_SCHOOL_MOUMA_BKO_2026."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

application = get_wsgi_application()
