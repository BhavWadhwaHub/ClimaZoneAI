"""
Prophet Model
-------------
Encapsulates forecasting logic using Meta's Prophet library.
"""

import pandas as pd
from prophet import Prophet


class ProphetForecast:
    """Forecast future renewable scores using Prophet."""

    def __init__(self, yearly_seasonality=True, daily_seasonality=False):
        self.model = Prophet(
            yearly_seasonality=yearly_seasonality,
            daily_seasonality=daily_seasonality
        )

    def train(self, df):
        """Fit Prophet model on provided DataFrame."""
        model_df = df.rename(columns={"date": "ds", "Renewable_Score": "y"})
        self.model.fit(model_df)

    def predict(self, days_ahead=30):
        """Predict next n days."""
        future = self.model.make_future_dataframe(periods=days_ahead)
        forecast = self.model.predict(future)
        return forecast[["ds", "yhat"]].rename(columns={"ds": "date", "yhat": "forecast"})
