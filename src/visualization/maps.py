"""
src/visualization/maps.py - VERSIÓN ACTUALIZADA
Mapas mejorados con integración de shapefiles y funcionalidad interactiva
"""

import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
import plotly.express as px
import geopandas as gpd
from pathlib import Path
import branca.colormap as cm

# Ruta base para archivos geográficos
ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"
GEO_DIR = Path(__file__).parent.parent.parent / "data" / "geo"


def load_tolima_geojson():
    """
    Carga el GeoJSON del departamento del Tolima con sus municipios.
    VERSIÓN ACTUALIZADA: Usa el nuevo sistema de carga de shapefiles
    
    Returns:
        gpd.GeoDataFrame o None: GeoDataFrame con los municipios del Tolima
    """
    try:
        # Intentar usar el nuevo cargador de geodatos
        from .geo_loader import get_geo_loader
        
        geo_loader = get_geo_loader()
        geodata = geo_loader.load_tolima_geodata()
        
        if 'municipios' in geodata:
            st.success("✅ Shapefiles de municipios cargados correctamente")
            return geodata['municipios']
        else:
            st.warning("⚠️ No se encontraron shapefiles de municipios")
            return load_tolima_geojson_legacy()
            
    except ImportError:
        # Fallback al método original
        return load_tolima_geojson_legacy()


def load_tolima_geojson_legacy():
    """
    Método original de carga de GeoJSON (fallback)
    """
    # Ruta al archivo GeoJSON (debe estar en assets/geo/)
    geo_path = GEO_DIR / "tolima_municipios.geojson"
    
    if geo_path.exists():
        try:
            return gpd.read_file(str(geo_path))
        except Exception as e:
            st.error(f"Error al cargar el archivo GeoJSON: {str(e)}")
            return None
    else:
        st.info(f"""
        Archivo GeoJSON de municipios no encontrado en {str(geo_path)}
        
        Para habilitar mapas, descargue un GeoJSON con los límites municipales del Tolima y 
        colóquelo en la carpeta data/geo/ con el nombre tolima_municipios.geojson
        
        O mejor aún, use shapefiles con el nuevo sistema integrado.
        """)
        return None


def create_choropleth_map(data, column, title, color_scale="YlOrRd", legend_name=None):
    """
    Crea un mapa coroplético del Tolima coloreado según el valor de una columna.
    VERSIÓN MEJORADA: Incluye soporte para shapefiles y mejor manejo de errores
    
    Args:
        data (pd.DataFrame): DataFrame con los datos de municipios
        column (str): Nombre de la columna con los valores a mapear
        title (str): Título del mapa
        color_scale (str): Escala de colores para el mapa
        legend_name (str): Nombre de la leyenda
        
    Returns:
        folium.Map: Mapa de Folium
    """
    # Cargar GeoJSON (ahora con soporte para shapefiles)
    geo_data = load_tolima_geojson()
    
    if geo_data is None:
        st.error("❌ No se pudieron cargar los datos geográficos")
        return create_simple_folium_map()
    
    # Verificar que exista la columna correspondiente al nombre del municipio
    if "DPMP" not in data.columns:
        st.error("El DataFrame no contiene la columna 'DPMP' necesaria para el mapa")
        return create_simple_folium_map()
    
    # Verificar que exista la columna con los valores
    if column not in data.columns:
        st.error(f"El DataFrame no contiene la columna '{column}' necesaria para el mapa")
        return create_simple_folium_map()
    
    # Buscar la columna de nombre de municipio en el GeoDataFrame
    municipio_col = None
    possible_cols = ['municipio', 'MPIO_CNMBR', 'nombre', 'DPMP', 'nom_mpio']
    
    for col in possible_cols:
        if col in geo_data.columns:
            municipio_col = col
            break
    
    if municipio_col is None:
        st.error("No se encontró una columna válida de nombre de municipio en los geodatos")
        return create_simple_folium_map()
    
    # Crear mapa base centrado en el Tolima
    m = folium.Map(location=[4.43889, -75.2322], zoom_start=8)
    
    # Normalizar nombres de municipios para mejor matching
    from src.data.normalize import normalize_municipality_names
    
    data_norm = normalize_municipality_names(data.copy(), 'DPMP')
    geo_data_norm = geo_data.copy()
    geo_data_norm['municipio_norm'] = geo_data_norm[municipio_col].astype(str).str.lower().str.strip()
    
    # Fusionar datos con geometría usando nombres normalizados
    merged_data = pd.merge(
        geo_data_norm,
        data_norm,
        left_on="municipio_norm",
        right_on="DPMP_norm",
        how="left"
    )
    
    # Verificar que haya datos fusionados
    if merged_data[column].isna().all():
        st.warning("No se pudieron fusionar los datos con el GeoJSON. Verifique que los nombres de municipios coincidan")
        
        # Mostrar información de debug
        with st.expander("🔍 Información de depuración"):
            st.write("**Municipios en geodatos:**")
            st.write(sorted(geo_data_norm[municipio_col].unique()[:10]))
            st.write("**Municipios en datos:**")
            st.write(sorted(data['DPMP'].unique()[:10]))
        
        return create_simple_folium_map()
    
    # Crear coroplético mejorado
    legend_name = legend_name or column
    
    # Calcular rango de valores para la escala de colores
    min_val = merged_data[column].min()
    max_val = merged_data[column].max()
    
    if pd.isna(min_val) or pd.isna(max_val) or min_val == max_val:
        # Si no hay variación, usar colores predeterminados
        colormap = cm.linear.YlOrRd_09.scale(0, 100)
    else:
        colormap = cm.linear.YlOrRd_09.scale(min_val, max_val)
    
    # Añadir características al mapa
    for idx, row in merged_data.iterrows():
        if pd.notna(row['geometry']):
            value = row[column] if pd.notna(row[column]) else 0
            color = colormap(value) if pd.notna(value) else '#808080'
            
            # Crear popup con información detallada
            municipio_name = row.get('DPMP', row.get(municipio_col, 'Sin nombre'))
            
            popup_content = f"""
            <div style="width:250px; font-family: Arial, sans-serif;">
                <h4 style="margin-bottom: 10px; color: #2E4057;">{municipio_name}</h4>
                <hr style="margin: 10px 0;">
                <div style="margin-bottom: 5px;">
                    <strong>{legend_name}:</strong> 
                    <span style="color: #E74C3C; font-weight: bold;">
                        {value:.2f}{'%' if 'cobertura' in column.lower() else ''}
                    </span>
                </div>
            """
            
            # Añadir información adicional si está disponible
            if 'Vacunados' in row:
                popup_content += f"""
                <div style="margin-bottom: 5px;">
                    <strong>Vacunados:</strong> {int(row['Vacunados']) if pd.notna(row['Vacunados']) else 0:,}
                </div>
                """.replace(',', '.')
            
            if 'DANE' in row:
                popup_content += f"""
                <div style="margin-bottom: 5px;">
                    <strong>Población DANE:</strong> {int(row['DANE']) if pd.notna(row['DANE']) else 0:,}
                </div>
                """.replace(',', '.')
            
            popup_content += "</div>"
            
            # Crear feature con estilo mejorado
            feature = folium.GeoJson(
                row['geometry'].__geo_interface__,
                style_function=lambda x, color=color: {
                    'fillColor': color,
                    'color': 'black',
                    'weight': 1,
                    'fillOpacity': 0.7,
                    'opacity': 1
                },
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=folium.Tooltip(f"{municipio_name}: {value:.1f}{'%' if 'cobertura' in column.lower() else ''}")
            )
            
            feature.add_to(m)
    
    # Añadir colormap mejorado
    colormap.caption = legend_name
    colormap.add_to(m)
    
    # Añadir título mejorado
    title_html = f'''
        <div style="position: fixed; 
                    top: 10px; left: 50px; width: 300px; height: auto; 
                    background-color: white; border: 2px solid grey; z-index: 9999; 
                    font-size: 14px; font-family: Arial, sans-serif; 
                    padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.3);">
             <h3 style="margin: 0; color: #2E4057;">{title}</h3>
             <small style="color: #7F8C8D;">Haz clic en cualquier municipio para ver detalles</small>
        </div>
        '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    return m


def create_simple_folium_map():
    """
    Crea un mapa básico del Tolima sin datos geográficos
    """
    m = folium.Map(location=[4.43889, -75.2322], zoom_start=8)
    
    # Añadir marcador del centro del Tolima
    folium.Marker(
        [4.43889, -75.2322],
        popup="Tolima - Centro Geográfico",
        tooltip="Departamento del Tolima",
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)
    
    return m


def create_bubble_map(data, location_col, size_col, color_col=None, title="", hover_data=None):
    """
    Crea un mapa de burbujas del Tolima usando Plotly Express.
    VERSIÓN MEJORADA: Mejor integración con shapefiles
    
    Args:
        data (pd.DataFrame): DataFrame con los datos
        location_col (str): Nombre de la columna con los municipios
        size_col (str): Nombre de la columna para determinar el tamaño de las burbujas
        color_col (str): Nombre de la columna para determinar el color (opcional)
        title (str): Título del mapa
        hover_data (list): Lista de columnas para mostrar en el hover
        
    Returns:
        fig: Figura de Plotly
    """
    # Cargar GeoJSON
    geo_data = load_tolima_geojson()
    
    if geo_data is None:
        return create_simple_plotly_map(data, title)
    
    # Verificar que existan las columnas necesarias
    if location_col not in data.columns:
        st.error(f"El DataFrame no contiene la columna '{location_col}' necesaria para el mapa")
        return create_simple_plotly_map(data, title)
    
    if size_col not in data.columns:
        st.error(f"El DataFrame no contiene la columna '{size_col}' necesaria para el mapa")
        return create_simple_plotly_map(data, title)
    
    if color_col and color_col not in data.columns:
        st.error(f"El DataFrame no contiene la columna '{color_col}' necesaria para el mapa")
        return create_simple_plotly_map(data, title)
    
    # Buscar columna de municipio en geodatos
    municipio_col = None
    possible_cols = ['municipio', 'MPIO_CNMBR', 'nombre', 'DPMP']
    
    for col in possible_cols:
        if col in geo_data.columns:
            municipio_col = col
            break
    
    if municipio_col is None:
        return create_simple_plotly_map(data, title)
    
    # Fusionar datos con geometría para obtener centroides
    merged_data = pd.merge(
        geo_data,
        data,
        left_on=municipio_col,
        right_on=location_col,
        how="right"
    )
    
    # Calcular centroides para ubicar las burbujas
    if not merged_data.empty and 'geometry' in merged_data.columns:
        merged_data["centroid"] = merged_data.geometry.centroid
        merged_data["latitude"] = merged_data.centroid.y
        merged_data["longitude"] = merged_data.centroid.x
        
        # Crear mapa de burbujas
        if color_col:
            fig = px.scatter_mapbox(
                merged_data,
                lat="latitude",
                lon="longitude",
                size=size_col,
                color=color_col,
                hover_name=location_col,
                hover_data=hover_data,
                zoom=7,
                height=600,
                title=title
            )
        else:
            fig = px.scatter_mapbox(
                merged_data,
                lat="latitude",
                lon="longitude",
                size=size_col,
                hover_name=location_col,
                hover_data=hover_data,
                zoom=7,
                height=600,
                title=title
            )
        
        # Configurar estilo del mapa
        fig.update_layout(
            mapbox_style="carto-positron",
            mapbox_zoom=7,
            mapbox_center={"lat": 4.43889, "lon": -75.2322},
            margin={"r": 0, "t": 50, "l": 0, "b": 0}
        )
        
        return fig
    else:
        return create_simple_plotly_map(data, title)


def create_simple_plotly_map(data, title):
    """
    Crea un mapa simple de Plotly sin geodatos
    """
    # Coordenadas aproximadas de algunos municipios del Tolima
    municipios_coords = {
        'IBAGUÉ': [4.4389, -75.2322],
        'ESPINAL': [4.1489, -74.8839],
        'HONDA': [5.2089, -74.7361],
        'MELGAR': [4.2069, -74.6431],
        'GIRARDOT': [4.3019, -74.8069],
        'CHAPARRAL': [3.7239, -75.4849],
        'LÍBANO': [4.9209, -75.0631],
        'PURIFICACIÓN': [3.8569, -74.9289],
        'MARIQUITA': [5.1989, -74.8929],
        'ARMERO': [5.0339, -74.8989],
    }
    
    # Crear datos de muestra para el mapa
    sample_data = []
    for municipio, coords in municipios_coords.items():
        sample_data.append({
            'municipio': municipio,
            'lat': coords[0],
            'lon': coords[1],
            'value': np.random.randint(10, 100)
        })
    
    sample_df = pd.DataFrame(sample_data)
    
    fig = px.scatter_mapbox(
        sample_df,
        lat="lat",
        lon="lon",
        size="value",
        hover_name="municipio",
        zoom=7,
        height=600,
        title=f"{title} (Mapa de muestra)"
    )
    
    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=7,
        mapbox_center={"lat": 4.43889, "lon": -75.2322},
        margin={"r": 0, "t": 50, "l": 0, "b": 0}
    )
    
    return fig


def show_map_integration_status():
    """
    Muestra el estado de integración de mapas
    """
    st.subheader("🗺️ Estado de Integración de Mapas")
    
    # Verificar disponibilidad de nuevos módulos
    try:
        from .geo_loader import get_geo_loader
        geo_loader_available = True
    except ImportError:
        geo_loader_available = False
    
    try:
        from .interactive_maps import get_map_manager
        interactive_maps_available = True
    except ImportError:
        interactive_maps_available = False
    
    # Verificar archivos de shapefiles
    shapefiles_available = GEO_DIR.exists() and len(list(GEO_DIR.glob("*.shp"))) > 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status = "✅" if geo_loader_available else "❌"
        st.write(f"{status} **Cargador de Geodatos**")
        if not geo_loader_available:
            st.caption("Módulo geo_loader.py no encontrado")
    
    with col2:
        status = "✅" if interactive_maps_available else "❌"
        st.write(f"{status} **Mapas Interactivos**")
        if not interactive_maps_available:
            st.caption("Módulo interactive_maps.py no encontrado")
    
    with col3:
        status = "✅" if shapefiles_available else "❌"
        st.write(f"{status} **Shapefiles**")
        if shapefiles_available:
            shp_count = len(list(GEO_DIR.glob("*.shp")))
            st.caption(f"{shp_count} archivo(s) .shp encontrado(s)")
        else:
            st.caption("Carpeta data/geo/ sin shapefiles")
    
    # Mostrar recomendaciones
    if not all([geo_loader_available, interactive_maps_available, shapefiles_available]):
        st.warning("⚠️ **Mapas interactivos no completamente disponibles**")
        
        if not geo_loader_available or not interactive_maps_available:
            st.info("""
            **Para habilitar mapas interactivos completos:**
            1. Crea los archivos `src/visualization/geo_loader.py` e `interactive_maps.py`
            2. Copia el contenido de los artefactos proporcionados
            3. Crea el archivo `vistas/maps.py` con la vista de mapas
            """)
        
        if not shapefiles_available:
            st.info("""
            **Para usar shapefiles:**
            1. Crea la carpeta `data/geo/`
            2. Coloca tus shapefiles del Tolima (municipios y veredas)
            3. Asegúrate de que cada .shp tenga sus archivos asociados (.shx, .dbf, .prj)
            """)
    
    else:
        st.success("✅ **Sistema de mapas completamente integrado y disponible**")


# Función de compatibilidad con el sistema existente
def create_enhanced_map_view(data, column, title, map_type="choropleth"):
    """
    Función principal para crear mapas mejorados con fallback
    """
    try:
        # Intentar usar mapas interactivos si están disponibles
        from .interactive_maps import get_map_manager
        
        map_manager = get_map_manager()
        
        if map_manager.load_geodata():
            # Usar sistema avanzado
            st.success("🗺️ Usando sistema de mapas interactivos avanzado")
            
            if map_type == "choropleth":
                # Calcular cobertura por municipio
                coverage_data = map_manager.calculate_coverage_by_municipio(
                    data["vacunacion"],
                    data["metricas"],
                    "DANE"  # o usar parámetro fuente_poblacion
                )
                
                # Crear mapa interactivo
                return map_manager.create_interactive_coverage_map(
                    coverage_data,
                    nivel='municipios',
                    title=title
                )
        else:
            # Fallback al sistema original
            return create_choropleth_map(data["metricas"], column, title)
            
    except ImportError:
        # Fallback al sistema original
        st.info("ℹ️ Usando sistema de mapas estándar")
        return create_choropleth_map(data["metricas"], column, title)