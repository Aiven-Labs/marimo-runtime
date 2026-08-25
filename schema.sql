-- Schema for the marimo + Aiven PostgreSQL persistence demo.
-- Applied already to the live "marimo-demo-pg" service in the hevans-demo
-- Aiven project. Kept here so the demo is reproducible against any
-- PostgreSQL instance (Aiven or otherwise).

-- Key/value store holding the *current* value of every persisted widget.
CREATE TABLE IF NOT EXISTS app_state (
    key         TEXT PRIMARY KEY,
    value       JSONB NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Append-only audit log of every change, proving state really survives
-- notebook restarts and comes from Postgres rather than memory.
CREATE TABLE IF NOT EXISTS state_history (
    id          BIGSERIAL PRIMARY KEY,
    key         TEXT NOT NULL,
    value       JSONB NOT NULL,
    changed_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS state_history_key_changed_at_idx
    ON state_history (key, changed_at DESC);
