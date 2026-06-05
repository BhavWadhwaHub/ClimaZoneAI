"""
ClimaZoneAI — Hybrid Forecasting Module (Prophet + XGBoost)
------------------------------------------------------------
- Uses Prophet for short-term (30-day) forecasts
- Uses XGBoost for 4-month and 1-year forecasts
- Falls back to Linear Regression if both unavailable
"""

import pandas as pd
import numpy as np
import os
from datetime import timedelta

# === Import available models ===
try:
    from models.prophet_model import ProphetForecast
    USE_PROPHET = True
except ImportError:
    USE_PROPHET = False

try:
    from models.xgboost_model import XGBoostForecast
    USE_XGBOOST = True
except ImportError:
    USE_XGBOOST = False

USE_LINEAR = False


# === File paths ===
INPUT_FILE = "data/processed_indices.csv"
OUTPUT_FILE = "data/forecast_results.csv"


# ------------------------------------------------------------
# 1️⃣ Load processed data
# ------------------------------------------------------------
def load_processed_data(path=INPUT_FILE):
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ Processed data not found: {path}")
    df = pd.read_csv(path, parse_dates=["date"], low_memory=False)
    print(f"✅ Loaded {len(df)} rows from {path}")
    return df


# ------------------------------------------------------------
# 2️⃣ Forecast logic
# ------------------------------------------------------------
def forecast_by_model(df, forecast_days, model_type):
    """Train and forecast with specified model type."""
    results = []
    groups = df.groupby(["province", "city"], dropna=False)

    for (prov, city), group in groups:
        try:
            if len(group) < 10:
                continue

            if model_type == "Prophet" and USE_PROPHET:
                model = ProphetForecast()
                model.train(group)
                forecast = model.predict(forecast_days)

            elif model_type == "XGBoost" and USE_XGBOOST:
                model = XGBoostForecast()
                model.train(group)
                forecast = model.predict_future(group, forecast_days)

            else:
                continue

            forecast["province"] = prov
            forecast["city"] = city
            forecast["model_used"] = model_type
            results.append(forecast)

        except Exception as e:
            print(f"⚠️ Forecast failed for {city}, {prov}: {e}")
            continue

    return pd.concat(results, ignore_index=True) if results else pd.DataFrame()


# ------------------------------------------------------------
# 3️⃣ Save results
# ------------------------------------------------------------
def save_forecast(df, path=OUTPUT_FILE):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"✅ Forecast results saved → {path}")


# ------------------------------------------------------------
# 4️⃣ Main
# ------------------------------------------------------------
def main():
    df = load_processed_data()

    # Prophet for short-term (30 days)
    print("\n🧙‍♂️ Running Prophet for 30-day forecast...")
    forecast_30 = forecast_by_model(df, forecast_days=30, model_type="Prophet")
    forecast_30["period"] = "30_days"

    # XGBoost for mid- and long-term
    print("\n⚡ Running XGBoost for 4-month (120-day) forecast...")
    forecast_120 = forecast_by_model(df, forecast_days=120, model_type="XGBoost")
    forecast_120["period"] = "4_months"

    print("\n⚡ Running XGBoost for 1-year (365-day) forecast...")
    forecast_365 = forecast_by_model(df, forecast_days=365, model_type="XGBoost")
    forecast_365["period"] = "1_year"

    # Combine all
    combined = pd.concat([forecast_30, forecast_120, forecast_365])
    save_forecast(combined)

    print("\n✅ Forecasting complete. Results combined and saved.")


if __name__ == "__main__":
    main()
