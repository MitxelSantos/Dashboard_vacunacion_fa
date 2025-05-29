"""
app.py - Dashboard de Vacunación Fiebre Amarilla - Tolima
VERSIÓN UNIFICADA COMPLETA con sistema integrado de datos y división temporal automática

Desarrollado para la Secretaría de Salud del Tolima
Autor: Ing. José Miguel Santos
Versión: 3.0.0 - Sistema Unificado Completo
"""

import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import traceback
import warnings
from datetime import datetime
import logging

# Suprimir warnings innecesarios
warnings.filterwarnings("ignore")

# Configuración de rutas
ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
SRC_DIR = ROOT_DIR / "src"

# Asegurar que las carpetas existan
DATA_DIR.mkdir(exist_ok=True)
(ROOT_DIR / "assets" / "images").mkdir(parents=True, exist_ok=True)

# Agregar rutas al path para importar módulos
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(SRC_DIR))

# =====================================================================
# CONFIGURACIÓN DE LOGGING
# =====================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("dashboard.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# =====================================================================
# IMPORTACIÓN DE COMPONENTES DEL SISTEMA UNIFICADO
# =====================================================================
SYSTEM_COMPONENTS_LOADED = False
COMPONENT_ERRORS = []

try:
    # Componentes principales del sistema unificado
    from src.data.unified_loader import UnifiedDataLoader
    from src.data.population_processor import PopulationEAPBProcessor
    from src.data.vaccination_combiner import VaccinationCombiner
    from src.data.age_calculator import AgeCalculator
    from src.data.data_cleaner import UnifiedDataCleaner

    # Utilidades
    from src.utils.date_utils import date_utils, format_date, get_vaccination_summary
    from src.utils.helpers import (
        dashboard_helpers,
        configure_page,
        format_number,
        get_colors,
        create_alert,
        create_metric,
        validate_data,
    )

    SYSTEM_COMPONENTS_LOADED = True
    logger.info("✅ Componentes del sistema unificado cargados exitosamente")

except ImportError as e:
    error_msg = f"Error importando componentes del sistema: {str(e)}"
    COMPONENT_ERRORS.append(error_msg)
    logger.error(error_msg)
    SYSTEM_COMPONENTS_LOADED = False

# =====================================================================
# IMPORTACIÓN DE VISTAS CON MANEJO DE ERRORES
# =====================================================================
AVAILABLE_VIEWS = {}
view_modules = [
    "overview",
    "geographic",
    "demographic",
    "insurance",
    "trends",
    "brigadas",
]

for view_name in view_modules:
    try:
        module = __import__(f"vistas.{view_name}", fromlist=[view_name])
        AVAILABLE_VIEWS[view_name] = module
        logger.info(f"✅ Vista {view_name} cargada exitosamente")
    except ImportError as e:
        error_msg = f"Vista {view_name} no disponible: {str(e)}"
        logger.warning(error_msg)
        AVAILABLE_VIEWS[view_name] = None

# =====================================================================
# CONFIGURACIÓN INSTITUCIONAL
# =====================================================================
INSTITUTIONAL_CONFIG = {
    "title": "Dashboard Vacunación Fiebre Amarilla - Tolima",
    "subtitle": "Secretaría de Salud del Tolima - Vigilancia Epidemiológica",
    "version": "3.0.0 - Sistema Unificado Completo",
    "author": "Ing. José Miguel Santos",
    "institution": "Secretaría de Salud del Tolima",
    "year": "2025",
    "description": "Sistema integral de análisis de vacunación con división temporal automática",
    "features": [
        "Población de referencia por EAPB (Abril 2025)",
        "División temporal automática (Pre-emergencia vs Emergencia)",
        "Cálculo de edades actuales (no momento vacunación)",
        "Limpieza unificada de datos",
        "Fecha de corte automática basada en brigadas",
    ],
}


# =====================================================================
# CLASE PRINCIPAL DE LA APLICACIÓN UNIFICADA
# =====================================================================
class UnifiedDashboardApp:
    """
    Aplicación principal del dashboard con sistema completamente unificado
    """

    def __init__(self):
        self.data_loader = None
        self.unified_data = None
        self.processing_metadata = {}
        self.colors = (
            get_colors() if SYSTEM_COMPONENTS_LOADED else self._get_default_colors()
        )
        self.current_date_info = None

        # Estado de la aplicación
        self.app_state = {
            "data_loaded": False,
            "loading_errors": [],
            "cutoff_date": None,
            "last_update": None,
            "total_records": 0,
            "system_version": INSTITUTIONAL_CONFIG["version"],
            "components_loaded": SYSTEM_COMPONENTS_LOADED,
            "available_views": len(
                [v for v in AVAILABLE_VIEWS.values() if v is not None]
            ),
        }

        logger.info("🚀 Aplicación UnifiedDashboardApp inicializada")

    def _get_default_colors(self):
        """Colores por defecto si no se cargan las utilidades"""
        return {
            "primary": "#7D0F2B",
            "secondary": "#F2A900",
            "accent": "#5A4214",
            "success": "#509E2F",
            "warning": "#F7941D",
            "danger": "#E51937",
        }

    def initialize_app(self):
        """
        Inicializa la aplicación con configuración institucional completa
        """
        logger.info("🔧 Inicializando aplicación unificada")

        # Configurar página
        if SYSTEM_COMPONENTS_LOADED:
            configure_page(INSTITUTIONAL_CONFIG["title"], "💉", "wide")
        else:
            st.set_page_config(
                page_title=INSTITUTIONAL_CONFIG["title"], page_icon="💉", layout="wide"
            )

        # Información de fecha actual
        if SYSTEM_COMPONENTS_LOADED:
            self.current_date_info = date_utils.get_current_date_info()

        # Mostrar estado del sistema si hay errores
        if not SYSTEM_COMPONENTS_LOADED or COMPONENT_ERRORS:
            self._show_system_status()

    def _show_system_status(self):
        """
        Muestra el estado del sistema y errores si los hay
        """
        with st.sidebar:
            st.markdown("---")
            st.subheader("🔧 Estado del Sistema")

            if COMPONENT_ERRORS:
                st.error("❌ Errores de componentes:")
                for error in COMPONENT_ERRORS:
                    st.write(f"• {error}")

            st.info(
                f"""
            **Estado actual:**
            - Componentes: {'✅' if SYSTEM_COMPONENTS_LOADED else '❌'}
            - Vistas: {self.app_state['available_views']}/6 disponibles
            """
            )

    def load_unified_data(self):
        """
        Carga datos usando el sistema completamente unificado
        """
        if not SYSTEM_COMPONENTS_LOADED:
            st.error("❌ Sistema de componentes no disponible")
            st.info(
                "🔄 Funcionalidad limitada - algunos componentes no se cargaron correctamente"
            )
            return False

        logger.info("🔄 Iniciando carga del sistema unificado")

        with st.spinner("🔄 Cargando sistema unificado..."):
            try:
                # ============================================================
                # PASO 1: Cargar y procesar población por EAPB
                # ============================================================
                with st.status(
                    "📊 **PASO 1:** Procesando población por EAPB...", expanded=True
                ) as status:
                    st.write("Cargando Poblacion_aseguramiento.xlsx...")

                    population_processor = PopulationEAPBProcessor(str(DATA_DIR))
                    population_data = population_processor.load_population_data()

                    if population_data is None:
                        st.error("❌ No se pudo cargar población por EAPB")
                        status.update(label="❌ Error en población EAPB", state="error")
                        return False

                    st.success(
                        f"✅ Población EAPB procesada: {len(population_data)} registros"
                    )
                    status.update(label="✅ Población EAPB cargada", state="complete")

                # ============================================================
                # PASO 2: Combinar datos de vacunación con fecha de corte automática
                # ============================================================
                with st.status(
                    "🔗 **PASO 2:** Combinando datos de vacunación...", expanded=True
                ) as status:
                    st.write("Determinando fecha de corte automática...")

                    combiner = VaccinationCombiner(str(DATA_DIR))
                    combined_vaccination = combiner.load_and_combine_data()

                    if combined_vaccination is None:
                        st.error("❌ No se pudo combinar datos de vacunación")
                        status.update(label="❌ Error en combinación", state="error")
                        return False

                    cutoff_date = combiner.cutoff_date
                    st.success(
                        f"✅ Datos combinados: {len(combined_vaccination)} registros"
                    )
                    st.info(f"📅 Fecha de corte: {format_date(cutoff_date, 'full')}")
                    status.update(
                        label="✅ Datos de vacunación combinados", state="complete"
                    )

                # ============================================================
                # PASO 3: Calcular edades actuales
                # ============================================================
                with st.status(
                    "🎂 **PASO 3:** Calculando edades actuales...", expanded=True
                ) as status:
                    st.write("Procesando fechas de nacimiento...")

                    if "fecha_nacimiento" in combined_vaccination.columns:
                        age_calculator = AgeCalculator()
                        combined_vaccination = (
                            age_calculator.calculate_ages_for_dataframe(
                                combined_vaccination,
                                birth_date_column="fecha_nacimiento",
                                target_age_column="edad_actual",
                                target_group_column="grupo_edad_actual",
                            )
                        )
                        st.success("✅ Edades actuales calculadas")
                    else:
                        st.warning("⚠️ Columna de fecha de nacimiento no encontrada")

                    status.update(
                        label="✅ Edades actuales procesadas", state="complete"
                    )

                # ============================================================
                # PASO 4: Aplicar limpieza unificada
                # ============================================================
                with st.status(
                    "🧹 **PASO 4:** Aplicando limpieza unificada...", expanded=True
                ) as status:
                    st.write("Normalizando y limpiando datos...")

                    cleaner = UnifiedDataCleaner()
                    clean_data = cleaner.clean_all_data(
                        {
                            "population": population_data,
                            "vaccination": combined_vaccination,
                        }
                    )

                    st.success("✅ Limpieza unificada completada")
                    status.update(
                        label="✅ Datos limpios y normalizados", state="complete"
                    )

                # ============================================================
                # PASO 5: Crear estructura de datos unificada
                # ============================================================
                with st.status(
                    "📋 **PASO 5:** Creando estructura unificada...", expanded=True
                ) as status:
                    st.write("Generando estructura compatible...")

                    self.unified_data = self._create_unified_structure(
                        clean_data["population"],
                        clean_data["vaccination"],
                        population_processor,
                        combiner,
                    )

                    if self.unified_data is None:
                        st.error("❌ Error creando estructura unificada")
                        status.update(label="❌ Error en estructura", state="error")
                        return False

                    st.success("✅ Estructura unificada creada")
                    status.update(label="✅ Sistema unificado listo", state="complete")

                # ============================================================
                # ACTUALIZAR ESTADO DE LA APLICACIÓN
                # ============================================================
                self.app_state.update(
                    {
                        "data_loaded": True,
                        "cutoff_date": combiner.cutoff_date,
                        "last_update": self.unified_data["metadata"]["last_update"],
                        "total_records": len(clean_data["vaccination"]),
                    }
                )

                logger.info("✅ Sistema unificado cargado exitosamente")
                self._show_loading_summary()
                return True

            except Exception as e:
                error_msg = f"Error crítico en carga unificada: {str(e)}"
                logger.error(error_msg)
                st.error(f"❌ {error_msg}")

                with st.expander("🔍 Detalles del error"):
                    st.code(traceback.format_exc())

                self.app_state["loading_errors"].append(str(e))
                return False

    def _create_unified_structure(
        self, population_data, vaccination_data, population_processor, combiner
    ):
        """
        Crea estructura de datos unificada compatible con vistas existentes
        """
        try:
            logger.info("📋 Creando estructura de datos unificada")

            # Obtener metadatos
            population_metadata = population_processor.get_processing_info()
            vaccination_metadata = combiner.get_processing_info()

            # Crear estructura compatible con el sistema existente
            unified_structure = {
                # ============================================================
                # DATOS DE POBLACIÓN (nueva referencia EAPB)
                # ============================================================
                "poblacion_eapb": population_data,
                # ============================================================
                # DATOS DE VACUNACIÓN COMBINADOS
                # ============================================================
                "vacunacion_unificada": vaccination_data,
                # Separar por períodos para análisis específicos
                "vacunacion_historica": (
                    vaccination_data[vaccination_data["periodo"] == "pre_emergencia"]
                    if "periodo" in vaccination_data.columns
                    else pd.DataFrame()
                ),
                "vacunacion_emergencia": (
                    vaccination_data[vaccination_data["periodo"] == "emergencia"]
                    if "periodo" in vaccination_data.columns
                    else pd.DataFrame()
                ),
                # ============================================================
                # COMPATIBILIDAD CON SISTEMA EXISTENTE
                # ============================================================
                "vacunacion": vaccination_data,  # Para compatibilidad con vistas
                "municipios": self._create_compatibility_municipalities(
                    population_data
                ),
                "metricas": self._calculate_municipality_metrics(
                    population_data, vaccination_data
                ),
                # ============================================================
                # METADATOS DEL SISTEMA UNIFICADO
                # ============================================================
                "metadata": {
                    "processing_date": datetime.now(),
                    "cutoff_date": vaccination_metadata.get("cutoff_date"),
                    "last_update": self._get_last_update_date(vaccination_data),
                    "population_reference_date": population_metadata.get(
                        "reference_month", "Abril 2025"
                    ),
                    "total_vaccination_records": len(vaccination_data),
                    "total_population_records": len(population_data),
                    "system_version": INSTITUTIONAL_CONFIG["version"],
                    "processing_summary": {
                        "historical_records": (
                            len(
                                vaccination_data[
                                    vaccination_data["periodo"] == "pre_emergencia"
                                ]
                            )
                            if "periodo" in vaccination_data.columns
                            else 0
                        ),
                        "emergency_records": (
                            len(
                                vaccination_data[
                                    vaccination_data["periodo"] == "emergencia"
                                ]
                            )
                            if "periodo" in vaccination_data.columns
                            else 0
                        ),
                        "unique_municipalities": (
                            vaccination_data["municipio_residencia"].nunique()
                            if "municipio_residencia" in vaccination_data.columns
                            else 0
                        ),
                        "unique_eapb": (
                            population_data["eapb"].nunique()
                            if "eapb" in population_data.columns
                            else 0
                        ),
                    },
                },
            }

            logger.info("✅ Estructura unificada creada exitosamente")
            return unified_structure

        except Exception as e:
            logger.error(f"Error creando estructura unificada: {str(e)}")
            st.error(f"❌ Error creando estructura unificada: {str(e)}")
            return None

    def _create_compatibility_municipalities(self, population_data):
        """
        Crea DataFrame de municipios compatible con el sistema existente
        """
        try:
            if population_data is None or len(population_data) == 0:
                return pd.DataFrame(columns=["DPMP", "DANE", "SISBEN"])

            # Agrupar población por municipio
            municipios_df = (
                population_data.groupby("nombre_municipio")
                .agg({"total": "sum"})
                .reset_index()
            )

            municipios_df.columns = ["DPMP", "DANE"]
            municipios_df["SISBEN"] = municipios_df["DANE"]  # Para compatibilidad

            return municipios_df

        except Exception as e:
            logger.warning(f"Error creando compatibilidad municipios: {str(e)}")
            return pd.DataFrame(columns=["DPMP", "DANE", "SISBEN"])

    def _calculate_municipality_metrics(self, population_data, vaccination_data):
        """
        Calcula métricas por municipio compatibles con el sistema existente
        """
        try:
            if population_data is None or vaccination_data is None:
                return pd.DataFrame()

            logger.info("📊 Calculando métricas municipales")

            # Obtener población por municipio desde EAPB
            if "nombre_municipio" in population_data.columns:
                population_by_mun = (
                    population_data.groupby("nombre_municipio")
                    .agg({"total": "sum"})
                    .reset_index()
                )
                population_by_mun.columns = ["DPMP", "POBLACION_EAPB"]
            else:
                logger.warning("Columna nombre_municipio no encontrada en población")
                return pd.DataFrame()

            # Contar vacunados por municipio
            if "municipio_residencia" in vaccination_data.columns:
                vaccination_by_mun = (
                    vaccination_data.groupby("municipio_residencia")
                    .size()
                    .reset_index()
                )
                vaccination_by_mun.columns = ["municipio", "Vacunados"]

                # Normalizar nombres para matching
                vaccination_by_mun["municipio_norm"] = (
                    vaccination_by_mun["municipio"].str.lower().str.strip()
                )
                population_by_mun["DPMP_norm"] = (
                    population_by_mun["DPMP"].str.lower().str.strip()
                )
            else:
                logger.warning(
                    "Columna municipio_residencia no encontrada en vacunación"
                )
                vaccination_by_mun = pd.DataFrame()

            # Combinar población y vacunación
            if not vaccination_by_mun.empty:
                metrics = pd.merge(
                    population_by_mun,
                    vaccination_by_mun,
                    left_on="DPMP_norm",
                    right_on="municipio_norm",
                    how="left",
                )

                # Llenar vacunados faltantes con 0
                metrics["Vacunados"] = metrics["Vacunados"].fillna(0)

                # Calcular coberturas y pendientes
                metrics["Cobertura_EAPB"] = (
                    metrics["Vacunados"] / metrics["POBLACION_EAPB"] * 100
                ).round(2)
                metrics["Pendientes_EAPB"] = (
                    metrics["POBLACION_EAPB"] - metrics["Vacunados"]
                )

                # Mantener compatibilidad con nombres existentes del sistema
                metrics["DANE"] = metrics["POBLACION_EAPB"]  # Para compatibilidad
                metrics["SISBEN"] = metrics["POBLACION_EAPB"]  # Para compatibilidad
                metrics["Cobertura_DANE"] = metrics["Cobertura_EAPB"]
                metrics["Cobertura_SISBEN"] = metrics["Cobertura_EAPB"]
                metrics["Pendientes_DANE"] = metrics["Pendientes_EAPB"]
                metrics["Pendientes_SISBEN"] = metrics["Pendientes_EAPB"]

                # Seleccionar columnas finales
                final_columns = [
                    "DPMP",
                    "DANE",
                    "SISBEN",
                    "Vacunados",
                    "Cobertura_DANE",
                    "Cobertura_SISBEN",
                    "Pendientes_DANE",
                    "Pendientes_SISBEN",
                    "POBLACION_EAPB",
                    "Cobertura_EAPB",
                    "Pendientes_EAPB",
                ]

                result = metrics[final_columns].fillna(0)
                logger.info(f"✅ Métricas calculadas para {len(result)} municipios")
                return result
            else:
                logger.warning(
                    "No se pudieron combinar datos de población y vacunación"
                )
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error calculando métricas municipales: {str(e)}")
            st.error(f"❌ Error calculando métricas municipales: {str(e)}")
            return pd.DataFrame()

    def _get_last_update_date(self, vaccination_data):
        """
        Obtiene la fecha de última actualización de los datos
        """
        try:
            if "fecha_vacunacion" in vaccination_data.columns:
                dates = pd.to_datetime(
                    vaccination_data["fecha_vacunacion"], errors="coerce"
                )
                return dates.max() if len(dates.dropna()) > 0 else None
            else:
                return None
        except:
            return None

    def _show_loading_summary(self):
        """
        Muestra resumen completo de la carga del sistema unificado
        """
        st.markdown("---")
        st.markdown("## 📊 Resumen del Sistema Unificado")

        if self.unified_data and self.app_state["data_loaded"]:
            metadata = self.unified_data["metadata"]

            # ============================================================
            # MÉTRICAS PRINCIPALES
            # ============================================================
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                total_vac = metadata["total_vaccination_records"]
                st.metric(
                    "Total Registros Vacunación",
                    format_number(total_vac),
                    delta="Registros procesados",
                )

            with col2:
                total_pop = metadata["total_population_records"]
                st.metric(
                    "Registros Población EAPB",
                    format_number(total_pop),
                    delta="Abril 2025",
                )

            with col3:
                cutoff_date = metadata.get("cutoff_date")
                if cutoff_date:
                    cutoff_formatted = format_date(cutoff_date, "short")
                    st.metric("Fecha de Corte", cutoff_formatted, delta="Automática")
                else:
                    st.metric("Fecha de Corte", "No determinada", delta="❌")

            with col4:
                last_update = metadata.get("last_update")
                if last_update:
                    update_formatted = format_date(last_update, "short")
                    st.metric("Última Actualización", update_formatted, delta="Datos")
                else:
                    st.metric("Última Actualización", "N/A", delta="❌")

            # ============================================================
            # DIVISIÓN POR PERÍODOS
            # ============================================================
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 📅 Período Pre-Emergencia")
                hist_count = metadata["processing_summary"]["historical_records"]
                if hist_count > 0:
                    st.success(f"✅ {format_number(hist_count)} registros históricos")
                    if cutoff_date:
                        st.caption(f"Antes del {format_date(cutoff_date, 'full')}")
                else:
                    st.info("ℹ️ Sin registros históricos")

            with col2:
                st.markdown("### 🚨 Período Emergencia")
                emerg_count = metadata["processing_summary"]["emergency_records"]
                if emerg_count > 0:
                    st.success(f"✅ {format_number(emerg_count)} registros de brigadas")
                    if cutoff_date:
                        st.caption(f"Desde el {format_date(cutoff_date, 'full')}")
                else:
                    st.info("ℹ️ Sin registros de emergencia")

            # ============================================================
            # INFORMACIÓN ADICIONAL DEL SISTEMA
            # ============================================================
            st.markdown("### ℹ️ Información del Sistema Unificado")

            summary = metadata["processing_summary"]
            alert_html = create_alert(
                f"""
            **🎯 Características del Sistema Unificado:**
            - **Referencia Población:** {metadata.get('population_reference_date', 'Abril 2025')} (EAPB)
            - **División Temporal:** Automática basada en fecha más antigua de brigadas
            - **Edades:** Calculadas a fecha actual (no momento vacunación)
            - **Municipios únicos:** {summary.get('unique_municipalities', 0)}
            - **EAPB únicas:** {summary.get('unique_eapb', 0)}
            - **Versión:** {metadata.get('system_version', '3.0.0')}
            """,
                "info",
            )
            st.markdown(alert_html, unsafe_allow_html=True)

    def create_sidebar_filters(self):
        """
        Crea filtros en la barra lateral adaptados al sistema unificado
        """
        with st.sidebar:
            # ============================================================
            # LOGO E INFORMACIÓN INSTITUCIONAL
            # ============================================================
            logo_path = ROOT_DIR / "assets" / "images" / "logo_gobernacion.png"
            if logo_path.exists():
                st.image(
                    str(logo_path), width=150, caption="Secretaría de Salud del Tolima"
                )

            st.title("🏥 Dashboard Vacunación")
            st.subheader("🦠 Fiebre Amarilla")

            # ============================================================
            # ESTADO DEL SISTEMA UNIFICADO
            # ============================================================
            if self.app_state["data_loaded"]:
                st.success("✅ Sistema Unificado Activo")

                cutoff_date = self.app_state.get("cutoff_date")
                if cutoff_date:
                    st.info(f"📅 Corte: {format_date(cutoff_date, 'short')}")

                st.caption(f"v{INSTITUTIONAL_CONFIG['version']}")
            else:
                st.error("❌ Sistema no inicializado")

            # ============================================================
            # INFORMACIÓN DE POBLACIÓN (NUEVA REFERENCIA EAPB)
            # ============================================================
            st.markdown("---")
            st.subheader("📊 Referencia Poblacional")

            population_info_html = create_alert(
                """
            **🏥 Nueva Referencia: EAPB**
            - Fuente: Poblacion_aseguramiento.xlsx
            - Fecha: Abril 2025  
            - Incluye todas las aseguradoras del Tolima
            - Reemplaza referencias DANE/SISBEN previas
            """,
                "info",
            )
            st.markdown(population_info_html, unsafe_allow_html=True)

            # ============================================================
            # FILTROS DE DATOS
            # ============================================================
            st.markdown("---")
            st.subheader("🔍 Filtros de Datos")

            filters = {}

            if self.unified_data and self.app_state["data_loaded"]:
                # Filtro de municipio
                municipios = ["Todos"]
                if "DPMP" in self.unified_data["metricas"].columns:
                    municipios_unicos = (
                        self.unified_data["metricas"]["DPMP"].dropna().unique()
                    )
                    municipios.extend(sorted(municipios_unicos))

                filters["municipio"] = st.selectbox("🏘️ Municipio", municipios)

                # Filtro de período (NUEVO - específico del sistema unificado)
                periodos = ["Todos", "Pre-emergencia", "Emergencia"]
                filters["periodo"] = st.selectbox(
                    "📅 Período de Análisis",
                    periodos,
                    help="Pre-emergencia: antes de brigadas | Emergencia: desde brigadas",
                )

                # Filtros demográficos
                if "vacunacion_unificada" in self.unified_data:
                    df_vac = self.unified_data["vacunacion_unificada"]

                    # Género
                    if "sexo" in df_vac.columns:
                        generos = ["Todos"] + sorted(df_vac["sexo"].dropna().unique())
                        filters["sexo"] = st.selectbox("👥 Género", generos)

                    # Grupo de edad actual (NUEVO)
                    if "grupo_edad_actual" in df_vac.columns:
                        grupos_edad = ["Todos"] + sorted(
                            df_vac["grupo_edad_actual"].dropna().unique()
                        )
                        filters["grupo_edad"] = st.selectbox(
                            "🎂 Grupo de Edad Actual", grupos_edad
                        )

                    # Régimen
                    if "regimen_afiliacion" in df_vac.columns:
                        regimenes = ["Todos"] + sorted(
                            df_vac["regimen_afiliacion"].dropna().unique()
                        )
                        filters["regimen"] = st.selectbox("🏥 Régimen", regimenes)

                    # EAPB/Aseguradora (NUEVO)
                    if "nombre_aseguradora" in df_vac.columns:
                        aseguradoras = ["Todos"] + list(
                            df_vac["nombre_aseguradora"].value_counts().head(15).index
                        )
                        filters["aseguradora"] = st.selectbox(
                            "🏨 EAPB/Aseguradora", aseguradoras
                        )

            # ============================================================
            # CONTROLES DE FILTROS
            # ============================================================
            col1, col2 = st.columns(2)

            with col1:
                if st.button("🔄 Restablecer"):
                    st.rerun()

            with col2:
                filters_applied = sum(1 for v in filters.values() if v != "Todos")
                st.caption(f"Filtros: {filters_applied}")

            # ============================================================
            # INFORMACIÓN DEL DESARROLLADOR
            # ============================================================
            st.markdown("---")
            st.markdown("### 👨‍💻 Información")
            st.caption(f"**{INSTITUTIONAL_CONFIG['author']}**")
            st.caption(f"{INSTITUTIONAL_CONFIG['institution']}")
            st.caption(f"© {INSTITUTIONAL_CONFIG['year']}")

            # Información técnica expandible
            with st.expander("🔧 Info Técnica"):
                st.write(f"**Versión:** {INSTITUTIONAL_CONFIG['version']}")
                st.write(
                    f"**Componentes:** {'✅' if SYSTEM_COMPONENTS_LOADED else '❌'}"
                )
                st.write(f"**Vistas:** {self.app_state['available_views']}/6")
                if self.app_state["data_loaded"]:
                    st.write(
                        f"**Registros:** {format_number(self.app_state['total_records'])}"
                    )

            return filters

    def apply_filters_to_data(self, filters):
        """
        Aplica filtros a los datos unificados de manera inteligente
        """
        if not self.unified_data or not self.app_state["data_loaded"]:
            return self.unified_data

        try:
            logger.info(f"🔍 Aplicando filtros: {filters}")
            filtered_data = self.unified_data.copy()

            # Aplicar filtros a datos de vacunación
            df_vac = filtered_data["vacunacion_unificada"].copy()

            # Filtro de período (específico del sistema unificado)
            if filters.get("periodo") != "Todos":
                if (
                    filters["periodo"] == "Pre-emergencia"
                    and "periodo" in df_vac.columns
                ):
                    df_vac = df_vac[df_vac["periodo"] == "pre_emergencia"]
                elif filters["periodo"] == "Emergencia" and "periodo" in df_vac.columns:
                    df_vac = df_vac[df_vac["periodo"] == "emergencia"]

            # Filtro de municipio
            if (
                filters.get("municipio") != "Todos"
                and "municipio_residencia" in df_vac.columns
            ):
                df_vac = df_vac[
                    df_vac["municipio_residencia"].str.contains(
                        filters["municipio"], case=False, na=False
                    )
                ]

            # Filtros demográficos
            demographic_filters = {
                "sexo": "sexo",
                "grupo_edad": "grupo_edad_actual",  # Usar edad actual
                "regimen": "regimen_afiliacion",
                "aseguradora": "nombre_aseguradora",
            }

            for filter_key, column_name in demographic_filters.items():
                if (
                    filters.get(filter_key) != "Todos"
                    and filters.get(filter_key) is not None
                    and column_name in df_vac.columns
                ):
                    df_vac = df_vac[df_vac[column_name] == filters[filter_key]]

            # Actualizar datos filtrados
            filtered_data["vacunacion_unificada"] = df_vac
            filtered_data["vacunacion"] = df_vac  # Para compatibilidad

            # Recalcular métricas si hay filtros aplicados
            if any(v != "Todos" for v in filters.values() if v is not None):
                filtered_data["metricas"] = self._calculate_municipality_metrics(
                    filtered_data["poblacion_eapb"], df_vac
                )

            logger.info(f"✅ Filtros aplicados - {len(df_vac)} registros resultantes")
            return filtered_data

        except Exception as e:
            logger.error(f"Error aplicando filtros: {str(e)}")
            st.error(f"❌ Error aplicando filtros: {str(e)}")
            return self.unified_data

    def show_main_content(self, filtered_data, filters):
        """
        Muestra el contenido principal con pestañas mejoradas
        """
        # ============================================================
        # BANNER PRINCIPAL
        # ============================================================
        col1, col2 = st.columns([3, 1])

        with col1:
            st.title(INSTITUTIONAL_CONFIG["title"])
            st.markdown(f"**{INSTITUTIONAL_CONFIG['subtitle']}**")
            st.caption(INSTITUTIONAL_CONFIG["description"])

        with col2:
            if self.current_date_info:
                date_info = self.current_date_info
                st.info(f"📅 {date_info['formatted_full']}")
                st.caption(f"🕐 {date_info['weekday']}")

        # ============================================================
        # BANNER DE FILTROS ACTIVOS
        # ============================================================
        active_filters = [
            f"**{k.replace('_', ' ').title()}:** {v}"
            for k, v in filters.items()
            if v != "Todos" and v is not None
        ]

        if active_filters:
            filter_text = " | ".join(active_filters)
            alert_html = create_alert(
                f"🔍 **Filtros aplicados:** {filter_text}", "warning"
            )
            st.markdown(alert_html, unsafe_allow_html=True)

        # ============================================================
        # PESTAÑAS PRINCIPALES MEJORADAS
        # ============================================================
        tabs = st.tabs(
            [
                "📊 Visión General",
                "🗺️ Distribución Geográfica",
                "👥 Perfil Demográfico",
                "🏥 Aseguramiento EAPB",
                "📈 Tendencias Temporales",
                "📍 Brigadas Territoriales",
            ]
        )

        # Configuración de pestañas con nuevas descripciones
        tab_configs = [
            (
                "overview",
                tabs[0],
                "Resumen general con métricas principales del sistema unificado",
            ),
            (
                "geographic",
                tabs[1],
                "Análisis territorial por municipios con cobertura EAPB",
            ),
            (
                "demographic",
                tabs[2],
                "Perfil demográfico con edades actuales calculadas",
            ),
            ("insurance", tabs[3], "Análisis detallado por EAPB y aseguradoras"),
            (
                "trends",
                tabs[4],
                "Tendencias temporales con división pre/post emergencia",
            ),
            ("brigadas", tabs[5], "Análisis de brigadas de emergencia territoriales"),
        ]

        # Renderizar cada pestaña
        for view_name, tab, description in tab_configs:
            with tab:
                # Mostrar descripción de la pestaña
                st.caption(f"ℹ️ {description}")
                self._render_view(view_name, filtered_data, filters)

    def _render_view(self, view_name, filtered_data, filters):
        """
        Renderiza una vista específica con manejo robusto de errores
        """
        try:
            if view_name in AVAILABLE_VIEWS and AVAILABLE_VIEWS[view_name] is not None:
                logger.info(f"🎨 Renderizando vista: {view_name}")

                # Adaptar datos para compatibilidad con vistas existentes
                adapted_data = self._adapt_data_for_view(filtered_data)

                # Llamar a la vista con los parámetros correctos
                AVAILABLE_VIEWS[view_name].show(
                    adapted_data,
                    filters,
                    self.colors,
                    "EAPB",  # Nueva fuente de población
                )

                logger.info(f"✅ Vista {view_name} renderizada exitosamente")
            else:
                st.error(f"❌ Vista '{view_name}' no disponible")
                self._show_view_placeholder(view_name)

        except Exception as e:
            logger.error(f"Error en vista '{view_name}': {str(e)}")
            st.error(f"❌ Error en vista '{view_name}': {str(e)}")

            with st.expander("🔍 Detalles del error"):
                st.code(traceback.format_exc())

            self._show_view_placeholder(view_name)

    def _show_view_placeholder(self, view_name):
        """
        Muestra placeholder para vistas no disponibles
        """
        st.info(
            f"""
        🔧 **Vista '{view_name}' en mantenimiento**
        
        Esta vista necesita ser actualizada para el sistema unificado.
        
        **Características que estará disponible:**
        - Integración con población EAPB
        - División temporal automática  
        - Cálculo de edades actuales
        - Compatibilidad con filtros unificados
        """
        )

    def _adapt_data_for_view(self, unified_data):
        """
        Adapta datos unificados para compatibilidad con vistas existentes
        """
        return {
            # Datos principales (compatibilidad con sistema existente)
            "vacunacion": unified_data.get("vacunacion_unificada", pd.DataFrame()),
            "metricas": unified_data.get("metricas", pd.DataFrame()),
            "municipios": unified_data.get("municipios", pd.DataFrame()),
            # Datos específicos del sistema unificado
            "poblacion_eapb": unified_data.get("poblacion_eapb", pd.DataFrame()),
            "vacunacion_historica": unified_data.get(
                "vacunacion_historica", pd.DataFrame()
            ),
            "vacunacion_emergencia": unified_data.get(
                "vacunacion_emergencia", pd.DataFrame()
            ),
            # Metadatos y información del sistema
            "metadata": unified_data.get("metadata", {}),
        }

    def show_footer(self):
        """
        Muestra pie de página completo con información del sistema unificado
        """
        st.markdown("---")
        st.markdown("## 📋 Estado del Sistema Unificado")

        # ============================================================
        # MÉTRICAS DEL SISTEMA
        # ============================================================
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("### 📊 Datos")
            if self.app_state["data_loaded"]:
                total_records = format_number(self.app_state["total_records"])
                st.success(f"✅ **{total_records}** registros procesados")

                last_update = self.app_state.get("last_update")
                if last_update:
                    update_str = format_date(last_update, "short")
                    st.caption(f"📅 Actualizado: {update_str}")
            else:
                st.error("❌ **Sistema no inicializado**")

        with col2:
            st.markdown("### 🔧 Componentes")
            components_status = (
                "✅ Cargados" if SYSTEM_COMPONENTS_LOADED else "❌ Error"
            )
            st.write(f"**Estado:** {components_status}")

            available_views = self.app_state["available_views"]
            st.write(f"**Vistas:** {available_views}/6 disponibles")

        with col3:
            st.markdown("### 🏥 Referencia")
            st.write("**Población:** EAPB (Abril 2025)")
            st.write("**División:** Automática por brigadas")
            st.write("**Edades:** Actuales (no momento vacunación)")

        with col4:
            st.markdown("### ℹ️ Versión")
            st.write(f"**Sistema:** {INSTITUTIONAL_CONFIG['version']}")
            st.write(f"**Desarrollador:** {INSTITUTIONAL_CONFIG['author']}")
            st.write(f"**Institución:** {INSTITUTIONAL_CONFIG['institution']}")

        # ============================================================
        # CARACTERÍSTICAS DEL SISTEMA UNIFICADO
        # ============================================================
        st.markdown("### ✨ Características del Sistema Unificado")

        features_text = []
        for i, feature in enumerate(INSTITUTIONAL_CONFIG["features"], 1):
            features_text.append(f"{i}. {feature}")

        features_html = create_alert(
            "**🎯 Nuevas capacidades del sistema:**\n" + "\n".join(features_text),
            "info",
        )
        st.markdown(features_html, unsafe_allow_html=True)

        # ============================================================
        # INFORMACIÓN DE SOPORTE
        # ============================================================
        with st.expander("🆘 Soporte y Troubleshooting"):
            st.markdown(
                """
            **Si experimentas problemas:**
            
            1. **Refresca la página** (Ctrl+R o F5)
            2. **Verifica los archivos de datos** en la carpeta `data/`
            3. **Revisa los logs** en `dashboard.log`
            4. **Contacta al desarrollador** para soporte técnico
            
            **Archivos requeridos:**
            - `data/Poblacion_aseguramiento.xlsx` (Nueva referencia EAPB)
            - `data/vacunacion_fa.csv` (Datos históricos)
            - `data/Resumen.xlsx` (Brigadas de emergencia)
            """
            )

    def run(self):
        """
        Ejecuta la aplicación completa del sistema unificado
        """
        try:
            logger.info("🚀 Iniciando aplicación del sistema unificado")

            # ============================================================
            # INICIALIZACIÓN DE LA APLICACIÓN
            # ============================================================
            self.initialize_app()

            # ============================================================
            # CARGA DE DATOS UNIFICADOS
            # ============================================================
            if not self.app_state["data_loaded"]:
                st.markdown("## 🔄 Inicializando Sistema Unificado")
                st.info(
                    "**El sistema unificado está cargando los datos por primera vez...**"
                )

                data_loaded = self.load_unified_data()

                if not data_loaded:
                    st.error("❌ **No se pudo inicializar el sistema unificado**")

                    # Mostrar información de ayuda
                    st.markdown("### 🆘 Guía de Solución de Problemas")
                    st.info(
                        """
                    **Pasos recomendados:**
                    1. Verifica que los archivos de datos estén en la carpeta `data/`
                    2. Revisa que los archivos tengan los nombres correctos
                    3. Reinicia la aplicación (Ctrl+R)
                    4. Consulta los logs para más detalles
                    """
                    )

                    # Mostrar errores específicos si los hay
                    if self.app_state["loading_errors"]:
                        st.error("**Errores específicos encontrados:**")
                        for error in self.app_state["loading_errors"]:
                            st.write(f"• {error}")

                    return

            # ============================================================
            # INTERFAZ PRINCIPAL
            # ============================================================
            # Crear filtros en sidebar
            filters = self.create_sidebar_filters()

            # Aplicar filtros a datos
            filtered_data = self.apply_filters_to_data(filters)

            # Mostrar contenido principal
            self.show_main_content(filtered_data, filters)

            # Mostrar pie de página
            self.show_footer()

            logger.info("✅ Aplicación ejecutada exitosamente")

        except Exception as e:
            logger.error(f"Error crítico en la aplicación: {str(e)}")
            st.error("❌ **Error crítico en la aplicación**")
            st.error(f"**Error:** {str(e)}")

            with st.expander("🔍 Información técnica completa"):
                st.code(traceback.format_exc())

            st.markdown(
                """
            ### 🚨 Error Crítico del Sistema Unificado
            
            La aplicación ha encontrado un error que impide su funcionamiento normal.
            
            **Acciones recomendadas:**
            1. Reinicia la aplicación (Ctrl+R o F5)
            2. Verifica que todos los archivos estén en su lugar
            3. Revisa los logs del sistema (`dashboard.log`)
            4. Contacta al administrador técnico si el problema persiste
            
            **Sistema:** {system_version}
            **Fecha:** {current_date}
            """.format(
                    system_version=INSTITUTIONAL_CONFIG["version"],
                    current_date=datetime.now().strftime("%d/%m/%Y %H:%M"),
                )
            )


# =====================================================================
# FUNCIÓN PRINCIPAL DE LA APLICACIÓN
# =====================================================================
def main():
    """
    Función principal de la aplicación del sistema unificado
    """
    try:
        logger.info("=" * 60)
        logger.info("🚀 INICIANDO DASHBOARD UNIFICADO DE VACUNACIÓN")
        logger.info(f"Versión: {INSTITUTIONAL_CONFIG['version']}")
        logger.info(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        logger.info("=" * 60)

        # Crear y ejecutar aplicación
        app = UnifiedDashboardApp()
        app.run()

        logger.info("✅ Dashboard ejecutado exitosamente")

    except Exception as e:
        logger.error(f"Error crítico al inicializar la aplicación: {str(e)}")

        st.error("❌ **Error crítico al inicializar la aplicación**")
        st.error(f"**Error:** {str(e)}")

        st.markdown(
            f"""
        ### 🚨 Fallo Crítico del Sistema
        
        No se pudo inicializar la aplicación principal del sistema unificado.
        
        **Información del error:**
        - **Versión del sistema:** {INSTITUTIONAL_CONFIG['version']}
        - **Componentes cargados:** {'✅' if SYSTEM_COMPONENTS_LOADED else '❌'}
        - **Fecha del error:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        
        **Acciones recomendadas:**
        1. Verifica que todos los archivos estén en su lugar
        2. Reinicia la aplicación (Ctrl+R o F5)
        3. Revisa los logs del sistema (`dashboard.log`)
        4. Contacta al administrador técnico
        
        **Archivos críticos requeridos:**
        - `src/data/unified_loader.py`
        - `src/data/population_processor.py`
        - `src/data/vaccination_combiner.py`
        - `src/data/age_calculator.py`
        - `src/data/data_cleaner.py`
        - `src/utils/date_utils.py`
        - `src/utils/helpers.py`
        """
        )

        with st.expander("🔧 Información técnica detallada"):
            st.code(traceback.format_exc())


# =====================================================================
# PUNTO DE ENTRADA DE LA APLICACIÓN
# =====================================================================
if __name__ == "__main__":
    main()
