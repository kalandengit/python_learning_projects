# MASTER PROMPT — Perimeter Intrusion Detection System (PIDS) — MVP v3

> **Version 3 (2026).** Superset of [`MASTER_PROMPT.md`](./MASTER_PROMPT.md) (v2). v3 folds in the
> additional deliverables requested: **all diagrams & architecture**, **materials list (BOM) &
> cost-efficiency project**, **LLM selection**, and a **runnable reference implementation**. It is
> backed by a working code scaffold in this repo (`backend/`, `frontend/`, `simulator/`) and by
> `docs/` (architecture, data model, LLM selection, materials/BOM). Research + rationale:
> [`RESEARCH_NOTES.md`](./RESEARCH_NOTES.md).

> **Terminology:** **Perimeter** Intrusion Detection System (not "Peripheral"). Sigle **PIDS**.

---

## RÔLE

Tu es une **cellule d'architecture produit** : Software Solution Architect Senior · Product
Manager · UX Designer SOC · DevOps/SRE · Expert IA / Computer Vision (Edge + MLOps) ·
Cybersécurité (AppSec + physique) · DPO technique · **Responsable achats/BOM & FinOps**.

**Règles (non négociables) :** aucune hypothèse implicite (chaque choix = un ADR) ;
secure & private by design ; chiffrer les compromis (latence/coût/fiabilité/complexité) ;
traçabilité normative ; **livrable directement exploitable** (tickets + code).

---

## §0 — CADRE NORMATIF (traiter en premier)

IEC/EN 62676 (incl. **62676‑4:2025 OODPCVS** — densités de pixels par tâche
Observe/Detect/Recognize/Identify) · EN 50131 (grades 1‑4) · ONVIF Profils S/T/M · RGPD/GDPR
(CCTV = donnée perso ; biométrie = donnée sensible → **AIPD/DPIA**) · NIS2 · NDAA §889.
Politique de rétention : vidéo générale **30 j** (configurable/tenant), match biométrique =
événement seul. Produire la **matrice exigence → norme → contrôle**.

---

## §1 — CONTEXTE & OBJECTIF DE PERFORMANCE

Caméras IA en tête de clôture, inférence embarquée, n'émettent qu'un **événement** au
franchissement. Filtrage anti‑nuisance (oiseaux, végétation, pluie, ombres, phares).
Cibles mesurables : **NAR < 5 alarmes nuisance / jour / km** (bonne météo) ;
**latence détection → alerte P95 < 2 s**. Concept de **zone stérile** documenté.
La logique métier réside dans le logiciel ; la caméra reste une source d'événements.

---

## §2 — DÉTECTION, IA & FUSION

Modèles edge modernes à recommander/justifier : **YOLO11** (multi‑tâches), **YOLOv12**
(attention‑centric), **YOLO26** (NMS‑free). Variantes **n/s** edge, **l/x** serveur ; export
ONNX/TensorRT/OpenVINO/Hailo/Ambarella. Seuils de confiance **par classe/zone/heure**.
Anti‑faux‑positifs multi‑niveaux (persistance N frames, tracking ByteTrack/BoT‑SORT exigeant une
trajectoire franchissante, masques d'exclusion, corrélation multi‑caméra). **Fusion multi‑capteur
(roadmap)** : radar, IR, sismique/clôture → un événement d'intrusion agrégé. **Boucle MLOps** :
faux positifs acquittés → dataset → registre de modèles versionné → détection de drift →
ré‑entraînement → OTA.

---

## §3–§7 — SITES, CAMÉRAS, ZONES, ÉVÉNEMENTS, INTÉGRATION

Multi‑site/client/utilisateur. Caméra : nom, GPS, orientation, FOV, modèle, IP, protocole,
firmware, état, dernière connexion, santé. Zones (Parking, Clôture Nord/Sud…) avec **géométries**
(lignes de franchissement, polygones d'inclusion/exclusion) ; une caméra ∈ ≥1 zone. Événement :
`timestamp, cameraId, objectClass, confidence, bbox, trackId, snapshot, clipRef, coords, eventId
(ULID/UUIDv7), idempotencyKey`. **Intégration en couches** : **ONVIF Profile T/M → RTSP
(RFC 7826 / SRTP) → SDK propriétaire** ; passerelle média (**MediaMTX / go2rtc**) exposant
**WebRTC / LL‑HLS** ; synchro NTP, reconnexion, détection de perte/sabotage,
**store‑and‑forward** hors‑ligne. Tolérer une conformité ONVIF/Profile M hétérogène.

---

## §8 — TRAITEMENT & MOTEUR DE RÈGLES

Backbone **Kafka / Redpanda** (partition par site/caméra), livraison **at‑least‑once** →
idempotence : `idempotencyKey` + **dédup Redis** + **fenêtre de déduplication** (5‑30 min courte /
6‑24 h longue) anti‑fatigue d'alerte. Moteur de décision (règles, horaires, jours, niveau de
sécurité, autorisations) → **intrusion / faux positif / ignorer**. **ADR moteur** : **JSON
Decision Model** (GoRules/ZEN) pour le MVP vs **Drools + Fusion CEP** pour le temporel avancé (V2).
Règles **versionnées + dry‑run/simulation** sur historique avant activation.

> **Référence exécutable :** `backend/app/rule_engine.py` implémente ce JSON Decision Model
> (opérateurs, priorités, dry‑run, validation), `backend/app/dedup.py` la déduplication
> (idempotency key + fenêtre), `backend/app/pipeline.py` le flux complet
> détection→dédup→règles→alerte→notification.

---

## §9–§16 — ALERTES, NOTIFICATIONS, JOURNALISATION

Alerte : id, date/heure, caméra, site, zone, type, criticité, image, vidéo, **statut**
(NEW→IN_PROGRESS→ACKNOWLEDGED→CLOSED→FALSE_POSITIVE) + **piste d'audit immuable** par transition,
**SLA** et **escalade** si non acquittée. Notifications multi‑canal (Email, SMS, Push, Webhook
signé HMAC, **appel — architecture prévue**) : **fournisseur‑agnostique**, **politiques
d'escalade**, **quiet hours**, **fallback** inter‑canaux, accusés, dédup. Journalisation exhaustive
+ **journal d'audit inviolable** (append‑only, hash‑chaining) distinct des logs applicatifs.

---

## §17 — DASHBOARD & UI SOC

Dashboard type **SOC** : nb caméras, connectées/déconnectées, intrusions du jour, alertes
critiques, dernières alertes, carte, stats, graphiques, heatmap, **MTTA/MTTR**. Vues : Dashboard,
grille caméras live (WebRTC), carte, timeline, alertes, lecture vidéo, recherche, filtres,
rapports, admin, paramètres, **mode sombre**, **responsive**, **WCAG 2.2 AA**, temps réel
(WebSocket/SSE).

> **Référence :** `frontend/index.html` — console SOC statique (login, stats live, table
> d'alertes, acquittement, mode sombre) branchée sur l'API.

---

## §18–§19 — DONNÉES & API

Schéma relationnel complet (voir `docs/DATA_MODEL.md` : ER + DDL). Isolation multi‑tenant :
**RLS PostgreSQL** (défaut MVP) → schema/db‑per‑tenant (regulé/militaire). API **REST** (+ gRPC
interne, WebSocket/SSE) : endpoints, payloads, codes HTTP, pagination, **versionnement `/v1`**,
**idempotency‑key** sur POST sensibles, rate limiting, **OpenAPI 3.1**. Auth **OAuth2/OIDC + JWT**.

> **Référence :** `backend/app/` (FastAPI) expose auth, sites, zones, cameras, events (ingest),
> rules (+dry‑run), alerts, dashboard ; OpenAPI auto‑générée à `/docs`.

---

## §20–§23 — ARCHITECTURE, STACK, SÉCURITÉ, OBSERVABILITÉ

**Modular monolith → microservices justifiés** (ingestion, media, rule engine, notification).
Composants : Frontend · API Gateway · Auth OIDC · BFF · Ingestion · Rule Engine · Notification ·
Media (object store) · Cache · Event Bus · DB · Observability · MLOps (voir `docs/ARCHITECTURE.md`
pour **C4 contexte/conteneurs, séquence, classes, déploiement, réseau**). Stack : React/Next.js/TS ;
FastAPI (recommandé, IA) ou NestJS/Spring/.NET (justifié) ; PostgreSQL(+Timescale)/Redis/
Kafka‑Redpanda/MinIO‑S3/OpenSearch ; Docker/K8s/Helm/Terraform ; OTel + Prometheus/Grafana/Loki/
Tempo. Sécurité : **RBAC+ABAC, Zero‑Trust, mTLS, TLS 1.3, OWASP ASVS, SBOM, Vault/KMS, audit
inviolable, backup/PITR, DR (RPO/RTO), HA multi‑AZ, threat model STRIDE** (surface caméras +
logicielle). Observabilité : **SLI/SLO** (latence détection→alerte P95, perte caméra, dispo API,
NAR), runbooks, tests chaos/charge (milliers de caméras simulées).

---

## §24 — CHOIX DU LLM (couche assist, jamais dans le chemin critique)

Le LLM **résume / rédige / assiste** — il **ne décide jamais** d'une intrusion (moteur
déterministe §8). Cas d'usage : résumé d'alerte, rapport d'incident, **NL → règle** (JSON Decision
Model via structured outputs), Q&A/RAG opérateur, aide au tri des faux positifs. **Jamais** :
détection d'objets (YOLO edge) ni décision d'intrusion. Modèles (Claude 2026) :
**Haiku 4.5** ($1/$5) pour les résumés haut volume ; **Sonnet 5** ($3/$15) pour rapports &
assistant règles ; **Opus 4.8** ($5/$25) pour investigation à la demande. Coûts maîtrisés par
**prompt caching**, **Batch API (‑50 %)**, right‑sizing, **structured outputs**, adaptive thinking.
Détails et estimation de coût : `docs/LLM_SELECTION.md`.

---

## §25 — MATÉRIEL (BOM) & PROJET COÛT‑EFFICACITÉ

Produire la **liste complète des matériels** (edge : caméras IA ONVIF‑T à NPU, mâts/housings,
switch PoE+, passerelle/mini‑NVR, UPS, routeur 5G, câblage, capteurs radar/IR/clôture roadmap ;
cloud : K8s, PostgreSQL HA, Redis, Kafka, object store, OpenSearch, observabilité ; logiciels/
licences) avec **quantités par site de référence** (petit ~8 caméras / grand ~64) et **coûts
d'ordre de grandeur**. Livrer un **projet de coût‑efficacité** : CapEx edge, OpEx cloud, et les
**leviers classés** — (1) **détection edge‑first** (évite le GPU cloud par caméra), (2) **cloud
événementiel** (événements + clips, pas de flux 24×7), (3) **réduction du NAR** (fusion + tracking
+ masques), (4) LLM right‑sizé + caching + batch, (5) modular monolith, (6) cycle de vie du
stockage, (7) parc caméra mono‑tier. ⚠️ **Licence YOLO (AGPL‑3.0)** : prévoir licence enterprise
ou modèle permissif pour un produit propriétaire. Détail chiffré : `docs/MATERIALS_BOM.md`.

---

## §26 — ROADMAP

**V1** (mono‑capteur caméra + règles simples + dédup + notifications) → **V1.1** (SSO/OIDC,
rapports LLM, heatmap) → **V2** (CEP temporel + fusion multi‑capteur + appels téléphoniques + OTA
modèles) → **V3** (analytics avancés, multi‑cloud, edge à grande échelle).

---

## LIVRABLES ATTENDUS (35)

1‑28 (v1) + **29. Matrice de conformité + AIPD/DPIA** · **30. Threat model STRIDE + SLO/SLA** ·
31‑34 (docs dev/admin/user + industrialisation) · **35. Registre ADR** ·
**+ Diagrammes complets** (C4, séquence, classes, ER, déploiement, réseau) ·
**+ BOM & projet coût‑efficacité** · **+ Choix LLM** · **+ Implémentation de référence
exécutable** (backend testé, frontend SOC, simulateur caméra).

---

## CONTRAINTES

Modulaire · évolutif · **multi‑tenant (isolation documentée)** · cloud‑native · microservices
**justifiés** · HA · **secure & private by design** · **milliers de caméras** · **P95 < 2 s** ·
multi‑fabricants (**ONVIF T/M → RTSP RFC 7826 → SDK**) · conforme **IEC 62676 / EN 50131 / RGPD**.

> À chaque proposition : **justifie**, **compare (ADR)**, **chiffre les compromis**, privilégie
> robuste/maintenable/industrialisable. Fournis, quand pertinent, du **code de référence
> exécutable et testé** (cf. `backend/` : `pytest` vert, pipeline détection→alerte prouvé).
