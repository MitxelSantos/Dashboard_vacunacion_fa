"""
app.py - Dashboard de Vacunación Fiebre Amarilla - Tolima
Version optimizada y simplificada con mejor manejo de errores
"""

import streamlit as st
import logging
from pathlib import Path
import traceback

# Single set_page_config call
st.set_page_config(
    page_title="Dashboard Fiebre Amarilla",
    page_icon="💉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Simplified logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("dashboard.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Simplified configuration
ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Core imports
try:
    from src.data.unified_loader import load_and_combine_data
    from vistas import overview, geographic, insurance
except ImportError as e:
    st.error(f"❌ Error importando módulos: {str(e)}")
    st.error("📋 Verificar que todos los archivos estén en su lugar")
    st.stop()

COLORS = {"primary": "#7D0F2B", "secondary": "#F2A900"}


@st.cache_data(ttl=1800)  # Reduced cache time
def load_data():
    """Simplified data loading with caching and better error handling"""
    try:
        st.info("🔄 Cargando datos del sistema...")

        # Definir rutas de archivos
        resumen_path = "data/Resumen.xlsx"
        historico_path = "data/vacunacion_fa.csv"
        aseguramiento_path = "data/Poblacion_aseguramiento.xlsx"

        # Verificar que existe al menos un archivo de datos
        files_exist = []
        for path in [resumen_path, historico_path, aseguramiento_path]:
            if Path(path).exists():
                files_exist.append(path)

        if not files_exist:
            st.error("❌ No se encontraron archivos de datos en la carpeta 'data/'")
            st.info(
                """
            📋 **Archivos requeridos:**
            - `data/Resumen.xlsx` - Datos de brigadas de emergencia
            - `data/vacunacion_fa.csv` - Datos históricos de vacunación
            - `data/Poblacion_aseguramiento.xlsx` - Datos de población por EAPB
            """
            )
            return None, None, None

        # Intentar cargar los datos
        result = load_and_combine_data(
            resumen_path,
            historico_path,
            aseguramiento_path,
        )

        if result is None or len(result) != 3:
            st.error("❌ Error en la estructura de datos retornada")
            return None, None, None

        df_combined, df_aseguramiento, fecha_corte = result

        # Validar que tenemos al menos algunos datos
        if df_combined is None and df_aseguramiento is None:
            st.error("❌ No se pudieron cargar datos de ninguna fuente")
            return None, None, None

        # Información de carga exitosa
        loaded_info = []
        if df_combined is not None:
            loaded_info.append(f"Vacunación: {len(df_combined)} registros")
        if df_aseguramiento is not None:
            loaded_info.append(f"Población: {len(df_aseguramiento)} registros")

        st.success(f"✅ Datos cargados exitosamente: {', '.join(loaded_info)}")

        return df_combined, df_aseguramiento, fecha_corte

    except Exception as e:
        logger.error(f"Error crítico cargando datos: {str(e)}")
        st.error(f"❌ Error crítico cargando datos: {str(e)}")

        # Mostrar detalles técnicos en un expander
        with st.expander("🔧 Detalles técnicos del error"):
            st.code(traceback.format_exc())

        # Sugerencias de solución
        st.info(
            """
        🔧 **Posibles soluciones:**
        1. Verificar que los archivos de datos existan en la carpeta `data/`
        2. Verificar que los archivos no estén corruptos o vacíos
        3. Verificar que tengas permisos de lectura en los archivos
        4. Revisar los logs del sistema para más detalles
        """
        )

        return None, None, None


def show_file_status():
    """
    Muestra el estado de los archivos de datos
    """
    st.subheader("📁 Estado de Archivos de Datos")

    required_files = {
        "data/Resumen.xlsx": "Datos de brigadas de emergencia",
        "data/vacunacion_fa.csv": "Datos históricos de vacunación",
        "data/Poblacion_aseguramiento.xlsx": "Datos de población por EAPB",
    }

    for file_path, description in required_files.items():
        path = Path(file_path)
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            st.success(f"✅ **{description}**")
            st.caption(f"   📄 {file_path} ({size_mb:.1f} MB)")
        else:
            st.error(f"❌ **{description}**")
            st.caption(f"   📄 {file_path} - Archivo no encontrado")


def main():
    """Simplified main function with better error handling"""
    try:
        # Título principal
        st.title("🏥 Dashboard de Vacunación Fiebre Amarilla - Tolima")
        st.markdown("---")

        # Load data
        data_result = load_data()

        if data_result is None or all(x is None for x in data_result):
            st.error("❌ No se pudieron cargar los datos del sistema")

            # Mostrar estado de archivos para diagnóstico
            show_file_status()

            # Opción para mostrar datos de ejemplo
            if st.button("📊 Mostrar Dashboard con Datos de Ejemplo"):
                st.info("🔄 Cargando dashboard con datos simulados...")
                # Aquí podrías cargar datos de ejemplo para demostración
                st.warning("⚠️ Funcionalidad de datos de ejemplo no implementada aún")

            return

        df_combined, df_aseguramiento, fecha_corte = data_result

        # Verificar que tenemos datos válidos
        has_vaccination_data = df_combined is not None and len(df_combined) > 0
        has_population_data = df_aseguramiento is not None and len(df_aseguramiento) > 0

        if not has_vaccination_data and not has_population_data:
            st.error("❌ Los archivos de datos están vacíos o corruptos")
            show_file_status()
            return

        # Información de los datos cargados
        with st.expander("ℹ️ Información de Datos Cargados", expanded=False):
            col1, col2, col3 = st.columns(3)

            with col1:
                if has_vaccination_data:
                    st.metric(
                        "Registros de Vacunación",
                        f"{len(df_combined):,}".replace(",", "."),
                    )
                else:
                    st.metric("Registros de Vacunación", "No disponible")

            with col2:
                if has_population_data:
                    st.metric(
                        "Registros de Población",
                        f"{len(df_aseguramiento):,}".replace(",", "."),
                    )
                else:
                    st.metric("Registros de Población", "No disponible")

            with col3:
                if fecha_corte:
                    st.metric("Fecha de Corte", fecha_corte.strftime("%d/%m/%Y"))
                else:
                    st.metric("Fecha de Corte", "No disponible")

        # Create tabs
        tab_general, tab_geo, tab_insurance = st.tabs(
            ["📊 General", "🗺️ Geográfico", "🏥 Aseguramiento"]
        )

        with tab_general:
            try:
                if has_vaccination_data:
                    overview.show(df_combined, {}, COLORS)
                else:
                    st.warning(
                        "⚠️ No hay datos de vacunación disponibles para la vista general"
                    )
            except Exception as e:
                st.error(f"❌ Error en vista general: {str(e)}")
                logger.error(f"Error en overview: {str(e)}")

        with tab_geo:
            try:
                if has_vaccination_data:
                    geographic.show(df_combined, {}, COLORS)
                else:
                    st.warning(
                        "⚠️ No hay datos de vacunación disponibles para la vista geográfica"
                    )
            except Exception as e:
                st.error(f"❌ Error en vista geográfica: {str(e)}")
                logger.error(f"Error en geographic: {str(e)}")

        with tab_insurance:
            try:
                if has_vaccination_data and has_population_data:
                    insurance.show(df_combined, df_aseguramiento, COLORS)
                else:
                    st.warning(
                        "⚠️ Se necesitan datos de vacunación y población para la vista de aseguramiento"
                    )
            except Exception as e:
                st.error(f"❌ Error en vista de aseguramiento: {str(e)}")
                logger.error(f"Error en insurance: {str(e)}")

    except Exception as e:
        logger.error(f"Error crítico en aplicación: {str(e)}")
        st.error("❌ Error crítico en la aplicación")

        with st.expander("🔧 Detalles técnicos"):
            st.code(traceback.format_exc())

        st.info(
            """
        🔧 **Recomendaciones:**
        1. Recargar la página (F5)
        2. Verificar los archivos de datos
        3. Revisar los logs del sistema
        4. Contactar al administrador del sistema
        """
        )


if __name__ == "__main__":
    main()
