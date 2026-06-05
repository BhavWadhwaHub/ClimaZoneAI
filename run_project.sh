#!/bin/bash

echo "========================================="
echo "  ClimaZoneAI - Complete Pipeline"
echo "========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    exit 1
fi

# Step 1: Prepare data (long → wide format)
echo "Step 1: Preparing data (long → wide format)..."
python3 src/prepare_data.py
if [ $? -ne 0 ]; then
    echo "❌ Data preparation failed!"
    exit 1
fi
echo ""

# Step 2: Calculate indices
echo "Step 2: Calculating renewable energy indices..."
python3 src/compute_indices.py
if [ $? -ne 0 ]; then
    echo "❌ Index calculation failed!"
    exit 1
fi
echo ""

# Step 3: Generate dashboard
echo "Step 3: Generating HTML dashboard..."
python3 generate_html_dashboard.py
if [ $? -ne 0 ]; then
    echo "❌ Dashboard generation failed!"
    exit 1
fi
echo ""

# Step 4: Open dashboard
echo "========================================="
echo "  ✅ SUCCESS! Opening dashboard..."
echo "========================================="
open web/dashboard.html

echo ""
echo "Dashboard is now running in your browser!"
echo ""

