"""
ClimaZoneAI - XGBoost Forecasting Model
---------------------------------------
Trains an XGBoost regressor to predict Renewable_Score
based on weather and environmental features.

Author: ClimaZoneAI Team
Version: 2.0
"""

import pandas as pd
import numpy as np
from datetime import timedelta
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error


class XGBoostForecast:
    """Machine Learning forecaster using XGBoost regression."""

    def __init__(self):
        self.model = XGBRegressor(
            n_estimators=400,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            objective="reg:squarederror"
        )

    # ------------------------------------------------------------
    # 🧩 1️⃣ Feature Engineering
    # ------------------------------------------------------------
    def prepare_features(self, df):
        """Create lag and rolling features for temporal learning."""
        df = df.sort_values("date").copy()

        # Generate lag-based features (previous day/week averages)
        df["lag_1"] = df["Renewable_Score"].shift(1)
        df["lag_7"] = df["Renewable_Score"].shift(7)
        df["rolling_mean_7"] = df["Renewable_Score"].rolling(7).mean()
        df["rolling_std_7"] = df["Renewable_Score"].rolling(7).std()

        # Drop NaNs from the first week
        df = df.dropna(subset=["lag_1", "lag_7", "rolling_mean_7"])

        # Core weather features (auto-selected if present)
        feature_cols = [
            col for col in [
                "PRCP", "TAVG", "TMIN", "TMAX", "SNOW", "SNWD",
                "elevation", "lag_1", "lag_7", "rolling_mean_7", "rolling_std_7"
            ]
            if col in df.columns
        ]

        X = df[feature_cols]
        y = df["Renewable_Score"]

        return X, y

    # ------------------------------------------------------------
    # 🧠 2️⃣ Model Training
    # ------------------------------------------------------------
    def train(self, df):
        """Train XGBoost model on historical data."""
        X, y = self.prepare_features(df)
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

        # Fit model (XGBoost 3.x doesn't support eval_metric in fit())
        self.model.fit(X_train, y_train, verbose=False)

        preds = self.model.predict(X_val)
        rmse = np.sqrt(mean_squared_error(y_val, preds))
        print(f"✅ XGBoost trained. Validation RMSE: {rmse:.4f}")

    # ------------------------------------------------------------
    # 🔮 3️⃣ Prediction / Forecasting (Improved)
    # ------------------------------------------------------------
    def predict_future(self, df, days_ahead=30):
        """
        Improved prediction using historical weather patterns.
        Reduces error accumulation by using seasonal weather averages.
        """
        df = df.sort_values("date").copy()
        max_date = df["date"].max()
        forecasts = []
        
        for i in range(days_ahead):
            next_date = max_date + timedelta(days=i+1)
            
            # Use historical same-month weather (reduce error accumulation)
            same_month_data = df[df["date"].dt.month == next_date.month]
            
            if not same_month_data.empty:
                # Use median weather values for the same month
                weather_features = {}
                for col in ["PRCP", "TAVG", "TMIN", "TMAX", "SNOW", "SNWD", "elevation"]:
                    if col in same_month_data.columns:
                        weather_features[col] = same_month_data[col].median()
            else:
                # Fallback to last known values
                weather_features = df.iloc[-1][["PRCP", "TAVG", "TMIN", "TMAX", "SNOW", "SNWD", "elevation"]].to_dict()
            
            # Calculate lag features from recent history and predictions
            if i == 0:
                lag_1 = df["Renewable_Score"].iloc[-1]
                lag_7 = df["Renewable_Score"].iloc[-7:].mean()
                rolling_mean = df["Renewable_Score"].iloc[-7:].mean()
                rolling_std = df["Renewable_Score"].iloc[-7:].std()
            else:
                recent_forecasts = [f["forecast"] for f in forecasts[-7:]]
                lag_1 = forecasts[-1]["forecast"]
                lag_7 = np.mean(recent_forecasts) if len(recent_forecasts) >= 7 else df["Renewable_Score"].iloc[-7:].mean()
                rolling_mean = np.mean(recent_forecasts) if recent_forecasts else df["Renewable_Score"].iloc[-7:].mean()
                rolling_std = np.std(recent_forecasts) if len(recent_forecasts) > 1 else df["Renewable_Score"].iloc[-7:].std()
            
            # Build feature vector
            feature_dict = {
                **weather_features,
                "lag_1": lag_1,
                "lag_7": lag_7,
                "rolling_mean_7": rolling_mean,
                "rolling_std_7": rolling_std
            }
            
            X_next = pd.DataFrame([feature_dict])
            
            # Make prediction
            y_pred = self.model.predict(X_next)[0]
            forecasts.append({"date": next_date, "forecast": y_pred})
        
        return pd.DataFrame(forecasts)
    
    # ------------------------------------------------------------
    # 📊 4️⃣ Feature Importance Analysis
    # ------------------------------------------------------------
    def get_feature_importance(self):
        """Get and return feature importance scores."""
        if not hasattr(self.model, 'feature_importances_'):
            print("⚠️ Model not trained yet. Train the model first.")
            return None
        
        importance_df = pd.DataFrame({
            'feature': self.model.feature_names_in_,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return importance_df
    
    def plot_feature_importance(self, output_path="outputs/xgb_feature_importance.png"):
        """Visualize feature importance."""
        import matplotlib.pyplot as plt
        import os
        
        importance_df = self.get_feature_importance()
        if importance_df is None:
            return
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        plt.figure(figsize=(10, 6))
        plt.barh(importance_df['feature'], importance_df['importance'], color='steelblue')
        plt.xlabel('Importance Score', fontsize=12)
        plt.ylabel('Features', fontsize=12)
        plt.title('XGBoost Feature Importance for Renewable Energy Prediction', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Feature importance plot saved to {output_path}")
        return importance_df
