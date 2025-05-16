"""
Módulos para visualización de datos del dashboard.
Incluye funciones para crear diferentes tipos de gráficos y mapas.
"""

from .charts import (
    create_bar_chart,
    create_pie_chart,
    create_scatter_plot,
    create_line_chart,
)

# Manejo seguro de la importación de maps
__maps_available__ = False
try:
    # Primero verificar si el archivo existe
    import os

    maps_path = os.path.join(os.path.dirname(__file__), "maps.py")

    if os.path.exists(maps_path):
        from .maps import create_choropleth_map, create_bubble_map, load_tolima_geojson

        __maps_available__ = True
except ImportError:
    # Si faltan dependencias para mapas, todavía se pueden usar otros gráficos
    pass

__all__ = [
    "create_bar_chart",
    "create_pie_chart",
    "create_scatter_plot",
    "create_line_chart",
]

if __maps_available__:
    __all__ += ["create_choropleth_map", "create_bubble_map", "load_tolima_geojson"]
