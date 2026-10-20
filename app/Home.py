"""Streamlit fallback dashboard (PRD §13 mitigation).

Runs against PostgreSQL. If the DB is unavailable, a helpful message is shown
so the app still launches. Launch: `python -m streamlit run app/Home.py`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

# Allow running from repo root without installing.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

st.set_page_config(page_title="Heathrow Punctuality", page_icon="✈️", layout="wide")

FOOTER = (
    "Source: UK Civil Aviation Authority monthly punctuality statistics. "
    "Independent portfolio project — not affiliated with Heathrow. Non-commercial."
)


@st.cache_resource
def get_engine():
    from sqlalchemy import create_engine

    url = os.getenv("DATABASE_URL", "postgresql+psycopg://heathrow:heathrow@localhost:5432/punctuality")
    return create_engine(url)


def main():
    st.title("✈️ UK Airport Punctuality Dashboard")
    st.caption("Heathrow focus — built on public CAA data.")

    import pandas as pd
    from sqlalchemy import text

    engine = get_engine()
    try:
        with engine.connect() as conn:
            df = pd.read_sql("SELECT * FROM v_kpi_monthly WHERE airport = 'Heathrow' ORDER BY report_month", conn)
    except Exception as exc:  # noqa: BLE001
        st.warning(
            "Could not reach the database. Start it with `docker compose up -d`, "
            "then run `python -m heathrow.cli run`."
        )
        st.code(str(exc))
        st.markdown(FOOTER)
        return

    if df.empty:
        st.info("No data loaded yet. Run the pipeline: `python -m heathrow.cli run`.")
        st.markdown(FOOTER)
        return

    # Sidebar filters (PRD §8: month range, airline, direction)
    airports = ["Heathrow"]  # peer set available once data includes peers
    st.sidebar.header("Filters")
    direction = st.sidebar.selectbox("Arrival / Departure", ["all", "arrival", "departure"])

    view = df[df["direction"] == direction] if direction != "all" else df

    col1, col2, col3, col4 = st.columns(4)
    latest = view.iloc[-1]
    col1.metric("On-time rate", f"{latest['on_time_rate_pct']:.1f}%")
    col2.metric("Avg delay", f"{latest['avg_delay_minutes']:.1f} min")
    col3.metric("Cancellation rate", f"{latest['cancellation_rate_pct']:.2f}%")
    col4.metric("Total flights", f"{int(latest['total_flights']):,}")

    st.subheader("On-time performance by month")
    import plotly.express as px

    fig = px.line(view, x="report_month", y="on_time_rate_pct", markers=True)
    fig.update_yaxes(title="On-time rate (%)")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Average delay by month")
    fig2 = px.line(view, x="report_month", y="avg_delay_minutes", markers=True)
    fig2.update_yaxes(title="Average delay (minutes)")
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.markdown(FOOTER)


if __name__ == "__main__":
    main()