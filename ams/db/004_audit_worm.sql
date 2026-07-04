-- =============================================================================
-- AMS Audit & Compliance context — append-only audit store (Section 7.6).
-- PostgreSQL 18. Companion to the WORM blob archive (immutable containers).
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE audit.audit_events (
    event_id        uuid        NOT NULL DEFAULT uuidv7(),
    occurred_at     timestamptz NOT NULL,
    ingested_at     timestamptz NOT NULL DEFAULT now(),
    actor           text        NOT NULL,      -- principal id / 'system' — never display names
    subject_type    text        NOT NULL,      -- BADGE | VISIT | GRANT | CARDHOLDER | ...
    subject_id      text        NOT NULL,      -- pseudonymous key for PII subjects (FR-050)
    action          text        NOT NULL,      -- badge.revoked, visit.checked-in, ...
    source_topic    text        NOT NULL,
    source_event_id uuid        NOT NULL,
    payload         jsonb       NOT NULL,      -- normalised envelope, PII-minimised
    payload_hash    bytea       NOT NULL,      -- SHA-256 of the source event payload
    trace_id        text        NULL,
    retention_class text        NOT NULL DEFAULT 'CONFIDENTIAL_7Y',
    PRIMARY KEY (event_id, occurred_at)
) PARTITION BY RANGE (occurred_at);

-- Dedupe protection: the same source event may arrive more than once (at-least-once).
CREATE UNIQUE INDEX ux_audit_source ON audit.audit_events (source_event_id, occurred_at);
CREATE INDEX ix_audit_subject ON audit.audit_events (subject_type, subject_id, occurred_at);
CREATE INDEX ix_audit_action  ON audit.audit_events (action, occurred_at);

CREATE OR REPLACE FUNCTION audit.forbid_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'audit tables are append-only';
END $$;

CREATE TRIGGER trg_audit_immutable
    BEFORE UPDATE OR DELETE ON audit.audit_events
    FOR EACH ROW EXECUTE FUNCTION audit.forbid_mutation();

-- Monthly partitions, same automation pattern as access.ensure_decision_partitions.
CREATE OR REPLACE FUNCTION audit.ensure_audit_partitions(months_ahead int DEFAULT 3)
RETURNS void
LANGUAGE plpgsql AS $$
DECLARE
    m date; pname text;
BEGIN
    FOR i IN 0 .. months_ahead LOOP
        m := date_trunc('month', now())::date + make_interval(months => i);
        pname := format('audit_events_%s', to_char(m, 'YYYY_MM'));
        IF NOT EXISTS (
            SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'audit' AND c.relname = pname
        ) THEN
            EXECUTE format(
                'CREATE TABLE audit.%I PARTITION OF audit.audit_events
                 FOR VALUES FROM (%L) TO (%L)',
                pname, m, (m + interval '1 month')::date);
        END IF;
    END LOOP;
END $$;

SELECT audit.ensure_audit_partitions(3);

-- -----------------------------------------------------------------------------
-- Tamper-evidence: Merkle-root digest per closed monthly partition.
-- This table is ALSO the blockchain-anchoring seam (ADR-020 / Section 2.5):
-- an external anchoring adapter may post digest_root elsewhere; nothing here
-- depends on it.
-- -----------------------------------------------------------------------------
CREATE TABLE audit.audit_partition_digests (
    partition_name  text        PRIMARY KEY,
    row_count       bigint      NOT NULL,
    digest_root     bytea       NOT NULL,      -- Merkle root over ordered payload_hash values
    computed_at     timestamptz NOT NULL DEFAULT now(),
    anchored_at     timestamptz NULL,          -- set by the (deferred) anchoring adapter
    anchor_ref      text        NULL
);

-- -----------------------------------------------------------------------------
-- GDPR pseudonymisation vault: PII pointer indirection (FR-050, Section 7.4).
-- Audit envelopes reference pseudonym_id; erasure deletes ONLY the vault row.
-- Separately encrypted (column encryption via app-layer AES-256-GCM, key in KV).
-- -----------------------------------------------------------------------------
CREATE TABLE audit.identity_vault (
    pseudonym_id    uuid        PRIMARY KEY DEFAULT uuidv7(),
    subject_kind    text        NOT NULL CHECK (subject_kind IN ('VISITOR','CARDHOLDER')),
    encrypted_pii   bytea       NOT NULL,      -- ciphertext blob
    key_id          text        NOT NULL,      -- Key Vault key version used
    created_at      timestamptz NOT NULL DEFAULT now(),
    erased_at       timestamptz NULL           -- soft tombstone; ciphertext zeroed on erasure
);

-- Roles: INSERT-only for the ingestion path; erasure job is a separate role.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ams_audit_ingest') THEN
        CREATE ROLE ams_audit_ingest NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ams_audit_reader') THEN
        CREATE ROLE ams_audit_reader NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ams_audit_erasure') THEN
        CREATE ROLE ams_audit_erasure NOLOGIN;
    END IF;
END $$;

GRANT USAGE ON SCHEMA audit TO ams_audit_ingest, ams_audit_reader, ams_audit_erasure;
GRANT INSERT ON audit.audit_events TO ams_audit_ingest;
GRANT SELECT ON audit.audit_events, audit.audit_partition_digests TO ams_audit_reader;
GRANT INSERT, UPDATE ON audit.audit_partition_digests TO ams_audit_ingest;
GRANT SELECT, INSERT ON audit.identity_vault TO ams_audit_ingest;
GRANT SELECT, UPDATE ON audit.identity_vault TO ams_audit_erasure;  -- zero ciphertext + set erased_at
ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT INSERT ON TABLES TO ams_audit_ingest;
ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT SELECT ON TABLES TO ams_audit_reader;

-- VERIFY: blob-side immutability (time-based retention policy on the container) is configured in Terraform — DB alone is not the WORM control.
