"""
ClimaZoneAI - Static HTML Dashboard Generator
---------------------------------------------
Generates a standalone HTML dashboard with interactive charts.
Can be deployed without a server.
"""

import pandas as pd
import json
import os
from datetime import datetime, timedelta
import numpy as np


def generate_monthly_summary(df, city, province):
    """Generate monthly aggregated data for charts."""
    # Filter city data
    city_data = df[(df['city'] == city) & (df['province'] == province)].copy()
    
    if len(city_data) == 0:
        return None
    
    # Add month column
    city_data['month'] = pd.to_datetime(city_data['date']).dt.to_period('M')
    
    # Aggregate by month - only include months with sufficient data
    monthly = city_data.groupby('month').agg({
        'Solar': 'mean',
        'Wind': 'mean',
        'Hydro': 'mean',
        'Renewable_Score': 'mean',
        'date': 'first',
        'city': 'count'  # Count data points per month
    }).reset_index()
    
    # Filter out months with too few data points (< 3 days)
    monthly = monthly[monthly['city'] >= 3].copy()
    
    # Drop the count column
    monthly = monthly.drop(columns=['city'])
    
    # Convert period to string
    monthly['month'] = monthly['month'].astype(str)
    monthly['date'] = monthly['date'].astype(str)
    
    # Remove any rows with NaN values
    monthly = monthly.dropna(subset=['Solar', 'Wind', 'Hydro', 'Renewable_Score'])
    
    return monthly if len(monthly) > 0 else None


def generate_forecast(df, city, province, days_ahead):
    """Generate simple forecast based on historical patterns."""
    # Filter city data
    city_data = df[(df['city'] == city) & (df['province'] == province)].copy()
    
    if len(city_data) == 0:
        return None
    
    # Get last date in data
    last_date = pd.to_datetime(city_data['date']).max()
    
    # Calculate monthly averages for each metric
    city_data['month_num'] = pd.to_datetime(city_data['date']).dt.month
    monthly_patterns = city_data.groupby('month_num').agg({
        'Solar': 'mean',
        'Wind': 'mean',
        'Hydro': 'mean',
        'Renewable_Score': 'mean'
    })
    
    # Generate future dates
    future_dates = [last_date + timedelta(days=i+1) for i in range(days_ahead)]
    
    # Create forecast based on monthly patterns
    forecast_data = []
    for date in future_dates:
        month_num = date.month
        if month_num in monthly_patterns.index:
            forecast_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'Solar': float(monthly_patterns.loc[month_num, 'Solar']),
                'Wind': float(monthly_patterns.loc[month_num, 'Wind']),
                'Hydro': float(monthly_patterns.loc[month_num, 'Hydro']),
                'Renewable_Score': float(monthly_patterns.loc[month_num, 'Renewable_Score'])
            })
    
    return forecast_data


def aggregate_forecast_by_period(forecast_data, period='daily'):
    """Aggregate forecast data by period (daily, monthly)."""
    if not forecast_data or len(forecast_data) == 0:
        return None
    
    df = pd.DataFrame(forecast_data)
    df['date'] = pd.to_datetime(df['date'])
    
    if period == 'daily':
        # Return as is
        result = []
        for _, row in df.iterrows():
            result.append({
                'period': row['date'].strftime('%Y-%m-%d'),
                'Solar': round(float(row['Solar']), 3),
                'Wind': round(float(row['Wind']), 3),
                'Hydro': round(float(row['Hydro']), 3),
                'Renewable_Score': round(float(row['Renewable_Score']), 3)
            })
        return result
    
    elif period == 'monthly':
        # Aggregate by month
        df['month'] = df['date'].dt.to_period('M')
        monthly = df.groupby('month').agg({
            'Solar': 'mean',
            'Wind': 'mean',
            'Hydro': 'mean',
            'Renewable_Score': 'mean'
        }).reset_index()
        
        result = []
        for _, row in monthly.iterrows():
            result.append({
                'period': str(row['month']),
                'Solar': round(float(row['Solar']), 3),
                'Wind': round(float(row['Wind']), 3),
                'Hydro': round(float(row['Hydro']), 3),
                'Renewable_Score': round(float(row['Renewable_Score']), 3)
            })
        return result


def get_available_cities(df):
    """Get list of provinces and their cities."""
    cities_by_province = {}
    for province in df['province'].unique():
        cities = df[df['province'] == province]['city'].unique().tolist()
        cities_by_province[province] = sorted(cities)
    
    return cities_by_province


def generate_html_dashboard():
    """Generate standalone HTML dashboard."""
    
    # Load data
    print("📂 Loading data...")
    df = pd.read_csv('data/processed_indices.csv', parse_dates=['date'])
    
    # Get cities
    cities_data = get_available_cities(df)
    
    # Generate data for default city (Vancouver)
    default_city = "Vancouver"
    default_province = "British Columbia"
    monthly_data = generate_monthly_summary(df, default_city, default_province)
    
    if monthly_data is None:
        print("❌ No data for default city")
        return
    
    # Convert to JSON
    chart_data = {
        'months': monthly_data['month'].tolist(),
        'solar': monthly_data['Solar'].round(3).tolist(),
        'wind': monthly_data['Wind'].round(3).tolist(),
        'hydro': monthly_data['Hydro'].round(3).tolist(),
        'renewable_score': monthly_data['Renewable_Score'].round(3).tolist()
    }
    
    # Get all cities historical data
    all_cities_data = {}
    for province, cities in cities_data.items():
        for city in cities:
            monthly = generate_monthly_summary(df, city, province)
            if monthly is not None and len(monthly) > 0:
                key = f"{city}|{province}"
                all_cities_data[key] = {
                    'months': monthly['month'].tolist(),
                    'solar': monthly['Solar'].round(3).tolist(),
                    'wind': monthly['Wind'].round(3).tolist(),
                    'hydro': monthly['Hydro'].round(3).tolist(),
                    'renewable_score': monthly['Renewable_Score'].round(3).tolist()
                }
    
    # Generate forecasts for all cities
    print("🔮 Generating forecasts...")
    all_cities_forecasts = {}
    for province, cities in cities_data.items():
        for city in cities:
            key = f"{city}|{province}"
            
            # Generate forecasts for different periods
            forecast_30d = generate_forecast(df, city, province, 30)
            forecast_4m = generate_forecast(df, city, province, 120)  # ~4 months
            forecast_1y = generate_forecast(df, city, province, 365)  # 1 year
            
            if forecast_30d:
                # Aggregate forecasts appropriately
                daily_30d = aggregate_forecast_by_period(forecast_30d, 'daily')
                monthly_4m = aggregate_forecast_by_period(forecast_4m, 'monthly')
                monthly_1y = aggregate_forecast_by_period(forecast_1y, 'monthly')
                
                all_cities_forecasts[key] = {
                    '30d': daily_30d,
                    '4m': monthly_4m,
                    '1y': monthly_1y
                }
    
    
    # HTML Template
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌍 ClimaZoneAI - Renewable Energy Forecasting</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 3rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header p {{
            font-size: 1.2rem;
            opacity: 0.95;
        }}
        
        .controls {{
            background: #f8f9fa;
            padding: 30px;
            border-bottom: 3px solid #667eea;
        }}
        
        .control-group {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .control-item {{
            display: flex;
            flex-direction: column;
        }}
        
        .control-item label {{
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
            font-size: 0.95rem;
        }}
        
        .control-item select {{
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 1rem;
            transition: all 0.3s;
            background: white;
        }}
        
        .control-item select:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
            transition: transform 0.3s;
        }}
        
        .metric-card:hover {{
            transform: translateY(-5px);
        }}
        
        .metric-card .icon {{
            font-size: 2.5rem;
            margin-bottom: 10px;
        }}
        
        .metric-card .value {{
            font-size: 2.5rem;
            font-weight: bold;
            margin: 10px 0;
        }}
        
        .metric-card .label {{
            font-size: 1rem;
            opacity: 0.9;
        }}
        
        .chart-container {{
            margin-bottom: 40px;
            background: #f8f9fa;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }}
        
        .chart-title {{
            font-size: 1.8rem;
            font-weight: 600;
            margin-bottom: 20px;
            color: #333;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .chart {{
            width: 100%;
            height: 500px;
        }}
        
        .info-box {{
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
        }}
        
        .info-box p {{
            margin: 0;
            color: #1565c0;
        }}
        
        .footer {{
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 30px;
        }}
        
        .footer p {{
            margin: 5px 0;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2rem;
            }}
            
            .control-group {{
                grid-template-columns: 1fr;
            }}
            
            .metrics {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🌍 ClimaZoneAI</h1>
            <p>AI-Powered Renewable Energy Forecasting for Canada</p>
        </div>
        
        <!-- Controls -->
        <div class="controls">
            <div class="control-group">
                <div class="control-item">
                    <label for="province-select">📍 Select Province</label>
                    <select id="province-select" onchange="updateCities()">
                        {generate_province_options(cities_data)}
                    </select>
                </div>
                
                <div class="control-item">
                    <label for="city-select">🏙️ Select City</label>
                    <select id="city-select" onchange="updateCharts()">
                        {generate_city_options(cities_data, default_province)}
                    </select>
                </div>
                
                <div class="control-item">
                    <label for="forecast-period">🔮 Forecast Period</label>
                    <select id="forecast-period" onchange="updateCharts()">
                        <option value="30d" selected>30 Days</option>
                        <option value="4m">4 Months</option>
                        <option value="1y">1 Year</option>
                    </select>
                </div>
            </div>
            
            <div class="info-box">
                <p>📊 Select a forecast period to view predictions. Historical patterns are used for forecasting.</p>
            </div>
        </div>
        
        <!-- Content -->
        <div class="content">
            <!-- Metrics -->
            <div class="metrics">
                <div class="metric-card">
                    <div class="icon">☀️</div>
                    <div class="value" id="solar-metric">-</div>
                    <div class="label">Solar Index</div>
                </div>
                <div class="metric-card">
                    <div class="icon">💨</div>
                    <div class="value" id="wind-metric">-</div>
                    <div class="label">Wind Index</div>
                </div>
                <div class="metric-card">
                    <div class="icon">💧</div>
                    <div class="value" id="hydro-metric">-</div>
                    <div class="label">Hydro Index</div>
                </div>
                <div class="metric-card">
                    <div class="icon">🌍</div>
                    <div class="value" id="overall-metric">-</div>
                    <div class="label">Overall Score</div>
                </div>
            </div>
            
            <!-- Chart 1: Energy Type Comparison -->
            <div class="chart-container">
                <div class="chart-title">
                    ⚡ Monthly Energy Type Comparison
                </div>
                <div id="energy-comparison-chart" class="chart"></div>
            </div>
            
            <!-- Chart 2: Overall Renewable Score -->
            <div class="chart-container">
                <div class="chart-title">
                    🌍 Overall Renewable Energy Score Trend
                </div>
                <div id="overall-score-chart" class="chart"></div>
            </div>
            
            <!-- Chart 3: Individual Energy Breakdown -->
            <div class="chart-container">
                <div class="chart-title">
                    📊 Individual Energy Type Breakdown
                </div>
                <div id="individual-energy-chart" class="chart"></div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p><strong>ClimaZoneAI</strong> | Developed by Team ClimaZoneAI</p>
            <p>SFU DataJam 2025 | Powered by AI & Climate Science 🌤️</p>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>
    </div>
    
    <script>
        // Data storage
        const citiesData = {json.dumps(cities_data, indent=8)};
        const allCitiesData = {json.dumps(all_cities_data, indent=8)};
        const allCitiesForecasts = {json.dumps(all_cities_forecasts, indent=8)};
        
        // Update cities dropdown when province changes
        function updateCities() {{
            const provinceSelect = document.getElementById('province-select');
            const citySelect = document.getElementById('city-select');
            const province = provinceSelect.value;
            
            citySelect.innerHTML = '';
            const cities = citiesData[province];
            cities.forEach(city => {{
                const option = document.createElement('option');
                option.value = city;
                option.textContent = city;
                citySelect.appendChild(option);
            }});
            
            updateCharts();
        }}
        
        // Update charts when city or forecast period changes
        function updateCharts() {{
            const province = document.getElementById('province-select').value;
            const city = document.getElementById('city-select').value;
            const forecastPeriod = document.getElementById('forecast-period').value;
            const key = `${{city}}|${{province}}`;
            
            // Get forecast data based on selected period
            const forecastData = allCitiesForecasts[key] ? allCitiesForecasts[key][forecastPeriod] : null;
            if (!forecastData || forecastData.length === 0) {{
                console.error('No forecast data for', key, forecastPeriod);
                return;
            }}
            
            // Extract data arrays
            const periods = forecastData.map(d => d.period);
            const solar = forecastData.map(d => d.Solar);
            const wind = forecastData.map(d => d.Wind);
            const hydro = forecastData.map(d => d.Hydro);
            const renewableScore = forecastData.map(d => d.Renewable_Score);
            
            const data = {{
                months: periods,
                solar: solar,
                wind: wind,
                hydro: hydro,
                renewable_score: renewableScore
            }};
            
            // Update metrics
            const avgSolar = (data.solar.reduce((a, b) => a + b, 0) / data.solar.length).toFixed(2);
            const avgWind = (data.wind.reduce((a, b) => a + b, 0) / data.wind.length).toFixed(2);
            const avgHydro = (data.hydro.reduce((a, b) => a + b, 0) / data.hydro.length).toFixed(2);
            const avgOverall = (data.renewable_score.reduce((a, b) => a + b, 0) / data.renewable_score.length).toFixed(2);
            
            document.getElementById('solar-metric').textContent = avgSolar;
            document.getElementById('wind-metric').textContent = avgWind;
            document.getElementById('hydro-metric').textContent = avgHydro;
            document.getElementById('overall-metric').textContent = avgOverall;
            
            // Chart 1: Energy Type Comparison (3 lines)
            const comparisonTrace1 = {{
                x: data.months,
                y: data.solar,
                type: 'scatter',
                mode: 'lines+markers',
                name: '☀️ Solar',
                line: {{ 
                    color: '#FFA500', 
                    width: 3,
                    shape: 'linear'  // Don't interpolate between gaps
                }},
                marker: {{ size: 8 }},
                connectgaps: false  // Don't connect line across gaps
            }};
            
            const comparisonTrace2 = {{
                x: data.months,
                y: data.wind,
                type: 'scatter',
                mode: 'lines+markers',
                name: '💨 Wind',
                line: {{ 
                    color: '#4682B4', 
                    width: 3,
                    shape: 'linear'
                }},
                marker: {{ size: 8 }},
                connectgaps: false
            }};
            
            const comparisonTrace3 = {{
                x: data.months,
                y: data.hydro,
                type: 'scatter',
                mode: 'lines+markers',
                name: '💧 Hydro',
                line: {{ 
                    color: '#008080', 
                    width: 3,
                    shape: 'linear'
                }},
                marker: {{ size: 8 }},
                connectgaps: false
            }};
            
            const comparisonLayout = {{
                title: `Monthly Comparison - ${{city}}, ${{province}}`,
                xaxis: {{ 
                    title: 'Month',
                    tickangle: -45
                }},
                yaxis: {{ 
                    title: 'Energy Potential Index',
                    range: [0, 1]
                }},
                hovermode: 'x unified',
                showlegend: true,
                legend: {{ x: 0.01, y: 0.99 }},
                plot_bgcolor: '#f8f9fa',
                paper_bgcolor: '#f8f9fa'
            }};
            
            Plotly.newPlot('energy-comparison-chart', 
                [comparisonTrace1, comparisonTrace2, comparisonTrace3], 
                comparisonLayout,
                {{ responsive: true }}
            );
            
            // Chart 2: Overall Renewable Score
            const overallTrace = {{
                x: data.months,
                y: data.renewable_score,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Renewable Score',
                line: {{ 
                    color: '#2ecc71', 
                    width: 4,
                    shape: 'linear'
                }},
                marker: {{ size: 10, color: '#27ae60' }},
                fill: 'tozeroy',
                fillcolor: 'rgba(46, 204, 113, 0.2)',
                connectgaps: false  // Don't connect across missing months
            }};
            
            const overallLayout = {{
                title: `Overall Renewable Energy Trend - ${{city}}, ${{province}}`,
                xaxis: {{ 
                    title: 'Month',
                    tickangle: -45
                }},
                yaxis: {{ 
                    title: 'Renewable Score',
                    range: [0, 1]
                }},
                hovermode: 'x unified',
                plot_bgcolor: '#f8f9fa',
                paper_bgcolor: '#f8f9fa'
            }};
            
            Plotly.newPlot('overall-score-chart', 
                [overallTrace], 
                overallLayout,
                {{ responsive: true }}
            );
            
            // Chart 3: Bar chart for individual energy types
            const barTrace1 = {{
                x: data.months,
                y: data.solar,
                name: '☀️ Solar',
                type: 'bar',
                marker: {{ color: '#FFA500' }}
            }};
            
            const barTrace2 = {{
                x: data.months,
                y: data.wind,
                name: '💨 Wind',
                type: 'bar',
                marker: {{ color: '#4682B4' }}
            }};
            
            const barTrace3 = {{
                x: data.months,
                y: data.hydro,
                name: '💧 Hydro',
                type: 'bar',
                marker: {{ color: '#008080' }}
            }};
            
            const barLayout = {{
                title: `Energy Distribution by Month - ${{city}}, ${{province}}`,
                xaxis: {{ 
                    title: 'Month',
                    tickangle: -45
                }},
                yaxis: {{ 
                    title: 'Energy Potential Index',
                    range: [0, 1]
                }},
                barmode: 'group',
                plot_bgcolor: '#f8f9fa',
                paper_bgcolor: '#f8f9fa'
            }};
            
            Plotly.newPlot('individual-energy-chart', 
                [barTrace1, barTrace2, barTrace3], 
                barLayout,
                {{ responsive: true }}
            );
        }}
        
        // Initialize on page load
        window.onload = function() {{
            updateCharts();
        }};
    </script>
</body>
</html>"""
    
    # Save HTML file
    output_path = "web/dashboard.html"
    os.makedirs("web", exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML dashboard generated: {output_path}")
    print(f"📊 Included {len(all_cities_data)} cities")
    print(f"🌐 Open {output_path} in your browser!")


def generate_province_options(cities_data):
    """Generate HTML options for provinces."""
    options = []
    for province in sorted(cities_data.keys()):
        selected = ' selected' if province == "British Columbia" else ''
        options.append(f'<option value="{province}"{selected}>{province}</option>')
    return '\n                        '.join(options)


def generate_city_options(cities_data, province):
    """Generate HTML options for cities."""
    options = []
    cities = sorted(cities_data[province])
    for city in cities:
        selected = ' selected' if city == "Vancouver" else ''
        options.append(f'<option value="{city}"{selected}>{city}</option>')
    return '\n                        '.join(options)


if __name__ == "__main__":
    generate_html_dashboard()

