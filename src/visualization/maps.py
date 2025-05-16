import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
import plotly.express as px
import geopandas as gpd
from pathlib import Path

# Ruta base para archivos geográficos
ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"
GEO_DIR = ASSETS_DIR / "geo"

def load_tolima_geojson():
    """
    Carga el GeoJSON del departamento del Tolima con sus municipios.
    Si no existe, muestra un mensaje de error.
    
    Returns:
        gpd.GeoDataFrame o None: GeoDataFrame con los municipios del Tolima
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
        colóquelo en la carpeta assets/geo/ con el nombre tolima_municipios.geojson
        """)
        return None

def create_choropleth_map(data, column, title, color_scale="YlOrRd", legend_name=None):
    """
    Crea un mapa coroplético del Tolima coloreado según el valor de una columna.
    
    Args:
        data (pd.DataFrame): DataFrame con los datos de municipios
        column (str): Nombre de la columna con los valores a mapear
        title (str): Título del mapa
        color_scale (str): Escala de colores para el mapa
        legend_name (str): Nombre de la leyenda
        
    Returns:
        folium.Map: Mapa de Folium
    """
    # Cargar GeoJSON
    geo_data = load_tolima_geojson()
    
    if geo_data is None:
        return None
    
    # Verificar que exista la columna correspondiente al nombre del municipio
    if "DPMP" not in data.columns:
        st.error("El DataFrame no contiene la columna 'DPMP' necesaria para el mapa")
        return None
    
    # Verificar que exista la columna con los valores
    if column not in data.columns:
        st.error(f"El DataFrame no contiene la columna '{column}' necesaria para el mapa")
        return None
    
    # Verificar que exista la columna con el nombre del municipio en el GeoJSON
    if "MPIO_CNMBR" not in geo_data.columns:
        st.error("El archivo GeoJSON no contiene la columna 'MPIO_CNMBR' necesaria para el mapa")
        return None
    
    # Crear mapa base centrado en el Tolima
    m = folium.Map(location=[4.43889, -75.2322], zoom_start=8)
    
    # Fusionar datos con geometría
    merged_data = pd.merge(
        geo_data,
        data,
        left_on="MPIO_CNMBR",
        right_on="DPMP",
        how="left"
    )
    
    # Verificar que haya datos fusionados
    if merged_data[column].isna().all():
        st.warning("No se pudieron fusionar los datos con el GeoJSON. Verifique que los nombres de municipios coincidan")
        return None
    
    # Crear coroplético
    legend_name = legend_name or column
    
    choropleth = folium.Choropleth(
        geo_data=merged_data.__geo_interface__,
        name=title,
        data=data,
        columns=["DPMP", column],
        key_on="feature.properties.MPIO_CNMBR",
        fill_color=color_scale,
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=legend_name
    ).add_to(m)
    
    # Añadir tooltips
    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(
            fields=["MPIO_CNMBR", column],
            aliases=["Municipio:", f"{legend_name}:"],
            style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
        )
    )
    
    # Añadir título
    title_html = f'''
        <div style="position: fixed; 
                    top: 10px; left: 50px; width: 250px; height: 40px; 
                    background-color: white; border:2px solid grey; z-index:9999; font-size:14px;
                    font-family: arial; padding: 10px;
                    border-radius: 5px;
                    ">
             <b>{title}</b>
        </div>
        '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    return m

def create_bubble_map(data, location_col, size_col, color_col=None, title="", hover_data=None):
    """
    Crea un mapa de burbujas del Tolima usando Plotly Express.
    
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
        return None
    
    # Verificar que existan las columnas necesarias
    if location_col not in data.columns:
        st.error(f"El DataFrame no contiene la columna '{location_col}' necesaria para el mapa")
        return None
    
    if size_col not in data.columns:
        st.error(f"El DataFrame no contiene la columna '{size_col}' necesaria para el mapa")
        return None
    
    if color_col and color_col not in data.columns:
        st.error(f"El DataFrame no contiene la columna '{color_col}' necesaria para el mapa")
        return None
    
    # Fusionar datos con geometría para obtener centroides
    merged_data = pd.merge(
        geo_data,
        data,
        left_on="MPIO_CNMBR",
        right_on=location_col,
        how="right"
    )
    
    # Calcular centroides para ubicar las burbujas
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