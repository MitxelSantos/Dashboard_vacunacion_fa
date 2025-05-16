"""
Módulos para visualización de datos del dashboard.
Incluye funciones para crear diferentes tipos de gráficos y mapas.
"""

from .charts import (
    create_bar_chart, 
    create_pie_chart, 
    create_scatter_plot, 
    create_line_chart
)

# Usar un bloque try-except más robusto para maps
__maps_available__ = False
try:
    # Primero verificar si el módulo existe
    import importlib.util
    maps_spec = importlib.util.find_spec('.maps', package='src.visualization')
    
    if maps_spec is not None:
        from .maps import (
            create_choropleth_map,
            create_bubble_map,
            load_tolima_geojson
        )
        __maps_available__ = True
except (ImportError, ModuleNotFoundError):
    # Si faltan dependencias para mapas, todavía se pueden usar otros gráficos
    pass

__all__ = [
    'create_bar_chart', 
    'create_pie_chart', 
    'create_scatter_plot', 
    'create_line_chart'
]

if __maps_available__:
    __all__ += ['create_choropleth_map', 'create_bubble_map', 'load_tolima_geojson']