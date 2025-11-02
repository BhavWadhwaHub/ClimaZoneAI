"""
ClimaZoneAI — Streamlit Visualization Dashboard
-----------------------------------------------
1. Loads forecast and ranking results.
2. Lets user select province and forecast period.
3. Displays line charts and top 3 renewable cities.

Run with:
    streamlit run src/visualize_dashboard.py
"""

import pandas as pd
import streamlit as st
import plotly.express as px
import os

# === File Paths ===
FORECAST_FILE = "data/forecast_results.csv"
TOP3_FILE = "data/top3_ranked_cities.csv"

# ------------------------------------------------------------
# 1️⃣ Load datasets
# ------------------------------------------------------------
@st.cache_data
def load_data():
    if not os.path.exists(FORECAST_FILE) or not os.path.exists(TOP3_FILE):
        st.error("⚠️ Missing forecast or ranking results. Please run compute and forecast steps first.")
        st.stop()

    forecast = pd.read_csv(FORECAST_FILE, parse_dates=["date"])
    top3 = pd.read_csv(TOP3_FILE)
    return forecast, top3


# ------------------------------------------------------------
# 2️⃣ App layout
# ------------------------------------------------------------
def main():
    st.set_page_config(page_title="ClimaZoneAI Dashboard", layout="wide")
    st.title("🌍 ClimaZoneAI — Renewable Energy Potential Across Canada")
    st.markdown("**AI-powered forecasting of Solar, Wind, and Hydro potential.**")

    forecast, top3 = load_data()

    # Sidebar filters
    provinces = sorted(top3["province"].unique())
    selected_province = st.sidebar.selectbox("Select Province", provinces)

    periods = ["30_days", "4_months", "1_year"]
    selected_period = st.sidebar.radio("Select Forecast Period", periods)

    # Filter data
    prov_forecast = forecast[
        (forecast["province"] == selected_province) &
        (forecast["period"] == selected_period)
    ]
    prov_top3 = top3[
        (top3["province"] == selected_province) &
        (top3["period"] == selected_period)
    ]

    # ------------------------------------------------------------
    # 3️⃣ Line Chart
    # ------------------------------------------------------------
    st.subheader(f"📈 Forecasted Renewable Score Trends — {selected_province} ({selected_period.replace('_', ' ')})")

    if prov_forecast.empty:
        st.warning("No forecast data available for this province.")
    else:
        fig = px.line(
            prov_forecast,
            x="date", y="forecast",
            color="city",
            title=f"Renewable Forecast per City in {selected_province}",
            labels={"forecast": "Predicted Renewable Score"},
        )
        fig.update_layout(height=500, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------
    # 4️⃣ Top 3 Table
    # ------------------------------------------------------------
    st.subheader(f"🏆 Top 3 Cities for Renewable Potential — {selected_province}")
    if prov_top3.empty:
        st.info("No top-ranked cities available yet.")
    else:
        st.dataframe(prov_top3[["city", "avg_forecast"]]
                     .rename(columns={"city": "City", "avg_forecast": "Forecast Score"})
                     .style.background_gradient(cmap="Greens"))

    # ------------------------------------------------------------
    # 5️⃣ Footer
    # ------------------------------------------------------------
    st.markdown("---")
    st.markdown("**Developed by ClimaZoneAI Team — DSSS DataJam 2025** 🌤️")


if __name__ == "__main__":
    main()
