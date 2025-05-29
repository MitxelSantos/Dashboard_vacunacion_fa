"""
app.py - Dashboard de Vacunación Fiebre Amarilla - Tolima
Version optimizada y simplificada con mejor manejo de errores
"""

import streamlit as st
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, date, timedelta  # ← AGREGADO
import traceback
import os
from typing import Union, Optional, Dict, Any  # ← AGREGADO

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


@st.cache_data(ttl=1800)  # Cache por 30 minutos
def load_data():
    """
    Carga unificada de datos con manejo robusto de errores y división temporal automática

    Returns:
        tuple: (df_combined, df_aseguramiento, fecha_corte, metadata)
    """
    try:
        st.info("🔄 Iniciando carga unificada de datos...")

        # =============================================
        # PASO 1: DEFINIR RUTAS DE ARCHIVOS
        # =============================================
        # Definir rutas como STRINGS (no DataFrames)
        resumen_path = "data/Resumen.xlsx"
        historico_path = "data/vacunacion_fa.csv"
        aseguramiento_path = "data/Poblacion_aseguramiento.xlsx"

        # =============================================
        # PASO 2: VERIFICAR EXISTENCIA DE ARCHIVOS
        # =============================================
        files_status = {}
        required_files = {
            "Resumen (Brigadas)": resumen_path,
            "Histórico": historico_path,
            "Población EAPB": aseguramiento_path,
        }

        files_exist = []
        for name, path in required_files.items():
            if Path(path).exists():
                size_mb = Path(path).stat().st_size / (1024 * 1024)
                files_status[name] = f"✅ Encontrado ({size_mb:.1f} MB)"
                files_exist.append(path)
            else:
                files_status[name] = "❌ No encontrado"

        # Mostrar estado de archivos
        st.write("📁 **Estado de archivos de datos:**")
        for name, status in files_status.items():
            st.write(f"  • {name}: {status}")

        # Verificar que tenemos al menos archivos básicos
        if not files_exist:
            st.error("❌ No se encontraron archivos de datos en la carpeta 'data/'")
            st.info(
                """
            📋 **Archivos requeridos:**
            - `data/Resumen.xlsx` - Datos de brigadas de emergencia
            - `data/vacunacion_fa.csv` - Datos históricos de vacunación  
            - `data/Poblacion_aseguramiento.xlsx` - Datos de población por EAPB
            
            **Nota:** El sistema puede funcionar con archivos parciales.
            """
            )
            return None, None, None, None

        # =============================================
        # PASO 3: CARGAR DATOS CON VALIDACIÓN
        # =============================================
        try:
            # Llamar a la función de carga unificada con STRINGS
            result = load_and_combine_data(
                resumen_path,  # String - ruta a brigadas
                historico_path,  # String - ruta a históricos
                aseguramiento_path,  # String - ruta a población
            )

            if result is None:
                st.error("❌ Error en la función de carga de datos")
                return None, None, None, None

            # Verificar que tenemos 3 elementos como esperamos
            if len(result) != 3:
                st.error(
                    f"❌ Error en estructura de datos retornada: esperados 3, recibidos {len(result)}"
                )
                return None, None, None, None

        except Exception as e:
            st.error(f"❌ Error crítico llamando load_and_combine_data(): {str(e)}")
            st.error("🔧 Verifique que las rutas de archivos sean correctas")
            return None, None, None, None

        # Desempacar resultado
        df_combined, df_aseguramiento, fecha_corte = result

        # =============================================
        # PASO 4: VALIDAR DATOS CARGADOS
        # =============================================
        validation_results = []

        # Validar datos combinados de vacunación
        if df_combined is not None and len(df_combined) > 0:
            validation_results.append(
                f"✅ Datos de vacunación: {len(df_combined):,} registros".replace(
                    ",", "."
                )
            )

            # Verificar columnas esenciales
            essential_columns = ["FA UNICA", "NombreMunicipioResidencia"]
            missing_columns = [
                col for col in essential_columns if col not in df_combined.columns
            ]

            if missing_columns:
                validation_results.append(
                    f"⚠️ Columnas faltantes en vacunación: {missing_columns}"
                )
            else:
                validation_results.append(
                    "✅ Columnas esenciales de vacunación presentes"
                )

        else:
            validation_results.append("❌ No se cargaron datos de vacunación")

        # Validar datos de aseguramiento/población
        if df_aseguramiento is not None and len(df_aseguramiento) > 0:
            validation_results.append(
                f"✅ Datos de población EAPB: {len(df_aseguramiento):,} registros".replace(
                    ",", "."
                )
            )
        else:
            validation_results.append("⚠️ No se cargaron datos de población EAPB")

        # Mostrar resultados de validación
        st.write("🔍 **Validación de datos:**")
        for result in validation_results:
            st.write(f"  • {result}")

        # =============================================
        # PASO 5: CREAR METADATA CON DIVISIÓN TEMPORAL
        # =============================================
        metadata = {
            "loading_date": datetime.now(),
            "cutoff_date": fecha_corte,
            "files_loaded": files_exist,
            "total_vaccination_records": (
                len(df_combined) if df_combined is not None else 0
            ),
            "total_population_records": (
                len(df_aseguramiento) if df_aseguramiento is not None else 0
            ),
            "has_temporal_division": fecha_corte is not None,
            "system_version": "unified_v1.0",
        }

        # Información sobre división temporal
        if fecha_corte is not None:
            # Calcular estadísticas de períodos si tenemos datos de vacunación
            if df_combined is not None and "FA UNICA" in df_combined.columns:
                try:
                    # Convertir fechas para análisis
                    df_combined_temp = df_combined.copy()
                    df_combined_temp["FA UNICA"] = pd.to_datetime(
                        df_combined_temp["FA UNICA"], errors="coerce"
                    )
                    fechas_validas = df_combined_temp["FA UNICA"].dropna()

                    if len(fechas_validas) > 0:
                        # Separar por períodos
                        pre_emergency = fechas_validas[fechas_validas < fecha_corte]
                        emergency = fechas_validas[fechas_validas >= fecha_corte]

                        metadata.update(
                            {
                                "pre_emergency_count": len(pre_emergency),
                                "emergency_count": len(emergency),
                                "pre_emergency_start": (
                                    pre_emergency.min()
                                    if len(pre_emergency) > 0
                                    else None
                                ),
                                "pre_emergency_end": (
                                    pre_emergency.max()
                                    if len(pre_emergency) > 0
                                    else None
                                ),
                                "emergency_start": (
                                    emergency.min() if len(emergency) > 0 else None
                                ),
                                "emergency_end": (
                                    emergency.max() if len(emergency) > 0 else None
                                ),
                            }
                        )

                except Exception as e:
                    st.warning(f"⚠️ Error calculando estadísticas temporales: {str(e)}")

        # =============================================
        # PASO 6: MOSTRAR RESUMEN DE CARGA EXITOSA
        # =============================================
        st.success("✅ Datos cargados exitosamente")

        # Información de carga
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Registros Vacunación",
                f"{metadata['total_vaccination_records']:,}".replace(",", "."),
                delta="registros totales",
            )

        with col2:
            st.metric(
                "Registros Población",
                f"{metadata['total_population_records']:,}".replace(",", "."),
                delta="por EAPB",
            )

        with col3:
            if fecha_corte:
                st.metric(
                    "División Temporal",
                    "Activada",
                    delta=f"Corte: {fecha_corte.strftime('%d/%m/%Y')}",
                )
            else:
                st.metric("División Temporal", "No disponible")

        # Información detallada de división temporal
        if metadata["has_temporal_division"]:
            st.info(
                f"""
            📅 **División Temporal Automática:**
            
            • **Fecha de corte:** {fecha_corte.strftime('%d de %B de %Y')}
            • **Pre-emergencia:** Vacunación regular (antes del corte)
            • **Emergencia:** Brigadas territoriales (desde el corte)
            """
            )

            # Solo mostrar estadísticas si están disponibles
            if "pre_emergency_count" in metadata and "emergency_count" in metadata:
                col1, col2 = st.columns(2)

                with col1:
                    st.write("**📚 Período Pre-emergencia:**")
                    st.write(
                        f"• Registros: {metadata['pre_emergency_count']:,}".replace(
                            ",", "."
                        )
                    )
                    if metadata.get("pre_emergency_start"):
                        st.write(
                            f"• Desde: {metadata['pre_emergency_start'].strftime('%d/%m/%Y')}"
                        )
                    if metadata.get("pre_emergency_end"):
                        st.write(
                            f"• Hasta: {metadata['pre_emergency_end'].strftime('%d/%m/%Y')}"
                        )

                with col2:
                    st.write("**🚨 Período Emergencia:**")
                    st.write(
                        f"• Registros: {metadata['emergency_count']:,}".replace(
                            ",", "."
                        )
                    )
                    if metadata.get("emergency_start"):
                        st.write(
                            f"• Desde: {metadata['emergency_start'].strftime('%d/%m/%Y')}"
                        )
                    if metadata.get("emergency_end"):
                        st.write(
                            f"• Hasta: {metadata['emergency_end'].strftime('%d/%m/%Y')}"
                        )

        return df_combined, df_aseguramiento, fecha_corte, metadata

    except Exception as e:
        logger.error(f"Error crítico cargando datos: {str(e)}")
        st.error(f"❌ Error crítico cargando datos: {str(e)}")

        # Mostrar detalles técnicos en un expander
        with st.expander("🔧 Detalles técnicos del error"):
            st.code(traceback.format_exc())

        # Información de diagnóstico
        st.info(
            """
        🔧 **Pasos de diagnóstico:**
        1. Verificar que los archivos existan en la carpeta `data/`
        2. Verificar que los archivos no estén corruptos
        3. Verificar permisos de lectura en los archivos
        4. Revisar los logs del sistema para más detalles
        5. Verificar que las rutas sean strings, no objetos DataFrame
        """
        )

        return None, None, None, None


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
    """Función principal corregida para manejar 4 elementos de retorno"""
    try:
        # Título principal
        st.title("🏥 Dashboard de Vacunación Fiebre Amarilla - Tolima")
        st.markdown("---")

        # Load data - ACTUALIZADO para recibir 4 elementos
        data_result = load_data()

        if data_result is None or all(x is None for x in data_result[:3]):
            st.error("❌ No se pudieron cargar los datos del sistema")
            show_file_status()

            # Opción para mostrar datos de ejemplo
            if st.button("📊 Mostrar Dashboard con Datos de Ejemplo"):
                st.info("🔄 Cargando dashboard con datos simulados...")
                st.warning("⚠️ Funcionalidad de datos de ejemplo no implementada aún")
            return

        # Desempacar TODOS los elementos (incluye metadata)
        df_combined, df_aseguramiento, fecha_corte, metadata = data_result

        # Verificar que tenemos datos válidos
        has_vaccination_data = df_combined is not None and len(df_combined) > 0
        has_population_data = df_aseguramiento is not None and len(df_aseguramiento) > 0

        if not has_vaccination_data and not has_population_data:
            st.error("❌ Los archivos de datos están vacíos o corruptos")
            show_file_status()
            return

        # Información de los datos cargados CON METADATA
        with st.expander("ℹ️ Información de Datos Cargados", expanded=False):
            col1, col2, col3, col4 = st.columns(4)

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

            with col4:
                if metadata and "system_version" in metadata:
                    st.metric("Versión Sistema", metadata["system_version"])
                else:
                    st.metric("Versión Sistema", "No disponible")

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
