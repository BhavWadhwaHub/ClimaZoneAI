@echo off
echo =========================================
echo   ClimaZoneAI - Complete Pipeline
echo =========================================
echo.

REM Step 1: Prepare data
echo Step 1: Preparing data (long to wide format)...
python src\prepare_data.py
if errorlevel 1 (
    echo ERROR: Data preparation failed!
    pause
    exit /b 1
)
echo.

REM Step 2: Calculate indices
echo Step 2: Calculating renewable energy indices...
python src\compute_indices.py
if errorlevel 1 (
    echo ERROR: Index calculation failed!
    pause
    exit /b 1
)
echo.

REM Step 3: Generate dashboard
echo Step 3: Generating HTML dashboard...
python generate_html_dashboard.py
if errorlevel 1 (
    echo ERROR: Dashboard generation failed!
    pause
    exit /b 1
)
echo.

REM Step 4: Open dashboard
echo =========================================
echo   SUCCESS! Opening dashboard...
echo =========================================
start web\dashboard.html

pause

