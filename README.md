# ClimaZoneAI

ClimaZoneAI is a Python-based renewable energy analysis and forecasting project for Canadian cities. It uses historical weather observations to calculate normalized solar, wind, hydro, and combined renewable energy potential scores, then visualizes the results through either a static HTML dashboard or a Streamlit dashboard.

The project includes prepared data files, data-processing scripts, forecasting model code, dashboard-generation code, and a prebuilt dashboard at `web/dashboard.html`.

## Project Status

This repository is partly ready to view and partly experimental for model training.

The static dashboard is already generated and can be opened directly from:

```text
web/dashboard.html
```

The main data pipeline is present and can regenerate the processed datasets and dashboard from the included CSV files.

The Streamlit forecasting app and some model modules need dependency and code cleanup before every forecasting feature will run smoothly. In particular, the repository contains code that imports XGBoost, but `xgboost` is not listed in `requirements.txt`. Also, some files call `ProphetForecast.predict()` with an `include_uncertainty` argument, but the current `ProphetForecast.predict()` method only accepts `days_ahead`.

## What the Project Does

ClimaZoneAI takes weather observations for Canadian locations and converts them into renewable energy potential indicators:

- **Solar index**: based mainly on average temperature and precipitation.
- **Wind index**: based on average wind speed and wind gust estimates.
- **Hydro index**: based on monthly precipitation, snowfall, and snow depth.
- **Renewable score**: the average of the solar, wind, and hydro indices.

The project then uses these scores to support visualization and forecasting of renewable energy potential by city and province.

## Included Dataset Summary

The repository includes three main CSV files inside the `data/` folder.

| File | Purpose | Observed Shape / Notes |
|---|---|---|
| `data/cleaned_data_with_city_filled.csv` | Cleaned long-format weather dataset | 103,246 rows and 10 columns |
| `data/processed_wide_format.csv` | Wide-format dataset created from the cleaned data | Contains weather observation types as columns |
| `data/processed_indices.csv` | Final processed dataset with renewable indices | 95,848 rows and 24 columns |

The processed index dataset contains data for:

- **231 cities**
- **13 provinces/territories**

The province/territory values present in the processed dataset are:

- Alberta
- British Columbia
- Manitoba
- New Brunswick
- Newfoundland and Labrador
- Northwest Territories
- Nova Scotia
- Nunavut
- Ontario
- Prince Edward Island
- Québec
- Saskatchewan
- Yukon

## Main Features

### 1. Long-to-Wide Weather Data Preparation

`src/prepare_data.py` loads the cleaned long-format dataset and pivots observation types into separate columns.

Input:

```text
data/cleaned_data_with_city_filled.csv
```

Output:

```text
data/processed_wide_format.csv
```

The script also creates a `province` column from `city_province`.

If wind columns are missing, the script creates estimated wind fields:

- `AWND`
- `WSF2`

These are inferred from available geographic/weather fields such as elevation, precipitation, and latitude. This should be treated as an estimate, not measured wind data.

### 2. Renewable Energy Index Calculation

`src/compute_indices.py` calculates raw and normalized renewable energy indices.

Input:

```text
data/processed_wide_format.csv
```

Fallback input, if the wide file is missing:

```text
data/cleaned_data_with_city_filled.csv
```

Output:

```text
data/processed_indices.csv
```

The generated columns include:

- `Solar_raw`
- `Wind_raw`
- `Hydro_raw`
- `Solar`
- `Wind`
- `Hydro`
- `Renewable_Score`

The normalized indices are scaled between 0 and 1 using 5th and 95th percentile clipping, instead of direct min-max scaling. This helps reduce the effect of extreme outliers.

### 3. Static HTML Dashboard

`generate_html_dashboard.py` generates a standalone dashboard file:

```text
web/dashboard.html
```

The dashboard uses Plotly.js through a CDN and includes interactive city/province selection, historical index charts, and simple forecasts based on historical monthly patterns.

The static dashboard does not require Streamlit or a Python server once it has already been generated.

### 4. Streamlit Dashboard

`app.py` defines an interactive Streamlit dashboard with:

- Province and city selection
- Historical solar, wind, hydro, and renewable score plots
- Forecast horizon selection
- Model-based forecasting sections
- Plotly visualizations

Run it with:

```bash
streamlit run app.py
```

Important: some model-based Streamlit features may need fixes before they work fully because of the current Prophet method-signature mismatch and the missing XGBoost dependency in `requirements.txt`.

### 5. Forecasting Models

The `models/` folder contains forecasting classes:

| File | Purpose |
|---|---|
| `models/prophet_model.py` | Wraps Meta Prophet for time-series forecasting of `Renewable_Score` |
| `models/xgboost_model.py` | Uses `XGBRegressor` with weather, lag, and rolling features |
| `models/ensemble_model.py` | Combines Prophet and XGBoost forecasts using weighted averaging |

There is also `src/forecast_model.py`, which is designed to run forecasts across city/province groups and save results to:

```text
data/forecast_results.csv
```

However, `data/forecast_results.csv` is not included in the current project files.

### 6. City Ranking Module

`src/rank_top_cities.py` ranks cities by average forecast score for each province and forecast period.

It expects this input file:

```text
data/forecast_results.csv
```

It outputs:

```text
data/top3_ranked_cities.csv
```

Since `forecast_results.csv` is not included, this ranking step requires `src/forecast_model.py` to run successfully first.

## Tech Stack

### Python Libraries Used

The listed `requirements.txt` includes:

- `pandas`
- `numpy`
- `scikit-learn`
- `prophet`
- `plotly`
- `streamlit`
- `python-dateutil`
- `pytz`
- `matplotlib`

### Additional Dependency Needed for XGBoost Features

The code imports:

```python
from xgboost import XGBRegressor
```

but `xgboost` is not currently listed in `requirements.txt`.

To use the XGBoost or ensemble model files, install it manually:

```bash
pip install xgboost
```

or add it to `requirements.txt`:

```text
xgboost
```

## Project Structure

This is the actual structure found in the uploaded project:

```text
ClimaZoneAI-main/
├── DataJam.zip
├── Enerlytics.pptx
├── File Structure.txt
├── README.md
├── app.py
├── dataclean.ipynb
├── generate_html_dashboard.py
├── ghnc_canada_cleanup.r
├── prepare_wide_format.py
├── requirements.txt
├── run_project.bat
├── run_project.sh
├── data/
│   ├── cleaned_data_with_city_filled.csv
│   ├── processed_indices.csv
│   └── processed_wide_format.csv
├── models/
│   ├── __init__.py
│   ├── _init_.py
│   ├── ensemble_model.py
│   ├── prophet_model.py
│   └── xgboost_model.py
├── src/
│   ├── _init_.py
│   ├── compute_indices.py
│   ├── data_processing.py
│   ├── forecast_model.py
│   ├── prepare_data.py
│   ├── rank_top_cities.py
│   └── visualization_dashboard.py
└── web/
    └── dashboard.html
```

Note: `File Structure.txt` describes some folders and files that are not actually present in the uploaded repository, such as `outputs/`, `notebooks/`, `forecast_results.csv`, and some differently named source files. The structure above reflects the real uploaded files.

## How to Run the Project

### Option 1: Open the Existing Static Dashboard

This is the fastest way to view the project.

On macOS/Linux:

```bash
open web/dashboard.html
```

On Windows:

```cmd
start web\dashboard.html
```

You can also double-click `web/dashboard.html` in your file explorer.

### Option 2: Install Dependencies

Create and activate a virtual environment if desired:

```bash
python -m venv .venv
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Windows:

```cmd
.venv\Scripts\activate
```

Install the listed dependencies:

```bash
pip install -r requirements.txt
```

For XGBoost-related functionality, also install:

```bash
pip install xgboost
```

### Option 3: Run the Data Pipeline Manually

From the project root:

```bash
python src/prepare_data.py
python src/compute_indices.py
python generate_html_dashboard.py
```

Expected outputs:

```text
data/processed_wide_format.csv
data/processed_indices.csv
web/dashboard.html
```

### Option 4: Run the Helper Script

macOS/Linux:

```bash
chmod +x run_project.sh
./run_project.sh
```

Windows:

```cmd
run_project.bat
```

These scripts run the preparation step, index calculation step, and dashboard generation step, then open the dashboard.

### Option 5: Run the Streamlit App

```bash
streamlit run app.py
```

Use this option for the Python-based interactive dashboard. The static dashboard is more reliable for quick viewing because it is already generated.

## Data Processing Workflow

The main workflow is:

```text
cleaned_data_with_city_filled.csv
        ↓
src/prepare_data.py
        ↓
processed_wide_format.csv
        ↓
src/compute_indices.py
        ↓
processed_indices.csv
        ↓
generate_html_dashboard.py
        ↓
web/dashboard.html
```

Optional forecasting and ranking workflow:

```text
processed_indices.csv
        ↓
src/forecast_model.py
        ↓
forecast_results.csv
        ↓
src/rank_top_cities.py
        ↓
top3_ranked_cities.csv
```

The optional workflow may require fixing dependencies and model-code issues before it runs completely.

## Renewable Index Methodology

### Solar Raw Score

The solar raw score is calculated as:

```text
Solar_raw = TAVG - (PRCP / 10.0)
```

This means higher average temperature increases the solar score, while precipitation reduces it.

### Wind Raw Score

The wind raw score is calculated as:

```text
Wind_raw = (AWND + WSF2) / 2.0
```

If `AWND` and `WSF2` are not present in the wide-format data, `src/prepare_data.py` estimates them from geographic/weather features.

### Hydro Raw Score

The hydro raw score uses monthly aggregated precipitation and snow variables:

```text
Hydro_raw = (monthly_PRCP * 2.0) + (monthly_SNOW * 1.5) + (monthly_SNWD * 0.5)
```

This is different from a daily-only hydro formula because the script treats hydro potential as related to monthly water availability.

### Normalized Indices

Each raw score is normalized to a 0-to-1 range after clipping values to the 5th and 95th percentiles.

The final renewable score is:

```text
Renewable_Score = mean(Solar, Wind, Hydro)
```

## Important Limitations

This project should be understood as a data-analysis and demonstration project, not a production-grade renewable energy planning tool.

Current limitations include:

- Wind values may be estimated when measured wind columns are missing.
- The renewable indices are heuristic scores, not direct measurements of real energy output in kWh.
- The static dashboard forecasts use historical monthly patterns rather than the Prophet/XGBoost classes.
- The Streamlit app and ensemble model call `ProphetForecast.predict()` with an unsupported `include_uncertainty` argument in the current code.
- `xgboost` is required by `models/xgboost_model.py`, but it is not listed in `requirements.txt`.
- `data/forecast_results.csv` and `data/top3_ranked_cities.csv` are not included in the uploaded repository.
- `src/forecast_model.py` references a fallback `models.regression_model.LinearForecast`, but `models/regression_model.py` is not included.
- The included `File Structure.txt` does not fully match the actual uploaded project structure.

## Known Issues and Fixes

### Issue: `ModuleNotFoundError: No module named 'xgboost'`

Install XGBoost:

```bash
pip install xgboost
```

Also consider adding it to `requirements.txt`.

### Issue: `TypeError: ProphetForecast.predict() got an unexpected keyword argument 'include_uncertainty'`

The current method in `models/prophet_model.py` is:

```python
def predict(self, days_ahead=30):
```

but other files call it like:

```python
predict(days, include_uncertainty=False)
```

A simple fix is to remove the `include_uncertainty` argument from those calls, or update `ProphetForecast.predict()` to accept and handle that argument.

### Issue: Ranking script cannot find `forecast_results.csv`

Run the forecasting script first:

```bash
python src/forecast_model.py
```

This may require installing XGBoost and fixing the Prophet argument mismatch first.

### Issue: Static dashboard does not display correctly offline

The dashboard loads Plotly.js from a CDN:

```html
https://cdn.plot.ly/plotly-2.27.0.min.js
```

An internet connection is needed unless Plotly.js is bundled locally.

## Suggested Improvements

Recommended cleanup items for the next version:

1. Add `xgboost` to `requirements.txt`.
2. Fix the Prophet `include_uncertainty` argument mismatch.
3. Add or remove the missing `models/regression_model.py` fallback.
4. Regenerate `File Structure.txt` so it matches the actual repository.
5. Add a license file if the project will be shared publicly.
6. Add sample screenshots of `web/dashboard.html` to the README.
7. Add clear units and source details for the weather observations.
8. Separate measured data from inferred fields in the dashboard.
9. Add tests for `prepare_data.py` and `compute_indices.py`.
10. Save generated forecast/ranking outputs if those modules are part of the final deliverable.

## Quick Command Reference

Install dependencies:

```bash
pip install -r requirements.txt
pip install xgboost
```

Regenerate processed files and dashboard:

```bash
python src/prepare_data.py
python src/compute_indices.py
python generate_html_dashboard.py
```

Open dashboard:

```bash
open web/dashboard.html
```

Run Streamlit dashboard:

```bash
streamlit run app.py
```

Run forecast script:

```bash
python src/forecast_model.py
```

Run ranking script:

```bash
python src/rank_top_cities.py
```

## Repository Summary

ClimaZoneAI is a renewable energy potential dashboard for Canadian cities. Its strongest working path is the prepared CSV data plus the static HTML dashboard. The data pipeline is included and can regenerate the wide-format and indexed datasets. The forecasting model code is present, but some dependency and function-call issues should be fixed before treating the full Prophet/XGBoost/ensemble workflow as complete.
