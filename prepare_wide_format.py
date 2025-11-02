"""
Convert long format data to wide format for processing.
"""
import pandas as pd
import numpy as np

# Load long format data
print("📂 Loading long format data...")
df = pd.read_csv('data/cleaned_data_with_city_filled.csv')
print(f"✅ Loaded {len(df):,} rows")

# Convert to wide format - pivot observation types into columns
print("🔄 Converting to wide format...")
df_wide = df.pivot_table(
    index=['station', 'date', 'city', 'city_province', 'latitude', 'longitude', 'elevation', 'name'],
    columns='observation',
    values='value',
    aggfunc='first'  # Take first value if there are duplicates
).reset_index()

# Rename city_province to province
df_wide = df_wide.rename(columns={'city_province': 'province'})

print(f"✅ Converted to wide format: {len(df_wide):,} rows, {len(df_wide.columns)} columns")
print(f"📊 Columns: {', '.join(df_wide.columns)}")

# Save wide format
df_wide.to_csv('data/processed_wide_format.csv', index=False)
print("✅ Saved to data/processed_wide_format.csv")