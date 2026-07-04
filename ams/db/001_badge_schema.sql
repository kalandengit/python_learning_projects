-- =============================================================================
-- AMS Badge context schema — PostgreSQL 18
-- Event-sourced badge lifecycle (ADR-003) + read models.
-- Apply as the ams_badge database owner; application roles defined at the end.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS badge;

-- -----------------------------------------------------------------------------
-- Event store: append-only stream per badge.
-- PK uuidv7(): time-ordered inserts land on the B-tree right edge (Section 7.1),
-- and the PK doubles as the global-order keyset cursor (ADR-018).
-- -----------------------------------------------------------------------------
CREATE TABLE badge.badge_events (
    event_id        uuid        PRIMARY KEY DEFAULT uuidv7(),
    badge_id        uuid        NOT NULL,
    version         bigint      NOT NULL CHECK (version > 0),
    event_type      text        NOT NULL,
    schema_version  smallint    NOT NULL DEFAULT 1,
    payload         jsonb       NOT NULL,
    actor           text        NOT NULL,               -- principal id, never display name (PII rule)
    causation_id    uuid        NULL,
    correlation_id  uuid        NULL,
    trace_parent    text        NULL,                   -- W3C traceparent for cross-hop tracing
    occurred_at     timestamptz NOT NULL DEFAULT now(),
    -- Optimistic concurrency: exactly one event per (stream, version).
    CONSTRAINT uq_badge_events_stream UNIQUE (badge_id, version)
);

CREATE INDEX ix_badge_events_badge ON badge.badge_events (badge_id, version);

-- Append-only enforcement (defence-in-depth on top of role grants).
CREATE OR REPLACE FUNCTION badge.forbid_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'table % is append-only', TG_TABLE_NAME
        USING ERRCODE = 'raise_exception';
END $$;

CREATE TRIGGER trg_badge_events_immutable
    BEFORE UPDATE OR DELETE ON badge.badge_events
    FOR EACH ROW EXECUTE FUNCTION badge.forbid_mutation();

-- -----------------------------------------------------------------------------
-- Read model: current state per badge (projection, rebuildable from the stream).
-- -----------------------------------------------------------------------------
CREATE TABLE badge.badge_current_state (
    badge_id        uuid        PRIMARY KEY,
    cardholder_id   uuid        NOT NULL,
    badge_type      text        NOT NULL CHECK (badge_type IN ('RFID','QR','TEMPORARY_RFID')),
    state           text        NOT NULL CHECK (state IN
                        ('REQUESTED','ISSUED','ACTIVE','SUSPENDED','REVOKED','EXPIRED','LOST','RETURNED')),
    valid_from      timestamptz NOT NULL,
    valid_until     timestamptz NOT NULL,
    qr_key_id       text        NULL,                   -- signing key id, never key material
    site_id         uuid        NULL,
    stream_version  bigint      NOT NULL,
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CHECK (valid_until > valid_from)
);

CREATE INDEX ix_badge_state_cardholder ON badge.badge_current_state (cardholder_id);
CREATE INDEX ix_badge_state_state      ON badge.badge_current_state (state)
    WHERE state IN ('ACTIVE','SUSPENDED');              -- partial: hot queries only

-- -----------------------------------------------------------------------------
-- Read model: compact validation snapshot rows pushed to Redis / edge caches.
-- snapshot_seq is a monotonic cursor edges use to pull deltas.
-- -----------------------------------------------------------------------------
CREATE SEQUENCE badge.snapshot_seq;

CREATE TABLE badge.credential_snapshot (
    credential_id   uuid        PRIMARY KEY DEFAULT uuidv7(),
    badge_id        uuid        NOT NULL REFERENCES badge.badge_current_state (badge_id),
    site_id         uuid        NULL,                   -- null = all sites
    rfid_hash       bytea       NULL,                   -- SHA-256 of card data; raw values never stored
    qr_key_id       text        NULL,
    is_valid        boolean     NOT NULL,
    valid_until     timestamptz NOT NULL,
    snapshot_seq    bigint      NOT NULL DEFAULT nextval('badge.snapshot_seq'),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX ix_snapshot_rfid ON badge.credential_snapshot (rfid_hash) WHERE rfid_hash IS NOT NULL;
CREATE INDEX ix_snapshot_seq ON badge.credential_snapshot (snapshot_seq);

-- -----------------------------------------------------------------------------
-- Local replica of cardholders (maintained from ams.cardholder events — not a
-- cross-service FK; DB-per-service rule, Section 6.2).
-- -----------------------------------------------------------------------------
CREATE TABLE badge.cardholder_ref (
    cardholder_id   uuid        PRIMARY KEY,
    display_name    text        NOT NULL,
    cardholder_type text        NOT NULL CHECK (cardholder_type IN ('EMPLOYEE','CONTRACTOR','VENDOR','VISITOR')),
    status          text        NOT NULL CHECK (status IN ('PENDING_ONBOARDING','ACTIVE','SUSPENDED','OFFBOARDED')),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- Roles: application role may INSERT events but never mutate them.
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ams_badge_app') THEN
        CREATE ROLE ams_badge_app NOLOGIN;
    END IF;
END $$;

GRANT USAGE ON SCHEMA badge TO ams_badge_app;
GRANT SELECT, INSERT                 ON badge.badge_events        TO ams_badge_app;
GRANT SELECT, INSERT, UPDATE         ON badge.badge_current_state TO ams_badge_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON badge.credential_snapshot TO ams_badge_app;
GRANT SELECT, INSERT, UPDATE         ON badge.cardholder_ref      TO ams_badge_app;
GRANT USAGE ON SEQUENCE badge.snapshot_seq TO ams_badge_app;
REVOKE UPDATE, DELETE ON badge.badge_events FROM ams_badge_app;

-- VERIFY: uuidv7() is built-in from PostgreSQL 18; on earlier majors install pg_uuidv7 instead.
