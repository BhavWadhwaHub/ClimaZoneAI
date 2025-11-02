"""
ClimaZoneAI — Ranking Module
----------------------------
1. Loads forecast_results.csv (from forecast_model.py)
2. Groups by province and forecast period
3. Computes the mean forecast score for each city
4. Ranks cities by renewable potential
5. Outputs top 3 cities per province and period

Author: ClimaZoneAI Team
Version: 2.0
"""

import pandas as pd
import os

INPUT_FILE = "data/forecast_results.csv"
OUTPUT_FILE = "data/top3_ranked_cities.csv"


# ------------------------------------------------------------
# 1️⃣ Load forecast results
# ------------------------------------------------------------
def load_forecasts(path=INPUT_FILE):
    """Load forecast data with city, province, forecast, and period."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ Forecast file not found: {path}")
    df = pd.read_csv(path, parse_dates=["date"], low_memory=False)
    print(f"✅ Loaded {len(df)} forecasted rows from {path}")
    return df


# ------------------------------------------------------------
# 2️⃣ Rank top 3 per province and forecast period
# ------------------------------------------------------------
def rank_top_cities(df):
    """Compute average forecast per city and rank top 3 per province and period."""
    summary = (
        df.groupby(["province", "city", "period"], as_index=False)["forecast"]
          .mean()
          .rename(columns={"forecast": "avg_forecast"})
    )

    top_cities = (
        summary.sort_values(["province", "period", "avg_forecast"], ascending=[True, True, False])
               .groupby(["province", "period"])
               .head(3)
               .reset_index(drop=True)
    )

    print(f"✅ Ranked top 3 cities for {top_cities['province'].nunique()} provinces.")
    return top_cities


# ------------------------------------------------------------
# 3️⃣ Save results
# ------------------------------------------------------------
def save_ranked(df, path=OUTPUT_FILE):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"🏆 Top 3 results saved → {path}")


# ------------------------------------------------------------
# 4️⃣ Main
# ------------------------------------------------------------
def main():
    df = load_forecasts()
    top_cities = rank_top_cities(df)
    save_ranked(top_cities)

    print("\n🌎 Sample of Top Results:")
    print(top_cities.head(12))


if __name__ == "__main__":
    main()
