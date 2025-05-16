import os

# Deshabilitar detección automática de páginas de Streamlit
os.environ["STREAMLIT_PAGES_ENABLED"] = "false"

import streamlit as st
import pandas as pd
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

from vistas import overview, geographic, demographic, insurance, trends
from src.data.loader import load_datasets
from src.utils.helpers import configure_page

# Configuración de la página
configure_page(
    page_title="Dashboard Vacunación Fiebre Amarilla - Tolima",
    page_icon="💉",
    layout="wide",
)

# Panel de diagnóstico visible
st.sidebar.markdown("## Diagnóstico")
show_debug = st.sidebar.checkbox("Mostrar diagnóstico", value=True)

if show_debug:
    debug_container = st.expander("Información de diagnóstico", expanded=True)
    with debug_container:
        st.write("### Verificación de directorios")
        st.write(f"Directorio raíz: {ROOT_DIR} (Existe: {ROOT_DIR.exists()})")
        st.write(f"Directorio de datos: {DATA_DIR} (Existe: {DATA_DIR.exists()})")
        st.write(f"Directorio de assets: {ASSETS_DIR} (Existe: {ASSETS_DIR.exists()})")
        st.write(
            f"Directorio de imágenes: {IMAGES_DIR} (Existe: {IMAGES_DIR.exists()})"
        )

        st.write("### Secretos configurados")
        if "google_drive" in st.secrets:
            st.write("✅ Configuración de Google Drive encontrada")
            st.json(st.secrets["google_drive"])
        else:
            st.error("❌ Configuración de Google Drive NO encontrada")

        if "gcp_service_account" in st.secrets:
            st.write("✅ Cuenta de servicio GCP encontrada")
            # Mostrar parte de la info sin exponer datos sensibles
            safe_info = {
                "type": st.secrets["gcp_service_account"].get("type"),
                "project_id": st.secrets["gcp_service_account"].get("project_id"),
                "client_email": st.secrets["gcp_service_account"].get("client_email"),
            }
            st.json(safe_info)
        else:
            st.error("❌ Cuenta de servicio GCP NO encontrada")

        # Información sobre archivos de datos
        st.write("### Archivos en el directorio de datos")
        if DATA_DIR.exists():
            files = list(DATA_DIR.glob("*"))
            if files:
                for file in files:
                    st.write(f"- {file.name} ({file.stat().st_size} bytes)")
            else:
                st.warning("⚠️ No hay archivos en el directorio de datos")
        else:
            st.error("❌ El directorio de datos no existe")

# Colores institucionales según la Secretaría de Salud del Tolima
COLORS = {
    "primary": "#7D0F2B",  # Vinotinto
    "secondary": "#F2A900",  # Amarillo dorado
    "accent": "#5A4214",  # Marrón dorado oscuro
    "background": "#F5F5F5",  # Fondo gris claro
    "success": "#509E2F",  # Verde
    "warning": "#F7941D",  # Naranja
    "danger": "#E51937",  # Rojo brillante
}


# Función auxiliar para limpiar listas con posibles valores NaN
def clean_list(lista):
    return [str(item) for item in lista if not pd.isna(item)]


def main():
    """Aplicación principal del dashboard."""

    # Cargar datos
    try:
        with st.spinner("Cargando datos..."):
            data = load_datasets()

            # Intentar encontrar la columna más parecida a "Grupo_Edad"
            grupo_edad_col = None
            for col in data["vacunacion"].columns:
                if "grupo" in col.lower() and "edad" in col.lower():
                    grupo_edad_col = col
                    break

            # Si no se encuentra ninguna columna similar, crear una
            if grupo_edad_col is None:
                st.warning(
                    "No se encontró columna de grupo de edad. Creando una temporal."
                )
                if "Edad_Vacunacion" in data["vacunacion"].columns:
                    # Crear grupo de edad a partir de edad
                    data["vacunacion"]["Grupo_Edad"] = data["vacunacion"][
                        "Edad_Vacunacion"
                    ].apply(
                        lambda x: (
                            "0-4"
                            if pd.notna(x) and x < 5
                            else (
                                "5-14"
                                if pd.notna(x) and x < 15
                                else (
                                    "15-19"
                                    if pd.notna(x) and x < 20
                                    else (
                                        "20-29"
                                        if pd.notna(x) and x < 30
                                        else (
                                            "30-39"
                                            if pd.notna(x) and x < 40
                                            else (
                                                "40-49"
                                                if pd.notna(x) and x < 50
                                                else (
                                                    "50-59"
                                                    if pd.notna(x) and x < 60
                                                    else (
                                                        "60-69"
                                                        if pd.notna(x) and x < 70
                                                        else (
                                                            "70-79"
                                                            if pd.notna(x) and x < 80
                                                            else (
                                                                "80+"
                                                                if pd.notna(x)
                                                                and x >= 80
                                                                else "Sin especificar"
                                                            )
                                                        )
                                                    )
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                    grupo_edad_col = "Grupo_Edad"
                else:
                    # Si no hay campo de edad, crear una columna con valor único
                    data["vacunacion"]["Grupo_Edad"] = "Sin especificar"
                    grupo_edad_col = "Grupo_Edad"
    except FileNotFoundError as e:
        st.error(f"Error al cargar datos: {str(e)}")
        st.info(
            "Por favor, asegúrate de que los archivos de datos estén en la carpeta correcta."
        )
        return

    # Barra lateral con logo y filtros
    with st.sidebar:
        # Logo de la Gobernación
        logo_path = IMAGES_DIR / "logo_gobernacion.png"
        if logo_path.exists():
            st.image(
                str(logo_path), width=150, caption="Secretaría de Salud del Tolima"
            )
        else:
            st.warning(
                "Logo no encontrado. Coloca el logo en assets/images/logo_gobernacion.png"
            )

        st.title("Dashboard Vacunación")
        st.subheader("Fiebre Amarilla")

        # Selector de fuente de datos de población
        st.subheader("Fuente de datos")

        def on_fuente_change():
            st.session_state.fuente_poblacion = st.session_state.fuente_radio

        fuente_poblacion = st.radio(
            "Seleccione la fuente de datos de población:",
            options=["DANE", "SISBEN"],
            key="fuente_radio",
            on_change=on_fuente_change,
            help="DANE: Población según censo oficial | SISBEN: Población registrada en el SISBEN",
        )

        # Inicializar la fuente seleccionada si no existe
        if "fuente_poblacion" not in st.session_state:
            st.session_state.fuente_poblacion = fuente_poblacion

        # Filtros globales
        st.subheader("Filtros")

        # Función para aplicar filtros automáticamente
        def on_filter_change():
            st.session_state.filters = {
                "municipio": st.session_state.municipio_filter,
                "grupo_edad": st.session_state.grupo_edad_filter,
                "sexo": st.session_state.sexo_filter,
                "grupo_etnico": st.session_state.grupo_etnico_filter,
                "regimen": st.session_state.regimen_filter,
                "aseguradora": st.session_state.aseguradora_filter,
            }

        # Limpiar municipios antes de ordenarlos
        municipios = clean_list(data["municipios"]["DPMP"].unique().tolist())
        municipio = st.selectbox(
            "Municipio",
            options=["Todos"] + sorted(municipios),
            key="municipio_filter",
            on_change=on_filter_change,
        )

        # Obtener valores únicos de la columna Grupo_Edad y limpiarlos
        try:
            grupos_edad = clean_list(data["vacunacion"]["Grupo_Edad"].unique().tolist())
        except KeyError:
            # Mostrar las columnas disponibles para diagnóstico
            st.error(
                f"Error: La columna 'Grupo_Edad' no existe. Columnas disponibles: {data['vacunacion'].columns.tolist()}"
            )
            # Usar un valor predeterminado
            grupos_edad = ["Sin especificar"]
        grupo_edad = st.selectbox(
            "Grupo de Edad",
            options=["Todos"] + sorted(grupos_edad),
            key="grupo_edad_filter",
            on_change=on_filter_change,
        )

        # Obtener valores únicos para el resto de filtros y limpiarlos
        sexos = clean_list(data["vacunacion"]["Sexo"].unique().tolist())
        sexo = st.selectbox(
            "Sexo",
            options=["Todos"] + sorted(sexos),
            key="sexo_filter",
            on_change=on_filter_change,
        )

        grupos_etnicos = clean_list(data["vacunacion"]["GrupoEtnico"].unique().tolist())
        grupo_etnico = st.selectbox(
            "Grupo Étnico",
            options=["Todos"] + sorted(grupos_etnicos),
            key="grupo_etnico_filter",
            on_change=on_filter_change,
        )

        regimenes = clean_list(
            data["vacunacion"]["RegimenAfiliacion"].unique().tolist()
        )
        regimen = st.selectbox(
            "Régimen",
            options=["Todos"] + sorted(regimenes),
            key="regimen_filter",
            on_change=on_filter_change,
        )

        aseguradoras = clean_list(
            data["vacunacion"]["NombreAseguradora"].unique().tolist()
        )
        aseguradora = st.selectbox(
            "Aseguradora",
            options=["Todos"] + sorted(aseguradoras),
            key="aseguradora_filter",
            on_change=on_filter_change,
        )

        # Función para resetear todos los filtros
        def reset_filters():
            # Usar las claves para reiniciar todos los filtros
            for key in [
                "municipio_filter",
                "grupo_edad_filter",
                "sexo_filter",
                "grupo_etnico_filter",
                "regimen_filter",
                "aseguradora_filter",
            ]:
                # Esta es la forma correcta de resetear, usando .update()
                st.session_state.update({key: "Todos"})

            # Actualizar filtros después del reset
            on_filter_change()

        # Botón para resetear filtros
        if st.button("Restablecer Filtros", on_click=reset_filters):
            pass  # La lógica está en reset_filters

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
            "aseguradora": "Todos",
        }

    # Banner principal y logos
    col1, col2 = st.columns([3, 1])

    with col1:
        st.title("Dashboard Vacunación Fiebre Amarilla - Tolima")
        st.write("Secretaría de Salud del Tolima - Vigilancia Epidemiológica")

    # Mostrar filtros activos en un banner con fondo vinotinto (banner global)
    active_filters = [
        f"{k.capitalize()}: {v}"
        for k, v in st.session_state.filters.items()
        if v != "Todos"
    ]
    if active_filters:
        st.markdown(
            f"""
            <div style="background-color: {COLORS['primary']}; color: white; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
                <strong>Filtros aplicados:</strong> {', '.join(active_filters)}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Pestañas de navegación
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Visión General",
            "Distribución Geográfica",
            "Perfil Demográfico",
            "Aseguramiento",
            "Tendencias",
        ]
    )

    # Contenido de cada pestaña
    with tab1:
        overview.show(
            data, st.session_state.filters, COLORS, st.session_state.fuente_poblacion
        )

    with tab2:
        geographic.show(
            data, st.session_state.filters, COLORS, st.session_state.fuente_poblacion
        )

    with tab3:
        demographic.show(
            data, st.session_state.filters, COLORS, st.session_state.fuente_poblacion
        )

    with tab4:
        insurance.show(
            data, st.session_state.filters, COLORS, st.session_state.fuente_poblacion
        )

    with tab5:
        trends.show(
            data, st.session_state.filters, COLORS, st.session_state.fuente_poblacion
        )


if __name__ == "__main__":
    main()
