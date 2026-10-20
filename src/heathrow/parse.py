"""FR-2: parse and standardise CAA punctuality files.

This module defines the canonical internal schema and provides parsers that
turn raw CAA files into tidy DataFrames with standardised airports, airlines,
routes, dates and units.
"""

from __future__ import annotations

from dataclasses import dataclass

# Canonical column names for the staged table (see db/schema.sql and the
# data dictionary). Parsers must emit a DataFrame with exactly these columns.
STAGE_COLUMNS = [
    "report_month",  # 'YYYY-MM' (YYYY-MM-01 as date)
    "airport",       # standardised airport name
    "airline",       # standardised airline name
    "route",         # route label, or '' for airport-level rows
    "direction",     # 'arrival' | 'departure' | 'all'
    "total_flights", # int
    "on_time_flights",  # int (CAA on-time definition, see KPI sheet)
    "cancelled_flights",  # int
    "delayed_flights",  # int (late by CAA threshold)
    "average_delay_minutes",  # float
    "early_share",  # share (0-100)
    "on_time_share",  # share (0-100)
    "small_delay_share",  # share (0-100)
    "medium_delay_share",  # share (0-100)
    "large_delay_share",  # share (0-100)
]


@dataclass(frozen=True)
class ParseResult:
    frame: object  # pandas.DataFrame
    source: str
    notes: list[str]


# Airline name standardisation map (extend as real names are discovered).
AIRLINE_ALIASES = {
    "BRITISH AIRWAYS": "British Airways",
    "BA": "British Airways",
    "EASYJET": "easyJet",
    "VIRGIN ATLANTIC": "Virgin Atlantic",
}


def standardise_airport(name: str) -> str:
    """Map an airport name onto the controlled list, preserving title case."""
    if not name:
        return name
    cleaned = " ".join(name.split()).title()
    # Common fixups for the peer set.
    fixes = {
        "London Heathrow": "Heathrow",
        "Heathrow Airport": "Heathrow",
        "London Gatwick": "Gatwick",
        "Gatwick Airport": "Gatwick",
        "London Stansted": "Stansted",
        "Stansted Airport": "Stansted",
        "London Luton": "Luton",
        "Luton Airport": "Luton",
        "Manchester Airport": "Manchester",
        "Birmingham Airport": "Birmingham",
    }
    return fixes.get(cleaned, cleaned)


def standardise_airline(name: str) -> str:
    """Map an airline name onto a canonical form."""
    if not name:
        return name
    key = " ".join(name.split()).upper()
    return AIRLINE_ALIASES.get(key, " ".join(name.split()).title())


def standardise_route(label: str) -> str:
    """Normalise a route label (e.g. 'LHR-JFK' stays as-is, whitespace trimmed)."""
    return " ".join((label or "").split())


__all__ = [
    "STAGE_COLUMNS",
    "ParseResult",
    "standardise_airport",
    "standardise_airline",
    "standardise_route",
]
