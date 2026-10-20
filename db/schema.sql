-- Heathrow Punctuality Dashboard — core schema (FR-3).
-- Applied to PostgreSQL. Idempotent.

BEGIN;

-- ---------------------------------------------------------------------------
-- staged_raw: tidy, standardised rows produced by the parser before DQ and
-- merge. One row per (report_month, airport, airline, route, direction).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staged_raw (
    id                     BIGSERIAL PRIMARY KEY,
    report_month           DATE NOT NULL,            -- first of month
    airport                TEXT NOT NULL,
    airline                TEXT NOT NULL,
    route                  TEXT NOT NULL DEFAULT '',
    direction              TEXT NOT NULL CHECK (direction IN ('arrival', 'departure', 'all')),
    total_flights          INTEGER,
    on_time_flights        INTEGER,
    cancelled_flights      INTEGER,
    delayed_flights        INTEGER,
    average_delay_minutes  DOUBLE PRECISION,
    early_share            DOUBLE PRECISION,         -- percentage, 0..100
    on_time_share          DOUBLE PRECISION,
    small_delay_share      DOUBLE PRECISION,
    medium_delay_share     DOUBLE PRECISION,
    large_delay_share      DOUBLE PRECISION,
    source_file            TEXT,
    loaded_at              TIMESTAMPTZ DEFAULT now(),
    UNIQUE (report_month, airport, airline, route, direction)
);

-- ---------------------------------------------------------------------------
-- fact_punctuality: the clean, published table the dashboards read from.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_punctuality (
    id                     BIGSERIAL PRIMARY KEY,
    report_month           DATE NOT NULL,
    airport                TEXT NOT NULL,
    airline                TEXT NOT NULL,
    route                  TEXT NOT NULL DEFAULT '',
    direction              TEXT NOT NULL CHECK (direction IN ('arrival', 'departure', 'all')),
    total_flights          INTEGER NOT NULL,
    on_time_flights        INTEGER,
    cancelled_flights      INTEGER NOT NULL DEFAULT 0,
    delayed_flights        INTEGER,
    average_delay_minutes  DOUBLE PRECISION,
    early_share            DOUBLE PRECISION,
    on_time_share          DOUBLE PRECISION,
    small_delay_share      DOUBLE PRECISION,
    medium_delay_share     DOUBLE PRECISION,
    large_delay_share      DOUBLE PRECISION,
    updated_at             TIMESTAMPTZ DEFAULT now(),
    UNIQUE (report_month, airport, airline, route, direction)
);

CREATE INDEX IF NOT EXISTS idx_fact_month   ON fact_punctuality (report_month);
CREATE INDEX IF NOT EXISTS idx_fact_airport ON fact_punctuality (airport);
CREATE INDEX IF NOT EXISTS idx_fact_airline ON fact_punctuality (airline);
CREATE INDEX IF NOT EXISTS idx_fact_route   ON fact_punctuality (route);

-- ---------------------------------------------------------------------------
-- data_quality_log: results of every DQ check on every load (FR-4).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS data_quality_log (
    id            BIGSERIAL PRIMARY KEY,
    run_id        TEXT NOT NULL,
    check_code    TEXT NOT NULL,             -- e.g. 'DQ-1'
    status        TEXT NOT NULL CHECK (status IN ('pass', 'fail', 'warn')),
    message       TEXT,
    n_rows        INTEGER,
    detail        JSONB,
    checked_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_dq_run ON data_quality_log (run_id);
CREATE INDEX IF NOT EXISTS idx_dq_code ON data_quality_log (check_code);

-- ---------------------------------------------------------------------------
-- load_runs: one row per pipeline run, for provenance and re-runnability.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS load_runs (
    run_id        TEXT PRIMARY KEY,
    started_at    TIMESTAMPTZ DEFAULT now(),
    finished_at   TIMESTAMPTZ,
    status        TEXT DEFAULT 'running',
    notes         JSONB
);

COMMIT;