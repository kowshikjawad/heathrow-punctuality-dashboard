"""FR-4 / PRD §8: data-quality checks.

Every check is pure and takes a tidy DataFrame, so the rules are unit-testable
without a database. ``run_all`` returns a list of check-result dicts and can
write them to the ``data_quality_log`` table.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from heathrow.config import DQ

log = logging.getLogger(__name__)


@dataclass
class DQResult:
    check_code: str
    status: str  # pass | fail | warn
    message: str
    n_rows: int = 0
    detail: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "check_code": self.check_code,
            "status": self.status,
            "message": self.message,
            "n_rows": self.n_rows,
            "detail": self.detail,
        }


def _share_cols(df: pd.DataFrame) -> list[str]:
    cols = [
        "early_share",
        "on_time_share",
        "small_delay_share",
        "medium_delay_share",
        "large_delay_share",
    ]
    return [c for c in cols if c in df.columns]


def check_band_sum(df: pd.DataFrame) -> DQResult:
    """DQ-1: delay-band shares sum to ~100% within tolerance."""
    cols = _share_cols(df)
    if not cols:
        return DQResult("DQ-1", "warn", "no share columns present to check")
    total = df[cols].sum(axis=1, skipna=True)
    bad = df[(total - 100.0).abs() > DQ.band_sum_tolerance_pct]
    n = len(bad)
    if n == 0:
        return DQResult("DQ-1", "pass", "delay-band shares sum to ~100%", n_rows=len(df))
    sample = bad.head(5).to_dict("records")
    return DQResult(
        "DQ-1",
        "fail",
        f"{n} rows exceed band-sum tolerance",
        n_rows=n,
        detail={"sample": sample},
    )


def check_cancelled_le_total(df: pd.DataFrame) -> DQResult:
    """DQ-2: cancelled flights never exceed total flights."""
    if "cancelled_flights" not in df or "total_flights" not in df:
        return DQResult("DQ-2", "warn", "columns missing; skipped")
    bad = df[df["cancelled_flights"] > df["total_flights"]]
    n = len(bad)
    if n == 0:
        return DQResult("DQ-2", "pass", "cancelled <= total flights everywhere", n_rows=len(df))
    return DQResult("DQ-2", "fail", f"{n} rows have cancelled > total", n_rows=n,
                    detail={"sample": bad.head(5).to_dict("records")})


def check_duplicates(df: pd.DataFrame) -> DQResult:
    """DQ-3: no duplicate rows for same airport/airline/route/month/direction."""
    keys = ["report_month", "airport", "airline", "route", "direction"]
    keys = [k for k in keys if k in df.columns]
    dup = df[df.duplicated(subset=keys, keep=False)]
    n = len(dup)
    if n == 0:
        return DQResult("DQ-3", "pass", "no duplicate natural keys", n_rows=len(df))
    return DQResult("DQ-3", "fail", f"{n} duplicate rows", n_rows=n,
                    detail={"sample": dup.head(5).to_dict("records")})


def check_missing_months(df: pd.DataFrame, expected_months: list[str] | None = None) -> DQResult:
    """DQ-4: no missing months inside the chosen range."""
    if "report_month" not in df:
        return DQResult("DQ-4", "warn", "report_month missing; skipped")
    months = pd.to_datetime(df["report_month"].dropna()).dt.to_period("M").sort_values()
    actual = set(months.astype(str).unique())
    if expected_months:
        missing = sorted(set(expected_months) - actual)
    else:
        if months.empty:
            return DQResult("DQ-4", "warn", "no months present")
        full = pd.period_range(months.min(), months.max(), freq="M")
        missing = sorted(set(full.astype(str)) - actual)
    if not missing:
        return DQResult("DQ-4", "pass", "no missing months in range")
    return DQResult("DQ-4", "fail", f"missing months: {missing}", n_rows=len(missing),
                    detail={"missing": missing})


def check_controlled_airports(df: pd.DataFrame, controlled: list[str]) -> DQResult:
    """DQ-5a: airport names map to the controlled list; report unmapped."""
    if "airport" not in df:
        return DQResult("DQ-5", "warn", "airport column missing; skipped")
    allowed = set(controlled)
    unmapped = sorted(set(df["airport"].dropna().unique()) - allowed)
    if not unmapped:
        return DQResult("DQ-5", "pass", "all airports in controlled list")
    return DQResult("DQ-5", "fail", f"unmapped airports: {unmapped}", n_rows=len(unmapped),
                    detail={"unmapped": unmapped})


def check_reconcile_summary(df_detailed: pd.DataFrame, df_summary: pd.DataFrame) -> DQResult:
    """DQ-6: detailed totals reconcile with summary totals within tolerance."""
    if df_detailed.empty or df_summary.empty:
        return DQResult("DQ-6", "warn", "detail or summary empty; skipped")
    if "total_flights" not in df_detailed or "total_flights" not in df_summary:
        return DQResult("DQ-6", "warn", "total_flights missing; skipped")
    d = float(df_detailed["total_flights"].sum())
    s = float(df_summary["total_flights"].sum())
    if s == 0:
        return DQResult("DQ-6", "warn", "summary total is zero; skipped")
    ratio = abs(d - s) / s
    status = "pass" if ratio <= DQ.reconcile_tolerance_ratio else "fail"
    return DQResult("DQ-6", status, f"detail/summary total reconcile ratio={ratio:.4f}",
                    detail={"detail_total": d, "summary_total": s, "ratio": ratio})


def check_outliers(df: pd.DataFrame) -> DQResult:
    """DQ-7: outliers flagged for review, not deleted."""
    flags = []
    if "average_delay_minutes" in df:
        flags.extend(df[
            df["average_delay_minutes"] > DQ.avg_delay_outlier_minutes
        ].head(10).to_dict("records"))
    if "cancelled_flights" in df and "total_flights" in df:
        rate = df["cancelled_flights"] / df["total_flights"].replace(0, pd.NA)
        flags.extend(df[rate > DQ.cancellation_rate_outlier].head(10).to_dict("records"))
    status = "warn" if flags else "pass"
    return DQResult("DQ-7", status,
                    "outliers flagged for review" if flags else "no outliers flagged",
                    n_rows=len(flags), detail={"outliers": flags})


def run_all(df: pd.DataFrame, *,
            controlled_airports: list[str] | None = None,
            expected_months: list[str] | None = None,
            df_summary: pd.DataFrame | None = None) -> list[DQResult]:
    """Run every DQ check. Returns a list of DQResult."""
    results = [
        check_band_sum(df),
        check_cancelled_le_total(df),
        check_duplicates(df),
        check_missing_months(df, expected_months),
        check_controlled_airports(df, controlled_airports or []),
        check_outliers(df),
    ]
    if df_summary is not None:
        results.append(check_reconcile_summary(df, df_summary))
    return results


def run_id() -> str:
    return uuid.uuid4().hex[:16]
