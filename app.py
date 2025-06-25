"""
app.py - Dashboard de Vacunación Fiebre Amarilla - Tolima
VERSIÓN CORREGIDA - Fix para TypeError en comparación de fechas
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import os
from pathlib import Path

# Configuración de página
st.set_page_config(
    page_title="Dashboard Vacunación Fiebre Amarilla - Tolima",
    page_icon="💉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Importar vistas
from vistas.overview import show_overview_tab
from vistas.temporal import show_temporal_tab
from vistas.geographic import show_geographic_tab
from vistas.population import show_population_tab

# Importar cargador de Google Drive
from google_drive_loader import load_from_drive, check_drive_availability

# Colores institucionales
COLORS = {
    "primary": "#7D0F2B",
    "secondary": "#F2A900",
    "accent": "#5A4214",
    "success": "#509E2F",
    "warning": "#F7941D",
    "white": "#FFFFFF",
}

# Rangos de edad definitivos
RANGOS_EDAD = {
    "<1": "< 1 año",
    "1-5": "1-5 años",
    "6-10": "6-10 años",
    "11-20": "11-20 años",
    "21-30": "21-30 años",
    "31-40": "31-40 años",
    "41-50": "41-50 años",
    "51-59": "51-59 años",
    "60+": "60 años y más",
}


def setup_sidebar():
    """Configura la barra lateral con información institucional"""
    with st.sidebar:
        # Logo institucional - cargar archivo real
        logo_path = "assets/images/logo_tolima.png"

        if os.path.exists(logo_path):
            st.image(logo_path, width=150, caption="Gobernación del Tolima")
        else:
            # Fallback si no existe el logo
            st.markdown(
                """
                <div style="text-align: center; padding: 10px;">
                    <div style="background: linear-gradient(135deg, #7D0F2B, #F2A900); 
                               color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                        <h3 style="margin: 0; font-size: 16px;">🏛️ GOBERNACIÓN</h3>
                        <h4 style="margin: 5px 0; font-size: 14px;">DEL TOLIMA</h4>
                        <p style="margin: 0; font-size: 11px;">Secretaría de Salud</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Título del dashboard
        st.markdown("### 💉 Dashboard Vacunación - Fiebre Amarilla")
        st.markdown("---")

        # Información del desarrollador
        st.markdown("#### 👨‍💻 **Desarrollado por:**")
        st.markdown("**Ing. José Miguel Santos**")
        st.markdown("*Secretaría de Salud del Tolima*")

        st.markdown("---")
        # Copyright
        st.markdown(
            """
            <div style="text-align: center; padding: 8px; 
                       background-color: #f0f0f0; border-radius: 5px;">
                <small><strong>Secretaría de Salud del Tolima</strong><br>
                © 2025 - Todos los derechos reservados</small>
            </div>
            """,
            unsafe_allow_html=True,
        )


def calculate_current_age(fecha_nacimiento):
    """Calcula la edad ACTUAL desde fecha de nacimiento"""
    if pd.isna(fecha_nacimiento):
        return None, "Fecha nula"

    try:
        hoy = datetime.now()
        edad = hoy.year - fecha_nacimiento.year

        # Ajustar si no ha llegado el cumpleaños este año
        if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
            edad -= 1

        edad_final = max(0, edad)
        return edad_final, f"Calculada: {edad_final} años"
    except Exception as e:
        return None, f"Error: {str(e)}"

def classify_age_group_debug(edad):
    """Clasifica edad en rango correspondiente con diagnóstico"""
    if pd.isna(edad) or edad is None:
        return None, "Edad nula"
    
    if edad < 1:
        return "<1", f"Edad {edad} → <1"
    elif 1 <= edad <= 5:
        return "1-5", f"Edad {edad} → 1-5"
    elif 6 <= edad <= 10:
        return "6-10", f"Edad {edad} → 6-10"
    elif 11 <= edad <= 20:
        return "11-20", f"Edad {edad} → 11-20"
    elif 21 <= edad <= 30:
        return "21-30", f"Edad {edad} → 21-30"
    elif 31 <= edad <= 40:
        return "31-40", f"Edad {edad} → 31-40"
    elif 41 <= edad <= 50:
        return "41-50", f"Edad {edad} → 41-50"
    elif 51 <= edad <= 59:
        return "51-59", f"Edad {edad} → 51-59"
    else:
        return "60+"


def load_data_smart():
    """
    Carga datos de forma inteligente:
    - Primero intenta Google Drive (para Streamlit Cloud)
    - Si falla, intenta archivos locales (para desarrollo local)
    """
    # Intentar Google Drive primero
    try:
        available, message = check_drive_availability()
        if available:
            st.info("🔄 Cargando datos desde Google Drive...")
            results = load_from_drive("all")

            if results["status"]["vacunacion"] and results["status"]["barridos"]:
                st.success("✅ Datos cargados exitosamente desde Google Drive")
                return results["vacunacion"], results["barridos"], results["poblacion"]
            else:
                st.warning("⚠️ Google Drive configurado pero faltan datos críticos")
        else:
            st.info("📁 Google Drive no disponible, intentando archivos locales...")
    except Exception as e:
        st.warning(f"⚠️ Error con Google Drive: {str(e)}")
        st.info("📁 Intentando cargar archivos locales...")

    # Fallback a archivos locales
    return load_local_data()


def load_local_data():
    """Carga datos desde archivos locales (desarrollo)"""
    # Cargar vacunación individual
    df_individual = load_individual_data_local()

    # Cargar barridos
    df_barridos = load_barridos_data_local()

    # Cargar población
    df_population = load_population_data_local()

    return df_individual, df_barridos, df_population


@st.cache_data
def load_individual_data_local():
    """Carga datos de vacunación individual desde archivos locales"""
    file_path = "data/vacunacion_fa.csv"

    if not os.path.exists(file_path):
        st.error(f"❌ Archivo no encontrado: {file_path}")
        st.info("💡 Para Streamlit Cloud, configura Google Drive en Settings > Secrets")
        return pd.DataFrame()

    try:
        df = pd.read_csv(file_path, low_memory=False, encoding="utf-8")

        # Procesar fechas con manejo robusto
        if "FechaNacimiento" in df.columns:
            st.write("🔄 **Procesando FechaNacimiento...**")
            df["FechaNacimiento"] = pd.to_datetime(df["FechaNacimiento"], errors="coerce")
            
            fechas_validas = df["FechaNacimiento"].dropna()
            st.write(f"- Fechas de nacimiento válidas: {len(fechas_validas):,}")
            
            if len(fechas_validas) > 0:
                st.write(f"- Rango de fechas: {fechas_validas.min()} a {fechas_validas.max()}")
        else:
            st.error("❌ Columna 'FechaNacimiento' no encontrada")
            
        if "FA UNICA" in df.columns:
            st.write("🔄 **Procesando FA UNICA...**")
            df["FA UNICA"] = pd.to_datetime(df["FA UNICA"], errors="coerce")
            
            fechas_vacuna_validas = df["FA UNICA"].dropna()
            st.write(f"- Fechas de vacuna válidas: {len(fechas_vacuna_validas):,}")
            
            if len(fechas_vacuna_validas) > 0:
                st.write(f"- Rango de fechas: {fechas_vacuna_validas.min()} a {fechas_vacuna_validas.max()}")
        else:
            st.error("❌ Columna 'FA UNICA' no encontrada")

        st.success(f"✅ Datos individuales cargados: {len(df):,} registros")
        return df

    except Exception as e:
        st.error(f"❌ Error cargando datos individuales: {str(e)}")
        return pd.DataFrame()

@st.cache_data
def load_barridos_data_local():
    """Carga datos de barridos territoriales desde archivos locales"""
    file_path = "data/Resumen.xlsx"

    if not os.path.exists(file_path):
        st.error(f"❌ Archivo no encontrado: {file_path}")
        st.info("💡 Para Streamlit Cloud, configura Google Drive en Settings > Secrets")
        return pd.DataFrame()

    try:
        # Intentar diferentes hojas
        for sheet in ["Barridos", "Vacunacion", 0]:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet)
                break
            except:
                continue
        else:
            st.error("❌ No se pudo leer el archivo de barridos")
            return pd.DataFrame()

        # Procesar fechas con manejo robusto
        if "FECHA" in df.columns:
            df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")

        st.success(f"✅ Datos de barridos: {len(df):,} registros")
        return df

    except Exception as e:
        st.error(f"❌ Error cargando barridos: {str(e)}")
        return pd.DataFrame()

@st.cache_data
def load_population_data_local():
    """Carga datos de población desde archivos locales"""
    file_path = "data/Poblacion_aseguramiento.xlsx"

    if not os.path.exists(file_path):
        st.info("📊 Archivo de población no encontrado - análisis básico")
        return pd.DataFrame()

    try:
        df = pd.read_excel(file_path)
        st.success(f"✅ Datos de población: {len(df):,} registros")
        return df

    except Exception as e:
        st.info(f"📊 Error cargando población: {str(e)} - análisis básico")
        return pd.DataFrame()

def safe_date_comparison(date_series, cutoff_date, operation="less"):
    """Realiza comparación de fechas de forma segura"""
    try:
        # Asegurar que ambas fechas están en el mismo formato
        if cutoff_date is None:
            return pd.Series([False] * len(date_series))
        
        # Convertir fecha de corte a timestamp si es necesario
        if isinstance(cutoff_date, datetime):
            cutoff_timestamp = pd.Timestamp(cutoff_date)
        elif isinstance(cutoff_date, pd.Timestamp):
            cutoff_timestamp = cutoff_date
        else:
            cutoff_timestamp = pd.Timestamp(cutoff_date)
        
        # Limpiar la serie de fechas - eliminar NaN y convertir a datetime
        clean_series = pd.to_datetime(date_series, errors='coerce')
        
        # Crear máscara booleana según la operación
        if operation == "less":
            mask = clean_series < cutoff_timestamp
        elif operation == "greater_equal":
            mask = clean_series >= cutoff_timestamp
        else:
            mask = clean_series < cutoff_timestamp
        
        # Reemplazar NaN por False
        mask = mask.fillna(False)
        
        return mask
        
    except Exception as e:
        st.error(f"Error en comparación de fechas: {str(e)}")
        # Retornar máscara vacía en caso de error
        return pd.Series([False] * len(date_series))

def determine_cutoff_date(df_barridos):
    """Determina fecha de corte (primer barrido) para evitar duplicados"""
    if df_barridos.empty or "FECHA" not in df_barridos.columns:
        return None

    fechas_validas = df_barridos["FECHA"].dropna()

    if len(fechas_validas) == 0:
        return None

    # Fecha del primer barrido = inicio de emergencia
    fecha_corte = fechas_validas.min()

    return fecha_corte


def safe_date_comparison(date_series, cutoff_date):
    """
    Realiza comparación de fechas de forma segura

    Args:
        date_series: Serie de pandas con fechas
        cutoff_date: Fecha de corte

    Returns:
        Serie booleana con el resultado de la comparación
    """
    try:
        # Asegurar que ambas fechas están en el mismo formato
        if cutoff_date is None:
            return pd.Series([False] * len(date_series))

        # Convertir fecha de corte a timestamp si es necesario
        if isinstance(cutoff_date, datetime):
            cutoff_timestamp = pd.Timestamp(cutoff_date)
        elif isinstance(cutoff_date, pd.Timestamp):
            cutoff_timestamp = cutoff_date
        else:
            cutoff_timestamp = pd.Timestamp(cutoff_date)

        # Limpiar la serie de fechas - eliminar NaN y convertir a datetime
        clean_series = pd.to_datetime(date_series, errors="coerce")

        # Crear máscara booleana con manejo de NaN
        mask = clean_series < cutoff_timestamp

        # Reemplazar NaN por False
        mask = mask.fillna(False)

        return mask

    except Exception as e:
        st.error(f"Error en comparación de fechas: {str(e)}")
        # Retornar máscara vacía en caso de error
        return pd.Series([False] * len(date_series))


def detect_barridos_columns(df):
    """Detecta columnas de vacunados en barrido (TPVB) y renuentes (TPNVP)"""

    # Patrones para rangos de edad
    age_patterns = {
        "<1": ["< 1", "<1", "MENOR 1", "LACTANTE"],
        "1-5": ["1-5", "1 A 5", "PREESCOLAR"],
        "6-10": ["6-10", "6 A 10", "ESCOLAR"],
        "11-20": ["11-20", "11 A 20", "ADOLESCENTE"],
        "21-30": ["21-30", "21 A 30"],
        "31-40": ["31-40", "31 A 40"],
        "41-50": ["41-50", "41 A 50"],
        "51-59": ["51-59", "51 A 59"],
        "60+": ["60+", "60 Y MAS", "MAYOR 60"],
        "60-69": ["60-69", "60 A 69"],
        "70+": ["70+", "70 Y MAS", "MAYOR 70"],
    }

    result = {
        "vacunados_barrido": {},  # TPVB: vacunados durante el barrido
        "renuentes": {},  # TPNVP: renuentes/no vacunados
        "consolidation_needed": [],
    }

    # Detectar columnas por sección
    for age_range, patterns in age_patterns.items():
        found_cols = []

        for col in df.columns:
            col_str = str(col).upper().strip()
            if any(pattern in col_str for pattern in patterns):
                # Evitar conflictos
                if age_range == "1-5" and any(
                    conflict in col_str for conflict in ["41-50", "51-59"]
                ):
                    continue
                if age_range == "60+" and any(
                    conflict in col_str for conflict in ["60-69"]
                ):
                    continue

                found_cols.append(col)

        if found_cols:
            # 4ta sección = TPVB (vacunados en barrido)
            if len(found_cols) >= 4:
                result["vacunados_barrido"][age_range] = found_cols[3]
            # 3ra sección = TPNVP (renuentes)
            if len(found_cols) >= 3:
                result["renuentes"][age_range] = found_cols[2]

            # Marcar para consolidación si es 60+ adicional
            if age_range in ["60-69", "70+"]:
                result["consolidation_needed"].extend(found_cols)

    return result


def process_individual_pre_barridos(df_individual, fecha_corte):
    """Procesa datos individuales PRE-barridos (sin duplicados) - VERSIÓN CORREGIDA"""
    if df_individual.empty:
        st.error("❌ DataFrame individual está vacío")
        return {"total": 0, "por_edad": {}, "por_municipio": {}}

    # Filtrar solo vacunas ANTES del primer barrido usando comparación segura
    if fecha_corte and "FA UNICA" in df_individual.columns:
        # Usar función de comparación segura
        mask_pre = safe_date_comparison(df_individual["FA UNICA"], fecha_corte)
        df_pre = df_individual[mask_pre].copy()

        fecha_corte_str = (
            fecha_corte.strftime("%d/%m/%Y")
            if hasattr(fecha_corte, "strftime")
            else str(fecha_corte)
        )
        st.info(f"📅 Usando vacunas individuales antes de {fecha_corte_str}")
    else:
        df_pre = df_individual.copy()
        st.warning("⚠️ No hay fecha de corte - usando todos los datos individuales")

        result = {"total": len(df_pre), "por_edad": {}, "por_municipio": {}}

        if df_pre.empty:
            st.warning("⚠️ No hay datos PRE-emergencia para procesar")
            return result

        # DIAGNÓSTICO DETALLADO DE CÁLCULO DE EDADES
        if "FechaNacimiento" in df_pre.columns:
            st.write(f"**🎂 Procesando edades:**")
            
            fechas_nacimiento_validas = df_pre["FechaNacimiento"].dropna()
            st.write(f"- Fechas de nacimiento válidas: {len(fechas_nacimiento_validas):,}")
            
            if len(fechas_nacimiento_validas) > 0:
                # Calcular edades con diagnóstico
                edades = []
                clasificaciones = []
                
                # Procesar muestra para diagnóstico
                sample_size = min(10, len(fechas_nacimiento_validas))
                sample_fechas = fechas_nacimiento_validas.head(sample_size)
                
                st.write(f"**🔍 Muestra de cálculo de edades ({sample_size} registros):**")
                
                for i, fecha_nac in enumerate(sample_fechas, 1):
                    edad, debug_msg = calculate_current_age_debug(fecha_nac)
                    if edad is not None:
                        rango, rango_msg = classify_age_group_debug(edad)
                        st.write(f"  {i}. {fecha_nac.date()} → {debug_msg} → {rango_msg}")
                        edades.append(edad)
                        clasificaciones.append(rango)
                    else:
                        st.write(f"  {i}. {fecha_nac} → {debug_msg}")
                
                # Procesar todas las edades
                st.write(f"**🔄 Procesando todas las edades...**")
                df_pre["edad_actual"] = df_pre["FechaNacimiento"].apply(lambda x: calculate_current_age_debug(x)[0])
                df_pre["rango_edad"] = df_pre["edad_actual"].apply(lambda x: classify_age_group_debug(x)[0])

                # Estadísticas de edades
                edades_validas = df_pre["edad_actual"].dropna()
                st.write(f"- Edades calculadas exitosamente: {len(edades_validas):,}")
                
                if len(edades_validas) > 0:
                    st.write(f"- Edad mínima: {edades_validas.min()}")
                    st.write(f"- Edad máxima: {edades_validas.max()}")
                    st.write(f"- Edad promedio: {edades_validas.mean():.1f}")

                # Contar por rangos de edad
                age_counts = df_pre["rango_edad"].value_counts()
                st.write(f"**📊 Distribución por rangos de edad:**")
                
                for rango in RANGOS_EDAD.keys():
                    count = age_counts.get(rango, 0)
                    result["por_edad"][rango] = count
                    st.write(f"  - {RANGOS_EDAD[rango]}: {count:,}")
                
                total_con_rango = sum(result["por_edad"].values())
                st.write(f"**Total con rango de edad:** {total_con_rango:,}")
                
            else:
                st.error("❌ No hay fechas de nacimiento válidas")
        else:
            st.error("❌ Columna 'FechaNacimiento' no encontrada")

        # Contar por municipio
        if "NombreMunicipioResidencia" in df_pre.columns:
            municipio_counts = df_pre["NombreMunicipioResidencia"].value_counts()
            result["por_municipio"] = municipio_counts.to_dict()
            st.write(f"**🏘️ Municipios únicos:** {len(municipio_counts)}")
        else:
            st.error("❌ Columna 'NombreMunicipioResidencia' no encontrada")

    return result

# [Resto de funciones sin cambios - process_barridos_data, process_population_data, etc.]

def main():
    """Función principal del dashboard con diagnóstico"""
    # Configurar barra lateral mejorada
    setup_sidebar()

    # Título principal
    st.title("🏥 Dashboard de Vacunación Fiebre Amarilla - DIAGNÓSTICO")
    st.markdown("**Versión de diagnóstico para identificar problemas**")

    # Cargar datos de forma inteligente
    st.markdown("### 📥 Cargando datos...")

    with st.spinner("Cargando datos..."):
        try:
            df_individual, df_barridos, df_population = load_data_smart()
        except Exception as e:
            st.error(f"❌ Error cargando datos: {str(e)}")
            return

    # Verificar datos mínimos
    if df_individual.empty and df_barridos.empty:
        st.error("❌ Sin datos suficientes para mostrar el dashboard")
        st.markdown(
            """
        ### 🔧 **Soluciones:**
        
        **Para Streamlit Cloud:**
        1. Ve a Settings > Secrets en tu app
        2. Configura tus IDs de Google Drive:
        ```toml
        [google_drive]
        vacunacion_csv = "TU_ID_AQUI"
        resumen_barridos_xlsx = "TU_ID_AQUI"
        poblacion_xlsx = "TU_ID_AQUI"  # Opcional
        ```
        
        **Para desarrollo local:**
        - Coloca los archivos en la carpeta `data/`
        """
        )
        return

    # Determinar fecha de corte
    fecha_corte = determine_cutoff_date(df_barridos)
    if fecha_corte:
        fecha_corte_str = (
            fecha_corte.strftime("%d/%m/%Y")
            if hasattr(fecha_corte, "strftime")
            else str(fecha_corte)
        )
        st.success(f"📅 **Fecha de corte (inicio emergencia):** {fecha_corte_str}")
        st.info(f"🏥 **Individuales PRE-emergencia:** Antes de {fecha_corte_str}")
        st.info(f"🚨 **Barridos DURANTE emergencia:** Desde {fecha_corte_str}")
    else:
        st.warning("⚠️ No se pudo determinar fecha de corte")

    # Procesar datos CON DIAGNÓSTICO DETALLADO
    st.markdown("### 📊 Procesando información...")

    with st.spinner("Procesando..."):
        try:
            # Datos PRE-emergencia (sin duplicados)
            individual_data = process_individual_pre_barridos(
                df_individual, fecha_corte
            )

            # Datos DURANTE emergencia
            barridos_data = process_barridos_data(df_barridos)

            # Datos de población
            population_data = process_population_data(df_population)
        except Exception as e:
            st.error(f"❌ Error procesando datos: {str(e)}")
            return

    # Preparar datos combinados (SIN DUPLICADOS)
    combined_data = {
        "individual_pre": individual_data,
        "barridos": barridos_data,
        "population": population_data,
        "fecha_corte": fecha_corte,
        # Totales combinados
        "total_individual_pre": individual_data["total"],
        "total_barridos": barridos_data["vacunados_barrido"]["total"],
        "total_renuentes": barridos_data["renuentes"]["total"],
        "total_real_combinado": individual_data["total"]
        + barridos_data["vacunados_barrido"]["total"],
    }

    # Estado de carga con lógica temporal
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Individual PRE-emergencia", f"{combined_data['total_individual_pre']:,}"
        )
    with col2:
        st.metric("Barridos DURANTE emergencia", f"{combined_data['total_barridos']:,}")
    with col3:
        st.metric("Renuentes", f"{combined_data['total_renuentes']:,}")
    with col4:
        st.metric(
            "**TOTAL REAL (Sin duplicados)**",
            f"{combined_data['total_real_combinado']:,}",
        )

    st.markdown("---")

    # Tabs principales
    try:
        tab1, tab2, tab3, tab4 = st.tabs(
            ["📊 Resumen", "📅 Temporal", "🗺️ Geográfico", "🏘️ Poblacional"]
        )

        with tab1:
            show_overview_tab(combined_data, COLORS, RANGOS_EDAD)

        with tab2:
            show_temporal_tab(combined_data, df_individual, df_barridos, COLORS)

        with tab3:
            show_geographic_tab(combined_data, COLORS)

        with tab4:
            show_population_tab(combined_data, COLORS)

    except Exception as e:
        st.error(f"❌ Error mostrando pestañas: {str(e)}")
        st.info("💡 Revisa que todas las vistas estén correctamente configuradas")


if __name__ == "__main__":
    main()
