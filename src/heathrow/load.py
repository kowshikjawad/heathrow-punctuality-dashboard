"""FR-3: load tidy data into PostgreSQL and write DQ results to the log table."""

from __future__ import annotations

import logging

import pandas as pd
from sqlalchemy import create_engine, text

from heathrow.config import DATABASE_URL
from heathrow.quality import DQResult

log = logging.getLogger(__name__)

SHEMA_PATH_NOTE = "Apply db/schema.sql and db/views.sql before loading."


def get_engine(url: str = DATABASE_URL):
    return create_engine(url)


def ensure_schema(engine) -> None:
    """Apply db/schema.sql and db/views.sql (idempotent)."""
    import heathrow.config as cfg

    for fname in ("schema.sql", "views.sql"):
        path = cfg.DB_DIR / fname
        sql = path.read_text(encoding="utf-8")
        with engine.begin() as conn:
            conn.execute(text(sql))
        log.info("applied %s", path.name)


def upsert_facts(engine, df: pd.DataFrame) -> int:
    """Upsert staged rows into fact_punctuality via the natural key."""
    if df.empty:
        return 0
    # Route/airline may be '' — ensure strings.
    df = df.copy()
    for c in ("airline", "route", "direction", "airport"):
        if c in df.columns:
            df[c] = df[c].fillna("").astype(str)
    df["report_month"] = pd.to_datetime(df["report_month"])
    n = df.to_sql("fact_punctuality", engine, if_exists="append", index=False)
    return n


def write_dq_log(engine, run: str, results: list[DQResult]) -> int:
    """Write DQ results to data_quality_log (FR-4)."""
    rows = [
        {
            "run_id": run,
            "check_code": r.check_code,
            "status": r.status,
            "message": r.message,
            "n_rows": r.n_rows,
            "detail": r.detail,  # will be JSON-encoded below
        }
        for r in results
    ]
    if not rows:
        return 0
    import json

    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO data_quality_log "
                "(run_id, check_code, status, message, n_rows, detail) "
                "VALUES (:run_id, :check_code, :status, :message, :n_rows, CAST(:detail AS jsonb))"
            ),
            [
                {
                    "run_id": run,
                    "check_code": r.check_code,
                    "status": r.status,
                    "message": r.message,
                    "n_rows": r.n_rows,
                    "detail": json.dumps(r.detail),
                }
                for r in results
            ],
        )
    return len(rows)


def record_run(engine, run: str, status: str, notes: dict | None = None) -> None:
    import json

    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO load_runs (run_id, status, notes) "
                "VALUES (:r, :s, :n) "
                "ON CONFLICT (run_id) DO UPDATE SET status = :s, notes = :n, finished_at = now()"
            ),
            {"r": run, "s": status, "n": json.dumps(notes or {})},
        )
