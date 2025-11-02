"""
ClimaZoneAI - Models Package
----------------------------
Forecasting models for renewable energy prediction.
"""

from .prophet_model import ProphetForecast
from .xgboost_model import XGBoostForecast
from .ensemble_model import EnsembleForecaster

__all__ = ["ProphetForecast", "XGBoostForecast", "EnsembleForecaster"]
__version__ = "2.0"

