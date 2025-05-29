"""
app.py - Dashboard de Vacunación Fiebre Amarilla - Tolima
VERSIÓN UNIFICADA con sistema integrado de datos y división temporal automática

Desarrollado para la Secretaría de Salud del Tolima
Autor: Ing. José Miguel Santos
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

# Importar componentes del sistema unificado
try:
    from src.data.unified_loader import UnifiedDataLoader
    from src.data.population_processor import PopulationEAPBProcessor
    from src.data.vaccination_combiner import VaccinationCombiner
    from src.data.age_calculator import AgeCalculator
    from src.data.data_cleaner import UnifiedDataCleaner
    from src.utils.date_utils import date_utils, format_date, get_vaccination_summary
    from src.utils.helpers import (
        dashboard_helpers,
        configure_page,
        format_number,
        get_colors,
        create_alert,
    )

    SYSTEM_COMPONENTS_LOADED = True

except ImportError as e:
    st.error(f"❌ Error importando componentes del sistema: {str(e)}")
    SYSTEM_COMPONENTS_LOADED = False

# Importar vistas con manejo de errores
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
    except ImportError as e:
        st.warning(f"⚠️ Vista {view_name} no disponible: {str(e)}")
        AVAILABLE_VIEWS[view_name] = None

# Configuración institucional
INSTITUTIONAL_CONFIG = {
    "title": "Dashboard Vacunación Fiebre Amarilla - Tolima",
    "subtitle": "Secretaría de Salud del Tolima - Vigilancia Epidemiológica",
    "version": "2.0.0 - Sistema Unificado",
    "author": "Ing. José Miguel Santos",
    "institution": "Secretaría de Salud del Tolima",
    "year": "2025",
}


class UnifiedDashboardApp:
    """
    Aplicación principal del dashboard con sistema unificado
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
        }

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
        Inicializa la aplicación con configuración institucional
        """
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

    def load_unified_data(self):
        """
        Carga datos usando el sistema unificado
        """
        if not SYSTEM_COMPONENTS_LOADED:
            st.error("❌ Sistema de componentes no disponible")
            return False

        st.info("🔄 **Iniciando carga del sistema unificado...**")

        try:
            # PASO 1: Cargar y procesar población por EAPB
            st.info("📊 **PASO 1:** Procesando población por EAPB...")
            population_processor = PopulationEAPBProcessor(str(DATA_DIR))
            population_data = population_processor.load_population_data()

            if population_data is None:
                st.error("❌ No se pudo cargar población por EAPB")
                return False

            # PASO 2: Combinar datos de vacunación con fecha de corte automática
            st.info("🔗 **PASO 2:** Combinando datos de vacunación...")
            combiner = VaccinationCombiner(str(DATA_DIR))
            combined_vaccination = combiner.load_and_combine_data()

            if combined_vaccination is None:
                st.error("❌ No se pudo combinar datos de vacunación")
                return False

            # PASO 3: Calcular edades actuales
            st.info("🎂 **PASO 3:** Calculando edades actuales...")
            if "fecha_nacimiento" in combined_vaccination.columns:
                age_calculator = AgeCalculator()
                combined_vaccination = age_calculator.calculate_ages_for_dataframe(
                    combined_vaccination,
                    birth_date_column="fecha_nacimiento",
                    target_age_column="edad_actual",
                    target_group_column="grupo_edad_actual",
                )

            # PASO 4: Aplicar limpieza unificada
            st.info("🧹 **PASO 4:** Aplicando limpieza unificada...")
            cleaner = UnifiedDataCleaner()

            clean_data = cleaner.clean_all_data(
                {"population": population_data, "vaccination": combined_vaccination}
            )

            # PASO 5: Crear estructura de datos unificada
            st.info("📋 **PASO 5:** Creando estructura unificada...")
            self.unified_data = self._create_unified_structure(
                clean_data["population"],
                clean_data["vaccination"],
                population_processor,
                combiner,
            )

            # Actualizar estado de la aplicación
            self.app_state.update(
                {
                    "data_loaded": True,
                    "cutoff_date": combiner.cutoff_date,
                    "last_update": self.unified_data["metadata"]["last_update"],
                    "total_records": len(clean_data["vaccination"]),
                }
            )

            st.success("✅ **Sistema unificado cargado exitosamente**")
            self._show_loading_summary()

            return True

        except Exception as e:
            st.error(f"❌ **Error crítico en carga unificada:** {str(e)}")

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
            # Obtener metadatos
            population_metadata = population_processor.get_processing_info()
            vaccination_metadata = combiner.get_processing_info()

            # Crear estructura compatible
            unified_structure = {
                # Datos de población (nueva referencia)
                "poblacion_eapb": population_data,
                # Datos de vacunación combinados
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
                # Crear métricas por municipio (compatible con vistas existentes)
                "metricas": self._calculate_municipality_metrics(
                    population_data, vaccination_data
                ),
                # Metadatos del sistema
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
                },
            }

            return unified_structure

        except Exception as e:
            st.error(f"❌ Error creando estructura unificada: {str(e)}")
            return None

    def _calculate_municipality_metrics(self, population_data, vaccination_data):
        """
        Calcula métricas por municipio compatibles con el sistema existente
        """
        try:
            # Obtener población por municipio desde EAPB
            if "nombre_municipio_norm" in population_data.columns:
                population_by_mun = (
                    population_data.groupby(
                        ["nombre_municipio", "nombre_municipio_norm"]
                    )["total"]
                    .sum()
                    .reset_index()
                )
                population_by_mun.columns = ["DPMP", "DPMP_norm", "POBLACION_EAPB"]
            else:
                st.warning("⚠️ Estructura de población no reconocida")
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
            else:
                st.warning("⚠️ Columna de municipio no encontrada en vacunación")
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

                # Calcular coberturas
                metrics["Cobertura_EAPB"] = (
                    metrics["Vacunados"] / metrics["POBLACION_EAPB"] * 100
                ).round(2)

                # Calcular pendientes
                metrics["Pendientes_EAPB"] = (
                    metrics["POBLACION_EAPB"] - metrics["Vacunados"]
                )

                # Mantener compatibilidad con nombres existentes
                metrics["DANE"] = metrics["POBLACION_EAPB"]  # Para compatibilidad
                metrics["SISBEN"] = metrics["POBLACION_EAPB"]  # Para compatibilidad
                metrics["Cobertura_DANE"] = metrics["Cobertura_EAPB"]
                metrics["Cobertura_SISBEN"] = metrics["Cobertura_EAPB"]
                metrics["Pendientes_DANE"] = metrics["Pendientes_EAPB"]
                metrics["Pendientes_SISBEN"] = metrics["Pendientes_EAPB"]

                # Limpiar y seleccionar columnas finales
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

                return metrics[final_columns].fillna(0)
            else:
                return pd.DataFrame()

        except Exception as e:
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
        Muestra resumen de la carga del sistema unificado
        """
        st.markdown("---")
        st.subheader("📊 Resumen del Sistema Unificado")

        if self.unified_data and self.app_state["data_loaded"]:
            metadata = self.unified_data["metadata"]

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Total Registros Vacunación",
                    format_number(metadata["total_vaccination_records"]),
                )

            with col2:
                st.metric(
                    "Registros Población EAPB",
                    format_number(metadata["total_population_records"]),
                )

            with col3:
                cutoff_date = metadata.get("cutoff_date")
                if cutoff_date:
                    cutoff_formatted = format_date(cutoff_date, "short")
                    st.metric("Fecha de Corte", cutoff_formatted)
                else:
                    st.metric("Fecha de Corte", "No determinada")

            with col4:
                last_update = metadata.get("last_update")
                if last_update:
                    update_formatted = format_date(last_update, "short")
                    st.metric("Última Actualización", update_formatted)
                else:
                    st.metric("Última Actualización", "N/A")

            # Información adicional
            st.info(
                f"""
            ✅ **Sistema Unificado Activo**
            - **Referencia Población:** {metadata.get('population_reference_date', 'Abril 2025')} (EAPB)
            - **División Temporal:** Automática basada en brigadas
            - **Edades:** Calculadas a fecha actual (no momento vacunación)
            - **Versión:** {metadata.get('system_version', '2.0.0')}
            """
            )

    def create_sidebar_filters(self):
        """
        Crea filtros en la barra lateral adaptados al sistema unificado
        """
        with st.sidebar:
            # Logo institucional
            logo_path = ROOT_DIR / "assets" / "images" / "logo_gobernacion.png"
            if logo_path.exists():
                st.image(
                    str(logo_path), width=150, caption="Secretaría de Salud del Tolima"
                )

            st.title("Dashboard Vacunación")
            st.subheader("Fiebre Amarilla")

            # Información del sistema unificado
            if self.app_state["data_loaded"]:
                st.success("✅ Sistema Unificado Activo")

                cutoff_date = self.app_state.get("cutoff_date")
                if cutoff_date:
                    st.info(f"📅 Corte: {format_date(cutoff_date, 'short')}")
            else:
                st.error("❌ Sistema no inicializado")

            # Selector de fuente de población (ahora informativo)
            st.subheader("Referencia Poblacional")
            st.info(
                """
            **Nueva Referencia: EAPB**
            - Fuente: Población_aseguramiento.xlsx
            - Fecha: Abril 2025
            - Incluye todas las aseguradoras
            """
            )

            # Filtros de datos
            st.subheader("Filtros de Datos")

            filters = {}

            if self.unified_data and self.app_state["data_loaded"]:
                # Filtro de municipio
                municipios = ["Todos"]
                if "DPMP" in self.unified_data["metricas"].columns:
                    municipios_unicos = (
                        self.unified_data["metricas"]["DPMP"].dropna().unique()
                    )
                    municipios.extend(sorted(municipios_unicos))

                filters["municipio"] = st.selectbox("Municipio", municipios)

                # Filtro de período (nuevo)
                periodos = ["Todos", "Pre-emergencia", "Emergencia"]
                filters["periodo"] = st.selectbox(
                    "Período de Análisis",
                    periodos,
                    help="Pre-emergencia: antes de brigadas | Emergencia: desde brigadas",
                )

                # Filtros demográficos
                if "vacunacion_unificada" in self.unified_data:
                    df_vac = self.unified_data["vacunacion_unificada"]

                    # Género
                    if "sexo" in df_vac.columns:
                        generos = ["Todos"] + sorted(df_vac["sexo"].dropna().unique())
                        filters["sexo"] = st.selectbox("Género", generos)

                    # Grupo de edad actual
                    if "grupo_edad_actual" in df_vac.columns:
                        grupos_edad = ["Todos"] + sorted(
                            df_vac["grupo_edad_actual"].dropna().unique()
                        )
                        filters["grupo_edad"] = st.selectbox(
                            "Grupo de Edad Actual", grupos_edad
                        )

                    # Régimen
                    if "regimen_afiliacion" in df_vac.columns:
                        regimenes = ["Todos"] + sorted(
                            df_vac["regimen_afiliacion"].dropna().unique()
                        )
                        filters["regimen"] = st.selectbox("Régimen", regimenes)

                    # EAPB/Aseguradora
                    if "nombre_aseguradora" in df_vac.columns:
                        aseguradoras = ["Todos"] + list(
                            df_vac["nombre_aseguradora"].value_counts().head(15).index
                        )
                        filters["aseguradora"] = st.selectbox(
                            "EAPB/Aseguradora", aseguradoras
                        )

            # Botón para resetear filtros
            if st.button("🔄 Restablecer Filtros"):
                for key in filters.keys():
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

            # Información del desarrollador
            st.markdown("---")
            st.caption(f"**{INSTITUTIONAL_CONFIG['author']}**")
            st.caption(f"{INSTITUTIONAL_CONFIG['institution']}")
            st.caption(
                f"© {INSTITUTIONAL_CONFIG['year']} - {INSTITUTIONAL_CONFIG['version']}"
            )

            return filters

    def apply_filters_to_data(self, filters):
        """
        Aplica filtros a los datos unificados
        """
        if not self.unified_data or not self.app_state["data_loaded"]:
            return self.unified_data

        try:
            filtered_data = self.unified_data.copy()

            # Aplicar filtros a datos de vacunación
            df_vac = filtered_data["vacunacion_unificada"].copy()

            # Filtro de período
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
                "grupo_edad": "grupo_edad_actual",
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

            # Recalcular métricas si hay filtros aplicados
            if any(v != "Todos" for v in filters.values() if v is not None):
                filtered_data["metricas"] = self._calculate_municipality_metrics(
                    filtered_data["poblacion_eapb"], df_vac
                )

            return filtered_data

        except Exception as e:
            st.error(f"❌ Error aplicando filtros: {str(e)}")
            return self.unified_data

    def show_main_content(self, filtered_data, filters):
        """
        Muestra el contenido principal con pestañas
        """
        # Banner principal
        col1, col2 = st.columns([3, 1])

        with col1:
            st.title(INSTITUTIONAL_CONFIG["title"])
            st.write(INSTITUTIONAL_CONFIG["subtitle"])

        with col2:
            if self.current_date_info:
                st.info(f"📅 {self.current_date_info['formatted_full']}")

        # Banner de filtros activos
        active_filters = [
            f"{k.replace('_', ' ').title()}: {v}"
            for k, v in filters.items()
            if v != "Todos" and v is not None
        ]

        if active_filters:
            filter_text = " | ".join(active_filters)
            alert_html = create_alert(
                f"🔍 **Filtros aplicados:** {filter_text}", "warning"
            )
            st.markdown(alert_html, unsafe_allow_html=True)

        # Pestañas principales
        tabs = st.tabs(
            [
                "📊 Visión General",
                "🗺️ Distribución Geográfica",
                "👥 Perfil Demográfico",
                "🏥 Aseguramiento",
                "📈 Tendencias Temporales",
                "📍 Brigadas Territoriales",
            ]
        )

        # Contenido de cada pestaña
        tab_configs = [
            ("overview", tabs[0]),
            ("geographic", tabs[1]),
            ("demographic", tabs[2]),
            ("insurance", tabs[3]),
            ("trends", tabs[4]),
            ("brigadas", tabs[5]),
        ]

        for view_name, tab in tab_configs:
            with tab:
                self._render_view(view_name, filtered_data, filters)

    def _render_view(self, view_name, filtered_data, filters):
        """
        Renderiza una vista específica con manejo de errores
        """
        try:
            if view_name in AVAILABLE_VIEWS and AVAILABLE_VIEWS[view_name] is not None:
                # Adaptar datos para compatibilidad con vistas existentes
                adapted_data = self._adapt_data_for_view(filtered_data)

                # Llamar a la vista
                AVAILABLE_VIEWS[view_name].show(
                    adapted_data,
                    filters,
                    self.colors,
                    "EAPB",  # Nueva fuente de población
                )
            else:
                st.error(f"❌ Vista '{view_name}' no disponible")
                st.info(
                    "🔧 Esta vista necesita ser actualizada para el sistema unificado"
                )

        except Exception as e:
            st.error(f"❌ Error en vista '{view_name}': {str(e)}")

            with st.expander("🔍 Detalles del error"):
                st.code(traceback.format_exc())

    def _adapt_data_for_view(self, unified_data):
        """
        Adapta datos unificados para compatibilidad con vistas existentes
        """
        return {
            # Datos principales
            "vacunacion": unified_data.get("vacunacion_unificada", pd.DataFrame()),
            "metricas": unified_data.get("metricas", pd.DataFrame()),
            "municipios": unified_data.get(
                "metricas", pd.DataFrame()
            ),  # Compatibilidad
            # Datos adicionales del sistema unificado
            "poblacion_eapb": unified_data.get("poblacion_eapb", pd.DataFrame()),
            "vacunacion_historica": unified_data.get(
                "vacunacion_historica", pd.DataFrame()
            ),
            "vacunacion_emergencia": unified_data.get(
                "vacunacion_emergencia", pd.DataFrame()
            ),
            # Metadatos
            "metadata": unified_data.get("metadata", {}),
        }

    def show_footer(self):
        """
        Muestra pie de página con información del sistema
        """
        st.markdown("---")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("### 📊 Sistema Unificado")
            if self.app_state["data_loaded"]:
                st.write(
                    f"✅ **Activo** - {format_number(self.app_state['total_records'])} registros"
                )
                st.write(
                    f"📅 Actualización: {format_date(self.app_state['last_update'], 'short') if self.app_state['last_update'] else 'N/A'}"
                )
            else:
                st.write("❌ **No inicializado**")

        with col2:
            st.markdown("### 🎯 Estado del Sistema")
            st.write(
                f"🔗 **Componentes:** {'✅ Cargados' if SYSTEM_COMPONENTS_LOADED else '❌ Error'}"
            )
            st.write(
                f"📋 **Vistas:** {len([v for v in AVAILABLE_VIEWS.values() if v is not None])}/6 disponibles"
            )

        with col3:
            st.markdown("### ℹ️ Información")
            st.write(f"**Versión:** {INSTITUTIONAL_CONFIG['version']}")
            st.write(f"**Desarrollador:** {INSTITUTIONAL_CONFIG['author']}")

        with col4:
            st.markdown("### 🏥 Referencia")
            st.write("**Población:** EAPB (Abril 2025)")
            st.write("**División:** Automática por brigadas")
            st.write("**Edades:** Actuales (no momento vacunación)")

    def run(self):
        """
        Ejecuta la aplicación completa
        """
        try:
            # Inicializar aplicación
            self.initialize_app()

            # Cargar datos unificados
            if not self.app_state["data_loaded"]:
                data_loaded = self.load_unified_data()
                if not data_loaded:
                    st.error("❌ **No se pudo inicializar el sistema unificado**")
                    st.info(
                        "🔄 **Reinicia la aplicación o verifica los archivos de datos**"
                    )
                    return

            # Crear filtros en sidebar
            filters = self.create_sidebar_filters()

            # Aplicar filtros a datos
            filtered_data = self.apply_filters_to_data(filters)

            # Mostrar contenido principal
            self.show_main_content(filtered_data, filters)

            # Mostrar pie de página
            self.show_footer()

        except Exception as e:
            st.error("❌ **Error crítico en la aplicación**")
            st.error(f"**Error:** {str(e)}")

            with st.expander("🔍 Información técnica"):
                st.code(traceback.format_exc())

            st.info(
                "🔄 **Reinicia la aplicación (Ctrl+R) o contacta al administrador**"
            )


def main():
    """
    Función principal de la aplicación
    """
    try:
        # Crear y ejecutar aplicación
        app = UnifiedDashboardApp()
        app.run()

    except Exception as e:
        st.error("❌ **Error crítico al inicializar la aplicación**")
        st.error(f"**Error:** {str(e)}")

        st.markdown(
            """
        ### 🚨 Error Crítico del Sistema
        
        No se pudo inicializar la aplicación principal.
        
        **Acciones recomendadas:**
        1. Verifica que todos los archivos estén en su lugar
        2. Reinicia la aplicación (Ctrl+R o F5)
        3. Revisa los logs del sistema
        4. Contacta al administrador técnico
        """
        )

        with st.expander("🔧 Información técnica detallada"):
            st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
