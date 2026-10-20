import pandas as pd

from heathrow import quality
from heathrow.parse import (
    STAGE_COLUMNS,
    standardise_airline,
    standardise_airport,
    standardise_route,
)


def make_df(rows):
    return pd.DataFrame(rows, columns=STAGE_COLUMNS)


# ---------------------------------------------------------------------------
# Standardisation (FR-2)
# ---------------------------------------------------------------------------
def test_standardise_airport_maps_peers():
    assert standardise_airport("London Heathrow") == "Heathrow"
    assert standardise_airport("heathrow airport") == "Heathrow"
    assert standardise_airport("Manchester Airport") == "Manchester"


def test_standardise_airline_title_case():
    assert standardise_airline("BRITISH AIRWAYS") == "British Airways"
    assert standardise_airline("easyJet") == "easyJet"


def test_standardise_route_trims():
    assert standardise_route("  LHR-JFK  ") == "LHR-JFK"


# ---------------------------------------------------------------------------
# DQ-1: band sum
# ---------------------------------------------------------------------------
def test_dq1_pass_when_bands_sum_to_100():
    df = make_df([{
        "report_month": "2026-01-01", "airport": "Heathrow", "airline": "BA",
        "route": "", "direction": "all", "total_flights": 100,
        "on_time_flights": 80, "cancelled_flights": 1, "delayed_flights": 19,
        "average_delay_minutes": 5.0, "early_share": 10.0, "on_time_share": 70.0,
        "small_delay_share": 15.0, "medium_delay_share": 4.0, "large_delay_share": 1.0,
    }])
    r = quality.check_band_sum(df)
    assert r.status == "pass"


def test_dq1_fail_when_bands_drift():
    df = make_df([{
        "report_month": "2026-01-01", "airport": "Heathrow", "airline": "BA",
        "route": "", "direction": "all", "total_flights": 100,
        "on_time_flights": 50, "cancelled_flights": 1, "delayed_flights": 49,
        "average_delay_minutes": 5.0, "early_share": 10.0, "on_time_share": 20.0,
        "small_delay_share": 5.0, "medium_delay_share": 5.0, "large_delay_share": 5.0,
    }])
    r = quality.check_band_sum(df)
    assert r.status == "fail"


# ---------------------------------------------------------------------------
# DQ-2: cancelled <= total
# ---------------------------------------------------------------------------
def test_dq2_cancelled_never_exceeds_total():
    bad = make_df([{
        "report_month": "2026-01-01", "airport": "Heathrow", "airline": "BA",
        "route": "", "direction": "all", "total_flights": 10,
        "on_time_flights": 5, "cancelled_flights": 12, "delayed_flights": 3,
        "average_delay_minutes": 5.0, "early_share": 0, "on_time_share": 50,
        "small_delay_share": 30, "medium_delay_share": 20, "large_delay_share": 0,
    }])
    assert quality.check_cancelled_le_total(bad).status == "fail"


# ---------------------------------------------------------------------------
# DQ-3: duplicates
# ---------------------------------------------------------------------------
def test_dq3_detects_duplicate_natural_key():
    base = {
        "report_month": "2026-01-01", "airport": "Heathrow", "airline": "BA",
        "route": "", "direction": "all", "total_flights": 100,
        "on_time_flights": 80, "cancelled_flights": 1, "delayed_flights": 19,
        "average_delay_minutes": 5.0, "early_share": 10, "on_time_share": 70,
        "small_delay_share": 15, "medium_delay_share": 4, "large_delay_share": 1,
    }
    df = make_df([base, base])
    assert quality.check_duplicates(df).status == "fail"


# ---------------------------------------------------------------------------
# DQ-4: missing months
# ---------------------------------------------------------------------------
def test_dq4_missing_months_flagged():
    df = make_df([{
        "report_month": "2026-01-01", "airport": "Heathrow", "airline": "BA",
        "route": "", "direction": "all", "total_flights": 100,
        "on_time_flights": 80, "cancelled_flights": 1, "delayed_flights": 19,
        "average_delay_minutes": 5.0, "early_share": 10, "on_time_share": 70,
        "small_delay_share": 15, "medium_delay_share": 4, "large_delay_share": 1,
    }])
    r = quality.check_missing_months(df, expected_months=["2026-01", "2026-02", "2026-03"])
    assert r.status == "fail"
    assert "2026-02" in r.detail["missing"]


# ---------------------------------------------------------------------------
# DQ-5: controlled airports
# ---------------------------------------------------------------------------
def test_dq5_unmapped_airport_reported():
    df = make_df([{
        "report_month": "2026-01-01", "airport": "Atlantis", "airline": "BA",
        "route": "", "direction": "all", "total_flights": 100,
        "on_time_flights": 80, "cancelled_flights": 1, "delayed_flights": 19,
        "average_delay_minutes": 5.0, "early_share": 10, "on_time_share": 70,
        "small_delay_share": 15, "medium_delay_share": 4, "large_delay_share": 1,
    }])
    r = quality.check_controlled_airports(df, ["Heathrow"])
    assert r.status == "fail"
    assert "Atlantis" in r.detail["unmapped"]


# ---------------------------------------------------------------------------
# DQ-7: outliers flagged, not deleted
# ---------------------------------------------------------------------------
def test_dq7_outlier_flagged():
    df = make_df([{
        "report_month": "2026-01-01", "airport": "Heathrow", "airline": "BA",
        "route": "", "direction": "all", "total_flights": 100,
        "on_time_flights": 50, "cancelled_flights": 10, "delayed_flights": 40,
        "average_delay_minutes": 95.0, "early_share": 0, "on_time_share": 50,
        "small_delay_share": 20, "medium_delay_share": 15, "large_delay_share": 15,
    }])
    r = quality.check_outliers(df)
    assert r.status == "warn"
    assert r.n_rows >= 1
