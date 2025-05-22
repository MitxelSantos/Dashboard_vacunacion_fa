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

import importlib.util
import sys

# Lista de vistas a importar
vista_modules = ["overview", "geographic", "demographic", "insurance", "trends"]
vistas = {}

# Import para vistas con manejo de errores
vistas_modules = {}

try:
    from vistas import overview

    vistas_modules["overview"] = overview
except ImportError:
    st.error("No se pudo importar el módulo overview")

try:
    from vistas import geographic

    vistas_modules["geographic"] = geographic
except ImportError:
    st.error("No se pudo importar el módulo geographic")

try:
    from vistas import demographic

    vistas_modules["demographic"] = demographic
except ImportError:
    st.error("No se pudo importar el módulo demographic")

try:
    from vistas import insurance

    vistas_modules["insurance"] = insurance
except ImportError:
    st.error("No se pudo importar el módulo insurance")

try:
    from vistas import trends

    vistas_modules["trends"] = trends
except ImportError:
    st.error("No se pudo importar el módulo trends")


from src.data.loader import load_datasets
from src.utils.helpers import configure_page

# Configuración de la página
configure_page(
    page_title="Dashboard Vacunación Fiebre Amarilla - Tolima",
    page_icon="💉",
    layout="wide",
)

# Cargar CSS personalizado
css_main = Path(__file__).parent.parent / "assets" / "styles" / "main.css"
css_responsive = Path(__file__).parent.parent / "assets" / "styles" / "responsive.css"

css = ""
if css_main.exists():
    with open(css_main) as f:
        css += f.read()

if css_responsive.exists():
    with open(css_responsive) as f:
        css += f.read()

# Aplicar CSS
st.markdown(
    f"""
<style>
    {css}
</style>
""",
    unsafe_allow_html=True,
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


def normalize_gender_for_filter(value):
    """
    Normaliza los valores de género para el filtro
    """
    if pd.isna(value) or str(value).lower().strip() in ['nan', '', 'none', 'null', 'na']:
        return "Sin dato"
    
    value_str = str(value).lower().strip()
    
    if value_str in ['masculino', 'm', 'masc', 'hombre', 'h', 'male', '1']:
        return "Masculino"
    elif value_str in ['femenino', 'f', 'fem', 'mujer', 'female', '2']:
        return "Femenino"
    else:
        # Todas las demás clasificaciones van a "No Binario"
        return "No Binario"


def clean_and_normalize_list(lista, normalize_func=None):
    """
    Limpia una lista eliminando valores NaN y aplicando normalización si se especifica
    """
    if normalize_func:
        # Aplicar función de normalización
        normalized_list = [normalize_func(item) for item in lista if not pd.isna(item)]
        # Eliminar duplicados manteniendo orden y excluyendo "Sin dato"
        clean_list = []
        for item in normalized_list:
            if item not in clean_list and item != "Sin dato":
                clean_list.append(item)
        return clean_list
    else:
        # Solo limpiar NaN
        return [str(item) for item in lista if not pd.isna(item) and str(item) != "Sin dato"]


def main():
    """Aplicación principal del dashboard mejorado."""

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
    # CARGA Y VALIDACIÓN DE DATOS
    # =====================================================================
    try:
        with st.spinner("Cargando y normalizando datos..."):
            data = load_datasets()

            # Validar calidad de datos
            from src.data.preprocessor import validate_data_quality
            quality_report = validate_data_quality(data)
            
            # Mostrar alertas de calidad si es necesario
            if quality_report["data_quality_score"] < 80:
                st.sidebar.warning(f"⚠️ Calidad de datos: {quality_report['data_quality_score']:.1f}%")
                if st.sidebar.expander("Ver detalles de calidad"):
                    for issue in quality_report["issues"]:
                        st.sidebar.write(f"• {issue}")

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
                    def categorize_age(x):
                        try:
                            age = float(x)
                            if pd.isna(age):
                                return "Sin dato"
                            elif age < 5:
                                return "0-4"
                            elif age < 15:
                                return "5-14"
                            elif age < 20:
                                return "15-19"
                            elif age < 30:
                                return "20-29"
                            elif age < 40:
                                return "30-39"
                            elif age < 50:
                                return "40-49"
                            elif age < 60:
                                return "50-59"
                            elif age < 70:
                                return "60-69"
                            elif age < 80:
                                return "70-79"
                            elif age >= 80:
                                return "80+"
                            else:
                                return "Sin dato"
                        except (ValueError, TypeError):
                            return "Sin dato"
                    
                    data["vacunacion"]["Grupo_Edad"] = data["vacunacion"]["Edad_Vacunacion"].apply(categorize_age)
                    grupo_edad_col = "Grupo_Edad"
                else:
                    # Si no hay campo de edad, crear una columna con valor único
                    data["vacunacion"]["Grupo_Edad"] = "Sin dato"
                    grupo_edad_col = "Grupo_Edad"

    except FileNotFoundError as e:
        st.error(f"Error al cargar datos: {str(e)}")
        st.info(
            "Por favor, asegúrate de que los archivos de datos estén en la carpeta correcta."
        )
        return

    # =====================================================================
    # BARRA LATERAL CON LOGO Y FILTROS MEJORADOS
    # =====================================================================
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

        # ================================================================
        # FILTROS GLOBALES MEJORADOS CON NORMALIZACIÓN
        # ================================================================
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

        # Filtro de municipios (sin cambios)
        municipios = clean_and_normalize_list(data["municipios"]["DPMP"].unique().tolist())
        municipio = st.selectbox(
            "Municipio",
            options=["Todos"] + sorted(municipios),
            key="municipio_filter",
            on_change=on_filter_change,
        )

        # Filtro de grupos de edad (normalizado)
        try:
            grupos_edad = clean_and_normalize_list(data["vacunacion"]["Grupo_Edad"].unique().tolist())
            # Ordenar grupos de edad lógicamente
            orden_grupos = ["0-4", "5-14", "15-19", "20-29", "30-39", 
                           "40-49", "50-59", "60-69", "70-79", "80+"]
            grupos_ordenados = [g for g in orden_grupos if g in grupos_edad]
            grupos_otros = sorted([g for g in grupos_edad if g not in orden_grupos])
            grupos_edad_final = grupos_ordenados + grupos_otros
        except KeyError:
            grupos_edad_final = ["Sin dato"]
        
        grupo_edad = st.selectbox(
            "Grupo de Edad",
            options=["Todos"] + grupos_edad_final,
            key="grupo_edad_filter",
            on_change=on_filter_change,
        )

        # Filtro de género (MEJORADO Y NORMALIZADO)
        # Preferir la columna Genero si existe
        if "Genero" in data["vacunacion"].columns:
            generos = clean_and_normalize_list(
                data["vacunacion"]["Genero"].unique().tolist(), 
                normalize_gender_for_filter
            )
        else:
            generos = clean_and_normalize_list(
                data["vacunacion"]["Sexo"].unique().tolist(), 
                normalize_gender_for_filter
            )

        # Asegurar orden específico para géneros
        orden_generos = ["Masculino", "Femenino", "No Binario"]
        generos_ordenados = [g for g in orden_generos if g in generos]
        generos_otros = [g for g in generos if g not in orden_generos]
        generos_final = generos_ordenados + generos_otros

        genero = st.selectbox(
            "Género",  # Cambiar de "Género" para ser más inclusivo
            options=["Todos"] + generos_final,
            key="sexo_filter",  # Mantener misma key para compatibilidad
            on_change=on_filter_change,
        )

        # Filtro de grupos étnicos (normalizado)
        grupos_etnicos = clean_and_normalize_list(data["vacunacion"]["GrupoEtnico"].unique().tolist())
        grupo_etnico = st.selectbox(
            "Grupo Étnico",
            options=["Todos"] + sorted(grupos_etnicos),
            key="grupo_etnico_filter",
            on_change=on_filter_change,
        )

        # Filtro de regímenes (normalizado)
        regimenes = clean_and_normalize_list(
            data["vacunacion"]["RegimenAfiliacion"].unique().tolist()
        )
        regimen = st.selectbox(
            "Régimen",
            options=["Todos"] + sorted(regimenes),
            key="regimen_filter",
            on_change=on_filter_change,
        )

        # Filtro de aseguradoras (normalizado)
        aseguradoras = clean_and_normalize_list(
            data["vacunacion"]["NombreAseguradora"].unique().tolist()
        )
        # Limitar las opciones de aseguradoras para mejor UX
        top_aseguradoras = sorted(data["vacunacion"]["NombreAseguradora"].value_counts().head(20).index.tolist())
        top_aseguradoras_clean = [a for a in top_aseguradoras if str(a) != "Sin dato" and not pd.isna(a)]
        
        aseguradora = st.selectbox(
            "EAPB/Aseguradora",
            options=["Todos"] + top_aseguradoras_clean,
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
        if st.button("🔄 Restablecer Filtros", on_click=reset_filters):
            pass  # La lógica está en reset_filters

        # Información sobre filtros activos
        if "filters" in st.session_state:
            active_filters = [
                f"{k.replace('_', ' ').title()}: {v}"
                for k, v in st.session_state.filters.items()
                if v != "Todos"
            ]
            if active_filters:
                st.info(f"🔍 **Filtros activos:** {len(active_filters)}")

        # Información del desarrollador
        st.sidebar.markdown("---")
        st.sidebar.caption("Desarrollado por: Ing. José Miguel Santos")
        st.sidebar.caption("Secretaría de Salud del Tolima © 2025")
        
        # Información de calidad de datos
        if quality_report["data_quality_score"] >= 80:
            st.sidebar.success(f"✅ Calidad de datos: {quality_report['data_quality_score']:.1f}%")

    # =====================================================================
    # INICIALIZACIÓN DE FILTROS
    # =====================================================================
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

    # =====================================================================
    # BANNER PRINCIPAL Y LOGOS
    # =====================================================================
    col1, col2 = st.columns([3, 1])

    with col1:
        st.title("Dashboard Vacunación Fiebre Amarilla - Tolima")
        st.write("Secretaría de Salud del Tolima - Vigilancia Epidemiológica")

    # Banner de filtros activos mejorado
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
    # CONTENIDO DE CADA PESTAÑA
    # =====================================================================
    with tab1:
        if "overview" in vistas_modules:
            vistas_modules["overview"].show(
                data,
                st.session_state.filters,
                COLORS,
                st.session_state.fuente_poblacion,
            )
        else:
            st.warning("⚠️ El módulo de visión general no está disponible")

    with tab2:
        if "geographic" in vistas_modules:
            vistas_modules["geographic"].show(
                data, st.session_state.filters, COLORS, st.session_state.fuente_poblacion
            )
        else:
            st.warning("⚠️ El módulo de distribución geográfica no está disponible")

    with tab3:
        if "demographic" in vistas_modules:
            vistas_modules["demographic"].show(
                data, st.session_state.filters, COLORS, st.session_state.fuente_poblacion
            )
        else:
            st.warning("⚠️ El módulo de perfil demográfico no está disponible")

    with tab4:
        if "insurance" in vistas_modules:
            vistas_modules["insurance"].show(
                data, st.session_state.filters, COLORS, st.session_state.fuente_poblacion
            )
        else:
            st.warning("⚠️ El módulo de aseguramiento no está disponible")

    with tab5:
        if "trends" in vistas_modules:
            vistas_modules["trends"].show(
                data, st.session_state.filters, COLORS, st.session_state.fuente_poblacion
            )
        else:
            st.warning("⚠️ El módulo de tendencias no está disponible")

    # =====================================================================
    # FOOTER CON INFORMACIÓN ADICIONAL
    # =====================================================================
    st.markdown("---")
    col_footer1, col_footer2, col_footer3 = st.columns(3)
    
    with col_footer1:
        st.markdown("### 📊 Dashboard Info")
        st.markdown(f"""
        - **Registros totales:** {len(data['vacunacion']):,}
        - **Municipios:** {len(data['municipios'])}
        - **Fuente población:** {st.session_state.fuente_poblacion}
        """.replace(",", "."))
    
    with col_footer2:
        st.markdown("### 🎯 Calidad de Datos")
        score_color = "🟢" if quality_report["data_quality_score"] >= 90 else "🟡" if quality_report["data_quality_score"] >= 70 else "🔴"
        st.markdown(f"""
        - **Score general:** {score_color} {quality_report["data_quality_score"]:.1f}%
        - **Completitud promedio:** {quality_report["data_quality_score"]:.1f}%
        - **Issues detectados:** {len(quality_report["issues"])}
        """)
    
    with col_footer3:
        st.markdown("### ℹ️ Soporte")
        st.markdown("""
        - **Desarrollador:** José Miguel Santos
        - **Email:** [contacto](mailto:contacto@example.com)
        - **Versión:** 2.0.0 (Mejorada)
        """)


if __name__ == "__main__":
    main()