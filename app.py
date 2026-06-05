"""
ClimaZoneAI - Main Streamlit Dashboard
--------------------------------------
Interactive dashboard for renewable energy analysis and forecasting.

Features:
- Historical data analysis (Solar, Wind, Hydro trends)
- Future predictions with 3 models (Prophet, XGBoost, Ensemble)
- Province and city selection
- Multiple forecast horizons (30 days, 4 months, 1 year)

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys
from datetime import datetime, timedelta

# Add src to path
sys.path.append('src')
sys.path.append('models')

# Page config
st.set_page_config(
    page_title="ClimaZoneAI - Renewable Energy Forecasting",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# Data Loading Functions
# ============================================================

@st.cache_data
def load_processed_data():
    """Load the processed wide-format data with indices."""
    data_path = "data/processed_indices.csv"
    if os.path.exists(data_path):
        df = pd.read_csv(data_path, parse_dates=['date'])
        return df
    else:
        st.error(f"❌ Data file not found: {data_path}")
        st.info("Please run: python src/prepare_data.py and python src/compute_indices.py first")
        return None


@st.cache_data
def load_wide_format_data():
    """Load wide-format data for model training."""
    data_path = "data/processed_wide_format.csv"
    if os.path.exists(data_path):
        df = pd.read_csv(data_path, parse_dates=['date'])
        return df
    else:
        return None


def compute_indices_on_the_fly(df):
    """Compute renewable energy indices if not already present."""
    from sklearn.preprocessing import MinMaxScaler
    
    if 'Renewable_Score' in df.columns:
        return df
    
    # Ensure required columns
    for col in ['PRCP', 'TAVG', 'AWND', 'WSF2', 'SNOW', 'SNWD']:
        if col not in df.columns:
            df[col] = 0
    
    # Compute raw indices
    df['Solar_raw'] = df['TAVG'] - (df['PRCP'] / 10.0)
    df['Wind_raw'] = (df['AWND'] + df['WSF2']) / 2.0
    df['Hydro_raw'] = df['PRCP'] + df['SNOW'] + df['SNWD']
    
    # Normalize
    scaler = MinMaxScaler()
    df['Solar'] = scaler.fit_transform(df[['Solar_raw']])
    df['Wind'] = scaler.fit_transform(df[['Wind_raw']])
    df['Hydro'] = scaler.fit_transform(df[['Hydro_raw']])
    
    # Renewable Score
    df['Renewable_Score'] = df[['Solar', 'Wind', 'Hydro']].mean(axis=1)
    
    return df


# ============================================================
# Forecasting Functions
# ============================================================

@st.cache_resource
def train_models(city_data):
    """Train all three models on city data."""
    from models.prophet_model import ProphetForecast
    from models.xgboost_model import XGBoostForecast
    from models.ensemble_model import EnsembleForecaster
    
    with st.spinner("🔧 Training models..."):
        prophet = ProphetForecast()
        xgboost = XGBoostForecast()
        ensemble = EnsembleForecaster()
        
        try:
            prophet.train(city_data)
            xgboost.train(city_data)
            ensemble.train(city_data)
            return prophet, xgboost, ensemble
        except Exception as e:
            st.error(f"Model training failed: {e}")
            return None, None, None


def generate_forecasts(prophet, xgboost, ensemble, city_data, days):
    """Generate forecasts from all three models."""
    forecasts = {}
    
    try:
        # Prophet
        prophet_pred = prophet.predict(days, include_uncertainty=True)
        forecasts['Prophet'] = prophet_pred
        
        # XGBoost
        xgb_pred = xgboost.predict_future(city_data, days)
        forecasts['XGBoost'] = xgb_pred
        
        # Ensemble
        ensemble_pred = ensemble.predict(city_data, days)
        forecasts['Ensemble'] = ensemble_pred
        
        return forecasts
    except Exception as e:
        st.error(f"Forecast generation failed: {e}")
        return None


# ============================================================
# Visualization Functions
# ============================================================

def plot_historical_trends(df, city, province):
    """Plot historical Solar, Wind, Hydro trends."""
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=('Solar Index', 'Wind Index', 'Hydro Index'),
        vertical_spacing=0.1
    )
    
    # Solar
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['Solar'], name='Solar', 
                   line=dict(color='orange', width=2)),
        row=1, col=1
    )
    
    # Wind
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['Wind'], name='Wind', 
                   line=dict(color='steelblue', width=2)),
        row=2, col=1
    )
    
    # Hydro
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['Hydro'], name='Hydro', 
                   line=dict(color='teal', width=2)),
        row=3, col=1
    )
    
    fig.update_xaxes(title_text="Date", row=3, col=1)
    fig.update_yaxes(title_text="Index", range=[0, 1])
    
    fig.update_layout(
        height=800,
        title_text=f"Historical Renewable Energy Trends - {city}, {province}",
        showlegend=False,
        hovermode='x unified'
    )
    
    return fig


def plot_renewable_score_history(df, city, province):
    """Plot historical Renewable Score."""
    fig = px.line(df, x='date', y='Renewable_Score',
                  title=f'Historical Renewable Energy Score - {city}, {province}')
    
    fig.update_traces(line=dict(color='green', width=2))
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Renewable Score",
        yaxis_range=[0, 1],
        hovermode='x unified',
        height=400
    )
    
    return fig


def aggregate_forecast_data(df, days):
    """
    Aggregate forecast data for better readability:
    - 30 days: Daily (no aggregation)
    - 120 days (4 months): Monthly average
    - 365 days (1 year): Monthly average
    """
    if days <= 30:
        # Daily: No aggregation
        return df, "Daily"
    elif days <= 150:
        # Monthly aggregation for 4 months
        df = df.copy()
        df['month'] = df['date'].dt.to_period('M')
        agg_df = df.groupby('month').agg({
            'date': 'first',  # Use first date of month
            'forecast': 'mean'
        }).reset_index(drop=True)
        return agg_df, "Monthly Average"
    else:
        # Monthly aggregation for 1 year
        df = df.copy()
        df['month'] = df['date'].dt.to_period('M')
        agg_df = df.groupby('month').agg({
            'date': 'first',
            'forecast': 'mean'
        }).reset_index(drop=True)
        return agg_df, "Monthly Average"


def plot_forecast_comparison(historical_df, forecasts, days):
    """Plot forecast comparison with smart aggregation based on time horizon."""
    fig = go.Figure()
    
    # Determine aggregation level
    if days <= 30:
        agg_level = "Daily"
        title_suffix = f"{days} days ahead - Daily Data"
    elif days <= 150:
        agg_level = "Monthly"
        title_suffix = f"4 months ahead - Monthly Averages"
    else:
        agg_level = "Monthly"
        title_suffix = f"1 year ahead - Monthly Averages"
    
    # Historical data (last 90 days for context)
    hist_recent = historical_df.tail(90) if len(historical_df) > 90 else historical_df
    fig.add_trace(go.Scatter(
        x=hist_recent['date'],
        y=hist_recent['Renewable_Score'],
        name='Historical',
        line=dict(color='gray', width=2),
        mode='lines',
        hovertemplate='Date: %{x}<br>Score: %{y:.3f}<extra></extra>'
    ))
    
    # Process and plot Prophet forecast
    if 'Prophet' in forecasts:
        prophet_data = forecasts['Prophet'].copy()
        prophet_agg, _ = aggregate_forecast_data(prophet_data, days)
        
        fig.add_trace(go.Scatter(
            x=prophet_agg['date'],
            y=prophet_agg['forecast'],
            name='Prophet',
            line=dict(color='blue', width=2, dash='dash'),
            mode='lines+markers' if agg_level == "Monthly" else 'lines',
            marker=dict(size=8) if agg_level == "Monthly" else None,
            hovertemplate='Date: %{x}<br>Forecast: %{y:.3f}<br>(Prophet)<extra></extra>'
        ))
        
        # Confidence interval (only for daily data)
        if 'lower_bound' in prophet_data.columns and days <= 30:
            fig.add_trace(go.Scatter(
                x=prophet_data['date'],
                y=prophet_data['upper_bound'],
                mode='lines',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            fig.add_trace(go.Scatter(
                x=prophet_data['date'],
                y=prophet_data['lower_bound'],
                mode='lines',
                line=dict(width=0),
                fillcolor='rgba(0, 0, 255, 0.2)',
                fill='tonexty',
                name='95% Confidence',
                hoverinfo='skip'
            ))
    
    # Process and plot XGBoost forecast
    if 'XGBoost' in forecasts:
        xgb_data = forecasts['XGBoost'].copy()
        xgb_agg, _ = aggregate_forecast_data(xgb_data, days)
        
        fig.add_trace(go.Scatter(
            x=xgb_agg['date'],
            y=xgb_agg['forecast'],
            name='XGBoost',
            line=dict(color='orange', width=2, dash='dot'),
            mode='lines+markers' if agg_level == "Monthly" else 'lines',
            marker=dict(size=8, symbol='square') if agg_level == "Monthly" else None,
            hovertemplate='Date: %{x}<br>Forecast: %{y:.3f}<br>(XGBoost)<extra></extra>'
        ))
    
    # Process and plot Ensemble forecast
    if 'Ensemble' in forecasts:
        ensemble_data = forecasts['Ensemble'].copy()
        ensemble_agg, _ = aggregate_forecast_data(ensemble_data, days)
        
        fig.add_trace(go.Scatter(
            x=ensemble_agg['date'],
            y=ensemble_agg['forecast'],
            name='Ensemble (Recommended)',
            line=dict(color='green', width=3),
            mode='lines+markers' if agg_level == "Monthly" else 'lines',
            marker=dict(size=10, symbol='diamond') if agg_level == "Monthly" else None,
            hovertemplate='Date: %{x}<br>Forecast: %{y:.3f}<br>(Ensemble)<extra></extra>'
        ))
    
    fig.update_layout(
        title=f'Renewable Energy Forecast - {title_suffix}',
        xaxis_title='Date',
        yaxis_title='Renewable Score',
        yaxis_range=[0, 1],
        hovermode='x unified',
        height=600,
        legend=dict(
            x=0.01, 
            y=0.99,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='gray',
            borderwidth=1
        ),
        template='plotly_white'
    )
    
    # Add annotation explaining aggregation
    if agg_level == "Monthly":
        fig.add_annotation(
            text="📊 Data aggregated to monthly averages for clarity",
            xref="paper", yref="paper",
            x=0.5, y=-0.15,
            showarrow=False,
            font=dict(size=11, color="gray"),
            xanchor='center'
        )
    
    return fig


def plot_index_breakdown(df):
    """Plot current average index breakdown."""
    latest = df.iloc[-30:]  # Last 30 days average
    
    avg_solar = latest['Solar'].mean()
    avg_wind = latest['Wind'].mean()
    avg_hydro = latest['Hydro'].mean()
    
    fig = go.Figure(data=[
        go.Bar(
            x=['Solar', 'Wind', 'Hydro'],
            y=[avg_solar, avg_wind, avg_hydro],
            marker_color=['orange', 'steelblue', 'teal'],
            text=[f'{v:.2f}' for v in [avg_solar, avg_wind, avg_hydro]],
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        title='Current Renewable Energy Index (30-day average)',
        yaxis_title='Index Value',
        yaxis_range=[0, 1],
        height=400
    )
    
    return fig


def plot_energy_breakdown_forecast(historical_df, city_data, days):
    """
    Plot Solar, Wind, and Hydro forecasts as three separate lines.
    Shows future potential for each energy type.
    """
    from models.prophet_model import ProphetForecast
    
    fig = go.Figure()
    
    # Historical data (last 90 days) - show all three indices
    hist_recent = historical_df.tail(90) if len(historical_df) > 90 else historical_df
    
    fig.add_trace(go.Scatter(
        x=hist_recent['date'],
        y=hist_recent['Solar'],
        name='☀️ Solar (Historical)',
        line=dict(color='orange', width=1.5, dash='solid'),
        opacity=0.6,
        showlegend=True
    ))
    
    fig.add_trace(go.Scatter(
        x=hist_recent['date'],
        y=hist_recent['Wind'],
        name='💨 Wind (Historical)',
        line=dict(color='steelblue', width=1.5, dash='solid'),
        opacity=0.6,
        showlegend=True
    ))
    
    fig.add_trace(go.Scatter(
        x=hist_recent['date'],
        y=hist_recent['Hydro'],
        name='💧 Hydro (Historical)',
        line=dict(color='teal', width=1.5, dash='solid'),
        opacity=0.6,
        showlegend=True
    ))
    
    # Forecast each energy type separately
    try:
        # Prepare data for each energy type
        for energy_type, color, emoji in [
            ('Solar', 'orange', '☀️'),
            ('Wind', 'steelblue', '💨'),
            ('Hydro', 'teal', '💧')
        ]:
            # Create a temporary dataframe with this energy index as the target
            temp_df = city_data[['date', energy_type]].copy()
            temp_df = temp_df.rename(columns={energy_type: 'Renewable_Score'})
            temp_df = temp_df.dropna()
            
            if len(temp_df) >= 10:
                # Train Prophet for this energy type
                prophet = ProphetForecast()
                prophet.train(temp_df)
                forecast = prophet.predict(days, include_uncertainty=False)
                
                # Aggregate if needed
                forecast_agg, agg_label = aggregate_forecast_data(forecast, days)
                
                # Add forecast line
                mode = 'lines+markers' if agg_label == "Monthly Average" else 'lines'
                
                fig.add_trace(go.Scatter(
                    x=forecast_agg['date'],
                    y=forecast_agg['forecast'],
                    name=f'{emoji} {energy_type} (Forecast)',
                    line=dict(color=color, width=3, dash='dash'),
                    mode=mode,
                    marker=dict(size=8) if mode == 'lines+markers' else None,
                    hovertemplate=f'{energy_type}: %{{y:.3f}}<extra></extra>'
                ))
    
    except Exception as e:
        st.warning(f"Could not generate individual energy forecasts: {e}")
    
    # Determine title based on days
    if days <= 30:
        title_suffix = f"{days} days ahead"
    elif days <= 150:
        title_suffix = "4 months ahead (Monthly Averages)"
    else:
        title_suffix = "1 year ahead (Monthly Averages)"
    
    fig.update_layout(
        title=f'Energy Type Breakdown - {title_suffix}',
        xaxis_title='Date',
        yaxis_title='Energy Potential Index',
        yaxis_range=[0, 1],
        hovermode='x unified',
        height=600,
        legend=dict(
            x=0.01,
            y=0.99,
            bgcolor='rgba(255, 255, 255, 0.9)',
            bordercolor='gray',
            borderwidth=1
        ),
        template='plotly_white'
    )
    
    return fig


# ============================================================
# Main App
# ============================================================

def main():
    # Header
    st.markdown('<p class="main-header">🌍 ClimaZoneAI</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Renewable Energy Forecasting for Canada</p>', 
                unsafe_allow_html=True)
    
    # Load data
    df = load_processed_data()
    
    if df is None:
        st.stop()
    
    # Check if indices are computed
    if 'Renewable_Score' not in df.columns:
        st.warning("Computing renewable energy indices...")
        df = compute_indices_on_the_fly(df)
    
    # ============================================================
    # Sidebar - Filters
    # ============================================================
    
    st.sidebar.title("🎛️ Controls")
    
    # Province selector
    provinces = sorted(df['province'].dropna().unique())
    selected_province = st.sidebar.selectbox("Select Province", provinces, index=0)
    
    # Filter cities by province
    cities_in_province = sorted(df[df['province'] == selected_province]['city'].dropna().unique())
    selected_city = st.sidebar.selectbox("Select City", cities_in_province, index=0)
    
    # Forecast horizon
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔮 Forecast Settings")
    forecast_options = {
        "30 days (1 month)": 30,
        "120 days (4 months)": 120,
        "365 days (1 year)": 365
    }
    forecast_choice = st.sidebar.selectbox("Forecast Horizon", list(forecast_options.keys()))
    forecast_days = forecast_options[forecast_choice]
    
    # Model selection
    show_prophet = st.sidebar.checkbox("Show Prophet", value=True)
    show_xgboost = st.sidebar.checkbox("Show XGBoost", value=True)
    show_ensemble = st.sidebar.checkbox("Show Ensemble", value=True)
    
    # ============================================================
    # Filter Data
    # ============================================================
    
    city_data = df[(df['province'] == selected_province) & (df['city'] == selected_city)].copy()
    city_data = city_data.sort_values('date').reset_index(drop=True)
    
    if len(city_data) < 30:
        st.error(f"❌ Not enough data for {selected_city}. Please select another city.")
        st.stop()
    
    # ============================================================
    # Main Content - Tabs
    # ============================================================
    
    tab1, tab2, tab3 = st.tabs(["📊 Historical Analysis", "🔮 Forecast", "📈 Model Insights"])
    
    # ------------------------------------------------------------
    # TAB 1: Historical Analysis
    # ------------------------------------------------------------
    with tab1:
        st.header(f"Historical Data - {selected_city}, {selected_province}")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        latest_30 = city_data.iloc[-30:]
        
        with col1:
            st.metric("📅 Data Points", f"{len(city_data):,}")
        with col2:
            st.metric("☀️ Solar Index", f"{latest_30['Solar'].mean():.2f}")
        with col3:
            st.metric("💨 Wind Index", f"{latest_30['Wind'].mean():.2f}")
        with col4:
            st.metric("💧 Hydro Index", f"{latest_30['Hydro'].mean():.2f}")
        
        # Renewable Score history
        st.plotly_chart(plot_renewable_score_history(city_data, selected_city, selected_province),
                       use_container_width=True)
        
        # Individual indices
        st.plotly_chart(plot_historical_trends(city_data, selected_city, selected_province),
                       use_container_width=True)
        
        # Index breakdown
        col1, col2 = st.columns([1, 1])
        with col1:
            st.plotly_chart(plot_index_breakdown(city_data), use_container_width=True)
        
        with col2:
            st.subheader("📋 Data Summary")
            st.write(f"**Date Range:** {city_data['date'].min().date()} to {city_data['date'].max().date()}")
            st.write(f"**Total Days:** {len(city_data)}")
            st.write(f"**Latest Renewable Score:** {city_data['Renewable_Score'].iloc[-1]:.3f}")
            st.write(f"**Average Renewable Score:** {city_data['Renewable_Score'].mean():.3f}")
            st.write(f"**Best Score:** {city_data['Renewable_Score'].max():.3f} on {city_data.loc[city_data['Renewable_Score'].idxmax(), 'date'].date()}")
    
    # ------------------------------------------------------------
    # TAB 2: Forecast
    # ------------------------------------------------------------
    with tab2:
        st.header(f"Renewable Energy Forecast - {selected_city}, {selected_province}")
        st.write(f"**Forecast Horizon:** {forecast_choice}")
        
        # Train models
        prophet_model, xgb_model, ensemble_model = train_models(city_data)
        
        if prophet_model is None:
            st.error("Model training failed. Please check your data.")
            st.stop()
        
        # Generate forecasts
        with st.spinner("🔮 Generating forecasts..."):
            forecasts = generate_forecasts(prophet_model, xgb_model, ensemble_model, 
                                          city_data, forecast_days)
        
        if forecasts is None:
            st.error("Forecast generation failed.")
            st.stop()
        
        # Plot overall renewable score comparison
        st.subheader("🌍 Overall Renewable Energy Score")
        st.plotly_chart(plot_forecast_comparison(city_data.iloc[-90:], forecasts, forecast_days),
                       use_container_width=True)
        
        # Plot energy type breakdown
        st.subheader("⚡ Energy Type Breakdown (Solar | Wind | Hydro)")
        st.info("👇 Each energy type is forecasted separately to show individual potential")
        st.plotly_chart(plot_energy_breakdown_forecast(city_data.iloc[-90:], city_data, forecast_days),
                       use_container_width=True)
        
        # Forecast statistics
        st.subheader("📊 Forecast Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'Prophet' in forecasts and show_prophet:
                prophet_avg = forecasts['Prophet']['forecast'].mean()
                st.metric("Prophet Avg Forecast", f"{prophet_avg:.3f}")
        
        with col2:
            if 'XGBoost' in forecasts and show_xgboost:
                xgb_avg = forecasts['XGBoost']['forecast'].mean()
                st.metric("XGBoost Avg Forecast", f"{xgb_avg:.3f}")
        
        with col3:
            if 'Ensemble' in forecasts and show_ensemble:
                ensemble_avg = forecasts['Ensemble']['forecast'].mean()
                st.metric("Ensemble Avg Forecast", f"{ensemble_avg:.3f}")
                st.info("✨ Recommended: Ensemble combines both models")
        
        # Download forecast data
        st.subheader("💾 Download Forecast Data")
        if 'Ensemble' in forecasts:
            csv = forecasts['Ensemble'].to_csv(index=False)
            st.download_button(
                label="Download Ensemble Forecast CSV",
                data=csv,
                file_name=f"forecast_{selected_city}_{forecast_days}days.csv",
                mime="text/csv"
            )
    
    # ------------------------------------------------------------
    # TAB 3: Model Insights
    # ------------------------------------------------------------
    with tab3:
        st.header("🧠 Model Insights & Feature Importance")
        
        # Feature importance (if models are trained)
        if xgb_model is not None:
            st.subheader("📊 XGBoost Feature Importance")
            
            try:
                importance_df = xgb_model.get_feature_importance()
                if importance_df is not None:
                    fig = px.bar(importance_df, x='importance', y='feature', 
                                orientation='h',
                                title='Which factors matter most for renewable energy prediction?')
                    fig.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.write("**Top 3 Most Important Features:**")
                    for i, row in importance_df.head(3).iterrows():
                        st.write(f"{i+1}. **{row['feature']}**: {row['importance']:.4f}")
            except Exception as e:
                st.warning(f"Feature importance not available: {e}")
        
        # Model comparison
        st.subheader("🏆 Model Comparison")
        st.write("""
        **Prophet:** Best for long-term trends and seasonal patterns. Uses time-series decomposition.
        
        **XGBoost:** Best for short-term predictions and weather dependencies. Machine learning-based.
        
        **Ensemble:** Combines both models for balanced performance across all horizons.
        """)
        
        # Data quality info
        st.subheader("📈 Data Quality")
        missing_pct = (city_data.isnull().sum() / len(city_data) * 100).round(2)
        st.write("Missing data percentage by feature:")
        st.dataframe(missing_pct[missing_pct > 0])
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p><strong>ClimaZoneAI</strong> | Developed by Team ClimaZoneAI | SFU DataJam 2025</p>
        <p>🌤️ Powered by Prophet, XGBoost, and climate science</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

