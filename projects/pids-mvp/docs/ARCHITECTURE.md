# PIDS — Architecture & Diagrams (2026)

All diagrams are **Mermaid** (render on GitHub and most Markdown viewers). This document
covers the C4 context/container views, the runtime sequence, the class model, the deployment
topology, and the network/edge topology.

---

## 1. C4 — System Context

```mermaid
C4Context
  title PIDS — System Context
  Person(operator, "SOC Operator", "Monitors alerts, acks intrusions")
  Person(admin, "Administrator", "Configures sites, cameras, rules")
  Person(tech, "Field Technician", "Installs / maintains cameras")

  System(pids, "PIDS Platform", "Perimeter Intrusion Detection System (multi-tenant SaaS)")

  System_Ext(cameras, "AI Edge Cameras", "ONVIF / RTSP / vendor SDK, on-board object detection")
  System_Ext(sensors, "Aux Sensors (roadmap)", "Radar, IR beams, fence/seismic")
  System_Ext(notif, "Notification Providers", "SMTP, Twilio SMS/Voice, WhatsApp, Telegram, FCM/APNs, Webhooks")
  System_Ext(idp, "Identity Provider", "OIDC / SSO / LDAP / Active Directory")
  System_Ext(llm, "LLM API (Claude)", "Alert summaries, NL->rules, report generation")

  Rel(operator, pids, "Uses SOC UI", "HTTPS/WebSocket")
  Rel(admin, pids, "Administers", "HTTPS")
  Rel(tech, pids, "Configures cameras", "HTTPS")
  Rel(cameras, pids, "Detection events + media", "ONVIF/RTSP/HTTPS")
  Rel(sensors, pids, "Sensor events", "TCP/UDP/API")
  Rel(pids, notif, "Sends alerts", "HTTPS/SMTP")
  Rel(pids, idp, "AuthN/AuthZ", "OIDC/LDAP")
  Rel(pids, llm, "Summarize / assist", "HTTPS")
```

---

## 2. C4 — Container View

```mermaid
flowchart TB
  subgraph Client["Client tier"]
    UI["SOC Web App<br/>(Next.js + TS)"]
    Mobile["Mobile push<br/>(FCM/APNs)"]
  end

  subgraph Edge["Edge tier (per site)"]
    CAM["AI Cameras<br/>(YOLO on-board)"]
    GW["Camera / Media Gateway<br/>(MediaMTX / go2rtc)"]
  end

  subgraph Platform["Cloud platform (Kubernetes)"]
    APIGW["API Gateway<br/>(auth, rate-limit, TLS)"]
    API["Core API / BFF<br/>(FastAPI)"]
    ING["Ingestion Service<br/>(event intake + dedup)"]
    RE["Rule Engine<br/>(JSON Decision Model)"]
    NOTIF["Notification Service<br/>(provider-agnostic)"]
    MEDIA["Media Service<br/>(clips/snapshots)"]
    LLMSVC["LLM Assist Service<br/>(Claude, cached)"]
    subgraph Data["Data & messaging"]
      PG[("PostgreSQL<br/>+ Timescale")]
      REDIS[("Redis<br/>cache / dedup")]
      BUS[["Kafka / Redpanda<br/>event bus"]]
      OBJ[("MinIO / S3<br/>object store")]
      SEARCH[("OpenSearch<br/>logs / search")]
    end
    OBS["Observability<br/>(OTel, Prometheus, Grafana, Loki, Tempo)"]
  end

  CAM -->|WebRTC/RTSP| GW
  GW -->|events + media| APIGW
  UI -->|HTTPS/WS| APIGW
  APIGW --> API
  APIGW --> ING
  ING --> BUS
  BUS --> RE
  RE -->|intrusion| NOTIF
  RE --> API
  API --> PG
  ING --> REDIS
  API --> REDIS
  MEDIA --> OBJ
  GW --> MEDIA
  NOTIF --> Mobile
  API --> LLMSVC
  API --> SEARCH
  API -.metrics/traces.-> OBS
  ING -.-> OBS
  RE -.-> OBS
  NOTIF -.-> OBS
```

---

## 3. Sequence — Detection to Alert to Notification

```mermaid
sequenceDiagram
    autonumber
    participant CAM as AI Camera (edge)
    participant GW as Camera Gateway
    participant ING as Ingestion Svc
    participant RD as Redis (dedup)
    participant BUS as Kafka
    participant RE as Rule Engine
    participant DB as PostgreSQL
    participant NS as Notification Svc
    participant OP as Operator UI

    CAM->>GW: Detection (class, bbox, confidence, snapshot)
    GW->>ING: POST /events (ONVIF/webhook)
    ING->>RD: check idempotencyKey (dedup window)
    alt duplicate within window
        RD-->>ING: hit -> drop
    else new event
        ING->>RD: store key (TTL)
        ING->>DB: persist Event + Detection
        ING->>BUS: publish detection.received
    end
    BUS->>RE: consume detection.received
    RE->>DB: load rules / schedule / security level
    RE->>RE: evaluate (class, zone, time, day)
    alt intrusion
        RE->>DB: create Alert (status=NEW, criticality)
        RE->>BUS: publish alert.created
        BUS->>NS: consume alert.created
        NS->>NS: escalation policy / quiet hours / fallback
        NS-->>OP: WebSocket push + Email/SMS/Push
    else false positive / ignore
        RE->>DB: log decision (audit)
    end
    OP->>DB: acknowledge / close (audit trail)
```

---

## 4. Class Diagram — Core Domain

```mermaid
classDiagram
    class Tenant {
      +UUID id
      +str name
      +str status
    }
    class User {
      +UUID id
      +str email
      +Role role
      +bool active
    }
    class Site {
      +UUID id
      +str name
      +float lat
      +float lon
    }
    class Zone {
      +UUID id
      +str name
      +Geometry geometry
    }
    class Camera {
      +UUID id
      +str name
      +str ip
      +Protocol protocol
      +str model
      +CameraStatus status
      +datetime last_seen
    }
    class Event {
      +UUID id
      +datetime timestamp
      +str object_class
      +float confidence
      +str idempotency_key
    }
    class Rule {
      +UUID id
      +int priority
      +dict conditions
      +dict action
      +bool enabled
    }
    class Alert {
      +UUID id
      +Criticality criticality
      +AlertStatus status
      +datetime created_at
    }
    class Notification {
      +UUID id
      +Channel channel
      +DeliveryStatus status
    }
    class AuditLog {
      +UUID id
      +str actor
      +str action
      +datetime at
    }

    Tenant "1" --> "*" User
    Tenant "1" --> "*" Site
    Site "1" --> "*" Zone
    Site "1" --> "*" Camera
    Zone "*" --> "*" Camera
    Camera "1" --> "*" Event
    Event "1" --> "0..1" Alert
    Rule "*" ..> Event : evaluates
    Alert "1" --> "*" Notification
    Alert "1" --> "*" AuditLog
```

---

## 5. Deployment Topology

```mermaid
flowchart LR
  subgraph SiteA["Site A (edge)"]
    CA["AI cameras"]
    GA["Gateway box<br/>(MediaMTX)"]
    CA --> GA
  end
  subgraph SiteB["Site B (edge)"]
    CB["AI cameras"]
    GB["Gateway box"]
    CB --> GB
  end

  subgraph Cloud["Cloud region (multi-AZ K8s)"]
    direction TB
    LB["Load Balancer / WAF"]
    subgraph AZ1["AZ-1"]
      P1["API / Ingestion pods"]
    end
    subgraph AZ2["AZ-2"]
      P2["Rule / Notification pods"]
    end
    PGHA[("PostgreSQL HA<br/>primary+replica")]
    KAFKA[["Kafka cluster (3 brokers)"]]
    S3[("Object store (S3/MinIO)")]
  end

  GA -->|TLS| LB
  GB -->|TLS| LB
  LB --> P1
  LB --> P2
  P1 --> PGHA
  P2 --> PGHA
  P1 --> KAFKA
  P2 --> KAFKA
  P1 --> S3
```

---

## 6. Network / Edge Topology & Integration Layering

```mermaid
flowchart TB
  subgraph Perimeter["Physical perimeter"]
    C1["Camera (North fence)"]
    C2["Camera (South fence)"]
    C3["Camera (Parking)"]
    R1["Radar (roadmap)"]
    F1["Fence sensor (roadmap)"]
  end

  subgraph LAN["Site LAN (VLAN, PoE)"]
    SW["PoE switch"]
    NVR["Edge gateway / mini-NVR"]
  end

  C1 & C2 & C3 -->|PoE + RTSP/ONVIF| SW
  R1 & F1 -.->|API/TCP| NVR
  SW --> NVR
  NVR -->|"outbound TLS (mTLS)"| CLOUD["PIDS Cloud"]

  subgraph Layering["Camera integration fallback (per model)"]
    L1["1. ONVIF Profile T/M<br/>(discovery, events, metadata)"]
    L2["2. RTSP (RFC 7826 / SRTP)"]
    L3["3. Vendor SDK (advanced features)"]
    L1 --> L2 --> L3
  end
```

**Design notes.** Cameras are on an isolated VLAN with PoE; only the edge gateway has outbound
connectivity, over **mTLS**, to the cloud (zero inbound). The gateway normalizes heterogeneous
cameras via the layered pattern (ONVIF → RTSP → vendor SDK) and buffers events during WAN
outages (store-and-forward). This keeps camera credentials off the public internet and bounds
the blast radius of a compromised camera.
