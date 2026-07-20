# Kalanfa

**Kalanfa** est la plateforme d'apprentissage **hors-ligne d'abord** du
**PROJET_SCHOOL_MOUMA_BKO_2026** (École MOUMA, Bamako) : enseigner et
apprendre avec la technologie, même sans connexion Internet fiable.

Kalanfa est un fork rebaptisé de la [plateforme Kolibri](https://github.com/learningequality/kolibri)
de [Learning Equality](https://learningequality.org/) (licence MIT — voir
[`LICENSE`](./LICENSE) et [`ATTRIBUTION.md`](./ATTRIBUTION.md)). Ce fork est
indépendant et n'est pas affilié à Learning Equality.

## Qu'est-ce que Kalanfa ?

Une plateforme SaaS multi-établissements pour l'éducation :

- **Hors-ligne d'abord** : fonctionne sans Internet, synchronise quand la
  connexion revient — pensée pour les réalités de Bamako et de l'Afrique de
  l'Ouest.
- **Bibliothèque de contenus** : chaînes de ressources pédagogiques
  (leçons, vidéos, exercices) distribuables par USB ou pair-à-pair.
- **Rôles** : apprenant, enseignant (coach), administrateur — avec tableaux
  de bord de suivi de progression en temps réel.
- **Établissements (facilities)** : chaque école est un espace isolé —
  la base du modèle SaaS multi-tenant.

### Feuille de route MOUMA

Modules de gestion scolaire à venir par-dessus la plateforme :
inscriptions (fiches de renseignement), notes & bulletins PDF, suivi
Montessori (observations, domaines), frais de scolarité, fiches de poste.

## Démarrage (développement)

```bash
# Environnement Python (3.9 - 3.13)
python -m venv .venv && source .venv/bin/activate
pip install -e .

# Lancer le serveur
kalanfa start --foreground
```

Le frontend se construit avec Node.js + pnpm (`pnpm install && pnpm build`).
Voir `docs/` pour l'architecture détaillée.

## Licence

MIT — © 2021 Learning Equality et autres contributeurs (projet d'origine),
adaptations Kalanfa pour le PROJET_SCHOOL_MOUMA_BKO_2026.
