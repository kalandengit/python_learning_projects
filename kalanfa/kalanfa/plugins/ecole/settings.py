"""
Réglages Django injectés par le plugin ecole.

Les modèles vivent dans l'app imbriquée « gestion » enregistrée ici comme
app Django ordinaire (label « ecole_gestion ») : la machinerie de plugins
Kalanfa donne aux plugins un app_label pointé qui casse les migrations des
champs relationnels, on la contourne donc pour la couche données.
"""
INSTALLED_APPS = ["kalanfa.plugins.ecole.gestion.apps.GestionConfig"]
