# src/__init__.py
from .data_preprocessing import main as preprocess_data
from .compute_indices import compute_indices
from .forecast_model import forecast_province
from .rank_top_cities import rank_top_cities

__all__ = ["preprocess_data", "compute_indices", "forecast_province", "rank_top_cities"]
__version__ = "1.0.0"
