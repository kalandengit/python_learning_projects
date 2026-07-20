# ADR-006 — Messagerie instantanée : Mattermost Team Edition

**Statut** : accepté (2026-07-12) · **Étiquette de preuve** : intégration
`repository_verified` (tests mockés) ; exploitation serveur `recommendation`
(à valider au déploiement pilote).

## Contexte

Kalanfa doit offrir une messagerie de type Slack (canaux, messages directs,
mobile) pour la direction, les enseignants et à terme les parents, en
respectant les contraintes du projet : auto-hébergeable sur un serveur
d'école à Bamako (ressources limitées, coupures), français, licence
compatible avec notre fork MIT, isolement strict entre établissements.

## Options étudiées (recherche du 2026-07-12)

| Option | Licence | Empreinte | Compatibilité |
|---|---|---|---|
| **Mattermost Team Edition** | MIT | 1 binaire Go + PostgreSQL ; ~2 Go RAM ≈ 1000 utilisateurs | API REST v4 complète, webhooks, mobile iOS/Android, français |
| Zulip | Apache 2.0 | 5 services (Django, Postgres FTS, Redis, RabbitMQ, Memcached) ; 2 Go+ minimum | Django comme nous, mais trop lourd pour un serveur d'école |
| Rocket.Chat | MIT (+ dossiers EE) | MongoDB, plus lourd | omnicanal orienté support client |
| Matrix / Element | AGPL (Synapse) | fédération complexe | protocole puissant mais hors besoin |

## Décision

**Mattermost Team Edition**, auto-hébergé à côté de Kalanfa
(`deployment/messagerie/docker-compose.yml`), français par défaut,
création d'équipes fermée.

Motifs : licence MIT identique au projet, empreinte minimale (critère
décisif pour le serveur local d'école), UX la plus proche de Slack
(adoption), API REST v4 simple pour le provisionnement.

## Architecture d'intégration

- **1 équipe Mattermost par établissement** (type « invitation seule ») —
  reflet du tenant Kalanfa ; canaux par défaut : `annonces` (ouvert),
  `enseignants`, `direction` (privés).
- **Provisionnement** : `kalanfa manage provisionmessagerie
  --etablissement "École MOUMA"` crée équipe, canaux et comptes des
  utilisateurs de l'établissement (idempotent). Les mots de passe initiaux
  sont générés aléatoirement et remis en main propre.
- **Annonces** : `POST /ecole/api/messagerie/annonce/` (staff uniquement)
  publie dans le canal `annonces` de l'école du demandeur.
- **Configuration** : `KALANFA_MATTERMOST_URL` et
  `KALANFA_MATTERMOST_TOKEN` (jeton admin) en variables d'environnement ;
  rien dans le dépôt.
- Code : `kalanfa/plugins/ecole/gestion/messagerie.py` (client API v4
  minimal sur `requests`, déjà dépendance du cœur).

## Conséquences

- (+) messagerie complète sans développement UI de chat ; mobile inclus.
- (+) même politique d'isolement que le reste du SaaS (équipe = tenant).
- (−) deuxième service à exploiter (sauvegardes, mises à jour) — couvert
  par les contrôles minimaux d'exploitation (ADR-002/§déploiement).
- (−) comptes Kalanfa et Mattermost distincts en v1 ; un SSO (OpenID
  Connect via l'édition Entreprise ou un pont de session) est une
  évolution possible, à décider dans une révision de cette ADR.
- Les 10 tests d'intégration (mockés) couvrent idempotence, slugs,
  configuration manquante et contrôle d'accès de l'endpoint d'annonce.
