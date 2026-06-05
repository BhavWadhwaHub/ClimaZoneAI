"""
ClimaZoneAI - Data Preparation Script
--------------------------------------
Converts long-format CSV to wide-format and adds province column.
"""

import pandas as pd
import numpy as np
import os

INPUT_FILE = "data/cleaned_data_with_city_filled.csv"
OUTPUT_FILE = "data/processed_wide_format.csv"


def load_data(path=INPUT_FILE):
    """Load the long-format CSV data."""
    print(f"📂 Loading data from {path}...")
    df = pd.read_csv(path)
    print(f"✅ Loaded {len(df):,} rows (long format)")
    return df


def pivot_data(df):
    """Convert long format to wide format."""
    print("🔄 Converting long format → wide format...")
    
    # Pivot: observations as columns
    df_pivot = df.pivot_table(
        index=['station', 'date', 'latitude', 'longitude',
               'elevation', 'name', 'city', 'city_province'],
        columns='observation',
        values='value',
        aggfunc='first'  # Take first value if duplicates
    ).reset_index()
    
    # Extract province from city_province
    # The city_province column already contains just the province name
    print("🗺️ Extracting province column...")
    df_pivot['province'] = df_pivot['city_province']
    
    print(f"✅ Converted to wide format: {len(df_pivot):,} rows × {len(df_pivot.columns)} columns")
    return df_pivot


def add_wind_columns(df):
    """Add AWND and WSF2 columns if they don't exist (using geographic inference)."""
    if 'AWND' not in df.columns or 'WSF2' not in df.columns:
        print("💨 Inferring wind data from geography...")
        
        # Fill NaN for calculations
        df['PRCP'] = df.get('PRCP', 0).fillna(0)
        df['latitude'] = df['latitude'].fillna(45)
        df['elevation'] = df['elevation'].fillna(0)
        
        # Geographic wind model
        df['AWND'] = (0.2 + 0.004 * df['elevation'] + 
                      0.0008 * df['PRCP'] +
                      0.03 * abs(df['latitude'] - 45)).clip(0.5, 12)
        
        df['WSF2'] = 1.5 * df['AWND']  # Gusts are typically 1.5x sustained wind
        
        print("✅ Wind columns added")
    
    return df


def save_data(df, path=OUTPUT_FILE):
    """Save the wide-format data."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"💾 Saved wide-format data → {path}")


def main():
    print("\n" + "="*60)
    print("  ClimaZoneAI - Data Preparation Pipeline")
    print("="*60 + "\n")
    
    # Load
    df = load_data()
    
    # Convert to wide format
    df = pivot_data(df)
    
    # Add wind inference if needed
    df = add_wind_columns(df)
    
    # Save
    save_data(df)
    
    print("\n✅ Data preparation complete!")
    print(f"📊 Final dataset: {len(df):,} rows × {len(df.columns)} columns")
    print("\nNext step: Run 'python3 src/compute_indices.py'\n")


if __name__ == "__main__":
    main()

