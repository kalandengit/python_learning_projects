-- =============================================================================
-- Transactional outbox + idempotent-consumer inbox (ADR-019).
-- Deployed into EVERY service database (shown here for ams_badge).
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS messaging;

-- Outbox: written in the SAME transaction as the state change / event append.
-- uuidv7 PK = publish order (time-ordered), no extra sequence needed.
CREATE TABLE messaging.outbox (
    outbox_id       uuid        PRIMARY KEY DEFAULT uuidv7(),
    aggregate_id    uuid        NOT NULL,      -- Event Hubs partition key
    topic           text        NOT NULL,      -- e.g. 'ams.badge'
    event_type      text        NOT NULL,      -- e.g. 'badge.revoked'
    schema_version  smallint    NOT NULL DEFAULT 1,
    payload         jsonb       NOT NULL,
    trace_parent    text        NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    processed_at    timestamptz NULL,
    attempts        int         NOT NULL DEFAULT 0,
    last_error      text        NULL
);

-- Dispatcher scan: only unprocessed rows, oldest first.
CREATE INDEX ix_outbox_unprocessed ON messaging.outbox (outbox_id)
    WHERE processed_at IS NULL;

-- Hygiene: processed rows pruned after 7 days by a background job.
CREATE INDEX ix_outbox_processed_at ON messaging.outbox (processed_at)
    WHERE processed_at IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Inbox: consumer-side dedupe -> exactly-once EFFECT over at-least-once delivery.
-- Insert event_id before handling inside the handler's transaction; a conflict
-- means "already processed, skip".
-- -----------------------------------------------------------------------------
CREATE TABLE messaging.processed_events (
    event_id      uuid        PRIMARY KEY,
    consumer      text        NOT NULL,
    processed_at  timestamptz NOT NULL DEFAULT now()
);

-- Idempotency-Key store fallback (primary store is Redis, ADR-017): used only
-- if Redis is unavailable and strict idempotency is still required on a route.
CREATE TABLE messaging.idempotency_keys (
    idempotency_key uuid        NOT NULL,
    principal       text        NOT NULL,
    request_hash    bytea       NOT NULL,
    response_status int         NOT NULL,
    response_body   jsonb       NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (idempotency_key, principal)
);

GRANT USAGE ON SCHEMA messaging TO ams_badge_app;
GRANT SELECT, INSERT, UPDATE ON messaging.outbox            TO ams_badge_app;
GRANT SELECT, INSERT         ON messaging.processed_events  TO ams_badge_app;
GRANT SELECT, INSERT         ON messaging.idempotency_keys  TO ams_badge_app;
GRANT DELETE ON messaging.outbox, messaging.idempotency_keys TO ams_badge_app; -- pruning jobs

-- VERIFY: dispatcher query uses FOR UPDATE SKIP LOCKED (see OutboxDispatcher.cs) — confirm isolation level READ COMMITTED.
