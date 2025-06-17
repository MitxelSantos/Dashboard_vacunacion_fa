"""
app.py - Dashboard de Vacunación Fiebre Amarilla - Tolima
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


def calculate_current_age(fecha_nacimiento):
    """Calcula la edad ACTUAL desde fecha de nacimiento"""
    if pd.isna(fecha_nacimiento):
        return None

    try:
        hoy = datetime.now()
        edad = hoy.year - fecha_nacimiento.year

        # Ajustar si no ha llegado el cumpleaños este año
        if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
            edad -= 1

        return max(0, edad)
    except:
        return None


def classify_age_group(edad):
    """Clasifica edad en rango correspondiente"""
    if pd.isna(edad) or edad is None:
        return None

    if edad < 1:
        return "<1"
    elif 1 <= edad <= 5:
        return "1-5"
    elif 6 <= edad <= 10:
        return "6-10"
    elif 11 <= edad <= 20:
        return "11-20"
    elif 21 <= edad <= 30:
        return "21-30"
    elif 31 <= edad <= 40:
        return "31-40"
    elif 41 <= edad <= 50:
        return "41-50"
    elif 51 <= edad <= 59:
        return "51-59"
    else:
        return "60+"


@st.cache_data
def load_individual_data():
    """Carga datos de vacunación individual"""
    file_path = "data/vacunacion_fa.csv"

    if not os.path.exists(file_path):
        st.error(f"❌ Archivo no encontrado: {file_path}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(file_path, low_memory=False, encoding="utf-8")

        # Procesar fechas
        if "FechaNacimiento" in df.columns:
            df["FechaNacimiento"] = pd.to_datetime(
                df["FechaNacimiento"], errors="coerce"
            )
        if "FA UNICA" in df.columns:
            df["FA UNICA"] = pd.to_datetime(df["FA UNICA"], errors="coerce")

        st.success(f"✅ Datos individuales: {len(df):,} registros")
        return df

    except Exception as e:
        st.error(f"❌ Error cargando datos individuales: {str(e)}")
        return pd.DataFrame()


@st.cache_data
def load_barridos_data():
    """Carga datos de barridos territoriales"""
    file_path = "data/Resumen.xlsx"

    if not os.path.exists(file_path):
        st.error(f"❌ Archivo no encontrado: {file_path}")
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

        # Procesar fechas
        if "FECHA" in df.columns:
            df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")

        st.success(f"✅ Datos de barridos: {len(df):,} registros")
        return df

    except Exception as e:
        st.error(f"❌ Error cargando barridos: {str(e)}")
        return pd.DataFrame()


@st.cache_data
def load_population_data():
    """Carga datos de población (opcional)"""
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


def detect_barridos_columns(df):
    """Detecta columnas de la sección de vacunados en barrido (4ta sección)"""

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
        "vacunados_barrido": {},  # 4ta sección: vacunados durante el barrido
        "renuentes": {},  # 3ra sección: renuentes/no vacunados
        "consolidation_needed": [],
    }

    # Detectar columnas de edad (buscar 4ta sección = vacunados en barrido)
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
            # Asignar 4ta columna como "vacunados en barrido" y 3ra como "renuentes"
            if len(found_cols) >= 4:  # 4ta sección
                result["vacunados_barrido"][age_range] = found_cols[3]
            if len(found_cols) >= 3:  # 3ra sección
                result["renuentes"][age_range] = found_cols[2]

            # Marcar para consolidación si es 60+ adicional
            if age_range in ["60-69", "70+"]:
                result["consolidation_needed"].extend(found_cols)

    return result


def process_individual_pre_barridos(df_individual, fecha_corte):
    """Procesa datos individuales PRE-barridos (sin duplicados)"""
    if df_individual.empty:
        return {"total": 0, "por_edad": {}, "por_municipio": {}}

    # Filtrar solo vacunas ANTES del primer barrido
    if fecha_corte and "FA UNICA" in df_individual.columns:
        mask_pre = df_individual["FA UNICA"] < fecha_corte
        df_pre = df_individual[mask_pre].copy()
        st.info(
            f"📅 Usando vacunas individuales antes de {fecha_corte.strftime('%d/%m/%Y')}"
        )
    else:
        df_pre = df_individual.copy()
        st.warning("⚠️ No hay fecha de corte - usando todos los datos individuales")

    result = {"total": len(df_pre), "por_edad": {}, "por_municipio": {}}

    if df_pre.empty:
        return result

    # Calcular edades actuales
    if "FechaNacimiento" in df_pre.columns:
        df_pre["edad_actual"] = df_pre["FechaNacimiento"].apply(calculate_current_age)
        df_pre["rango_edad"] = df_pre["edad_actual"].apply(classify_age_group)

        # Contar por rangos de edad
        age_counts = df_pre["rango_edad"].value_counts()
        for rango in RANGOS_EDAD.keys():
            result["por_edad"][rango] = age_counts.get(rango, 0)

    # Contar por municipio
    if "NombreMunicipioResidencia" in df_pre.columns:
        municipio_counts = df_pre["NombreMunicipioResidencia"].value_counts()
        result["por_municipio"] = municipio_counts.to_dict()

    return result


def process_barridos_data(df_barridos):
    """Procesa datos de barridos (vacunados + renuentes)"""
    if df_barridos.empty:
        return {
            "vacunados_barrido": {"total": 0, "por_edad": {}, "por_municipio": {}},
            "renuentes": {"total": 0, "por_edad": {}, "por_municipio": {}},
        }

    columns_info = detect_barridos_columns(df_barridos)

    result = {
        "vacunados_barrido": {"total": 0, "por_edad": {}, "por_municipio": {}},
        "renuentes": {"total": 0, "por_edad": {}, "por_municipio": {}},
        "columns_info": columns_info,
    }

    # Procesar vacunados en barrido (4ta sección)
    for rango, col_name in columns_info["vacunados_barrido"].items():
        if col_name in df_barridos.columns:
            valores = pd.to_numeric(df_barridos[col_name], errors="coerce").fillna(0)
            total_rango = valores.sum()
            result["vacunados_barrido"]["por_edad"][rango] = total_rango
            result["vacunados_barrido"]["total"] += total_rango

    # Procesar renuentes (3ra sección)
    for rango, col_name in columns_info["renuentes"].items():
        if col_name in df_barridos.columns:
            valores = pd.to_numeric(df_barridos[col_name], errors="coerce").fillna(0)
            total_rango = valores.sum()
            result["renuentes"]["por_edad"][rango] = total_rango
            result["renuentes"]["total"] += total_rango

    # Consolidar rangos 60+
    for section in ["vacunados_barrido", "renuentes"]:
        total_60_plus = 0
        for rango_60 in ["60+", "60-69", "70+"]:
            if rango_60 in result[section]["por_edad"]:
                total_60_plus += result[section]["por_edad"][rango_60]

        if total_60_plus > 0:
            result[section]["por_edad"]["60+"] = total_60_plus
            # Eliminar subrangos
            for subrango in ["60-69", "70+"]:
                result[section]["por_edad"].pop(subrango, None)

        # Procesar por municipio
        if "MUNICIPIO" in df_barridos.columns:
            municipio_totals = {}
            for municipio in df_barridos["MUNICIPIO"].unique():
                if pd.notna(municipio):
                    df_mun = df_barridos[df_barridos["MUNICIPIO"] == municipio]
                    total_municipio = 0

                    section_cols = (
                        columns_info[section] if section in columns_info else {}
                    )
                    for col_name in section_cols.values():
                        if col_name in df_mun.columns:
                            valores = pd.to_numeric(
                                df_mun[col_name], errors="coerce"
                            ).fillna(0)
                            total_municipio += valores.sum()

                    if total_municipio > 0:
                        municipio_totals[municipio] = total_municipio

            result[section]["por_municipio"] = municipio_totals

    return result


def process_population_data(df_population):
    """Procesa datos de población agrupando por municipio"""
    if df_population.empty:
        return {"por_municipio": {}, "total": 0}

    # Identificar columnas
    municipio_col = None
    total_col = None

    for col in df_population.columns:
        col_upper = str(col).upper()
        if "MUNICIPIO" in col_upper:
            municipio_col = col
        elif "TOTAL" in col_upper:
            total_col = col

    if not municipio_col or not total_col:
        return {"por_municipio": {}, "total": 0}

    # Agrupar por municipio sumando todas las EAPB
    poblacion_municipios = df_population.groupby(municipio_col)[total_col].sum()

    return {
        "por_municipio": poblacion_municipios.to_dict(),
        "total": poblacion_municipios.sum(),
    }


def main():
    """Función principal del dashboard"""
    st.title("🏥 Dashboard de Vacunación Fiebre Amarilla")
    st.markdown("**Departamento del Tolima - Combinación Temporal Sin Duplicados**")

    # Sidebar
    with st.sidebar:
        st.image(
            "https://via.placeholder.com/150x100/7D0F2B/FFFFFF?text=TOLIMA", width=150
        )
        st.title("Dashboard Vacunación")
        st.subheader("Fiebre Amarilla")
        st.markdown("---")
        st.markdown("**Lógica:** Combinación temporal")
        st.markdown("**PRE-emergencia:** Individuales")
        st.markdown("**DURANTE emergencia:** Barridos")
        st.markdown("---")
        st.markdown("Secretaría de Salud del Tolima © 2025")

    # Cargar datos
    st.markdown("### 📥 Cargando datos...")

    with st.spinner("Cargando datos..."):
        df_individual = load_individual_data()
        df_barridos = load_barridos_data()
        df_population = load_population_data()

    # Verificar datos mínimos
    if df_individual.empty and df_barridos.empty:
        st.error("❌ Sin datos suficientes para mostrar el dashboard")
        return

    # Determinar fecha de corte
    fecha_corte = determine_cutoff_date(df_barridos)

    if fecha_corte:
        st.success(
            f"📅 **Fecha de corte (inicio emergencia):** {fecha_corte.strftime('%d/%m/%Y')}"
        )
        st.info(
            f"🏥 **Individuales PRE-emergencia:** Antes de {fecha_corte.strftime('%d/%m/%Y')}"
        )
        st.info(
            f"🚨 **Barridos DURANTE emergencia:** Desde {fecha_corte.strftime('%d/%m/%Y')}"
        )
    else:
        st.warning("⚠️ No se pudo determinar fecha de corte")

    # Procesar datos
    st.markdown("### 📊 Procesando información...")

    with st.spinner("Procesando..."):
        # Datos PRE-emergencia (sin duplicados)
        individual_data = process_individual_pre_barridos(df_individual, fecha_corte)

        # Datos DURANTE emergencia
        barridos_data = process_barridos_data(df_barridos)

        # Datos de población
        population_data = process_population_data(df_population)

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


if __name__ == "__main__":
    main()
