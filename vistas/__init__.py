"""
Módulo de vistas para el dashboard de vacunación
"""

__version__ = "1.0"
__author__ = "Ing. José Miguel Santos"

from .overview import show_overview_tab
from .temporal import show_temporal_tab
from .geographic import show_geographic_tab
from .population import show_population_tab

__all__ = [
    'show_overview_tab',
    'show_temporal_tab', 
    'show_geographic_tab',
    'show_population_tab'
]
