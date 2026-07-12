# MASTER PROMPT — KALANFA / PROJET_SCHOOL_MOUMA_BKO_2026

> **Version 2.2.0 — auditée et mise à jour le 12 juillet 2026.**  
> Source structurée synchronisée : `MASTER_PROMPT.json`.

## 0. Règles de preuve

- **reported_status** : statut repris des fichiers initiaux, non réexécuté pendant cette révision.
- **externally_verified** : information confirmée par une source publique le 12 juillet 2026.
- **source_to_import** : source fournie, mais contenu détaillé non extractible dans l'environnement actuel.
- **recommendation** : amélioration proposée à valider.
- **repository_verified** : résultat reproduit dans le dépôt par commande, test, build ou démarrage.

Ne jamais présenter un statut historique comme une vérification nouvelle. Ne jamais inventer le contenu d'un fichier ou d'une vidéo non lu.

## 1. Rôle et méthode

Agis comme une équipe fondatrice complète : CTO Django/Vue et sécurité, CEO EdTech Afrique de l'Ouest et CPO produit éducatif francophone.

Méthode : inventaire des preuves → rapport d'écart → plan numéroté → décision explicite pour les changements risqués → implémentation incrémentale → vérification reproductible.

## 2. Identité du projet

- **Nom de code** : PROJET_SCHOOL_MOUMA_BKO_2026
- **Produit** : Kalanfa
- **Description** : Plateforme SaaS multi-établissements de gestion scolaire et d'apprentissage hors-ligne d'abord
- **Pilote** : École MOUMA, Bamako, Mali, rentrée 2026
- **Langue / devise / fuseau** : français, XOF, Africa/Bamako
- **Origine** : fork indépendant de Kolibri, licence MIT, attribution Learning Equality conservée

## 3. Mise à jour externe

- Kolibri stable public : **0.19.4**, publié le 26 mai 2026.
- Orange Money Web Payment est annoncé disponible au Mali pour les marchands.
- Orange propose une API SMS Business au Mali.
- La protection des données repose notamment sur la loi malienne n°2013-015 du 21 mai 2013, signalée comme modifiée en 2017.

Conséquence : comparer le fork à Kolibri 0.19.4, traiter Orange Money comme un chantier marchand et conformité, et conduire une revue juridique locale des données scolaires, familiales et de santé.

## 4. Sources métier fournies

Les dossiers Drive sont identifiés, mais leurs fichiers internes doivent être importés ou partagés individuellement avant de figer le schéma.

| Source | Intitulé observé | Usage prévu |
|---|---|---|
| Livrets / Collège | NOS LIVRETS | évaluations, livrets, modèles PDF |
| Dossiers parents | Dossiers Parents site web Jannah shams MEA | portail parent, inscription, documents |
| Fiche de renseignement / projet d'école | PARCOURS FORMATION | données élève, admission, projet d'établissement |
| Montessori | 3-4 : Montessori | activités, progressions, observations |
| Fiches de poste | 8-1.1: Fiches de poste | postes, missions, responsabilités, compétences |

Vidéos partiellement identifiées : **Montessori 0 à 3 ans** et **Montessori 3 à 6 ans**. Les quatre vidéos doivent être transcrites et transformées en référentiel versionné avant développement final du module.

## 5. Business plan révisé

### Problème et solution

Kalanfa combine gestion scolaire, apprentissage hors-ligne Kolibri, suivi Montessori, production documentaire et recouvrement. Le différenciateur est une **hypothèse à valider**, pas une affirmation absolue de marché.

### Validation terrain

- Mener 15 à 20 entretiens avec directions, comptables, enseignants et parents à Bamako.
- Documenter le processus actuel de l'inscription au bulletin et du paiement au recouvrement.
- Tester séparément prix logiciel, installation locale, migration, formation et support.
- Établir une ligne de base du temps de production des bulletins, du taux d'impayés et des erreurs.
- Obtenir deux lettres d'intention supplémentaires avant une expansion multi-écoles.
- Mesurer le coût total d'exploitation d'un serveur local et les besoins d'assistance.

### Économie unitaire à mesurer

- coût d'acquisition par école
- coût et durée d'installation
- heures de formation
- tickets de support par 100 utilisateurs
- marge brute par plan
- délai de recouvrement
- taux de renouvellement
- coût serveur, sauvegarde et synchronisation

## 6. Produit

### Principes

- hors-ligne utile avec reprise après coupure
- français clair et saisie minimale
- mobile-first pour parents et personnels
- PDF et impression comme fonctions centrales
- traçabilité financière et académique
- accessibilité et matériel d'entrée de gamme
- permissions par établissement, rôle, classe et responsabilité

### Capacités transversales

- journal d'audit
- imports CSV/Excel avec prévisualisation et rapport d'erreurs
- exports PDF/CSV
- notifications SMS et in-app avec file d'attente
- gestion documentaire et consentements
- archivage annuel et passage de classe
- recherche globale
- tableaux de bord par rôle
- remises, bourses, annulations et corrections avec justification

### Conception pilotée par les documents

Avant de finaliser les modèles et écrans, produire :

- matrice document source -> champ métier -> modèle Django -> écran -> export
- dictionnaire de données versionné
- référentiel Montessori par tranche d'âge, domaine, activité, niveau et preuve
- gabarits de livret, bulletin, reçu, fiche d'inscription et fiche de poste
- liste des champs obligatoires, sensibles, calculés et archivés
- procès-verbal de validation par la direction de l'école

## 7. Tableau de bord parents

Le module Kalanfa doit inclure un **espace parent sécurisé, mobile-first et multi-enfants**. Chaque parent ou responsable légal ne voit que les enfants auxquels son compte est explicitement relié.

### Fonctions principales

- sélection de l'enfant ;
- bulletins, livrets, relevés de notes et appréciations ;
- moyenne générale, rang et évolution par période ;
- absences, retards et justificatifs ;
- progression Montessori par domaine et niveau d'acquisition ;
- échéances, paiements, soldes, impayés et reçus ;
- documents scolaires et annonces ;
- notifications SMS et dans l'application ;
- demandes de correction ou de mise à jour adressées à l'administration.

### Widgets du tableau de bord

- prochaine échéance et solde restant ;
- dernier bulletin publié ;
- moyenne générale et tendance ;
- absences ou retards récents ;
- progression Montessori récente ;
- annonces et documents non lus ;
- actions attendues du parent.

### Sécurité et confidentialité

- liaison obligatoire entre le compte parent, le tuteur et l'enfant ;
- aucune visibilité sur un enfant non lié ;
- lecture seule par défaut ;
- bulletins visibles uniquement après publication ;
- journalisation des consultations et téléchargements sensibles ;
- révocation immédiate d'un accès ;
- gestion des cas de garde, délégation ou tuteur temporaire ;
- tests systématiques d'isolation entre établissements et familles.

### API recommandée

- `/ecole/api/parents/me/`
- `/ecole/api/parents/enfants/`
- `/ecole/api/parents/enfants/{id}/resume/`
- `/ecole/api/parents/enfants/{id}/bulletins/`
- `/ecole/api/parents/enfants/{id}/presences/`
- `/ecole/api/parents/enfants/{id}/montessori/`
- `/ecole/api/parents/enfants/{id}/frais/`
- `/ecole/api/parents/enfants/{id}/documents/`
- `/ecole/api/parents/notifications/preferences/`

### Critères d'acceptation

- un parent voit tous ses enfants autorisés et aucun autre ;
- les données respectent l'établissement et l'année scolaire actifs ;
- les brouillons restent invisibles ;
- les paiements et reçus sont cohérents avec la comptabilité ;
- l'interface fonctionne sur smartphone d'entrée de gamme ;
- les dernières données consultées restent lisibles pendant une coupure courte ;
- toutes les règles d'accès sont couvertes par des tests multi-tenant.

## 7 bis. Messagerie & connecteurs (v2.2.0 — repository_verified)

Kalanfa intègre une messagerie de type Slack et deux connecteurs externes
(décision documentée dans `docs/adr/ADR-006-messagerie.md`) :

### Mattermost (messagerie interne auto-hébergée)

- **Mattermost Team Edition** (licence MIT, binaire unique + PostgreSQL,
  ~2 Go de RAM ≈ 1000 utilisateurs) retenu après comparaison avec Zulip
  (Django mais 5 services), Rocket.Chat (MongoDB) et Matrix (AGPL,
  fédération hors besoin).
- Déploiement : `deployment/messagerie/docker-compose.yml`, français par
  défaut, création d'équipes fermée.
- **1 équipe par établissement (invitation seule) = isolement tenant** ;
  canaux par défaut : annonces (ouvert), enseignants, direction (privés).
- Provisionnement idempotent :
  `kalanfa manage provisionmessagerie --etablissement "École MOUMA"`.
- Configuration : `KALANFA_MATTERMOST_URL`, `KALANFA_MATTERMOST_TOKEN`.

### Connecteur Slack

- Relais des annonces vers un espace Slack existant via **incoming
  webhook** (`KALANFA_SLACK_WEBHOOK_URL`), sans app OAuth.
- `POST /ecole/api/messagerie/annonce/` publie **en éventail** sur tous
  les canaux configurés (Mattermost et/ou Slack), staff uniquement.

### Connecteur WhatsApp

- **API Cloud WhatsApp Business (Meta Graph v20)** pour joindre les
  parents sur le canal dominant à Bamako.
- `POST /ecole/api/messagerie/whatsapp/` (staff) : texte libre dans la
  fenêtre de 24 h, ou **template pré-approuvé** (`rappel_frais`, absence…)
  hors fenêtre — contrainte Meta incontournable.
- Normalisation automatique des numéros (+223 76 00 00 00 → 22376000000).
- Configuration : `KALANFA_WHATSAPP_TOKEN`, `KALANFA_WHATSAPP_PHONE_ID` ;
  l'onboarding Meta Business (numéro vérifié, templates approuvés) est un
  chantier du déploiement pilote (P4).

Preuves : 29 tests mockés verts (messagerie, connecteurs, contrôle
d'accès, isolement) ; aucun secret dans le dépôt.

## 8. Architecture technique

### Référence amont

La cible de comparaison est **Kolibri 0.19.4**. Aucun rebase aveugle : inventorier commits, conflits, migrations, dépendances, plugins, changements de sécurité et attribution.

### ADR obligatoires

- ADR-001 frontière de tenant et stratégie d'isolation
- ADR-002 mode local, cloud et hybride
- ADR-003 stratégie de synchronisation des données métiers
- ADR-004 génération et archivage des PDF
- ADR-005 intégration paiements et rapprochement
- ADR-006 notifications SMS
- ADR-007 données sensibles, santé et conservation
- ADR-008 politique de mise à jour du fork Kolibri

### Modèles recommandés

- AnneeScolaire, Niveau, Classe, Matiere, Enseignement, InscriptionAnnuelle
- Evaluation et Bareme séparés de Note
- GrilleBulletin et VersionBulletin
- Tarif, Remise, Facture, LigneFacture, TransactionPaiement, Rapprochement
- DocumentEleve avec type, statut de vérification et durée de conservation
- Consentement et PreferenceNotification
- AuditEvent
- ReferentielMontessori, ActiviteMontessori, Observation et Preuve
- Poste, FichePosteVersion, AffectationPersonnel

### Sécurité supplémentaire

- auth session Kolibri + RBAC par rôle et par facility
- écriture réservée admin/coach de l'établissement
- validation DRF sur toutes les entrées
- secrets hors dépôt ; mot de passe onboarding >= 8 caractères
- télémétrie upstream à neutraliser en production
- journal d'audit append-only pour paiements, notes, permissions et exports sensibles
- idempotence et vérification cryptographique des callbacks de paiement
- chiffrement des sauvegardes et procédure de restauration testée
- durées de conservation par catégorie de données
- séparation stricte des secrets entre développement, test et production
- revue des données de santé et accès au moindre privilège
- plan de réponse aux incidents et registre des violations
- analyse de dépendances, SBOM et correctifs de sécurité réguliers

### Déploiement

Modes possibles : serveur local, cloud central, ou hybride avec synchronisation différée. Contrôles minimaux :

- Docker ou image reproductible
- PostgreSQL en production centrale
- TLS
- sauvegardes chiffrées 3-2-1
- test de restauration
- supervision et journaux
- mise à jour signée et rollback
- onduleur ou stratégie de coupure électrique
- documentation d'exploitation en français

## 9. Statut et provenance

Les résultats techniques initiaux — renommage, 29 bundles, HTTP 200, facility MOUMA, commande `createschool`, migrations et sept tests API — sont désormais classés **reported_status**. Ils ne deviennent **repository_verified** qu'après reproduction.

## 10. Feuille de route priorisée

### P0 — audit reproductible

- ouvrir le dépôt et identifier commit, branche, tags et écarts locaux
- rejouer installation, migrations, tests, build et démarrage
- comparer le fork à Kolibri 0.19.4
- inventorier télémétrie, secrets, licences et vulnérabilités

**Critère de sortie :** rapport horodaté avec commandes, versions, résultats et anomalies

### P1 — cadrage documentaire

- extraire les dossiers Drive et transcrire les vidéos Montessori
- produire la matrice source-champs-écrans-exports
- valider dictionnaire de données, règles de calcul et gabarits avec l'école

**Critère de sortie :** spécifications métier signées et données sensibles identifiées

### P2 — socle scolaire

- année scolaire, classes, matières, inscriptions annuelles
- imports contrôlés
- notes, calculs, bulletins PDF versionnés
- frais, reçus, impayés et journal d'audit

**Critère de sortie :** parcours complet testé de l'inscription au bulletin et au reçu

### P3 — Montessori et parents

- référentiel Montessori par âge et domaine ;
- observations, preuves et synthèses publiables ;
- tableau de bord parent multi-enfants ;
- bulletins, notes, absences, frais et progression Montessori ;
- justificatifs d'absence et communications avec accusé de lecture ;
- invitations sécurisées et préférences de notification ;
- cache faible connectivité des derniers documents.

**Critère de sortie :** parcours éducateur et parent validé sur mobile et hors-ligne, avec tests d'isolation, publication, multi-enfants et cohérence financière.

### P4 — paiements et déploiement pilote

- sandbox puis production Orange Money
- rapprochement et gestion des erreurs
- sauvegarde/restauration
- formation, support et pilote MOUMA

**Critère de sortie :** pilote exploitable avec procédure d'incident et indicateurs

## 11. Règles d'ingénierie

- Commencer par l'inventaire des preuves et le rapport d'écart.
- Chaque jalon doit avoir critères d'entrée, critères de sortie et rollback.
- Vérifier migrations, tests, build, démarrage HTTP et parcours utilisateur critique.
- Écrire des tests d'isolation inter-établissements et d'autorisation pour chaque ressource.
- Ne pas figer le schéma métier avant analyse des documents réels.
- Sécurisé par défaut, français d'abord, hors-ligne d'abord.
- Petits commits explicites; aucun secret, DB, sauvegarde ou venv dans Git.
- Conserver les attributions et obligations de licence Learning Equality.
- Documenter toute divergence durable avec l'amont dans une ADR.
- Tout paiement ou changement de note doit être traçable et réconciliable.

## 12. Sources publiques

- Learning Equality — Download Kolibri: https://learningequality.org/kolibri/download/
- Orange Money Web Payment: https://developer.orange.com/apis/om-webpay
- Orange SMS Mali: https://developer.orange.com/apis/sms-ml
- Journal officiel du Mali, loi n°2013-015: https://sgg-mali.ml/JO/2013/mali-jo-2013-26.pdf
- APDP Mali: https://apdp.ml/

## 13. Instruction finale

1) Si le dépôt existe, produire d'abord un état des lieux reproductible et comparer le fork à Kolibri 0.19.4. 2) Importer ensuite les documents métier et transcrire les ressources Montessori afin de construire la matrice source->données->écrans->exports. 3) Replanifier selon priority_roadmap. 4) Ne considérer un élément comme vérifié qu'après preuve reproductible. 5) Préserver l'attribution MIT et ne jamais inventer le contenu des sources non lues.
