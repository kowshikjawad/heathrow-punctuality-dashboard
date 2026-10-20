# Heathrow Punctuality Dashboard — pipeline configuration.
#
# All tunable knobs live here so the pipeline is re-runnable (FR-5) and
# behaviour is documented in one place rather than hidden inside code.

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DB_DIR = PROJECT_ROOT / "db"
SQL_DIR = DB_DIR / "sql"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
# PostgreSQL is the primary store (FR-3). Override via DATABASE_URL in .env.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://heathrow:heathrow@localhost:5432/punctuality",
)

# ---------------------------------------------------------------------------
# Peer set (PRD §7) — to be confirmed against the published airport list.
# ---------------------------------------------------------------------------
HEATHROW = "Heathrow"
PEER_AIRPORTS = ["Gatwick", "Manchester", "Stansted", "Luton", "Birmingham"]
ALL_AIRPORTS = [HEATHROW, *PEER_AIRPORTS]

# ---------------------------------------------------------------------------
# Data-quality tolerances (PRD §8)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class DQConfig:
    # DQ-1: delay-band shares must sum to ~100% within this tolerance (percentage pts).
    band_sum_tolerance_pct: float = 1.0
    # DQ-6: detailed vs summary totals must reconcile within this fraction.
    reconcile_tolerance_ratio: float = 0.02
    # DQ-7: average delay above this many minutes is flagged for review (not deleted).
    avg_delay_outlier_minutes: float = 60.0
    # DQ-7: a cancellation rate above this triggers review.
    cancellation_rate_outlier: float = 0.20


DQ = DQConfig()

# ---------------------------------------------------------------------------
# Methodology change point (PRD §7 risk). CAA changed its punctuality
# calculation method; older months may not be directly comparable. The exact
# month will be confirmed from the source documentation and recorded here so
# charts can flag it rather than silently blending series.
# ---------------------------------------------------------------------------
METHOD_CHANGE_MONTH: str | None = os.getenv("METHOD_CHANGE_MONTH", None)
# e.g. METHOD_CHANGE_MONTH="2025-01"
