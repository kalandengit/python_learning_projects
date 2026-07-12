# PROJET_SCHOOL_MOUMA_BKO_2026

Plateforme de gestion scolaire pour l'**École MOUMA** (Bamako, 2026) — cycles
**Montessori** (maternelle) et **Collège**. Construite avec **Django 5**,
rendu côté serveur, pensée pour une connexion à faible débit.

> État actuel : **Milestone 1 — initialisation du projet**. Le squelette,
> l'authentification, le tableau de bord et l'outillage sont en place. Les
> modules métier (inscriptions, notes/bulletins, Montessori, frais) arrivent
> aux milestones suivants.

## Fonctionnalités prévues

| Module | Description |
|--------|-------------|
| Inscriptions | Fiches de renseignement élèves / parents |
| Notes & bulletins | Saisie des notes, moyennes, rang, bulletin PDF |
| Montessori | Observations, domaines, suivi des acquis |
| Frais de scolarité | Échéanciers, reçus, impayés |
| Personnel | Fiches de poste, rôles |

## Pile technique

- **Backend** : Django 5 (admin, auth, ORM, i18n français)
- **Base de données** : SQLite (dev) → PostgreSQL (prod)
- **Frontend** : gabarits Django + CSS léger (sans dépendance JS lourde)
- **PDF** : WeasyPrint
- **Déploiement** : Docker + Gunicorn + PostgreSQL

## Démarrage rapide (développement)

```bash
cd school_mouma
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # puis générez une clé secrète
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- Application : http://127.0.0.1:8000/
- Administration : http://127.0.0.1:8000/admin/

### Générer une clé secrète

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Tests

```bash
pytest
```

## Déploiement (production)

```bash
cp .env.example .env          # renseignez SECRET_KEY, ALLOWED_HOSTS, POSTGRES_PASSWORD
docker compose up --build -d
```

La configuration de production force HTTPS, sécurise les cookies et exige
`DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` et `DATABASE_URL`.

## Organisation du code

```
school_mouma/
├── config/            # projet Django (settings dev/prod, urls, wsgi)
├── apps/
│   └── core/          # base commune : mixins, tableau de bord
├── templates/         # gabarits partagés (base, connexion)
├── static/            # CSS / actifs
├── locale/            # traductions
└── tests/             # tests pytest
```

## Sécurité

Sécurisé par défaut : protection CSRF/XSS de Django, mots de passe hachés,
séparation des rôles, secrets en variables d'environnement, durcissement
HTTPS/HSTS en production. Ne jamais committer le fichier `.env`.
