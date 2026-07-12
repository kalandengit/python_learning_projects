# MASTER PROMPT — KALANFA / PROJET_SCHOOL_MOUMA_BKO_2026

> **Reverse master prompt.** Ce document reconstitue, sous forme de prompt
> directeur, la totalité du projet : vision business, plan d'affaires,
> produit, architecture technique, état d'avancement et règles
> d'ingénierie. Donné tel quel à un assistant IA (ou à une équipe), il
> permet de régénérer, poursuivre ou auditer le projet à l'identique.
> Version JSON structurée : [`MASTER_PROMPT.json`](./MASTER_PROMPT.json).

---

## 1. RÔLE À ENDOSSER

Agis comme une équipe fondatrice complète : **CTO** (architecte logiciel
senior, Django/Vue, sécurité), **CEO** (stratégie EdTech Afrique de
l'Ouest) et **CPO** (produit éducatif francophone). Travaille en
français, méthodiquement : analyse → plan numéroté → validation →
implémentation incrémentale vérifiée (tests + démarrage réel).

## 2. IDENTITÉ DU PROJET

- **Nom de code** : PROJET_SCHOOL_MOUMA_BKO_2026
- **Produit** : **Kalanfa** — plateforme SaaS multi-établissements de
  gestion scolaire et d'apprentissage **hors-ligne d'abord**
- **Origine technique** : fork rebaptisé de **Kolibri** (Learning
  Equality, licence MIT — attribution conservée dans `LICENSE` et
  `ATTRIBUTION.md` ; fork indépendant, non affilié)
- **Premier client / tenant pilote** : **École MOUMA**, Bamako, Mali
  (cycles Montessori/maternelle + Collège), rentrée 2026
- **Langue produit** : français ; **devise** : XOF (FCFA) ;
  fuseau : Africa/Bamako

## 3. BUSINESS PLAN

### 3.1 Problème
Les écoles privées d'Afrique de l'Ouest francophone gèrent inscriptions,
notes, bulletins, frais et suivi pédagogique sur papier ou tableurs :
pertes de données, impayés mal suivis, bulletins lents à produire,
aucun suivi Montessori structuré. La connectivité Internet est chère et
intermittente — les SaaS classiques « cloud-only » y échouent.

### 3.2 Solution
Une plateforme unique qui combine :
1. **Gestion d'établissement** (inscriptions, notes/bulletins avec
   moyennes pondérées et rang, frais en FCFA avec suivi des impayés,
   fiches de poste, présences) ;
2. **Apprentissage numérique hors-ligne** hérité de Kolibri
   (bibliothèque de contenus par chaînes, leçons, quiz, tableaux de bord
   enseignant, distribution par USB/pair-à-pair) ;
3. **Suivi Montessori** par observations (5 domaines, niveaux
   d'acquisition, synthèse de progression par enfant).

**Différenciateur clé** : hors-ligne d'abord + multi-tenant + modules
francophones (bulletins à la malienne) — aucun concurrent local ne
combine les trois.

### 3.3 Marché
- **Cible primaire** : écoles privées maternelle→collège au Mali
  (Bamako d'abord), puis Sénégal, Côte d'Ivoire, Burkina, Guinée, Niger.
- **Acheteur** : directeur/promoteur d'école ; **utilisateurs** :
  direction, enseignants, comptable, parents, élèves.
- **Concurrents observés** : Novacole, GestionÉcole, Wacni, Sicolo,
  Logesco, EduGest, MyScol — tous « gestion » sans plateforme
  d'apprentissage hors-ligne intégrée.

### 3.4 Modèle économique (hypothèses à valider terrain)
- **Abonnement SaaS par établissement et par an**, indexé sur
  l'effectif :
  - *Essentiel* : gestion (inscriptions, notes, bulletins, frais) —
    ~150 000 FCFA/an jusqu'à 300 élèves ;
  - *Pro* : + contenus hors-ligne & suivi Montessori —
    ~300 000 FCFA/an ;
  - *Réseau* : multi-campus, tarif négocié.
- **Services** : installation locale (serveur école hors-ligne),
  formation, migration des données, personnalisation des bulletins.
- **Encaissement** : Orange Money / Moov / virement ; relances
  automatiques des impayés.

### 3.5 Go-to-market
1. Pilote École MOUMA (rentrée 2026) → étude de cas chiffrée ;
2. Bouche-à-oreille des promoteurs d'écoles + associations d'écoles
   privées de Bamako ;
3. Démonstrations hors-ligne (la démo tourne sans Internet — argument
   massue) ;
4. Partenariats : fournisseurs de contenus pédagogiques francophones,
   programmes ministériels de numérisation.

### 3.6 Risques principaux
| Risque | Mitigation |
|---|---|
| Connectivité/électricité | hors-ligne d'abord, serveur local basse conso, sync différée |
| Capacité à payer | tarifs FCFA par palier, facturation à la rentrée |
| Maintenance du fork Kolibri | vendoring discipliné, périmètre de divergence documenté |
| Adoption enseignants | UI simple en français, formation incluse, saisie minimale |
| Réglementation données élèves | minimisation, chiffrement, hébergement local possible |

### 3.7 KPIs
Écoles actives, élèves gérés, taux de bulletins générés dans les délais,
taux de recouvrement des frais, rétention annuelle des écoles, NPS
directeurs, sessions d'apprentissage hors-ligne par élève.

## 4. PRODUIT & APPLICATION

### 4.1 Rôles
`super-admin plateforme` (nous), `admin établissement` (direction),
`coach/enseignant`, `apprenant/élève`, `parent` (portail lecture :
bulletins, frais, progression).

### 4.2 Modules
1. **Inscriptions** — fiche de renseignement complète : état civil,
   sexe, naissance, nationalité, adresse, santé (groupe sanguin,
   allergies, contact d'urgence), scolarité antérieure et documents,
   statut boursier/réduction ; tuteurs (père/mère/tuteur, profession,
   contacts) liés aux dossiers.
2. **Notes & bulletins** — notes /20 par matière avec coefficients et
   périodes (trimestres) ; bulletin calculé : moyenne pondérée par
   matière, moyenne générale, **rang**, effectif ; export PDF (à venir).
3. **Frais de scolarité (FCFA)** — échéanciers par élève, paiements
   partiels avec mode (espèces, Orange Money) et référence de reçu,
   endpoint des **impayés**.
4. **Montessori** — observations datées par éducateur : domaine
   (Vie pratique, Sensoriel, Langage, Mathématiques, Culture), activité,
   niveau (Présenté → En cours → Acquis → Maîtrisé), synthèse de
   progression par enfant et par domaine.
5. **Fiches de poste** — intitulé, missions, responsabilités,
   compétences, titulaire.
6. **Présences** — app `attendance` héritée du cœur (sessions d'appel
   par classe, registres).
7. **Apprentissage** — tout Kolibri : chaînes de contenus, leçons,
   quiz/examens, rapports coach, sync pair-à-pair.

### 4.3 Architecture technique
- **Base** : fork Kolibri renommé — Python/Django 3.2 + DRF + morango
  (sync) + Vue 2 (frontend, monorepo pnpm), SQLite par défaut,
  PostgreSQL possible.
- **Multi-tenant** : la **Facility** Kolibri = l'établissement. Plugin
  `kalanfa.plugins.ecole` : chaque queryset API est filtré sur la
  facility de l'utilisateur ; la création force la facility du
  demandeur ; accès inter-écoles → 404. Commande d'onboarding :
  `kalanfa manage createschool --nom … --admin … --motdepasse … --preset formal`.
- **Structure du plugin** : coquille plugin (URLs API sous
  `/ecole/api/`, namespace `kalanfa:kalanfa.plugins.ecole`) + app
  Django ordinaire imbriquée `gestion` (label `ecole_gestion`) portant
  modèles/migrations/commandes/tests.
- **Modèles** (UUID pk, FK facility, horodatage) : DossierEleve,
  Tuteur, DossierTuteur (jonction), Periode, Note, EcheanceFrais,
  Paiement, ObservationMontessori, FichePoste.
- **Endpoints spéciaux** : `notes/bulletin/?eleve=&periode=`,
  `frais/impayes/`, `observations/progression/?enfant=`.

### 4.4 Pièges connus (indispensables pour reproduire)
1. **Version** : setuptools-scm exige un tag git — installer avec
   `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_KALANFA=0.1.0 pip install -e . --no-deps`,
   dépendances = groupe `base` du `pyproject.toml`.
2. **Renommage total kolibri→kalanfa** : ~930 chemins + ~3 078 fichiers
   textes, toutes casses ; préserver `LICENSE`, `ATTRIBUTION.md`,
   `UPSTREAM_KOLIBRI_*` (attribution MIT).
3. **Paquets npm externes** : `kolibri-constants` et
   `kolibri-design-system` n'existent pas sous le nom kalanfa —
   alias pnpm `kalanfa-x: npm:kolibri-x@version` dans le catalog ;
   packageExtension injectant `browserslist-config-kolibri` dans KDS.
4. **Labels d'app pointés** : la machinerie de plugins Kalanfa donne
   `app_label = chemin.du.module`, ce qui casse les migrations des
   champs relationnels → mettre les modèles dans une app Django
   ordinaire enregistrée via le module `settings` du plugin ; pas de
   ManyToManyField automatique (jonction explicite).
5. **Build frontend** : `pnpm build` doit tourner avec le venv Python
   actif (la découverte des plugins shelle vers `python`).
6. **Usernames** : lettres/chiffres/underscores uniquement (pas de
   points).

### 4.5 Sécurité
Auth session Kolibri + RBAC par rôle et par facility ; écriture réservée
admin/coach de l'établissement ; validation DRF ; secrets hors dépôt ;
mots de passe ≥ 8 caractères à l'onboarding ; télémétrie upstream à
neutraliser en production.

## 5. ÉTAT D'AVANCEMENT (2026-07-12)

**Fait et vérifié** (branche `claude/school-management-clone-uicab0`) :
fork vendorisé + renommage intégral ; build frontend 29 bundles sans
erreur ; serveur démarré (page de connexion française, HTTP 200) ;
device provisionné avec la facility « École MOUMA » (preset formal,
fr-fr) ; commande `createschool` opérationnelle (2e école test créée) ;
plugin `ecole` complet avec migrations appliquées et **7 tests API
verts** (isolement multi-tenant, restrictions de rôle, calcul du
bulletin 13,8/20 rang 2) ; API en ligne (`/ecole/api/` → 403 anonyme).

**Reste à faire** : UI Vue des modules école (actuellement API-only) ;
PDF bulletins/reçus ; portail parents ; intégration Orange Money ;
import des documents réels (fiches, maquette de bulletin, fiches de
poste) pour aligner les champs ; facturation SaaS et console
super-admin ; déploiement production (Docker/VPS ou serveur local
école) ; neutralisation télémétrie ; sauvegardes.

## 6. RÈGLES D'INGÉNIERIE

1. **Planning-first** : analyser, proposer architecture + plan numéroté,
   attendre validation, puis implémenter par jalons courts.
2. **Vérifier réellement** : chaque jalon = migrations + tests + boot
   HTTP réel, pas seulement « ça compile ».
3. **Sécurisé par défaut** ; **français d'abord** ; **hors-ligne
   d'abord** (toute fonctionnalité doit dégrader proprement sans
   Internet).
4. Git : petits commits explicites ; jamais de secrets/DB/venv dans le
   dépôt ; pousser sur la branche de travail désignée.
5. Respect de la licence MIT upstream : ne jamais supprimer
   l'attribution Learning Equality.

## 7. INSTRUCTION FINALE

À partir de ce prompt : (a) si le dépôt existe, fais l'état des lieux
puis reprends la feuille de route §5 ; (b) sinon, reconstruis dans
l'ordre : fork+rebrand (§4.4), boot vérifié, multi-tenant, plugin
`ecole`, puis UI/PDF/paiements — en respectant §6 à chaque étape.
