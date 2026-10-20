# Power BI Data Model & DAX Specification — Heathrow Punctuality Dashboard

This document is the authoritative spec for building the Power BI report
(`dashboard/*.pbix`). Power BI `.pbix` files are a proprietary binary format
that cannot be authored by hand, so this spec captures every decision you need
to import the model and build the visuals in Power BI Desktop, connecting
directly to PostgreSQL.

## 1. Connection

| Setting | Value |
|---|---|
| Source | PostgreSQL database |
| Server | `localhost:5432` |
| Database | `punctuality` |
| Auth | `heathrow` / `heathrow` (see `.env`) |
| Import or DirectQuery | **Import** (works offline, snapshot per refresh) |

> Power BI Desktop needs the **NPGSQL** PostgreSQL connector (installed by
> default). Use "Get Data > PostgreSQL database".

## 2. Tables to import

Import these three tables/views:

1. `fact_punctuality` — the fact table.
2. `v_kpi_monthly` — month × airport × direction KPI summary (with MoM/YoY).
3. `v_kpi_rank` — Heathrow's rank among peers.
4. `v_airline_route` — airline/route detail.
5. `data_quality_log` — latest DQ run results (for the Data Quality page).

## 3. Relations (data model)

- Filter both `v_kpi_monthly` and `v_airline_route` by a shared **Month table**.
- Create a calculated **Date/Month table** and mark it as a date table:

```dax
Month = 
VAR _min = MIN(fact_punctuality[report_month])
VAR _max = MAX(fact_punctuality[report_month])
RETURN ADDCOLUMNS(
    CALENDAR(_min, _max),
    "MonthStart", EOMONTH([Date], -1) + 1,
    "YearMonth", FORMAT([Date], "YYYY-MM")
)
```

Relationships:
- `Month[MonthStart] 1 — * fact_punctuality[report_month]`
- `Month[MonthStart] 1 — * v_kpi_monthly[report_month]`
- `Month[MonthStart] 1 — * v_airline_route[report_month]`

## 4. DAX measures

```dax
// On-time performance (share of flights on time, CAA definition)
On Time Rate = 
    DIVIDE(SUM(fact_punctuality[on_time_flights]), SUM(fact_punctuality[total_flights]), 0)

// Average delay, minutes (weighted by flights)
Avg Delay = 
    DIVIDE(
        SUMX(fact_punctuality, fact_punctuality[total_flights] * fact_punctuality[average_delay_minutes]),
        SUM(fact_punctuality[total_flights]), 0)

// Cancellation rate
Cancellation Rate = 
    DIVIDE(SUM(fact_punctuality[cancelled_flights]), SUM(fact_punctuality[total_flights]), 0)

// Total flights
Total Flights = SUM(fact_punctuality[total_flights])

// Month-on-month change in on-time rate (percentage points)
On Time MoM = 
    VAR _cur = [On Time Rate]
    VAR _prev = CALCULATE([On Time Rate], PREVIOUSMONTH(Month[Date]))
    RETURN _cur - _prev

// Year-on-year change in on-time rate
On Time YoY = 
    VAR _cur = [On Time Rate]
    VAR _prev = CALCULATE([On Time Rate], SAMEPERIODLASTYEAR(Month[Date]))
    RETURN _cur - _prev

// Heathrow on-time rank among peers (1 = best)
On Time Rank = 
    RANKX(ALLSELECTED(fact_punctuality[airport]), [On Time Rate], , DESC)
```

## 5. Pages & visuals

### Page 1 — Overview
- KPI cards: `On Time Rate`, `Avg Delay`, `Cancellation Rate`, `Total Flights`,
  each with a `MoM` / `YoY` callout using `On Time MoM`, `On Time YoY`.
- Line chart: `On Time Rate` by `Month[Date]` (legend = `direction`).
- Line chart: `Avg Delay` by month.
- A vertical reference line marks the methodology change month
  (`METHOD_CHANGE_MONTH`, see `config.py`).

### Page 2 — Benchmark
- Bar chart: `On Time Rate` by `airport` (peers) for the selected month.
- Table: peers with `On Time Rate`, `Avg Delay`, `Cancellation Rate`, and rank.
- Slicer: month.

### Page 3 — Airlines & routes
- Bar chart: `Avg Delay` by `airline` (top N).
- Bar chart: `Cancellation Rate` by `route`.
- Table: airline × route with `Total Flights`, `Avg Delay`, `Cancellation Rate`.
- Drill-through to a route detail page (same filters).

### Page 4 — Data quality
- Table of `data_quality_log` (latest run), status colour-coded.
- Cards: count of `pass` / `fail` / `warn`.
- Text box: methodology-change marker + data source + refresh date.
- The CAA attribution footer (visible on every page).

### Global filters (all pages)
- Month range slicer (bound to `Month[Date]`).
- Airline slicer (`fact_punctuality[airline]`).
- Arrival / Departure slicer (`fact_punctuality[direction]`).

## 6. CAA attribution (required on every page)

> Source: UK Civil Aviation Authority monthly punctuality statistics.
> This project is independent and not affiliated with Heathrow.
> Non-commercial use only; full attribution in `README.md`.