import streamlit as st
import pandas as pd
import os
from pathlib import Path

# Definir rutas
ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
ASSETS_DIR = ROOT_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"

# Asegurar que las carpetas existan
DATA_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)

# Agregar rutas al path para importar módulos
import sys
sys.path.insert(0, str(ROOT_DIR))

from src.data.loader import load_datasets
from src.utils.helpers import configure_page
from pages import overview, geographic, demographic, insurance, trends

# Configuración de la página
configure_page(
    page_title="Dashboard Vacunación Fiebre Amarilla - Tolima",
    page_icon="💉",
    layout="wide"
)

# Colores institucionales
COLORS = {
    "primary": "#7D0F2B",      # Vinotinto
    "secondary": "#CFB53B",    # Dorado/Oro
    "accent": "#215E8F",       # Azul complementario
    "background": "#F5F5F5",   # Fondo gris claro
}

def main():
    """Aplicación principal del dashboard."""
    
    # Cargar datos
    try:
        with st.spinner("Cargando datos..."):
            data = load_datasets()
    except FileNotFoundError as e:
        st.error(f"Error al cargar datos: {str(e)}")
        st.info("Por favor, asegúrate de que los archivos de datos estén en la carpeta correcta.")
        return
        
    # Barra lateral con logo y filtros
    with st.sidebar:
        # Logo de la Gobernación
        logo_path = IMAGES_DIR / "logo_gobernacion.png"
        if logo_path.exists():
            st.image(
                str(logo_path), 
                width=150,
                caption="Secretaría de Salud del Tolima"
            )
        else:
            st.warning("Logo no encontrado. Coloca el logo en assets/images/logo_gobernacion.png")
        
        st.title("Dashboard Vacunación")
        st.subheader("Fiebre Amarilla")
        
        # Selector de fuente de datos de población
        st.subheader("Fuente de datos")
        fuente_poblacion = st.radio(
            "Seleccione la fuente de datos de población:",
            options=["DANE", "SISBEN"],
            help="DANE: Población según censo oficial | SISBEN: Población registrada en el SISBEN"
        )
        
        # Guardar la fuente seleccionada en el estado de la sesión
        if "fuente_poblacion" not in st.session_state or st.session_state.fuente_poblacion != fuente_poblacion:
            st.session_state.fuente_poblacion = fuente_poblacion
        
        # Filtros globales
        st.subheader("Filtros")
        
        municipio = st.selectbox(
            "Municipio", 
            options=["Todos"] + sorted(data["municipios"]["DPMP"].unique().tolist())
        )
        
        # Obtener valores únicos de la columna Grupo_Edad
        grupos_edad = data["vacunacion"]["Grupo_Edad"].unique().tolist()
        grupo_edad = st.selectbox(
            "Grupo de Edad",
            options=["Todos"] + sorted(grupos_edad)
        )
        
        # Obtener valores únicos para el resto de filtros
        sexos = data["vacunacion"]["Sexo"].unique().tolist()
        grupos_etnicos = data["vacunacion"]["GrupoEtnico"].unique().tolist()
        regimenes = data["vacunacion"]["RegimenAfiliacion"].unique().tolist()
        aseguradoras = data["vacunacion"]["NombreAseguradora"].unique().tolist()
        
        sexo = st.selectbox(
            "Sexo",
            options=["Todos"] + sorted(sexos)
        )
        
        grupo_etnico = st.selectbox(
            "Grupo Étnico",
            options=["Todos"] + sorted(grupos_etnicos)
        )
        
        regimen = st.selectbox(
            "Régimen",
            options=["Todos"] + sorted(regimenes)
        )
        
        aseguradora = st.selectbox(
            "Aseguradora",
            options=["Todos"] + sorted(aseguradoras)
        )
        
        # Botón para aplicar filtros
        if st.button("Aplicar Filtros", type="primary"):
            st.session_state.filters = {
                "municipio": municipio,
                "grupo_edad": grupo_edad,
                "sexo": sexo,
                "grupo_etnico": grupo_etnico,
                "regimen": regimen,
                "aseguradora": aseguradora
            }
        
        # Botón para resetear filtros
        if st.button("Restablecer Filtros"):
            st.session_state.filters = {
                "municipio": "Todos",
                "grupo_edad": "Todos",
                "sexo": "Todos",
                "grupo_etnico": "Todos",
                "regimen": "Todos",
                "aseguradora": "Todos"
            }
        
        # Información del desarrollador
        st.sidebar.markdown("---")
        st.sidebar.caption("Desarrollado por: Ing. José Miguel Santos")
        st.sidebar.caption("Secretaría de Salud del Tolima © 2025")
    
    # Inicializar filtros si no existen
    if "filters" not in st.session_state:
        st.session_state.filters = {
            "municipio": "Todos",
            "grupo_edad": "Todos",
            "sexo": "Todos",
            "grupo_etnico": "Todos",
            "regimen": "Todos",
            "aseguradora": "Todos"
        }
    
    # Inicializar fuente de población si no existe
    if "fuente_poblacion" not in st.session_state:
        st.session_state.fuente_poblacion = "DANE"
    
    # Agregar banner que muestra la fuente de datos seleccionada
    st.info(f"Análisis basado en datos de población {st.session_state.fuente_poblacion}")
    
    # Pestañas de navegación
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Visión General", 
        "Distribución Geográfica", 
        "Perfil Demográfico",
        "Aseguramiento",
        "Tendencias"
    ])
    
    # Contenido de cada pestaña
    with tab1:
        overview.show(data, st.session_state.filters, COLORS, st.session_state.fuente_poblacion)
    
    with tab2:
        geographic.show(data, st.session_state.filters, COLORS, st.session_state.fuente_poblacion)
    
    with tab3:
        demographic.show(data, st.session_state.filters, COLORS, st.session_state.fuente_poblacion)
    
    with tab4:
        insurance.show(data, st.session_state.filters, COLORS, st.session_state.fuente_poblacion)
    
    with tab5:
        trends.show(data, st.session_state.filters, COLORS, st.session_state.fuente_poblacion)

if __name__ == "__main__":
    main()