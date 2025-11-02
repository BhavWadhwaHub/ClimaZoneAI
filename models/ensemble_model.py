"""
ClimaZoneAI - Ensemble Forecasting Model
---------------------------------------
Combines Prophet and XGBoost predictions for improved accuracy.

Prophet excels at: Long-term trends and seasonal patterns
XGBoost excels at: Short-term variations and weather dependencies

Author: ClimaZoneAI Team
Version: 1.0
"""

import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error
from .prophet_model import ProphetForecast
from .xgboost_model import XGBoostForecast


class EnsembleForecaster:
    """
    Hybrid forecaster combining Prophet and XGBoost.
    Uses weighted average based on forecast horizon.
    """
    
    def __init__(self, prophet_weight=0.5, xgb_weight=0.5):
        """
        Initialize ensemble with two models.
        
        Args:
            prophet_weight: Weight for Prophet predictions (0-1)
            xgb_weight: Weight for XGBoost predictions (0-1)
        """
        self.prophet = ProphetForecast()
        self.xgboost = XGBoostForecast()
        self.prophet_weight = prophet_weight
        self.xgb_weight = xgb_weight
        
        # Normalize weights
        total = prophet_weight + xgb_weight
        self.prophet_weight /= total
        self.xgb_weight /= total
    
    def train(self, df):
        """Train both Prophet and XGBoost models."""
        print("🔧 Training Ensemble Model...")
        print("  → Training Prophet...")
        self.prophet.train(df)
        
        print("  → Training XGBoost...")
        self.xgboost.train(df)
        
        print("✅ Ensemble training complete!")
    
    def predict(self, df, days_ahead=30):
        """
        Generate ensemble forecast by combining both models.
        
        Args:
            df: Historical data with Renewable_Score
            days_ahead: Number of days to forecast
            
        Returns:
            DataFrame with date, forecast, and individual model predictions
        """
        # Get Prophet forecast
        prophet_forecast = self.prophet.predict(days_ahead, include_uncertainty=False)
        
        # Get XGBoost forecast
        xgb_forecast = self.xgboost.predict_future(df, days_ahead)
        
        # Merge on date
        ensemble = pd.merge(
            prophet_forecast, 
            xgb_forecast, 
            on="date", 
            suffixes=("_prophet", "_xgb")
        )
        
        # Weighted average
        ensemble["forecast"] = (
            self.prophet_weight * ensemble["forecast_prophet"] +
            self.xgb_weight * ensemble["forecast_xgb"]
        )
        
        # Keep individual predictions for analysis
        ensemble = ensemble[["date", "forecast", "forecast_prophet", "forecast_xgb"]]
        
        return ensemble
    
    def adaptive_predict(self, df, days_ahead=30):
        """
        Adaptive weighting: More weight to Prophet for long-term,
        more weight to XGBoost for short-term.
        """
        prophet_forecast = self.prophet.predict(days_ahead, include_uncertainty=False)
        xgb_forecast = self.xgboost.predict_future(df, days_ahead)
        
        ensemble = pd.merge(
            prophet_forecast, 
            xgb_forecast, 
            on="date", 
            suffixes=("_prophet", "_xgb")
        )
        
        # Adaptive weights based on forecast horizon
        ensemble["days_out"] = range(1, len(ensemble) + 1)
        
        # Short-term: favor XGBoost (more weight in first 7 days)
        # Long-term: favor Prophet (more weight after 7 days)
        ensemble["adaptive_xgb_weight"] = np.maximum(0.3, 0.8 - (ensemble["days_out"] / days_ahead) * 0.5)
        ensemble["adaptive_prophet_weight"] = 1 - ensemble["adaptive_xgb_weight"]
        
        ensemble["forecast"] = (
            ensemble["adaptive_prophet_weight"] * ensemble["forecast_prophet"] +
            ensemble["adaptive_xgb_weight"] * ensemble["forecast_xgb"]
        )
        
        return ensemble[["date", "forecast", "forecast_prophet", "forecast_xgb"]]
    
    def evaluate(self, df, test_days=30):
        """
        Evaluate ensemble performance on test set.
        
        Args:
            df: Full dataset
            test_days: Number of days to use for testing
        """
        if len(df) < test_days + 30:
            print("⚠️ Not enough data for evaluation")
            return None
        
        # Split data
        train_df = df.iloc[:-test_days].copy()
        test_df = df.iloc[-test_days:].copy()
        
        # Train models
        self.train(train_df)
        
        # Generate predictions
        predictions = self.predict(train_df, test_days)
        
        # Get actual values
        actual = test_df["Renewable_Score"].values
        
        # Calculate metrics for ensemble
        ensemble_pred = predictions["forecast"].values
        prophet_pred = predictions["forecast_prophet"].values
        xgb_pred = predictions["forecast_xgb"].values
        
        def calc_metrics(y_true, y_pred, model_name):
            rmse = np.sqrt(mean_squared_error(y_true, y_pred))
            mae = mean_absolute_error(y_true, y_pred)
            mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-10))) * 100
            return {
                "Model": model_name,
                "RMSE": round(rmse, 4),
                "MAE": round(mae, 4),
                "MAPE": round(mape, 2)
            }
        
        results = [
            calc_metrics(actual, ensemble_pred, "Ensemble"),
            calc_metrics(actual, prophet_pred, "Prophet"),
            calc_metrics(actual, xgb_pred, "XGBoost")
        ]
        
        results_df = pd.DataFrame(results)
        
        print("\n📊 Model Performance Comparison:")
        print(results_df.to_string(index=False))
        
        return results_df

