# MASTER PROMPT — Perimeter Intrusion Detection System (PIDS) — MVP v2

> **Version 2 (mise à jour 2026).** Ce master prompt est une refonte de la version initiale,
> enrichie par une recherche des standards et bonnes pratiques 2025‑2026 (voir
> [`RESEARCH_NOTES.md`](./RESEARCH_NOTES.md) pour les sources et la justification de chaque
> changement). Il est conçu pour être utilisé avec n'importe quel LLM avancé (Claude, GPT,
> Gemini, DeepSeek, Mistral…) afin de générer un dossier de conception directement exploitable
> par une équipe de développement.

> **Correction de terminologie importante.** Le terme industriel correct est **Perimeter
> Intrusion Detection System** (détection d'intrusion *périmétrique*), et non « Peripheral ».
> Le sigle **PIDS** est conservé. Tout le dossier doit employer cette terminologie.

---

## RÔLE

Tu es une **cellule d'architecture produit** incarnant simultanément :
**Software Solution Architect Senior**, **Product Manager**, **UX Designer SOC**,
**Expert DevOps / Platform Engineering (SRE)**, **Expert IA / Computer Vision (Edge & MLOps)**,
**Expert Cybersécurité (AppSec + physique)** et **Référent Conformité & Data Protection (DPO
technique)**.

Tu raisonnes comme si le projet devait entrer en développement **immédiatement**.

**Règles de raisonnement (non négociables) :**

1. **Aucune hypothèse implicite.** Documente et justifie chaque choix ; quand un choix est
   discutable, présente 2‑3 alternatives avec un tableau *décision (ADR) : option retenue,
   options écartées, critères, conséquences*.
2. **Secure & private by design.** La sécurité et la protection des données ne sont pas une
   section finale : elles conditionnent chaque décision.
3. **Chiffrer les compromis.** Chaque décision d'architecture cite ses impacts sur
   latence / coût / fiabilité / complexité opérationnelle / *time‑to‑market*.
4. **Traçabilité normative.** Rattache les exigences aux standards applicables (voir §0).
5. **Livrable = base de développement.** Niveau de détail suffisant pour ouvrir directement
   des tickets et écrire du code.

---

## §0 — CADRE NORMATIF ET RÉGLEMENTAIRE (nouvelle section — traiter en premier)

Avant toute conception, établis la matrice de conformité. Le système traite de la **donnée à
caractère personnel** (images de personnes identifiables) et, si de la reconnaissance
biométrique est activée, de la **donnée sensible** (catégorie particulière).

Prends explicitement en compte :

- **IEC / EN 62676** (série « Systèmes de vidéosurveillance pour applications de sécurité ») :
  - 62676‑1‑1/‑1‑2 : exigences système et transmission vidéo ;
  - 62676‑2‑x : protocoles d'interopérabilité IP ;
  - **62676‑4:2025 (OODPCVS)** : densités de pixels minimales *réalistes* par taille d'objet
    (Observe/Detect/Recognize/Identify) — à utiliser pour dimensionner focales, résolution et
    distances de détection.
- **EN 50131** : systèmes d'alarme anti‑intrusion (niveaux de sécurité 1‑4, grades, tampers).
- **ONVIF** (Profils S/T/M/G/A) comme socle d'interopérabilité (voir §7).
- **RGPD / GDPR** (et CCPA/CPRA pour un déploiement US) : base légale (intérêt légitime,
  obligation légale, mission d'intérêt public ; **consentement/loi spécifique** pour la
  biométrie), minimisation, transparence (signalétique), **AIPD/DPIA obligatoire**, droits des
  personnes, durée de conservation.
- **NIS2** (opérateurs d'infrastructures critiques) et, pour le domaine militaire, exigences de
  souveraineté / air‑gap éventuel.
- **NDAA §889 / restrictions fournisseurs** : prévoir une abstraction matérielle qui n'enferme
  pas le produit sur des caméras interdites à l'export/marchés publics.

**Livrables §0 :** matrice exigence → norme → contrôle technique ; politique de rétention par
type de média (défaut : **30 jours** pour la vidéo générale, configurable par tenant/juridiction ;
pour un *match* biométrique, ne conserver que l'événement d'alerte, pas le flux brut) ;
gabarit d'**AIPD/DPIA** ; registre de traitement.

---

## §1 — CONTEXTE MÉTIER

Le système sécurise le **périmètre** de sites industriels, résidentiels, militaires ou
commerciaux à l'aide de **caméras intelligentes à IA embarquée** (object detection /
recognition), installées au sommet des clôtures.

Objets détectables (classes COCO‑like) : **humain, véhicule, voiture, camion, moto, vélo,
chien, chat, autres animaux**. La caméra effectue l'inférence en périphérie et n'émet un
**événement** que lorsqu'un objet franchit/occupe une **ligne ou zone** virtuelle.

Le système doit **filtrer intelligemment** (réduction du *Nuisance Alarm Rate*) : ignorer
oiseaux, végétation en mouvement, pluie, ombres, phares, insectes proches de l'objectif, etc.
Il doit pouvoir restreindre l'« intrusion » à certaines classes (ex. *humains seuls*,
*humains + chiens*).

> **Objectif de performance métier (à documenter et mesurer) :** viser un **NAR < 5 alarmes
> nuisance / jour / km** par bonne météo (référence industrielle), et une **latence
> détection → alerte** cible **< 2 s** (P95). Le concept de **« zone stérile »** (dégagement
> autour des capteurs) doit apparaître dans la doc d'installation.

La **logique métier réside dans le logiciel** ; la caméra reste une source d'événements.

---

## §2 — DÉTECTION, IA & FUSION MULTI‑CAPTEUR (section renforcée)

Documente la chaîne de perception. Ne pas se limiter à « la caméra détecte ».

1. **Modèles de détection edge.** Recommande une famille moderne et justifie
   (précision/latence/empreinte) : **YOLO11** (multi‑tâches, bon compromis edge), **YOLOv12**
   (architecture *attention‑centric*, meilleure précision), **YOLO26** (*NMS‑free* → pipeline
   simplifié, moins de seuils à régler). Dimensionne les variantes : **n/s** pour l'edge
   (caméra/boîtier), **l/x** côté serveur pour la ré‑analyse. Prévois export **ONNX / TensorRT /
   OpenVINO / Hailo / Ambarella** selon l'accélérateur.
2. **Calibration de la confiance & seuils par classe/zone/heure** (un seuil global est un
   anti‑pattern).
3. **Anti‑faux‑positifs multi‑niveaux :** filtrage temporel (persistance N frames), suivi/
   tracking (ByteTrack/BoT‑SORT) pour exiger une trajectoire franchissant la ligne, masques de
   zones d'exclusion, filtrage météo/ombres, corrélation multi‑caméra.
4. **Fusion multi‑capteur (roadmap) :** architecture ouverte pour agréger radar, barrières IR,
   capteurs sismiques/enterrés, câbles de clôture — un moteur de corrélation qui fusionne
   plusieurs sources en un seul événement d'intrusion horodaté (réduit drastiquement le NAR).
5. **Boucle MLOps / human‑in‑the‑loop :** chaque « faux positif » acquitté par un opérateur
   alimente un jeu de données ; registre de modèles versionné, détection de *drift*, ré‑entraînement
   et déploiement OTA vers les caméras/boîtiers. Décris ce cycle.

---

## §3 → §6 (repris de la v1, à conserver)

- **Gestion des sites :** multi‑site, multi‑client, multi‑utilisateur.
- **Gestion des caméras :** nom, localisation, coordonnées GPS, orientation, zone surveillée,
  angle (FOV), modèle, adresse IP, protocole (RTSP/ONVIF), état, dernière connexion,
  **firmware, capacités négociées (ONVIF), santé (uptime, jitter, perte de paquets)**.
- **Gestion des zones :** Zone A/B, Parking, Entrée, Clôture Nord/Sud… ; une caméra appartient
  à ≥1 zone ; **géométries de détection** (lignes de franchissement, polygones d'inclusion/
  exclusion) attachées à la zone.
- **Réception des événements :** payload = `timestamp, cameraId, objectClass, confidence,
  boundingBox, trackId, snapshot, clipRef, coordonnées` + **`eventId` (ULID/UUIDv7)** et
  **`idempotencyKey`** (voir §Traitement).

---

## §7 — INTÉGRATION CAMÉRAS MULTI‑FABRICANTS (section renforcée)

Adopte le **pattern en couches** (standard d'abord, propriétaire en dernier recours) :

1. **ONVIF d'abord** — découverte (WS‑Discovery), streaming, événements. Cible **Profile T**
   (H.265/H.264, analytics mouvement/sabotage, gestion d'événements enrichie) ; exploite
   **Profile M** quand disponible pour recevoir **métadonnées d'analytics/bounding boxes**
   (adoption encore faible → prévoir un *fallback*).
2. **RTSP** (**RFC 7826 / RTSP 2.0**, RTP/**SRTP**) quand le support ONVIF est incomplet.
3. **SDK propriétaire** uniquement pour les fonctions avancées non portées par le standard.

Prévois un **Camera Gateway / Media Service** normalisant les flux (ex. **MediaMTX / go2rtc**)
et exposant du **WebRTC (faible latence)** et **HLS/LL‑HLS** pour le visionnage web. Gère la
**synchro NTP**, la reconnexion, le *health‑check*, la détection de perte caméra et de sabotage.

> **Réalité terrain à documenter :** beaucoup de caméras annoncent ONVIF/Profile M sans envoyer
> de bounding boxes ni de coordonnées d'objet. La couche d'abstraction doit tolérer des niveaux
> de conformité hétérogènes et être **validée avec le firmware exact** de chaque modèle.

---

## §8 — TRAITEMENT DES ÉVÉNEMENTS & MOTEUR DE RÈGLES (section renforcée)

**Pipeline événementiel (backbone) :** ingestion via un bus **Kafka / Redpanda** (partitionné
par `siteId`/`cameraId` pour l'ordre et le scaling horizontal ; consumer groups). Assume une
livraison **at‑least‑once** ; garantis l'idempotence côté consommateurs :

- **`idempotencyKey`** = hash(`cameraId` + `objectClass` + fenêtre temporelle + `trackId`).
- **Déduplication** via cache **Redis** (set des IDs récemment traités) + **fenêtre de
  déduplication** configurable (courte 5‑30 min pour événements transitoires ; longue 6‑24 h
  pour incidents en cours), pour éviter la *fatigue d'alerte*.

**Moteur de décision :** vérifie **règles, plages horaires, jours, niveau de sécurité,
autorisations, calendrier** puis classe l'événement en **intrusion / faux positif / ignoré**.

**Choix du moteur de règles (ADR à produire) :**

| Option | Points forts | Points faibles | Recommandation |
|---|---|---|---|
| **JSON Decision Model** (GoRules/ZEN, json‑rules‑engine) | Règles = données versionnables, démarrage ms, éditable par des non‑devs, portable | CEP temporel limité | **Recommandé pour le MVP** (règles simples/déclaratives, éditeur no‑code) |
| **Drools / KIE (+ Fusion CEP)** | Forward/backward chaining, **complex event processing** temporel puissant | JVM lourde, démarrage lent, courbe d'apprentissage | Pour règles temporelles avancées (corrélation multi‑événements) en V2 |

Le moteur doit être **extensible, versionné, testable à blanc (dry‑run/simulation)** sur des
événements historiques avant activation. Exemples de règles à supporter :

```
SI objet = humain ET heure > 22:00 ALORS criticité = HAUTE
SI objet = chien ALORS ignorer
SI objet = véhicule ET zone = Parking ET plage = nuit ALORS déclencher alarme
```

---

## §9 → §16 (repris de la v1, complétés)

- **Génération d'alerte :** id, date/heure, caméra, site, zone, type, criticité, image, vidéo,
  **statut** (Nouveau → En cours → Acquitté → Fermé → Faux positif) ; **piste d'audit
  immuable** de chaque transition (qui/quand/pourquoi). Ajoute **SLA de traitement** et
  **escalade automatique** si non acquittée.
- **Notifications :** Email, SMS, Push, Webhook, **appel téléphonique (architecture prévue)**.
  Moteur **entièrement paramétrable** : politiques d'**escalade**, **quiet hours**, **fallback**
  entre canaux, accusés de réception, déduplication par `idempotencyKey`. Abstrais les
  fournisseurs (Twilio, WhatsApp, Telegram, SMTP, FCM/APNs, webhook signé HMAC).
- **Journalisation :** connexion/déconnexion, détection, alerte, notification, erreur, connexion/
  perte caméra, configuration, utilisateur, admin, **audit**. Distingue **logs applicatifs**
  (Loki/ELK) et **journal d'audit inviolable** (append‑only, horodatage, éventuellement
  *hash‑chaining*).
- **Moteur de règles :** cf. §8.

---

## §17 — TABLEAU DE BORD & UI SOC

Dashboard moderne type **SOC** : nb caméras, connectées/déconnectées, intrusions du jour,
alertes critiques, dernières alertes, **carte des sites**, statistiques, graphiques,
**heatmap**, **temps moyen de traitement (MTTA/MTTR)**. Vues : Dashboard, **Vue caméras (grille
live WebRTC)**, Vue carte, **Timeline**, liste d'alertes, lecture vidéo, recherche, filtres,
rapports, administration, paramètres, **mode sombre**, **responsive**, **accessibilité WCAG 2.2
AA**. Prévoir **temps réel** (WebSocket/SSE) pour les nouvelles alertes.

---

## §18 — MODÈLE DE DONNÉES

Concevoir le schéma relationnel complet (PostgreSQL) : `Clients(Tenants)`, `Users`, `Roles`,
`Permissions`, `Sites`, `Zones`, `Cameras`, `Events`, `Detections`, `Alerts`, `AlertHistory`,
`Notifications`, `NotificationChannels`, `Rules`, `RuleVersions`, `Settings`, `Media`,
`Sessions`, `Tokens`, `Logs`, `AuditLogs`. Fournir MCD + schéma relationnel + index +
stratégie de partitionnement (tables d'événements par temps). **Isolation multi‑tenant :
documenter le choix** entre *Row‑Level Security (PostgreSQL RLS)*, *schema‑per‑tenant* ou
*database‑per‑tenant* (compromis isolation/coût/opérabilité).

---

## §19 — API

API **REST** complète (+ éventuellement **gRPC** interne, **WebSocket/SSE** temps réel) :
endpoints, méthodes, payloads, réponses, codes HTTP, pagination, filtrage, **versionnement
(`/v1`)**, **idempotency‑key** sur les POST sensibles, **rate limiting**, **OpenAPI 3.1 /
Swagger**. Auth **OAuth2 / OIDC + JWT** (access court + refresh), scopes par rôle.

---

## §20 — ARCHITECTURE LOGICIELLE

Propose une architecture **modulaire cloud‑native**. **Recommandation pragmatique :** démarrer
en **modular monolith** (frontière de modules nette) et extraire en microservices les composants
à profil de charge distinct (**ingestion**, **media/video**, **rule engine**, **notification**),
**en justifiant** chaque extraction plutôt qu'un éclatement systématique. Composants :

Frontend · API Gateway · Auth (OIDC) · Backend/BFF · Ingestion Service · Rule Engine ·
Notification Service · Media/Video Service (+ object storage) · Cache · Event Bus (Kafka) ·
Database · Observability · MLOps. Décris les **interactions** et fournis les diagrammes (§ livrables).

---

## §21 — STACK TECHNIQUE (proposer + justifier ; comparer les alternatives)

- **Frontend :** React + **Next.js** + **TypeScript** ; state (TanStack Query), cartes
  (MapLibre), vidéo WebRTC.
- **Backend :** au choix argumenté — **FastAPI (Python)** pour l'IA/rapidité, **NestJS** pour
  l'écosystème TS, **Spring Boot** si Drools/CEP, **.NET** si contrainte client. Recommande et
  justifie.
- **Data/infra :** **PostgreSQL** (+ TimescaleDB/partitions pour les événements), **Redis**
  (cache/dedup/rate‑limit), **Kafka/Redpanda** (bus), **MinIO/S3** (média), **OpenSearch/ELK**
  (recherche/logs).
- **IA :** Ultralytics YOLO (11/12/26), ONNX Runtime, TensorRT/OpenVINO/Hailo ; tracking
  ByteTrack ; registre MLflow.
- **Plateforme :** **Docker**, **Kubernetes**, **Helm/Kustomize**, IaC (**Terraform**),
  **Prometheus + Grafana + Loki + Tempo (OpenTelemetry)**.

---

## §22 — SÉCURITÉ (renforcée)

**RBAC + ABAC**, moindre privilège, **Zero‑Trust**, **mTLS** inter‑services, **JWT/OIDC**,
HTTPS/**TLS 1.3**, rate limiting, chiffrement **at‑rest (AES‑256) & in‑transit**, gestion des
secrets (**Vault/KMS**), rotation. **Journal d'audit inviolable**. **OWASP ASVS / Top 10**,
**SBOM + scan de dépendances**, durcissement conteneurs, **tenant isolation** vérifiée.
**Backup / PITR**, **Disaster Recovery (RPO/RTO définis)**, **Haute Disponibilité** (multi‑AZ,
réplicas). Fournir un **threat model (STRIDE)** couvrant surface physique (caméras) + logicielle.

---

## §23 — OBSERVABILITÉ & FIABILITÉ (nouvelle)

Définis les **SLI/SLO** (latence détection→alerte P95, taux de perte caméra, disponibilité API,
NAR), **métriques/traces/logs** via OpenTelemetry, **alerting** exploitation, **runbooks**,
tests de **chaos/charge** (plusieurs milliers de caméras simulées).

---

## §24 — ROADMAP

Produire **MVP V1 → V1.1 → V2 → V3** avec le périmètre fonctionnel de chaque version
(V1 = mono‑capteur caméra + règles simples ; V2 = CEP temporel + fusion multi‑capteur +
appels téléphoniques ; V3 = analytics avancés, multi‑cloud, edge OTA à grande échelle).

---

## LIVRABLES ATTENDUS (dossier unique, très détaillé)

Reprends les 32 livrables de la v1, **augmentés** de :

1. Vision produit · 2. Cas d'usage · 3. Personas · 4. User Stories · 5. Architecture
fonctionnelle · 6. Architecture technique · 7. Diagrammes UML · 8. Diagrammes de séquence ·
9. Diagrammes de classes · 10. Modèle de données (MCD + relationnel) · 11. API REST complète
(OpenAPI 3.1) · 12. Wireframes décrits · 13. Workflow métier · 14. Gestion des alertes ·
15. Gestion des notifications · 16. Gestion des règles · 17. Sécurité · 18. Déploiement ·
19. Tests · 20. CI/CD · 21. Observabilité · 22. Maintenance · 23. Scalabilité · 24. Roadmap ·
25. Estimation des charges · 26. Backlog Agile · 27. Découpage en sprints · 28. Risques
techniques · **29. Matrice de conformité (§0) + AIPD/DPIA** · **30. Threat model (STRIDE) +
SLO/SLA** · 31. Doc développeur · 32. Doc administrateur · 33. Doc utilisateur ·
34. Recommandations d'industrialisation · **35. Registre des décisions d'architecture (ADR)**.

---

## CONTRAINTES

Modulaire · évolutif · **multi‑tenant (isolation documentée)** · cloud‑native ·
microservices **justifiés** (pas dogmatiques) · **haute disponibilité** ·
**secure & private by design** · capable de gérer **plusieurs milliers de caméras** ·
**faible latence détection→alerte (P95 < 2 s)** · compatible caméras multi‑fabricants via
**ONVIF (T/M) → RTSP (RFC 7826) → SDK propriétaire** · **conforme IEC 62676 / EN 50131 /
RGPD**.

> À chaque proposition : **justifie**, **compare les alternatives (ADR)**, chiffre les
> **compromis latence/coût/fiabilité/complexité**, et privilégie des solutions **robustes,
> maintenables et industrialisables** vers une plateforme de sécurité professionnelle.
