"""
Plugin « ecole » — gestion scolaire pour PROJET_SCHOOL_MOUMA_BKO_2026.

Ajoute à Kalanfa les modules de gestion d'établissement francophone :
inscriptions (fiches de renseignement), notes & bulletins, frais de
scolarité, observations Montessori et fiches de poste — le tout isolé
par établissement (facility) pour le fonctionnement SaaS multi-écoles.
"""
from kalanfa.plugins import KalanfaPluginBase
from kalanfa.utils import translation
from kalanfa.utils.translation import gettext as _


class Ecole(KalanfaPluginBase):
    untranslated_view_urls = "api_urls"
    django_settings = "settings"

    @property
    def url_slug(self):
        return "ecole"

    def name(self, lang):
        with translation.override(lang):
            return _("School management")
