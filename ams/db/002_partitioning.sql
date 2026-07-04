-- =============================================================================
-- AMS Access Control context — high-volume decision log with monthly range
-- partitions (Section 7.3). PostgreSQL 18.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS access;

-- Append-only decision log: immutable facts, not an event-sourced aggregate
-- (ADR-003). Partitioned by occurred_at for retention + prune performance.
CREATE TABLE access.access_decisions (
    decision_id     uuid        NOT NULL DEFAULT uuidv7(),
    badge_id        uuid        NULL,               -- null for UNKNOWN_CREDENTIAL
    cardholder_id   uuid        NULL,
    site_id         uuid        NOT NULL,
    zone_id         uuid        NOT NULL,
    reader_id       uuid        NOT NULL,
    direction       text        NOT NULL CHECK (direction IN ('ENTRY','EXIT')),
    decision        text        NOT NULL CHECK (decision IN ('PERMIT','DENY')),
    reason_code     text        NOT NULL,
    policy_version  text        NOT NULL,
    offline         boolean     NOT NULL DEFAULT false,
    trace_parent    text        NULL,
    occurred_at     timestamptz NOT NULL,
    recorded_at     timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (decision_id, occurred_at)          -- partition key must be in the PK
) PARTITION BY RANGE (occurred_at);

CREATE INDEX ix_decisions_zone_time   ON access.access_decisions (zone_id, occurred_at);
CREATE INDEX ix_decisions_badge_time  ON access.access_decisions (badge_id, occurred_at)
    WHERE badge_id IS NOT NULL;
CREATE INDEX ix_decisions_deny        ON access.access_decisions (reader_id, occurred_at)
    WHERE decision = 'DENY';                        -- FR-035 alarm queries

CREATE OR REPLACE FUNCTION access.forbid_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'table % is append-only', TG_TABLE_NAME;
END $$;

CREATE TRIGGER trg_decisions_immutable
    BEFORE UPDATE OR DELETE ON access.access_decisions
    FOR EACH ROW EXECUTE FUNCTION access.forbid_mutation();

-- -----------------------------------------------------------------------------
-- Partition automation: create partitions 3 months ahead; called monthly by a
-- scheduled job (pg_cron on Flexible Server, or an AKS CronJob running psql).
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION access.ensure_decision_partitions(months_ahead int DEFAULT 3)
RETURNS void
LANGUAGE plpgsql AS $$
DECLARE
    m      date;
    p_from date;
    p_to   date;
    pname  text;
BEGIN
    FOR i IN 0 .. months_ahead LOOP
        m      := date_trunc('month', now())::date + make_interval(months => i);
        p_from := m;
        p_to   := (m + interval '1 month')::date;
        pname  := format('access_decisions_%s', to_char(m, 'YYYY_MM'));
        IF NOT EXISTS (
            SELECT 1 FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'access' AND c.relname = pname
        ) THEN
            EXECUTE format(
                'CREATE TABLE access.%I PARTITION OF access.access_decisions
                 FOR VALUES FROM (%L) TO (%L)',
                pname, p_from, p_to);
        END IF;
    END LOOP;
END $$;

-- Bootstrap current + next 3 months.
SELECT access.ensure_decision_partitions(3);

-- Retention (Section 7.4): detach partitions older than 13 months for archive.
-- The archive job exports the detached table to WORM blob (parquet/csv) then drops it.
CREATE OR REPLACE FUNCTION access.detach_expired_decision_partitions(retain_months int DEFAULT 13)
RETURNS setof text
LANGUAGE plpgsql AS $$
DECLARE
    cutoff date := (date_trunc('month', now()) - make_interval(months => retain_months))::date;
    r record;
BEGIN
    FOR r IN
        SELECT c.relname
        FROM pg_inherits i
        JOIN pg_class c ON c.oid = i.inhrelid
        JOIN pg_class p ON p.oid = i.inhparent
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'access' AND p.relname = 'access_decisions'
          AND to_date(right(c.relname, 7), 'YYYY_MM') < cutoff
    LOOP
        EXECUTE format('ALTER TABLE access.access_decisions DETACH PARTITION access.%I', r.relname);
        RETURN NEXT r.relname;
    END LOOP;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ams_access_app') THEN
        CREATE ROLE ams_access_app NOLOGIN;
    END IF;
END $$;

GRANT USAGE ON SCHEMA access TO ams_access_app;
GRANT SELECT, INSERT ON access.access_decisions TO ams_access_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA access GRANT SELECT, INSERT ON TABLES TO ams_access_app;

-- VERIFY: pg_cron availability/allow-listing on Azure Flexible Server before relying on in-DB scheduling.
