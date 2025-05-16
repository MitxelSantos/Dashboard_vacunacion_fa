"""
Módulos para carga y procesamiento de datos del dashboard.
Incluye funciones para cargar datos desde archivos, preprocesarlos y aplicar filtros.
"""

from .loader import load_datasets, calculate_metrics
from .preprocessor import apply_filters

__all__ = ['load_datasets', 'calculate_metrics', 'apply_filters']