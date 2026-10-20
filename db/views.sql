-- Heathrow Punctuality Dashboard — KPI views (PRD §7 KPI definitions).
-- These are the analytical layer Power BI and Streamlit both read from.

-- ---------------------------------------------------------------------------
-- v_kpi_monthly: airport-month KPI summary with MoM and YoY change.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_kpi_monthly AS
WITH agg AS (
    SELECT
        report_month,
        airport,
        direction,
        SUM(total_flights)                                        AS total_flights,
        SUM(on_time_flights)                                      AS on_time_flights,
        SUM(cancelled_flights)                                    AS cancelled_flights,
        SUM(delayed_flights)                                      AS delayed_flights,
        SUM(total_flights * average_delay_minutes)
            / NULLIF(SUM(total_flights), 0)                       AS avg_delay_minutes,
        SUM(total_flights * on_time_share)
            / NULLIF(SUM(total_flights), 0)                       AS on_time_rate,
        SUM(total_flights * cancelled_flights_rate)
            / NULLIF(SUM(total_flights), 0)                       AS cancellation_rate,
        COUNT(*) FILTER (WHERE cancelled_flights > 0)             AS n_rows
    FROM (
        SELECT
            report_month, airport, direction, total_flights,
            on_time_flights, cancelled_flights, delayed_flights,
            average_delay_minutes,
            COALESCE(on_time_share, 0)                            AS on_time_share,
            CASE WHEN total_flights > 0
                 THEN cancelled_flights::float / total_flights ELSE 0 END AS cancelled_flights_rate
        FROM fact_punctuality
    ) t
    GROUP BY report_month, airport, direction
)
SELECT
    a.report_month,
    a.airport,
    a.direction,
    a.total_flights,
    COALESCE(a.on_time_flights, 0)                 AS on_time_flights,
    a.cancelled_flights,
    a.avg_delay_minutes,
    a.on_time_rate * 100.0                          AS on_time_rate_pct,
    a.cancellation_rate * 100.0                     AS cancellation_rate_pct,
    -- Month-on-month
    a.on_time_rate - LAG(a.on_time_rate) OVER (
        PARTITION BY a.airport, a.direction ORDER BY a.report_month
    )                                               AS on_time_mom,
    a.avg_delay_minutes - LAG(a.avg_delay_minutes) OVER (
        PARTITION BY a.airport, a.direction ORDER BY a.report_month
    )                                               AS avg_delay_mom,
    -- Year-on-year
    a.on_time_rate - LAG(a.on_time_rate, 12) OVER (
        PARTITION BY a.airport, a.direction ORDER BY a.report_month
    )                                               AS on_time_yoy,
    a.avg_delay_minutes - LAG(a.avg_delay_minutes, 12) OVER (
        PARTITION BY a.airport, a.direction ORDER BY a.report_month
    )                                               AS avg_delay_yoy
FROM agg a;

-- ---------------------------------------------------------------------------
-- v_kpi_rank: Heathrow's rank among the peer set for each KPI per month.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_kpi_rank AS
SELECT
    report_month,
    airport,
    direction,
    RANK() OVER (PARTITION BY report_month, direction ORDER BY on_time_rate_pct DESC)
        AS on_time_rank,
    RANK() OVER (PARTITION BY report_month, direction ORDER BY avg_delay_minutes ASC)
        AS avg_delay_rank,
    RANK() OVER (PARTITION BY report_month, direction ORDER BY cancellation_rate_pct ASC)
        AS cancellation_rank
FROM v_kpi_monthly;

-- ---------------------------------------------------------------------------
-- v_airline_route: airline (and route) contribution to delay/cancellations.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_airline_route AS
SELECT
    report_month,
    airport,
    airline,
    route,
    direction,
    SUM(total_flights)                                      AS total_flights,
    SUM(cancelled_flights)                                  AS cancelled_flights,
    SUM(total_flights * average_delay_minutes)
        / NULLIF(SUM(total_flights), 0)                     AS avg_delay_minutes,
    CASE WHEN SUM(total_flights) > 0
         THEN SUM(cancelled_flights)::float / SUM(total_flights) ELSE 0 END AS cancellation_rate
FROM fact_punctuality
GROUP BY report_month, airport, airline, route, direction;