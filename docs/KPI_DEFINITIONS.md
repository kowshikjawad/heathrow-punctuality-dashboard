# KPI Definitions

These definitions are written for a non-technical reader. The SQL
implementation is in `db/views.sql`, and the DAX is in
`dashboard/POWER_BI_SPEC.md`.

## 1. On-time performance

> **Definition**: the share of flights that operated on time.

On-time share = on-time flights ÷ total flights, expressed as a percentage.

*The exact meaning of "on time" follows the CAA's published definition — e.g.
arrivals within 15 minutes of schedule — and is stated verbatim here once the
source documentation is inspected.*

**Example**: if 80 of 100 flights were on time, on-time performance is 80%.

## 2. Average delay

> **Definition**: the mean delay, in minutes, across the flights in the slice.

Delays are averaged across **all** flights (including on-time flights, which
count as zero or a small negative value for early flights), so this number
reflects delay across the whole operation, not just late flights.

## 3. Cancellation rate

> **Definition**: the share of flights that were cancelled.

Cancellation rate = cancelled flights ÷ total flights.

**Example**: 2 cancellations out of 100 flights is a 2% cancellation rate.

## 4. Delay-band distribution

> **Definition**: the share of flights falling into each delay band (early,
> on-time, small, medium, large), summing to 100%.

The band boundaries are the CAA's published thresholds and are recorded in the
data dictionary.

## 5. Month-on-month and year-on-year change

- **MoM**: this month's KPI minus last month's KPI.
- **YoY**: this month's KPI minus the same month last year.

Both are expressed in the KPI's own units (percentage points for rates,
minutes for delay).

## 6. Rank among the peer set

> **Definition**: Heathrow's position (1 = best) among the peer airports —
> Gatwick, Manchester, Stansted, Luton, Birmingham — for a given KPI and month.

For rates, lower is better (so cancellation rate ranks ascending); for on-time
share, higher is better (ranks descending).

---

## Methodology note

The CAA changed its punctuality calculation method at a specific point. Months
on either side of that point are **not directly comparable**. The dashboard
identifies this change point (`METHOD_CHANGE_MONTH`) and flags it on charts
rather than blending the two series silently.