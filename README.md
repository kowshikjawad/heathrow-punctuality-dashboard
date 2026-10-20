# UK Airport Punctuality Dashboard (Heathrow Focus)

A data pipeline and decision-support dashboard that turns the UK Civil
Aviation Authority's public monthly punctuality statistics into a single,
trustworthy view of how Heathrow performs on punctuality, how it compares with
peer UK airports, and where delays concentrate by airline and route.

> **Attribution** — Source data: UK Civil Aviation Authority monthly
> punctuality statistics. This is an independent portfolio project, **not
> affiliated with Heathrow**, and uses **no Heathrow internal data**. It is
> non-commercial. See [Attribution & licensing](#attribution--licensing).

---

## What this project answers

1. How has Heathrow's on-time performance changed month by month?
2. How does Heathrow compare with other major UK airports?
3. Which airlines and routes contribute most to delay and cancellations?
4. Do arrivals and departures behave differently?
5. Can I trust this month's figures, and what changed in the data?

---

## Architecture

```
data/sources.json   ->  heathrow/download (FR-1)   ->  data/raw/   (unchanged)
data/raw/*          ->  heathrow/parse    (FR-2)   ->  tidy DataFrame
tidy rows           ->  heathrow/load     (FR-3)   ->  PostgreSQL fact_punctuality
tidy rows           ->  heathrow/quality  (FR-4)   ->  data_quality_log
PostgreSQL          ->  db/views.sql (KPIs)        ->  Power BI / Streamlit
```

| Component | FR | Path |
|---|---|---|
| Download raw files | FR-1 | `src/heathrow/download.py` |
| Parse & standardise | FR-2 | `src/heathrow/parse.py` |
| Load to PostgreSQL | FR-3 | `src/heathrow/load.py`, `db/schema.sql` |
| Data-quality checks | FR-4 | `src/heathrow/quality.py` |
| Re-runnable pipeline | FR-5 | `src/heathrow/cli.py` |
| KPI views | §7 | `db/views.sql` |
| Power BI spec | §8 | `dashboard/POWER_BI_SPEC.md` |
| Streamlit fallback | §8 | `app/` |

---

## Prerequisites

- **Docker Desktop** (for PostgreSQL) — running.
- **Python 3.11+** with **uv** (or `pip`).
- **Power BI Desktop** (optional, for the Power BI report; the data model spec
  is in `dashboard/POWER_BI_SPEC.md`).

---

## Quick start

```powershell
# 1. Start PostgreSQL
docker compose up -d

# 2. Create a virtualenv and install
uv venv
uv pip install -e ".[dev]"

# 3. Run the pipeline (download -> parse -> load -> DQ)
py -3 -m heathrow.cli run

# 4. Run data-quality checks against the loaded data
py -3 -m heathrow.cli dq

# 5. (Optional) launch the Streamlit fallback dashboard
py -3 -m streamlit run app/Home.py
```

Configuration lives in `.env` (copy from `.env.example`) and
`src/heathrow/config.py`.

---

## Data quality (PRD §8)

| Check | Rule |
|---|---|
| DQ-1 | Delay-band shares sum to ~100% (tolerance ±1.0 pt) |
| DQ-2 | Cancelled flights never exceed total flights |
| DQ-3 | No duplicate rows per airport/airline/route/month/direction |
| DQ-4 | No missing months inside the chosen range |
| DQ-5 | Airport/airline names map to a controlled list |
| DQ-6 | Detailed totals reconcile with summary totals |
| DQ-7 | Outliers flagged for review, never deleted |

Results are written to `data_quality_log` on every load and shown on the Data
Quality dashboard page.

---

## Methodology change marker

The CAA introduced a new punctuality calculation method; older months may not
be directly comparable with newer ones. The change point is recorded in
`METHOD_CHANGE_MONTH` (see `config.py`) and flagged on charts rather than
silently blending the series. **Set this once the exact month is confirmed
from the CAA source documentation.**

---

## Documentation

- [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md) — field names and definitions.
- [`docs/KPI_DEFINITIONS.md`](docs/KPI_DEFINITIONS.md) — KPI definitions for non-technical readers.
- [`docs/INSIGHTS.md`](docs/INSIGHTS.md) — three findings with recommended actions.
- [`dashboard/POWER_BI_SPEC.md`](dashboard/POWER_BI_SPEC.md) — Power BI data model, DAX and page specs.

---

## Tests & lint

```powershell
py -3 -m pytest      # parsing + DQ rules
py -3 -m ruff check src tests
```

---

## Attribution & licensing

- **CAA attribution**: any publication using these statistics must reference
  the UK Civil Aviation Authority. Acknowledged in the dashboard footer and
  throughout the docs.
- **Non-commercial**: the CAA does not permit the data to be sold on. This
  project is non-commercial.
- **Personas** in the PRD are assumed, not researched.

---

## Repository structure

```
.
├── app/                  # Streamlit fallback dashboard
├── dashboard/            # Power BI spec (and .pbix, gitignored)
├── data/                 # sources.json + raw/processed (gitignored)
├── db/                   # schema.sql, views.sql
├── docs/                 # data dictionary, KPI definitions, insights
├── src/heathrow/         # pipeline package
├── tests/                # pytest suite
├── docker-compose.yml    # PostgreSQL
├── pyproject.toml
└── Makefile
```