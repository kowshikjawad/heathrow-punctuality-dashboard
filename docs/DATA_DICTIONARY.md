# Data Dictionary

This documents the canonical internal schema. The exact CAA source-column
names are confirmed by inspecting the downloaded files and recorded here.

## fact_punctuality

| Column | Type | Definition |
|---|---|---|
| `report_month` | date | Reporting month; always the first of the month (`YYYY-MM-01`). |
| `airport` | text | Standardised airport name from the controlled list. |
| `airline` | text | Standardised airline name. |
| `route` | text | Route label (e.g. `LHR-JFK`); empty for airport-level rows. |
| `direction` | text | `arrival`, `departure`, or `all`. |
| `total_flights` | int | Total flights for the slice. |
| `on_time_flights` | int | Flights on time (CAA definition — see KPI definitions). |
| `cancelled_flights` | int | Cancelled flights. |
| `delayed_flights` | int | Flights delayed beyond the CAA threshold. |
| `average_delay_minutes` | float | Average delay in minutes. |
| `early_share` | float | Share of flights arriving/departing early (0–100). |
| `on_time_share` | float | Share of flights on time (0–100). |
| `small_delay_share` | float | Share with a small delay (0–100). |
| `medium_delay_share` | float | Share with a medium delay (0–100). |
| `large_delay_share` | float | Share with a large delay (0–100). |

**Natural key**: (`report_month`, `airport`, `airline`, `route`, `direction`) —
enforced with a unique constraint (DQ-3).

## Units & conventions

- **Shares** are percentages in the range 0–100.
- **Average delay** is in minutes.
- **Dates** are stored as `date` (first of month).
- **Names** are title-cased and mapped onto controlled lists (`airport`,
  `airline`); unmapped values are reported by DQ-5.

## Delay bands

The delay-band boundaries follow the CAA's published definitions. These must be
recorded verbatim from the source once the files are inspected. Until then,
the band columns above are the placeholder for whatever bands the CAA files
provide (typically early / on-time / small / medium / large).

## Controlled lists

- **Airports** (peer set): Heathrow, Gatwick, Manchester, Stansted, Luton,
  Birmingham — to be confirmed against the published airport list.
- **Airlines**: mapped via `AIRLINE_ALIASES` in `src/heathrow/parse.py`; the map
  grows as real names are discovered during inspection.