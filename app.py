import os
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import traceback

# Deshabilitar detección automática de páginas de Streamlit
os.environ["STREAMLIT_PAGES_ENABLED"] = "false"

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
sys.path.insert(0, str(ROOT_DIR))

from src.data.loader import load_datasets
from src.utils.helpers import configure_page

# Configuración de la página
configure_page(
    page_title="Dashboard Vacunación Fiebre Amarilla - Tolima",
    page_icon="💉",
    layout="wide",
)

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


def create_empty_safe_data():
    """
    Crea una estructura de datos segura y vacía para casos de emergencia
    """
    return {
        "municipios": pd.DataFrame(
            {
                "DPMP": ["Ibagué", "Espinal", "Honda"],
                "DANE": [1000, 800, 600],
                "SISBEN": [1100, 850, 650],
            }
        ),
        "vacunacion": pd.DataFrame(
            {
                "IdPaciente": ["001", "002", "003"],
                "Sexo": ["Masculino", "Femenino", "Masculino"],
                "Grupo_Edad": ["20 a 29 años", "30 a 39 años", "40 a 49 años"],
                "GrupoEtnico": ["Mestizo", "Mestizo", "Afrodescendiente"],
                "RegimenAfiliacion": ["Contributivo", "Subsidiado", "Contributivo"],
                "NombreMunicipioResidencia": ["Ibagué", "Espinal", "Honda"],
                "NombreAseguradora": ["NUEVA EPS", "SALUD TOTAL", "MEDIMAS"],
                "FA UNICA": ["2024-01-15", "2024-01-16", "2024-01-17"],
            }
        ),
        "metricas": pd.DataFrame(
            {
                "DPMP": ["Ibagué", "Espinal", "Honda"],
                "DANE": [1000, 800, 600],
                "SISBEN": [1100, 850, 650],
                "Vacunados": [1, 1, 1],
                "Cobertura_DANE": [0.1, 0.125, 0.167],
                "Cobertura_SISBEN": [0.091, 0.118, 0.154],
                "Pendientes_DANE": [999, 799, 599],
                "Pendientes_SISBEN": [1099, 849, 649],
            }
        ),
    }


def load_data_with_fallback():
    """
    Carga los datos con múltiples niveles de fallback para mayor robustez
    """
    try:
        st.info("🔄 Cargando datos del sistema...")

        # Intento 1: Cargar datos normalmente
        try:
            data = load_datasets()

            # Validar que los datos cargados sean válidos
            if data is None:
                raise ValueError("load_datasets() devolvió None")

            if not isinstance(data, dict):
                raise ValueError("load_datasets() no devolvió un diccionario")

            required_keys = ["municipios", "vacunacion", "metricas"]
            for key in required_keys:
                if key not in data:
                    raise ValueError(f"Falta la clave '{key}' en los datos")
                if data[key] is None:
                    raise ValueError(f"La clave '{key}' es None")
                if not isinstance(data[key], pd.DataFrame):
                    raise ValueError(f"La clave '{key}' no es un DataFrame")

            # Verificar que haya al menos algunos datos
            if len(data["vacunacion"]) == 0:
                st.warning("⚠️ No se encontraron datos de vacunación")

            if len(data["municipios"]) == 0:
                st.warning("⚠️ No se encontraron datos de municipios")

            st.success("✅ Datos cargados exitosamente")
            return data

        except FileNotFoundError as e:
            st.error(f"❌ Archivos de datos no encontrados: {str(e)}")
            st.info("💡 Asegúrate de que los archivos estén en la carpeta 'data/'")
            raise

        except Exception as e:
            st.error(f"❌ Error cargando datos: {str(e)}")
            raise

    except Exception as e:
        st.error("❌ No se pudieron cargar los datos del sistema")

        # Intento 2: Usar datos de emergencia
        st.warning("⚠️ Usando datos de demostración para evitar fallos críticos")
        st.markdown(
            """
        **Modo de Emergencia Activado**
        
        Los datos mostrados son solo para demostración. Para usar datos reales:
        1. Verifica que los archivos estén en la carpeta `data/`
        2. Asegúrate de que tengas conexión a Google Drive (si corresponde)
        3. Reinicia la aplicación
        """
        )

        return create_empty_safe_data()


def safe_import_vistas():
    """
    Importa las vistas de manera segura con manejo de errores
    """
    vistas_modules = {}
    vista_names = ["overview", "geographic", "demographic", "insurance", "trends"]

    for vista_name in vista_names:
        try:
            if vista_name == "overview":
                from vistas import overview

                vistas_modules["overview"] = overview
            elif vista_name == "geographic":
                from vistas import geographic

                vistas_modules["geographic"] = geographic
            elif vista_name == "demographic":
                from vistas import demographic

                vistas_modules["demographic"] = demographic
            elif vista_name == "insurance":
                from vistas import insurance

                vistas_modules["insurance"] = insurance
            elif vista_name == "trends":
                from vistas import trends

                vistas_modules["trends"] = trends

            st.success(f"✅ Módulo {vista_name} cargado correctamente")

        except ImportError as e:
            st.error(f"❌ No se pudo importar el módulo {vista_name}: {str(e)}")
            vistas_modules[vista_name] = None
        except Exception as e:
            st.error(f"❌ Error inesperado cargando {vista_name}: {str(e)}")
            vistas_modules[vista_name] = None

    return vistas_modules


def show_error_view(error_message, vista_name):
    """
    Muestra una vista de error cuando una vista específica falla
    """
    st.title(f"Error en {vista_name.title()}")
    st.error(f"❌ {error_message}")

    st.markdown(
        f"""
    ### Soluciones posibles:
    
    1. **Reinicia la aplicación** - Usa Ctrl+R o F5
    2. **Verifica los datos** - Asegúrate de que los archivos estén disponibles
    3. **Cambia de pestaña** - Prueba otra sección del dashboard
    4. **Contacta soporte** - Si el problema persiste
    
    ### Información técnica:
    - Vista afectada: `{vista_name}`
    - Error: `{error_message}`
    """
    )


def main():
    """
    Aplicación principal del dashboard mejorado con manejo robusto de errores.
    NUNCA debería fallar completamente - siempre muestra algo útil al usuario.
    """

    try:
        # Detectar tamaño de pantalla con JavaScript
        st.markdown(
            """
        <script>
            // Detectar tamaño de pantalla
            var updateScreenSize = function() {
                var width = window.innerWidth;
                var isSmall = width < 1200;
                
                // Almacenar en sessionStorage para que Streamlit pueda acceder
                sessionStorage.setItem('_screen_width', width);
                sessionStorage.setItem('_is_small_screen', isSmall);
            };
            
            // Actualizar inmediatamente y al cambiar tamaño
            updateScreenSize();
            window.addEventListener('resize', updateScreenSize);
        </script>
        """,
            unsafe_allow_html=True,
        )

        # Intentar recuperar el tamaño de pantalla
        screen_width = st.session_state.get("_screen_width", 1200)
        st.session_state["_is_small_screen"] = screen_width < 1200

        # =====================================================================
        # CARGA Y VALIDACIÓN DE DATOS CON MANEJO ROBUSTO DE ERRORES
        # =====================================================================

        data = None
        data_loaded_successfully = False

        try:
            with st.spinner("Cargando y normalizando datos..."):
                data = load_data_with_fallback()

                if data is not None:
                    # Validar calidad de datos
                    try:
                        from src.data.preprocessor import validate_data_quality

                        quality_report = validate_data_quality(data)

                        # Mostrar alertas de calidad si es necesario
                        if quality_report.get("data_quality_score", 0) < 80:
                            st.sidebar.warning(
                                f"⚠️ Calidad de datos: {quality_report.get('data_quality_score', 0):.1f}%"
                            )
                            if st.sidebar.expander("Ver detalles de calidad"):
                                for issue in quality_report.get("issues", []):
                                    st.sidebar.write(f"• {issue}")
                        else:
                            st.sidebar.success(
                                f"✅ Calidad de datos: {quality_report.get('data_quality_score', 100):.1f}%"
                            )

                    except Exception as e:
                        st.sidebar.warning(
                            f"⚠️ No se pudo validar calidad de datos: {str(e)}"
                        )

                    data_loaded_successfully = True

        except Exception as e:
            st.error(f"❌ Error crítico cargando datos: {str(e)}")
            st.markdown("### 🚨 Error Crítico")
            st.markdown(
                """
            No se pudieron cargar los datos necesarios para el dashboard.
            
            **Posibles causas:**
            - Los archivos de datos no están disponibles
            - Error de conexión a Google Drive
            - Corrupción en los archivos de datos
            - Error en la configuración del sistema
            """
            )

            # Ofrecer reiniciar o usar datos de demostración
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Reintentar Carga"):
                    st.rerun()
            with col2:
                if st.button("🎬 Usar Datos de Demo"):
                    data = create_empty_safe_data()
                    data_loaded_successfully = True
                    st.rerun()

            if not data_loaded_successfully:
                return  # Salir si no se pudieron cargar datos

        # Si llegamos aquí, tenemos datos válidos (reales o de demostración)
        if data is None:
            st.error("❌ Error crítico: No hay datos disponibles")
            return

        # =====================================================================
        # CONFIGURACIÓN DE INTERFAZ DE USUARIO
        # =====================================================================

        # Barra lateral con logo y filtros
        with st.sidebar:
            # Logo de la Gobernación
            logo_path = IMAGES_DIR / "logo_gobernacion.png"
            if logo_path.exists():
                st.image(str(logo_path), width=150)
            else:
                st.info("💡 Logo no encontrado en assets/images/logo_gobernacion.png")

            st.title("Dashboard Vacunación")
            st.subheader("Fiebre Amarilla")

            # Selector de fuente de datos de población
            st.subheader("Fuente de datos")

            if "fuente_radio" not in st.session_state:
                st.session_state.fuente_radio = "DANE"  # Valor predeterminado

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

            # FILTROS GLOBALES
            st.subheader("Filtros")

            # Función para aplicar filtros automáticamente
            def on_filter_change():
                st.session_state.filters = {
                    "municipio": st.session_state.get("municipio_filter", "Todos"),
                    "grupo_edad": st.session_state.get("grupo_edad_filter", "Todos"),
                    "sexo": st.session_state.get("sexo_filter", "Todos"),
                    "grupo_etnico": st.session_state.get(
                        "grupo_etnico_filter", "Todos"
                    ),
                    "regimen": st.session_state.get("regimen_filter", "Todos"),
                    "aseguradora": st.session_state.get("aseguradora_filter", "Todos"),
                }

            # Crear filtros seguros
            try:
                # Filtro de municipios
                municipios = ["Todos"]
                if "municipios" in data and "DPMP" in data["municipios"].columns:
                    municipios_unicos = (
                        data["municipios"]["DPMP"].dropna().unique().tolist()
                    )
                    municipios.extend(
                        sorted([str(m) for m in municipios_unicos if str(m) != "nan"])
                    )

                municipio = st.selectbox(
                    "Municipio",
                    options=municipios,
                    key="municipio_filter",
                    on_change=on_filter_change,
                )

                # Filtro de grupos de edad
                grupos_edad = ["Todos"]
                if "vacunacion" in data and "Grupo_Edad" in data["vacunacion"].columns:
                    grupos_unicos = (
                        data["vacunacion"]["Grupo_Edad"].dropna().unique().tolist()
                    )
                    grupos_clean = sorted(
                        [
                            str(g)
                            for g in grupos_unicos
                            if str(g) not in ["nan", "Sin dato"]
                        ]
                    )
                    grupos_edad.extend(grupos_clean)

                grupo_edad = st.selectbox(
                    "Grupo de Edad",
                    options=grupos_edad,
                    key="grupo_edad_filter",
                    on_change=on_filter_change,
                )

                # Filtro de género
                generos = ["Todos", "Masculino", "Femenino", "No Binario"]
                genero = st.selectbox(
                    "Género",
                    options=generos,
                    key="sexo_filter",
                    on_change=on_filter_change,
                )

                # Filtro de grupos étnicos
                grupos_etnicos = ["Todos"]
                if "vacunacion" in data and "GrupoEtnico" in data["vacunacion"].columns:
                    etnicos_unicos = (
                        data["vacunacion"]["GrupoEtnico"].dropna().unique().tolist()
                    )
                    etnicos_clean = sorted(
                        [
                            str(e)
                            for e in etnicos_unicos
                            if str(e) not in ["nan", "Sin dato"]
                        ]
                    )
                    grupos_etnicos.extend(etnicos_clean[:20])  # Limitar para UX

                grupo_etnico = st.selectbox(
                    "Grupo Étnico",
                    options=grupos_etnicos,
                    key="grupo_etnico_filter",
                    on_change=on_filter_change,
                )

                # Filtro de regímenes
                regimenes = ["Todos"]
                if (
                    "vacunacion" in data
                    and "RegimenAfiliacion" in data["vacunacion"].columns
                ):
                    regimenes_unicos = (
                        data["vacunacion"]["RegimenAfiliacion"]
                        .dropna()
                        .unique()
                        .tolist()
                    )
                    regimenes_clean = sorted(
                        [
                            str(r)
                            for r in regimenes_unicos
                            if str(r) not in ["nan", "Sin dato"]
                        ]
                    )
                    regimenes.extend(regimenes_clean)

                regimen = st.selectbox(
                    "Régimen",
                    options=regimenes,
                    key="regimen_filter",
                    on_change=on_filter_change,
                )

                # Filtro de aseguradoras
                aseguradoras = ["Todos"]
                if (
                    "vacunacion" in data
                    and "NombreAseguradora" in data["vacunacion"].columns
                ):
                    aseguradoras_unicos = (
                        data["vacunacion"]["NombreAseguradora"]
                        .value_counts()
                        .head(20)
                        .index.tolist()
                    )
                    aseguradoras_clean = [
                        str(a)
                        for a in aseguradoras_unicos
                        if str(a) not in ["nan", "Sin dato"]
                    ]
                    aseguradoras.extend(aseguradoras_clean)

                aseguradora = st.selectbox(
                    "EAPB/Aseguradora",
                    options=aseguradoras,
                    key="aseguradora_filter",
                    on_change=on_filter_change,
                )

            except Exception as e:
                st.sidebar.error(f"❌ Error creando filtros: {str(e)}")
                # Usar filtros básicos por defecto
                municipio = "Todos"
                grupo_edad = "Todos"
                genero = "Todos"
                grupo_etnico = "Todos"
                regimen = "Todos"
                aseguradora = "Todos"

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

            # Función para resetear filtros
            def reset_filters():
                for key in [
                    "municipio_filter",
                    "grupo_edad_filter",
                    "sexo_filter",
                    "grupo_etnico_filter",
                    "regimen_filter",
                    "aseguradora_filter",
                ]:
                    st.session_state[key] = "Todos"
                on_filter_change()

            if st.button("🔄 Restablecer Filtros", on_click=reset_filters):
                pass

            # Información del desarrollador
            st.sidebar.markdown("---")
            st.sidebar.caption("Desarrollado por: Ing. José Miguel Santos")
            st.sidebar.caption("Secretaría de Salud del Tolima © 2025")

        # =====================================================================
        # BANNER PRINCIPAL
        # =====================================================================
        col1, col2 = st.columns([3, 1])

        with col1:
            st.title("Dashboard Vacunación Fiebre Amarilla - Tolima")
            st.write("Secretaría de Salud del Tolima - Vigilancia Epidemiológica")

        # Banner de filtros activos
        active_filters = [
            f"{k.replace('_', ' ').title()}: {v}"
            for k, v in st.session_state.filters.items()
            if v != "Todos"
        ]
        if active_filters:
            st.markdown(
                f"""
                <div style="background: linear-gradient(90deg, {COLORS['primary']}, {COLORS['accent']}); 
                            color: white; padding: 12px; border-radius: 8px; margin-bottom: 20px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <strong>🔍 Filtros aplicados:</strong> {' | '.join(active_filters)}
                    <small style="float: right; opacity: 0.8;">
                        Mostrando datos filtrados de {fuente_poblacion}
                    </small>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # =====================================================================
        # IMPORTAR Y CONFIGURAR VISTAS
        # =====================================================================

        vistas_modules = safe_import_vistas()

        # =====================================================================
        # PESTAÑAS DE NAVEGACIÓN
        # =====================================================================
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            [
                "📊 Visión General",
                "🗺️ Distribución Geográfica",
                "👥 Perfil Demográfico",
                "🏥 Aseguramiento",
                "📈 Tendencias",
            ]
        )

        # =====================================================================
        # CONTENIDO DE CADA PESTAÑA CON MANEJO DE ERRORES
        # =====================================================================

        with tab1:
            try:
                if vistas_modules.get("overview") is not None:
                    vistas_modules["overview"].show(
                        data,
                        st.session_state.filters,
                        COLORS,
                        st.session_state.fuente_poblacion,
                    )
                else:
                    show_error_view(
                        "El módulo de visión general no está disponible", "overview"
                    )
            except Exception as e:
                st.error(f"❌ Error en Visión General: {str(e)}")
                with st.expander("🔍 Detalles del error"):
                    st.code(traceback.format_exc())

        with tab2:
            try:
                if vistas_modules.get("geographic") is not None:
                    vistas_modules["geographic"].show(
                        data,
                        st.session_state.filters,
                        COLORS,
                        st.session_state.fuente_poblacion,
                    )
                else:
                    show_error_view(
                        "El módulo de distribución geográfica no está disponible",
                        "geographic",
                    )
            except Exception as e:
                st.error(f"❌ Error en Distribución Geográfica: {str(e)}")
                with st.expander("🔍 Detalles del error"):
                    st.code(traceback.format_exc())

        with tab3:
            try:
                if vistas_modules.get("demographic") is not None:
                    vistas_modules["demographic"].show(
                        data,
                        st.session_state.filters,
                        COLORS,
                        st.session_state.fuente_poblacion,
                    )
                else:
                    show_error_view(
                        "El módulo de perfil demográfico no está disponible",
                        "demographic",
                    )
            except Exception as e:
                st.error(f"❌ Error en Perfil Demográfico: {str(e)}")
                with st.expander("🔍 Detalles del error"):
                    st.code(traceback.format_exc())

        with tab4:
            try:
                if vistas_modules.get("insurance") is not None:
                    vistas_modules["insurance"].show(
                        data,
                        st.session_state.filters,
                        COLORS,
                        st.session_state.fuente_poblacion,
                    )
                else:
                    show_error_view(
                        "El módulo de aseguramiento no está disponible", "insurance"
                    )
            except Exception as e:
                st.error(f"❌ Error en Aseguramiento: {str(e)}")
                with st.expander("🔍 Detalles del error"):
                    st.code(traceback.format_exc())

        with tab5:
            try:
                if vistas_modules.get("trends") is not None:
                    vistas_modules["trends"].show(
                        data,
                        st.session_state.filters,
                        COLORS,
                        st.session_state.fuente_poblacion,
                    )
                else:
                    show_error_view(
                        "El módulo de tendencias no está disponible", "trends"
                    )
            except Exception as e:
                st.error(f"❌ Error en Tendencias: {str(e)}")
                with st.expander("🔍 Detalles del error"):
                    st.code(traceback.format_exc())

        # =====================================================================
        # FOOTER CON INFORMACIÓN ADICIONAL
        # =====================================================================
        st.markdown("---")
        col_footer1, col_footer2, col_footer3 = st.columns(3)

        with col_footer1:
            st.markdown("### 📊 Dashboard Info")
            try:
                total_records = len(data.get("vacunacion", pd.DataFrame()))
                total_municipios = len(data.get("municipios", pd.DataFrame()))
                st.markdown(
                    f"""
                - **Registros totales:** {total_records:,}
                - **Municipios:** {total_municipios}
                - **Fuente población:** {st.session_state.fuente_poblacion}
                """.replace(
                        ",", "."
                    )
                )
            except:
                st.markdown("- **Estado:** Datos cargados")

        with col_footer2:
            st.markdown("### 🎯 Estado del Sistema")
            system_status = (
                "🟢 Operativo" if data_loaded_successfully else "🔴 Modo Emergencia"
            )
            st.markdown(
                f"""
            - **Estado:** {system_status}
            - **Vistas cargadas:** {sum(1 for v in vistas_modules.values() if v is not None)}/5
            - **Filtros activos:** {len(active_filters)}
            """
            )

        with col_footer3:
            st.markdown("### ℹ️ Soporte")
            st.markdown(
                """
            - **Desarrollador:** José Miguel Santos
            - **Email:** [Contacto](mailto:contacto@example.com)
            - **Versión:** 2.1.0 (Robusta)
            """
            )

    except Exception as e:
        # Último nivel de manejo de errores - nunca debería llegar aquí
        st.error("❌ Error crítico en la aplicación principal")
        st.markdown(
            f"""
        ### 🚨 Error Crítico del Sistema
        
        Ha ocurrido un error inesperado en el sistema principal.
        
        **Error:** `{str(e)}`
        
        **Acciones recomendadas:**
        1. Refresca la página (F5 o Ctrl+R)
        2. Limpia la caché del navegador
        3. Contacta al administrador del sistema
        """
        )

        # Mostrar detalles técnicos si el usuario los necesita
        if st.checkbox("🔧 Mostrar detalles técnicos"):
            st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
