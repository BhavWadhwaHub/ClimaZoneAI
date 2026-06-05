"""
ClimaZoneAI — Data Preprocessing Module
---------------------------------------
1. Loads GHCN (Canada) dataset.
2. Cleans missing / malformed values.
3. Infers missing variables using heuristics:
   - Temperature (TMIN, TMAX, TAVG)
   - Snow depth (SNOW, SNWD)
   - Wind speed (AWND, WSF2)
4. Converts tenths-based GHCN units to real-world values.
5. Outputs cleaned_data.csv for index computation.
"""

import pandas as pd
import numpy as np
import os

# === File paths ===
INPUT_FILE = "data/cleaned_data_with_city_filled.csv"  # your current final dataset
OUTPUT_FILE = "data/cleaned_data_verified.csv"



# ------------------------------------------------------------
# 1️⃣ Load and basic clean
# ------------------------------------------------------------
def load_data(path=INPUT_FILE):
    """Load GHCN dataset and parse dates."""
    df = pd.read_csv(path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    print(f"✅ Loaded {len(df)} raw rows from {path}")
    return df


# ------------------------------------------------------------
# 2️⃣ Unit conversion
# ------------------------------------------------------------
def convert_units(df):
    """Convert tenths-based values to standard units."""
    for col in ["TMAX", "TMIN", "TAVG", "PRCP", "SNOW", "SNWD"]:
        if col in df.columns:
            df[col] = df[col] / 10.0
    return df


# ------------------------------------------------------------
# 3️⃣ Infer missing variables
# ------------------------------------------------------------
def infer_missing_variables(df):
    """Infer temperature, snow, and wind values."""
    # ΔT heuristic based on elevation & latitude
    df["delta_T"] = np.clip(8 - 0.005 * df["elevation"] + 0.1 * abs(df["latitude"] - 45), 4, 12)

    # --- TEMPERATURE ---
    if "TAVG" in df and "TMAX" not in df:
        df["TMAX"] = df["TAVG"] + df["delta_T"] / 2
    if "TAVG" in df and "TMIN" not in df:
        df["TMIN"] = df["TAVG"] - df["delta_T"] / 2
    if "TMAX" in df and "TMIN" not in df:
        df["TMIN"] = df["TMAX"] - df["delta_T"]
    if "TMIN" in df and "TMAX" not in df:
        df["TMAX"] = df["TMIN"] + df["delta_T"]
    if "TAVG" not in df and {"TMIN", "TMAX"}.issubset(df.columns):
        df["TAVG"] = (df["TMIN"] + df["TMAX"]) / 2
    for c in ["TMIN", "TMAX", "TAVG"]:
        df[c] = df[c].clip(-50, 45)

    # --- SNOW / SNWD ---
    if "SNWD" in df and "SNOW" not in df:
        df["SNOW"] = 0.1 * df["SNWD"]
    elif "SNOW" in df and "SNWD" not in df:
        df["SNWD"] = 10 * df["SNOW"]
    else:
        df["SNOW"] = df.get("SNOW", 0)
        df["SNWD"] = df.get("SNWD", 0)

    # --- WIND ---
    # Estimate wind based on elevation, latitude, and precipitation
    df["AWND"] = (0.2 + 0.004 * df["elevation"] + 0.0008 * df["PRCP"] +
                  0.03 * abs(df["latitude"] - 45)).clip(0.5, 12)
    df["WSF2"] = 1.5 * df["AWND"]

    return df


# ------------------------------------------------------------
# 4️⃣ Save cleaned dataset
# ------------------------------------------------------------
def save_cleaned_data(df, path=OUTPUT_FILE):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"✅ Cleaned dataset saved → {path}")


def main():
    df = load_data()
    df = convert_units(df)
    df = infer_missing_variables(df)
    save_cleaned_data(df)


if __name__ == "__main__":
    main()
