"""
ClimaZoneAI — Compute Renewable Energy Indices
----------------------------------------------
1. Loads cleaned_data.csv from preprocessing step.
2. Computes Solar, Wind, and Hydro indices.
3. Normalizes each index to [0,1].
4. Calculates Renewable_Score as their mean.
5. Saves processed_indices.csv.
"""

import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import MinMaxScaler

INPUT_FILE_WIDE = "data/processed_wide_format.csv"  # Wide format from prepare_data.py
INPUT_FILE_LONG = "data/cleaned_data_with_city_filled.csv"  # Fallback to long format
OUTPUT_FILE = "data/processed_indices.csv"


# ------------------------------------------------------------
# 1️⃣ Load data
# ------------------------------------------------------------
def load_cleaned_data():
    """Load data - tries wide format first, then long format."""
    
    # Try wide format first (preferred)
    if os.path.exists(INPUT_FILE_WIDE):
        print(f"📂 Loading wide-format data from {INPUT_FILE_WIDE}...")
        df = pd.read_csv(INPUT_FILE_WIDE, parse_dates=["date"])
        print(f"✅ Loaded {len(df):,} rows (wide format)")
        return df
    
    # Fallback to long format
    elif os.path.exists(INPUT_FILE_LONG):
        print(f"⚠️ Wide format not found. Loading long format from {INPUT_FILE_LONG}...")
        df = pd.read_csv(INPUT_FILE_LONG, parse_dates=["date"])
        print(f"✅ Loaded {len(df):,} rows (long format)")
        return df
    
    else:
        raise FileNotFoundError(f"❌ No data file found.")


# ------------------------------------------------------------
# 2️⃣ Compute raw indices
# ------------------------------------------------------------
def compute_raw_indices(df):
    # Ensure required columns exist with proper defaults
    for c in ["PRCP", "TAVG", "AWND", "WSF2", "SNOW", "SNWD"]:
        if c not in df.columns:
            df[c] = 0.0
    
    # Fill NaN values
    df["PRCP"] = df["PRCP"].fillna(0)
    df["SNOW"] = df["SNOW"].fillna(0)
    df["SNWD"] = df["SNWD"].fillna(0)
    df["TAVG"] = df["TAVG"].fillna(df["TAVG"].mean())
    df["AWND"] = df["AWND"].fillna(2.0)
    df["WSF2"] = df["WSF2"].fillna(3.0)

    # Add year-month for aggregation
    df['year_month'] = df['date'].dt.to_period('M')
    df['city_month'] = df['city'].astype(str) + '_' + df['year_month'].astype(str)
    
    # Calculate monthly cumulative precipitation per city (for hydro potential)
    monthly_precip = df.groupby('city_month')[['PRCP', 'SNOW', 'SNWD']].agg({
        'PRCP': 'sum',  # Total monthly precipitation
        'SNOW': 'sum',  # Total monthly snowfall
        'SNWD': 'mean'  # Average snow depth
    }).reset_index()
    monthly_precip.columns = ['city_month', 'monthly_PRCP', 'monthly_SNOW', 'monthly_SNWD']
    
    # Merge back to daily data
    df = df.merge(monthly_precip, on='city_month', how='left')
    
    # Solar: temperature vs precipitation (daily)
    df["Solar_raw"] = df["TAVG"] - (df["PRCP"] / 10.0)

    # Wind: mean of average wind and gusts (daily)
    df["Wind_raw"] = (df["AWND"] + df["WSF2"]) / 2.0

    # Hydro: REALISTIC FORMULA using monthly cumulative data
    # Canada has excellent hydro - reflect actual monthly water availability
    # This represents the water resources available for hydro generation
    df["Hydro_raw"] = (df["monthly_PRCP"] * 2.0) + (df["monthly_SNOW"] * 1.5) + (df["monthly_SNWD"] * 0.5)
    
    # Drop temporary columns
    df = df.drop(['year_month', 'city_month', 'monthly_PRCP', 'monthly_SNOW', 'monthly_SNWD'], axis=1)
    
    return df


# ------------------------------------------------------------
# 3️⃣ Normalize to [0,1] using robust scaling
# ------------------------------------------------------------
def normalize_indices(df):
    """
    Normalize indices using percentile-based scaling to handle outliers.
    This gives more balanced scores across all three energy types.
    """
    for col in ["Solar_raw", "Wind_raw", "Hydro_raw"]:
        norm_col = col.replace("_raw", "")
        
        # Use 5th and 95th percentiles instead of min/max to handle outliers
        p5 = df[col].quantile(0.05)
        p95 = df[col].quantile(0.95)
        
        # Clip values to percentile range and normalize
        df[norm_col] = (df[col].clip(p5, p95) - p5) / (p95 - p5)
        
        # Ensure values are between 0 and 1
        df[norm_col] = df[norm_col].clip(0, 1)
        
    print(f"✅ Normalized indices:")
    print(f"   Solar - mean: {df['Solar'].mean():.3f}, median: {df['Solar'].median():.3f}")
    print(f"   Wind  - mean: {df['Wind'].mean():.3f}, median: {df['Wind'].median():.3f}")
    print(f"   Hydro - mean: {df['Hydro'].mean():.3f}, median: {df['Hydro'].median():.3f}")
    
    return df


# ------------------------------------------------------------
# 4️⃣ Combine into Renewable Score
# ------------------------------------------------------------
def compute_combined_score(df):
    df["Renewable_Score"] = df[["Solar", "Wind", "Hydro"]].mean(axis=1)
    return df


# ------------------------------------------------------------
# 5️⃣ Save results
# ------------------------------------------------------------
def save_processed(df, path=OUTPUT_FILE):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"✅ Indexed dataset saved → {path}")


def main():
    df = load_cleaned_data()
    df = compute_raw_indices(df)
    df = normalize_indices(df)
    df = compute_combined_score(df)
    save_processed(df)


if __name__ == "__main__":
    main()
