"""
src/data/brigadas_maps.py
Módulo de mapas para brigadas territoriales (versión inicial)
"""

import streamlit as st
import pandas as pd
import numpy as np
import folium
from pathlib import Path


class BrigadasMapManager:
    """
    Manejador básico de mapas para brigadas territoriales
    """
    
    def __init__(self):
        self.tolima_center = [4.43889, -75.2322]  # Centro aproximado del Tolima
        self.geo_dir = Path("data/geo")
        
    def create_base_map(self, zoom_start=8):
        """
        Crea el mapa base del Tolima
        """
        m = folium.Map(
            location=self.tolima_center,
            zoom_start=zoom_start,
            tiles='CartoDB positron'
        )
        
        return m
    
    def check_shapefiles_available(self):
        """
        Verifica si hay shapefiles disponibles
        """
        if not self.geo_dir.exists():
            return False
        
        shp_files = list(self.geo_dir.glob("*.shp"))
        return len(shp_files) > 0
    
    def list_available_shapefiles(self):
        """
        Lista los shapefiles disponibles
        """
        if not self.geo_dir.exists():
            return []
        
        shp_files = list(self.geo_dir.glob("*.shp"))
        return [shp.name for shp in shp_files]
    
    def create_simple_brigadas_map(self, brigadas_data):
        """
        Crea un mapa simple con puntos de brigadas
        (sin shapefiles por ahora)
        """
        m = self.create_base_map()
        
        if brigadas_data.empty:
            return m
        
        # Coordenadas aproximadas de algunos municipios del Tolima
        # (Esta es una tabla de referencia básica)
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
            'CAJAMARCA': [4.3189, -75.4319],
            'ROVIRA': [4.2359, -75.2379],
            'SALDAÑA': [3.9269, -75.0159],
            'GUAMO': [4.0269, -74.9679],
            'FLANDES': [4.2909, -74.8139],
        }
        
        # Agregar marcadores para cada brigada
        for _, brigada in brigadas_data.iterrows():
            municipio = brigada['MUNICIPIO'].upper().strip()
            
            # Buscar coordenadas del municipio
            coords = municipios_coords.get(municipio)
            
            if coords:
                lat, lon = coords
                
                # Determinar color basado en efectividad
                efectividad = brigada.get('tasa_efectividad', 0)
                if efectividad >= 80:
                    color = 'green'
                elif efectividad >= 60:
                    color = 'orange'
                else:
                    color = 'red'
                
                # Crear popup con información
                popup_text = f"""
                <b>{brigada['MUNICIPIO']}</b><br>
                <b>Fecha:</b> {brigada['FECHA'].strftime('%d/%m/%Y') if pd.notna(brigada['FECHA']) else 'N/A'}<br>
                <b>Veredas:</b> {brigada['VEREDAS']}<br>
                <b>Efectividad:</b> {efectividad:.1f}%<br>
                <b>Población encontrada:</b> {int(brigada['TPE'])}<br>
                <b>Vacunados:</b> {int(brigada['TPVB'])}
                """
                
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_text, max_width=300),
                    tooltip=f"{brigada['MUNICIPIO']} - {efectividad:.1f}%",
                    icon=folium.Icon(color=color)
                ).add_to(m)
        
        # Añadir leyenda
        legend_html = """
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 200px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:12px; padding: 10px">
        <p><b>Efectividad de Brigadas</b></p>
        <p><i class="fa fa-circle" style="color:green"></i> Alta (≥80%)</p>
        <p><i class="fa fa-circle" style="color:orange"></i> Media (60-79%)</p>
        <p><i class="fa fa-circle" style="color:red"></i> Baja (<60%)</p>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))
        
        return m
    
    def show_map_interface(self, brigadas_data):
        """
        Interface para mostrar mapas en Streamlit
        """
        st.subheader("🗺️ Mapa de Brigadas Territoriales")
        
        # Verificar disponibilidad de shapefiles
        shapefiles_available = self.check_shapefiles_available()
        
        if shapefiles_available:
            available_files = self.list_available_shapefiles()
            st.info(f"📁 Shapefiles encontrados: {', '.join(available_files)}")
            st.warning("🚧 Integración con shapefiles en desarrollo")
        else:
            st.info("💡 Para mapas detallados, coloca los shapefiles en data/geo/")
        
        # Crear mapa simple
        if not brigadas_data.empty:
            try:
                mapa = self.create_simple_brigadas_map(brigadas_data)
                
                # Mostrar el mapa usando st.components.v1.html como alternativa
                # si streamlit-folium no está disponible
                try:
                    from streamlit_folium import folium_static
                    folium_static(mapa, width=1200, height=600)
                except ImportError:
                    st.warning("⚠️ streamlit-folium no disponible")
                    # Mostrar mapa como HTML embebido
                    map_html = mapa._repr_html_()
                    st.components.v1.html(map_html, height=600)
                
            except Exception as e:
                st.error(f"❌ Error creando mapa: {str(e)}")
                st.info("💡 Mostrando tabla de ubicaciones en su lugar")
                
                # Mostrar tabla como alternativa
                self.show_locations_table(brigadas_data)
        else:
            st.warning("⚠️ No hay datos de brigadas para mostrar en el mapa")
    
    def show_locations_table(self, brigadas_data):
        """
        Muestra tabla de ubicaciones como alternativa al mapa
        """
        if brigadas_data.empty:
            return
        
        # Crear resumen por municipio
        municipio_stats = brigadas_data.groupby('MUNICIPIO').agg({
            'tasa_efectividad': 'mean',
            'TPE': 'sum',
            'TPVB': 'sum',
            'FECHA': 'count'
        }).round(2).reset_index()
        
        municipio_stats.columns = [
            'Municipio', 'Efectividad Promedio (%)', 
            'Población Total', 'Total Vacunados', 'Número de Brigadas'
        ]
        
        st.dataframe(
            municipio_stats.style.format({
                'Efectividad Promedio (%)': '{:.1f}%'
            }),
            use_container_width=True
        )


def create_brigadas_map_section(brigadas_data):
    """
    Función principal para crear la sección de mapas
    """
    map_manager = BrigadasMapManager()
    map_manager.show_map_interface(brigadas_data)


def check_mapping_requirements():
    """
    Verifica los requisitos para mapas
    """
    requirements = {
        'folium': False,
        'streamlit_folium': False,
        'geopandas': False,
        'shapefiles': False
    }
    
    try:
        import folium
        requirements['folium'] = True
    except ImportError:
        pass
    
    try:
        from streamlit_folium import folium_static
        requirements['streamlit_folium'] = True
    except ImportError:
        pass
    
    try:
        import geopandas
        requirements['geopandas'] = True
    except ImportError:
        pass
    
    # Verificar shapefiles
    geo_dir = Path("data/geo")
    if geo_dir.exists():
        shp_files = list(geo_dir.glob("*.shp"))
        requirements['shapefiles'] = len(shp_files) > 0
    
    return requirements


def show_mapping_status():
    """
    Muestra el estado de los requisitos para mapas
    """
    st.subheader("🔧 Estado de Requisitos para Mapas")
    
    requirements = check_mapping_requirements()
    
    st.write("**Librerías:**")
    for lib, available in requirements.items():
        if lib != 'shapefiles':
            status = "✅" if available else "❌"
            st.write(f"{status} {lib}")
    
    st.write("**Archivos:**")
    status = "✅" if requirements['shapefiles'] else "❌"
    st.write(f"{status} Shapefiles en data/geo/")
    
    if not all(requirements.values()):
        st.info("""
        💡 **Para habilitar mapas completos:**
        - Instalar: pip install folium streamlit-folium geopandas
        - Colocar archivos .shp en data/geo/
        """)


if __name__ == "__main__":
    # Para probar el módulo
    st.title("Prueba del Módulo de Mapas")
    show_mapping_status()