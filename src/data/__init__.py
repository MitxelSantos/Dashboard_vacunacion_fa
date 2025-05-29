"""
Data loading and processing modules
"""

from .unified_loader import load_and_combine_data
from .data_cleaner import clean_data, calculate_current_age
from .aseguramiento_loader import load_aseguramiento

__all__ = [
    "load_and_combine_data",
    "clean_data",
    "calculate_current_age",
    "load_aseguramiento",
]
