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
    <title>ClimaZoneAI &mdash; Renewable Energy Forecasting</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg:        #0a0f1e;
            --surface:   #111827;
            --border2:   #334155;
            --accent:    #10b981;
            --accent-dim:rgba(16,185,129,0.12);
            --solar:     #f59e0b;
            --wind:      #3b82f6;
            --hydro:     #06b6d4;
            --text:      #f1f5f9;
            --muted:     #64748b;
            --radius:    10px;
        }}
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{
            font-family:'Inter','Segoe UI',sans-serif;
            background:var(--bg); color:var(--text);
            min-height:100vh; display:flex; flex-direction:column;
        }}
        .topbar {{
            display:flex; align-items:center; justify-content:space-between;
            padding:0 28px; height:60px;
            background:linear-gradient(90deg,#052e16 0%,#0a0f1e 60%);
            border-bottom:1px solid rgba(16,185,129,0.25);
            position:sticky; top:0; z-index:200;
        }}
        .topbar-logo {{ display:flex; align-items:center; gap:10px; font-size:1.25rem; font-weight:800; letter-spacing:-0.5px; }}
        .leaf {{ color:var(--accent); font-size:1.4rem; }}
        .zone {{ color:var(--accent); }}
        .topbar-center {{ font-size:0.8rem; color:var(--muted); }}
        .topbar-badge {{
            background:var(--accent-dim); border:1px solid rgba(16,185,129,0.3);
            color:var(--accent); border-radius:20px; padding:4px 12px;
            font-size:0.72rem; font-weight:600;
        }}
        .app {{ display:flex; flex:1; overflow:hidden; }}
        .sidebar {{
            width:260px; min-width:260px; background:var(--surface);
            border-right:1px solid var(--border2); padding:24px 16px;
            display:flex; flex-direction:column; gap:20px; overflow-y:auto;
        }}
        .section-label {{
            font-size:0.65rem; font-weight:700; text-transform:uppercase;
            letter-spacing:1.2px; color:var(--muted); margin-bottom:10px;
        }}
        .form-label {{ font-size:0.78rem; color:#94a3b8; margin-bottom:5px; display:flex; align-items:center; gap:5px; }}
        .form-select {{
            width:100%; padding:9px 34px 9px 12px; background:var(--bg);
            border:1px solid var(--border2); border-radius:8px;
            color:var(--text); font-size:0.85rem; font-family:inherit;
            cursor:pointer; appearance:none; margin-bottom:12px;
            background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20' fill='%2364748b'%3E%3Cpath fill-rule='evenodd' d='M5.22 8.22a.75.75 0 0 1 1.06 0L10 11.94l3.72-3.72a.75.75 0 1 1 1.06 1.06l-4.25 4.25a.75.75 0 0 1-1.06 0L5.22 9.28a.75.75 0 0 1 0-1.06Z'/%3E%3C/svg%3E");
            background-repeat:no-repeat; background-position:right 10px center; background-size:16px;
            transition:border-color 0.15s;
        }}
        .form-select:focus {{ outline:none; border-color:var(--accent); }}
        .period-group {{ display:flex; gap:6px; }}
        .period-btn {{
            flex:1; padding:7px 4px; background:var(--bg);
            border:1px solid var(--border2); border-radius:7px;
            color:var(--muted); font-size:0.75rem; font-weight:500;
            font-family:inherit; cursor:pointer; text-align:center; transition:all 0.15s;
        }}
        .period-btn:hover {{ border-color:var(--accent); color:var(--accent); }}
        .period-btn.active {{ background:var(--accent); border-color:var(--accent); color:#fff; font-weight:600; }}
        .info-box {{
            background:var(--accent-dim); border:1px solid rgba(16,185,129,0.2);
            border-radius:8px; padding:12px; font-size:0.75rem;
            color:#34d399; line-height:1.55;
        }}
        .divider {{ border:none; border-top:1px solid var(--border2); }}
        .main {{ flex:1; padding:24px; overflow-y:auto; display:flex; flex-direction:column; gap:20px; }}
        .location-row {{ display:flex; align-items:center; justify-content:space-between; }}
        .location-title {{ font-size:1.35rem; font-weight:700; letter-spacing:-0.3px; }}
        .location-title .province {{ color:var(--accent); }}
        .status-tag {{
            display:flex; align-items:center; gap:6px;
            font-size:0.72rem; font-weight:500; color:#34d399;
            background:var(--accent-dim); border:1px solid rgba(16,185,129,0.25);
            border-radius:20px; padding:4px 12px;
        }}
        .status-dot {{
            width:6px; height:6px; background:var(--accent);
            border-radius:50%; animation:pulse 2s infinite;
        }}
        @keyframes pulse {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.4; }} }}
        .metrics-row {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }}
        .metric-card {{
            background:var(--surface); border:1px solid var(--border2);
            border-radius:var(--radius); padding:18px; position:relative;
            overflow:hidden; transition:transform 0.2s,border-color 0.2s,box-shadow 0.2s;
        }}
        .metric-card:hover {{ transform:translateY(-3px); box-shadow:0 8px 24px rgba(0,0,0,0.4); }}
        .metric-card::after {{
            content:''; position:absolute; top:0; left:0; right:0; height:3px;
            border-radius:var(--radius) var(--radius) 0 0;
        }}
        .mc-solar::after  {{ background:var(--solar);  }} .mc-solar:hover  {{ border-color:var(--solar);  }}
        .mc-wind::after   {{ background:var(--wind);   }} .mc-wind:hover   {{ border-color:var(--wind);   }}
        .mc-hydro::after  {{ background:var(--hydro);  }} .mc-hydro:hover  {{ border-color:var(--hydro);  }}
        .mc-overall::after {{ background:var(--accent); }} .mc-overall:hover {{ border-color:var(--accent); }}
        .mc-icon {{ font-size:1.4rem; margin-bottom:10px; }}
        .mc-value {{ font-size:2rem; font-weight:800; line-height:1; margin-bottom:4px; }}
        .mc-solar   .mc-value {{ color:var(--solar);  }}
        .mc-wind    .mc-value {{ color:var(--wind);   }}
        .mc-hydro   .mc-value {{ color:var(--hydro);  }}
        .mc-overall .mc-value {{ color:var(--accent); }}
        .mc-label {{ font-size:0.72rem; color:var(--muted); text-transform:uppercase; letter-spacing:0.8px; margin-bottom:10px; }}
        .mc-bar {{ height:3px; background:var(--border2); border-radius:2px; overflow:hidden; }}
        .mc-bar-fill {{ height:100%; border-radius:2px; transition:width 0.6s ease; }}
        .mc-solar   .mc-bar-fill {{ background:var(--solar);  }}
        .mc-wind    .mc-bar-fill {{ background:var(--wind);   }}
        .mc-hydro   .mc-bar-fill {{ background:var(--hydro);  }}
        .mc-overall .mc-bar-fill {{ background:var(--accent); }}
        .chart-card {{ background:var(--surface); border:1px solid var(--border2); border-radius:var(--radius); overflow:hidden; }}
        .chart-top {{
            display:flex; align-items:center; justify-content:space-between;
            padding:14px 18px; border-bottom:1px solid var(--border2);
        }}
        .chart-top h3 {{ font-size:0.88rem; font-weight:600; }}
        .chart-legend {{ display:flex; gap:14px; }}
        .legend-item {{ display:flex; align-items:center; gap:6px; font-size:0.72rem; color:#94a3b8; }}
        .legend-dot {{ width:8px; height:8px; border-radius:50%; flex-shrink:0; }}
        .chart-body {{ padding:6px; }}
        .plotly-chart {{ width:100%; height:360px; }}
        .footer {{
            background:var(--surface); border-top:1px solid var(--border2);
            padding:16px 28px; display:flex; align-items:center;
            justify-content:space-between; font-size:0.75rem; color:var(--muted); flex-shrink:0;
        }}
        .footer strong {{ color:var(--accent); }}
        @media (max-width:1100px) {{ .metrics-row {{ grid-template-columns:repeat(2,1fr); }} }}
        @media (max-width:768px) {{
            .app {{ flex-direction:column; }}
            .sidebar {{ width:100%; min-width:unset; }}
            .metrics-row {{ grid-template-columns:1fr 1fr; }}
            .topbar-center {{ display:none; }}
        }}
    </style>
</head>
<body>
    <nav class="topbar">
        <div class="topbar-logo">
            <span class="leaf">&#127807;</span>
            <span>Clima<span class="zone">Zone</span>AI</span>
        </div>
        <div class="topbar-center">AI-Powered Renewable Energy Forecasting for Canada</div>
        <div class="topbar-badge">SFU DataJam 2025</div>
    </nav>

    <div class="app">
        <aside class="sidebar">
            <div>
                <div class="section-label">Location</div>
                <label class="form-label">&#128205; Province</label>
                <select class="form-select" id="province-select" onchange="updateCities()">
                    {generate_province_options(cities_data)}
                </select>
                <label class="form-label">&#127960;&#65039; City</label>
                <select class="form-select" id="city-select" onchange="updateCharts()">
                    {generate_city_options(cities_data, default_province)}
                </select>
            </div>
            <hr class="divider">
            <div>
                <div class="section-label">Forecast Period</div>
                <div class="period-group">
                    <button class="period-btn active" onclick="setPeriod('30d',this)">30 Days</button>
                    <button class="period-btn" onclick="setPeriod('4m',this)">4 Months</button>
                    <button class="period-btn" onclick="setPeriod('1y',this)">1 Year</button>
                </div>
            </div>
            <hr class="divider">
            <div class="info-box">&#128202; Forecasts use historical climate patterns across 231 Canadian cities.</div>
        </aside>

        <main class="main">
            <div class="location-row">
                <h2 class="location-title" id="location-title">Vancouver, <span class="province">British Columbia</span></h2>
                <div class="status-tag"><div class="status-dot"></div>Live Data</div>
            </div>

            <div class="metrics-row">
                <div class="metric-card mc-solar">
                    <div class="mc-icon">&#9728;&#65039;</div>
                    <div class="mc-value" id="solar-metric">&mdash;</div>
                    <div class="mc-label">Solar Index</div>
                    <div class="mc-bar"><div class="mc-bar-fill" id="solar-bar" style="width:0%"></div></div>
                </div>
                <div class="metric-card mc-wind">
                    <div class="mc-icon">&#128168;</div>
                    <div class="mc-value" id="wind-metric">&mdash;</div>
                    <div class="mc-label">Wind Index</div>
                    <div class="mc-bar"><div class="mc-bar-fill" id="wind-bar" style="width:0%"></div></div>
                </div>
                <div class="metric-card mc-hydro">
                    <div class="mc-icon">&#128167;</div>
                    <div class="mc-value" id="hydro-metric">&mdash;</div>
                    <div class="mc-label">Hydro Index</div>
                    <div class="mc-bar"><div class="mc-bar-fill" id="hydro-bar" style="width:0%"></div></div>
                </div>
                <div class="metric-card mc-overall">
                    <div class="mc-icon">&#127757;</div>
                    <div class="mc-value" id="overall-metric">&mdash;</div>
                    <div class="mc-label">Renewable Score</div>
                    <div class="mc-bar"><div class="mc-bar-fill" id="overall-bar" style="width:0%"></div></div>
                </div>
            </div>

            <div class="chart-card">
                <div class="chart-top">
                    <h3>&#9889; Energy Type Comparison</h3>
                    <div class="chart-legend">
                        <div class="legend-item"><div class="legend-dot" style="background:#f59e0b"></div>Solar</div>
                        <div class="legend-item"><div class="legend-dot" style="background:#3b82f6"></div>Wind</div>
                        <div class="legend-item"><div class="legend-dot" style="background:#06b6d4"></div>Hydro</div>
                    </div>
                </div>
                <div class="chart-body"><div id="energy-comparison-chart" class="plotly-chart"></div></div>
            </div>

            <div class="chart-card">
                <div class="chart-top">
                    <h3>&#127757; Overall Renewable Energy Score</h3>
                    <div class="chart-legend">
                        <div class="legend-item"><div class="legend-dot" style="background:#10b981"></div>Renewable Score</div>
                    </div>
                </div>
                <div class="chart-body"><div id="overall-score-chart" class="plotly-chart"></div></div>
            </div>

            <div class="chart-card">
                <div class="chart-top">
                    <h3>&#128202; Monthly Energy Distribution</h3>
                    <div class="chart-legend">
                        <div class="legend-item"><div class="legend-dot" style="background:#f59e0b"></div>Solar</div>
                        <div class="legend-item"><div class="legend-dot" style="background:#3b82f6"></div>Wind</div>
                        <div class="legend-item"><div class="legend-dot" style="background:#06b6d4"></div>Hydro</div>
                    </div>
                </div>
                <div class="chart-body"><div id="individual-energy-chart" class="plotly-chart"></div></div>
            </div>
        </main>
    </div>

    <footer class="footer">
        <div><strong>ClimaZoneAI</strong> &mdash; Developed by Team ClimaZoneAI</div>
        <div>SFU DataJam 2025 &middot; Powered by AI &amp; Climate Science</div>
        <div>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
    </footer>

    <script>
        const citiesData = {json.dumps(cities_data, indent=8)};
        const allCitiesData = {json.dumps(all_cities_data, indent=8)};
        const allCitiesForecasts = {json.dumps(all_cities_forecasts, indent=8)};

        let currentPeriod = '30d';

        function setPeriod(period, btn) {{
            currentPeriod = period;
            document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            updateCharts();
        }}

        function updateCities() {{
            const province = document.getElementById('province-select').value;
            const citySelect = document.getElementById('city-select');
            citySelect.innerHTML = '';
            (citiesData[province] || []).forEach(city => {{
                const opt = document.createElement('option');
                opt.value = city; opt.textContent = city;
                citySelect.appendChild(opt);
            }});
            updateCharts();
        }}

        function updateCharts() {{
            const province = document.getElementById('province-select').value;
            const city     = document.getElementById('city-select').value;
            const key      = city + '|' + province;

            document.getElementById('location-title').innerHTML =
                city + ', <span class="province">' + province + '</span>';

            const forecastData = (allCitiesForecasts[key] || {{}})[currentPeriod];
            if (!forecastData || !forecastData.length) {{ console.warn('No data for', key, currentPeriod); return; }}

            const periods = forecastData.map(d => d.period);
            const solar   = forecastData.map(d => d.Solar);
            const wind    = forecastData.map(d => d.Wind);
            const hydro   = forecastData.map(d => d.Hydro);
            const score   = forecastData.map(d => d.Renewable_Score);

            const avg = arr => arr.reduce((a,b) => a+b, 0) / arr.length;
            const aS = avg(solar).toFixed(2), aW = avg(wind).toFixed(2),
                  aH = avg(hydro).toFixed(2), aO = avg(score).toFixed(2);

            document.getElementById('solar-metric').textContent   = aS;
            document.getElementById('wind-metric').textContent    = aW;
            document.getElementById('hydro-metric').textContent   = aH;
            document.getElementById('overall-metric').textContent = aO;
            document.getElementById('solar-bar').style.width   = (aS * 100) + '%';
            document.getElementById('wind-bar').style.width    = (aW * 100) + '%';
            document.getElementById('hydro-bar').style.width   = (aH * 100) + '%';
            document.getElementById('overall-bar').style.width = (aO * 100) + '%';

            const base = {{
                plot_bgcolor:'#111827', paper_bgcolor:'#111827',
                font:{{ family:'Inter,sans-serif', color:'#64748b', size:11 }},
                xaxis:{{ tickangle:-30, gridcolor:'#1e293b', linecolor:'#1e293b', tickfont:{{ color:'#64748b' }}, title:'' }},
                yaxis:{{ range:[0,1], gridcolor:'#1e293b', linecolor:'#1e293b', tickfont:{{ color:'#64748b' }}, title:{{ text:'Index', font:{{ color:'#64748b' }} }} }},
                hovermode:'x unified',
                hoverlabel:{{ bgcolor:'#1e293b', bordercolor:'#334155', font:{{ color:'#f1f5f9', family:'Inter' }} }},
                margin:{{ t:16, r:12, b:56, l:50 }},
                legend:{{ bgcolor:'rgba(10,15,30,0.8)', bordercolor:'#334155', borderwidth:1, font:{{ color:'#94a3b8' }} }},
                showlegend:false
            }};
            const opts = {{ responsive:true, displayModeBar:false }};

            Plotly.newPlot('energy-comparison-chart', [
                {{ x:periods, y:solar, name:'Solar', type:'scatter', mode:'lines+markers', line:{{ color:'#f59e0b', width:2.5 }}, marker:{{ size:5, color:'#f59e0b' }}, connectgaps:false }},
                {{ x:periods, y:wind,  name:'Wind',  type:'scatter', mode:'lines+markers', line:{{ color:'#3b82f6', width:2.5 }}, marker:{{ size:5, color:'#3b82f6' }}, connectgaps:false }},
                {{ x:periods, y:hydro, name:'Hydro', type:'scatter', mode:'lines+markers', line:{{ color:'#06b6d4', width:2.5 }}, marker:{{ size:5, color:'#06b6d4' }}, connectgaps:false }}
            ], base, opts);

            const overallLayout = Object.assign({{}}, base, {{ yaxis: Object.assign({{}}, base.yaxis, {{ title:{{ text:'Renewable Score', font:{{ color:'#64748b' }} }} }}) }});
            Plotly.newPlot('overall-score-chart', [{{
                x:periods, y:score, name:'Score', type:'scatter', mode:'lines+markers',
                line:{{ color:'#10b981', width:3 }}, marker:{{ size:6, color:'#10b981' }},
                fill:'tozeroy', fillcolor:'rgba(16,185,129,0.1)', connectgaps:false
            }}], overallLayout, opts);

            const barLayout = Object.assign({{}}, base, {{ barmode:'group', bargap:0.18, bargroupgap:0.06, showlegend:true, yaxis: Object.assign({{}}, base.yaxis, {{ title:{{ text:'Index Value', font:{{ color:'#64748b' }} }} }}) }});
            Plotly.newPlot('individual-energy-chart', [
                {{ x:periods, y:solar, name:'Solar', type:'bar', marker:{{ color:'#f59e0b', opacity:0.85 }} }},
                {{ x:periods, y:wind,  name:'Wind',  type:'bar', marker:{{ color:'#3b82f6', opacity:0.85 }} }},
                {{ x:periods, y:hydro, name:'Hydro', type:'bar', marker:{{ color:'#06b6d4', opacity:0.85 }} }}
            ], barLayout, opts);
        }}

        window.onload = function () {{ updateCities(); }};
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

