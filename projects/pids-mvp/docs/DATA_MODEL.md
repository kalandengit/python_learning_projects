# PIDS — Data Model (ER + Schema)

Target: **PostgreSQL 16** (+ TimescaleDB hypertables for `events`, `notifications`, `audit_logs`).
Multi-tenant isolation via **Row-Level Security (RLS)** keyed on `tenant_id` (recommended MVP
default — lowest operational cost, strong isolation when combined with a per-request
`SET app.tenant_id`). `database-per-tenant` is the upgrade path for regulated/military tenants.

## Entity-Relationship Diagram

```mermaid
erDiagram
    TENANT ||--o{ USER : has
    TENANT ||--o{ SITE : owns
    TENANT ||--o{ RULE : defines
    TENANT ||--o{ SETTING : configures
    ROLE ||--o{ USER : assigned
    ROLE ||--o{ ROLE_PERMISSION : grants
    PERMISSION ||--o{ ROLE_PERMISSION : in
    SITE ||--o{ ZONE : contains
    SITE ||--o{ CAMERA : hosts
    ZONE ||--o{ CAMERA_ZONE : maps
    CAMERA ||--o{ CAMERA_ZONE : maps
    CAMERA ||--o{ EVENT : emits
    EVENT ||--o{ DETECTION : contains
    EVENT ||--o| ALERT : triggers
    ALERT ||--o{ ALERT_HISTORY : logs
    ALERT ||--o{ NOTIFICATION : sends
    ALERT ||--o{ MEDIA : attaches
    USER ||--o{ SESSION : opens
    USER ||--o{ TOKEN : holds
    TENANT ||--o{ AUDIT_LOG : records

    TENANT {
      uuid id PK
      text name
      text status
      timestamptz created_at
    }
    USER {
      uuid id PK
      uuid tenant_id FK
      text email UK
      text password_hash
      uuid role_id FK
      bool active
    }
    ROLE {
      uuid id PK
      text name
    }
    PERMISSION {
      uuid id PK
      text code
    }
    ROLE_PERMISSION {
      uuid role_id FK
      uuid permission_id FK
    }
    SITE {
      uuid id PK
      uuid tenant_id FK
      text name
      double lat
      double lon
    }
    ZONE {
      uuid id PK
      uuid site_id FK
      text name
      jsonb geometry
    }
    CAMERA {
      uuid id PK
      uuid site_id FK
      text name
      inet ip_address
      text protocol
      text model
      text orientation
      double fov_angle
      text status
      text firmware
      timestamptz last_seen
    }
    CAMERA_ZONE {
      uuid camera_id FK
      uuid zone_id FK
    }
    EVENT {
      uuid id PK
      uuid tenant_id FK
      uuid camera_id FK
      timestamptz ts
      text object_class
      double confidence
      jsonb bbox
      text track_id
      text idempotency_key UK
    }
    DETECTION {
      uuid id PK
      uuid event_id FK
      text object_class
      double confidence
    }
    RULE {
      uuid id PK
      uuid tenant_id FK
      int priority
      jsonb conditions
      jsonb action
      bool enabled
      int version
    }
    ALERT {
      uuid id PK
      uuid tenant_id FK
      uuid event_id FK
      uuid camera_id FK
      uuid zone_id FK
      text type
      text criticality
      text status
      timestamptz created_at
    }
    ALERT_HISTORY {
      uuid id PK
      uuid alert_id FK
      text from_status
      text to_status
      text actor
      text reason
      timestamptz at
    }
    NOTIFICATION {
      uuid id PK
      uuid alert_id FK
      text channel
      text target
      text status
      text idempotency_key
      timestamptz sent_at
    }
    MEDIA {
      uuid id PK
      uuid alert_id FK
      text kind
      text object_key
    }
    SETTING {
      uuid id PK
      uuid tenant_id FK
      text key
      jsonb value
    }
    SESSION {
      uuid id PK
      uuid user_id FK
      text ip
      timestamptz created_at
    }
    TOKEN {
      uuid id PK
      uuid user_id FK
      text kind
      timestamptz expires_at
    }
    AUDIT_LOG {
      uuid id PK
      uuid tenant_id FK
      text actor
      text action
      jsonb detail
      timestamptz at
    }
```

## Reference DDL (excerpt)

```sql
-- Tenancy + RLS
CREATE TABLE tenant (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name        text NOT NULL,
    status      text NOT NULL DEFAULT 'active',
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE camera (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id    uuid NOT NULL REFERENCES tenant(id),
    site_id      uuid NOT NULL REFERENCES site(id),
    name         text NOT NULL,
    ip_address   inet,
    protocol     text NOT NULL CHECK (protocol IN ('ONVIF','RTSP','VENDOR')),
    model        text,
    orientation  text,
    fov_angle    double precision,
    status       text NOT NULL DEFAULT 'unknown'
                 CHECK (status IN ('online','offline','tamper','unknown')),
    firmware     text,
    last_seen    timestamptz
);

-- Event table as a Timescale hypertable, partitioned by time
CREATE TABLE event (
    id               uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id        uuid NOT NULL,
    camera_id        uuid NOT NULL,
    ts               timestamptz NOT NULL,
    object_class     text NOT NULL,
    confidence       double precision NOT NULL,
    bbox             jsonb,
    track_id         text,
    idempotency_key  text NOT NULL,
    PRIMARY KEY (id, ts),
    UNIQUE (idempotency_key, ts)
);
-- SELECT create_hypertable('event','ts');

-- Row-Level Security example
ALTER TABLE camera ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON camera
    USING (tenant_id = current_setting('app.tenant_id')::uuid);
```

## Retention & compliance (ties to §0 of the master prompt)

| Data | Default retention | Notes |
|------|-------------------|-------|
| Video clips / snapshots (`media`) | 30 days (per-tenant configurable) | GDPR minimization; object-store lifecycle policy |
| `event` / `detection` | 90 days hot, then downsampled | Timescale continuous aggregates |
| `alert` / `alert_history` | 1–3 years | Security/forensic value |
| `audit_log` | 1–7 years (immutable, append-only) | Tamper-evident (hash-chained) |
| Biometric match (if enabled) | Keep alert only, **not** raw frame | Special-category data |
