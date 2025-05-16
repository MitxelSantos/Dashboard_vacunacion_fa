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

# Manejo de importación segura para maps
__maps_available__ = False
try:
    # Verificar si el archivo maps.py existe
    import os
    if os.path.exists(os.path.join(os.path.dirname(__file__), 'maps.py')):
        from .maps import (
            create_choropleth_map,
            create_bubble_map,
            load_tolima_geojson
        )
        __maps_available__ = True
except ImportError:
    # Si no existe o hay error al importar, simplemente continuar
    pass

__all__ = [
    'create_bar_chart', 
    'create_pie_chart', 
    'create_scatter_plot', 
    'create_line_chart'
]

if __maps_available__:
    __all__ += ['create_choropleth_map', 'create_bubble_map', 'load_tolima_geojson']