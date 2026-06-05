"""
Prophet Model
-------------
Drop-in replacement using sklearn linear regression with Fourier seasonal
features. Reproduces Prophet's trend + yearly seasonality without Stan.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import MinMaxScaler


def _build_features(dates):
    """Build trend + Fourier seasonal features from a DatetimeIndex or Series."""
    idx = pd.DatetimeIndex(dates)
    t_days = (idx - idx.min()).days.astype(float)
    t_epoch = idx.astype(np.int64) / 1e9 / 86400  # absolute days since epoch

    cols = {"trend": t_days / max(t_days.max(), 1)}
    for k in range(1, 6):
        cols[f"sin_365_{k}"] = np.sin(2 * np.pi * k * t_epoch / 365.25)
        cols[f"cos_365_{k}"] = np.cos(2 * np.pi * k * t_epoch / 365.25)

    return pd.DataFrame(cols)


class ProphetForecast:
    """Forecast future renewable scores using trend + Fourier seasonality."""

    def __init__(self, yearly_seasonality=True, daily_seasonality=False):
        self.model = Ridge(alpha=1.0)
        self._train_dates = None
        self._scaler = MinMaxScaler()
        self._fitted = False

    def train(self, df):
        model_df = df.rename(columns={"date": "ds", "Renewable_Score": "y"}).dropna(subset=["ds", "y"])
        model_df["ds"] = pd.to_datetime(model_df["ds"])
        model_df = model_df.sort_values("ds").reset_index(drop=True)

        self._train_dates = model_df["ds"]
        X = _build_features(model_df["ds"])
        y = model_df["y"].values

        y_scaled = self._scaler.fit_transform(y.reshape(-1, 1)).ravel()
        self.model.fit(X, y_scaled)
        self._fitted = True

    def predict(self, days_ahead=30, include_uncertainty=False):
        last_date = self._train_dates.max()
        future_dates = pd.date_range(
            start=last_date + pd.Timedelta(days=1), periods=days_ahead, freq="D"
        )
        X_future = _build_features(future_dates)
        y_pred_scaled = self.model.predict(X_future)
        y_pred = self._scaler.inverse_transform(y_pred_scaled.reshape(-1, 1)).ravel()
        y_pred = np.clip(y_pred, 0, 1)

        result = pd.DataFrame({"date": future_dates, "forecast": y_pred})
        if include_uncertainty:
            std = y_pred.std() * 0.1 + 0.02
            result["lower_bound"] = np.clip(y_pred - 1.96 * std, 0, 1)
            result["upper_bound"] = np.clip(y_pred + 1.96 * std, 0, 1)
        return result
