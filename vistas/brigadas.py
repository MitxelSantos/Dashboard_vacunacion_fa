"""
vistas/brigadas.py - CÓDIGO COMPLETO
Vista de Brigadas Territoriales para el Dashboard de Vacunación
Incluye normalización completa de nombres de columnas y manejo de espacios
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
import re
import unicodedata
from src.data import load_and_combine_data


def normalize_column_name(col_name):
    """
    Normaliza completamente un nombre de columna
    - Elimina espacios al principio y final
    - Normaliza acentos y caracteres especiales
    - Convierte a mayúsculas para comparación
    - Elimina espacios múltiples
    """
    if pd.isna(col_name):
        return ""

    # Convertir a string y eliminar espacios extremos
    col_str = str(col_name).strip()

    # Normalizar acentos y caracteres especiales
    col_str = unicodedata.normalize("NFKD", col_str)
    col_str = "".join(c for c in col_str if not unicodedata.combining(c))

    # Convertir a mayúsculas
    col_str = col_str.upper()

    # Eliminar espacios múltiples y reemplazar por uno solo
    col_str = re.sub(r"\s+", " ", col_str)

    # Eliminar caracteres especiales excepto paréntesis y guiones
    col_str = re.sub(r"[^\w\s\(\)\-]", "", col_str)

    return col_str.strip()


def create_column_mapping_dict():
    """
    Crea un diccionario de mapeo para normalizar nombres de columnas
    """
    return {
        # Columnas de efectividad - todas las variaciones posibles
        "EFECTIVAS": [
            "Efectivas (E)",
            "EFECTIVAS (E)",
            "EFECTIVAS(E)",
            "EFECTIVAS",
            "EFECTIVA",
            " Efectivas (E)",
            "Efectivas (E) ",
            " EFECTIVAS (E) ",
            "  Efectivas (E)  ",
        ],
        "NO_EFECTIVAS": [
            "No Efectivas (NE)",
            "NO EFECTIVAS (NE)",
            "NO EFECTIVAS(NE)",
            "NO EFECTIVAS",
            "NO EFECTIVA",
            " No Efectivas (NE)",
            "No Efectivas (NE) ",
            " NO EFECTIVAS (NE) ",
            "  No Efectivas (NE)  ",
        ],
        "FALLIDAS": [
            "Fallidas (F)",
            "FALLIDAS (F)",
            "FALLIDAS(F)",
            "FALLIDAS",
            "FALLIDA",
            " Fallidas (F)",
            "Fallidas (F) ",
            " FALLIDAS (F) ",
            "  Fallidas (F)  ",
        ],
        # Columnas de población
        "TPE": [
            "TPE",
            "T.P.E",
            "T P E",
            "TOTAL POBLACION ENCONTRADA",
            " TPE",
            "TPE ",
            " TPE ",
            "  TPE  ",
        ],
        "TPVP": [
            "TPVP",
            "T.P.V.P",
            "TOTAL POBLACION VACUNADA PREVIA",
            " TPVP",
            "TPVP ",
            " TPVP ",
            "  TPVP  ",
        ],
        "TPNVP": [
            "TPNVP",
            "T.P.N.V.P",
            "TOTAL POBLACION NO VACUNADA",
            " TPNVP",
            "TPNVP ",
            " TPNVP ",
            "  TPNVP  ",
        ],
        "TPVB": [
            "TPVB",
            "T.P.V.B",
            "TOTAL POBLACION VACUNADA BRIGADA",
            " TPVB",
            "TPVB ",
            " TPVB ",
            "  TPVB  ",
        ],
        "CASA_RENUENTE": [
            "Casa renuente",
            "CASA RENUENTE",
            "CASAS RENUENTES",
            "RENUENTE",
            " Casa renuente",
            "Casa renuente ",
            " CASA RENUENTE ",
            "  Casa renuente  ",
        ],
        # Información básica
        "FECHA": [
            "FECHA",
            "Date",
            "DATE",
            "Fecha",
            " FECHA",
            "FECHA ",
            " FECHA ",
            "  FECHA  ",
        ],
        "MUNICIPIO": [
            "MUNICIPIO",
            "Municipio",
            "MPIO",
            " MUNICIPIO",
            "MUNICIPIO ",
            " MUNICIPIO ",
            "  MUNICIPIO  ",
        ],
        "VEREDAS": [
            "VEREDAS",
            "Veredas",
            "VEREDA",
            "Vereda",
            " VEREDAS",
            "VEREDAS ",
            " VEREDAS ",
            "  VEREDAS  ",
        ],
    }


def safe_column_access(df, column_names, default_value=0):
    """
    Accede seguramente a una columna considerando posibles variaciones de nombres

    Args:
        df: DataFrame
        column_names: Lista de posibles nombres de columna o string único
        default_value: Valor por defecto si no se encuentra la columna

    Returns:
        Serie de pandas o valor por defecto
    """
    if isinstance(column_names, str):
        column_names = [column_names]

    # Buscar la primera columna que exista
    for col_name in column_names:
        # Buscar coincidencia exacta
        if col_name in df.columns:
            return df[col_name]

        # Buscar coincidencia sin importar espacios extremos
        for df_col in df.columns:
            if str(df_col).strip() == str(col_name).strip():
                return df[df_col]

        # Buscar coincidencia case-insensitive
        for df_col in df.columns:
            if str(df_col).strip().upper() == str(col_name).strip().upper():
                return df[df_col]

        # Buscar coincidencia normalizada
        col_normalized = normalize_column_name(col_name)
        for df_col in df.columns:
            if normalize_column_name(df_col) == col_normalized:
                return df[df_col]

    # Si no se encuentra, devolver serie con valor por defecto
    return pd.Series([default_value] * len(df), index=df.index)


def normalize_dataframe_columns(df):
    """
    Normaliza todos los nombres de columnas de un DataFrame
    y crea un mapeo de columnas estándar
    """
    if df.empty:
        return df, {}

    # Crear copia del DataFrame
    df_normalized = df.copy()

    # Primero, limpiar nombres de columnas (eliminar espacios extremos)
    df_normalized.columns = [str(col).strip() for col in df_normalized.columns]

    # Crear mapeo de columnas
    column_mapping = create_column_mapping_dict()
    standard_mapping = {}

    # Buscar coincidencias para cada tipo de columna estándar
    for standard_name, possible_names in column_mapping.items():
        for possible_name in possible_names:
            # Buscar coincidencia exacta (case insensitive y sin espacios extremos)
            for col in df_normalized.columns:
                if col.strip().upper() == possible_name.strip().upper():
                    standard_mapping[standard_name] = col
                    break

            if standard_name in standard_mapping:
                break

    # Crear alias para columnas estándar
    for standard_name, actual_column in standard_mapping.items():
        if (
            standard_name == "EFECTIVAS"
            and "Efectivas (E)" not in df_normalized.columns
        ):
            df_normalized["Efectivas (E)"] = df_normalized[actual_column]
        elif (
            standard_name == "NO_EFECTIVAS"
            and "No Efectivas (NE)" not in df_normalized.columns
        ):
            df_normalized["No Efectivas (NE)"] = df_normalized[actual_column]
        elif (
            standard_name == "FALLIDAS" and "Fallidas (F)" not in df_normalized.columns
        ):
            df_normalized["Fallidas (F)"] = df_normalized[actual_column]
        elif (
            standard_name == "CASA_RENUENTE"
            and "Casa renuente" not in df_normalized.columns
        ):
            df_normalized["Casa renuente"] = df_normalized[actual_column]

    return df_normalized, standard_mapping


def create_sample_brigadas_data():
    """
    Crea datos de ejemplo para demostrar la funcionalidad
    """
    np.random.seed(42)  # Para resultados reproducibles

    # Generar fechas de ejemplo
    base_date = datetime(2024, 1, 15)
    dates = [base_date + timedelta(days=i) for i in range(0, 60, 2)]  # 30 brigadas

    municipios = [
        "IBAGUÉ",
        "ESPINAL",
        "HONDA",
        "MELGAR",
        "CHAPARRAL",
        "LÍBANO",
        "PURIFICACIÓN",
        "MARIQUITA",
        "CAJAMARCA",
        "ROVIRA",
    ]

    veredas = [
        "Centro",
        "La Esperanza",
        "El Progreso",
        "San José",
        "Las Flores",
        "Villa Nueva",
        "El Carmen",
        "Santa Rosa",
        "La Libertad",
        "Buenos Aires",
    ]

    sample_data = []

    for i, fecha in enumerate(dates):
        municipio = np.random.choice(municipios)
        vereda = np.random.choice(veredas)

        # Generar datos realistas
        tpe = np.random.randint(20, 150)  # Total Población Encontrada
        tpvp = int(tpe * np.random.uniform(0.1, 0.4))  # Ya vacunados (10-40%)
        tpnvp = int(tpe * np.random.uniform(0.05, 0.2))  # No vacunados (5-20%)
        tpvb = max(0, tpe - tpvp - tpnvp)  # Vacunados por brigada

        efectivas = np.random.randint(15, min(50, tpvb + 10))
        no_efectivas = np.random.randint(2, 15)
        fallidas = np.random.randint(0, 8)
        casa_renuente = np.random.randint(0, 10)

        # Generar distribución por edad (realista)
        edad_data = {
            "< 1 AÑO": np.random.poisson(2),
            "1-5 AÑOS": np.random.poisson(8),
            "6-10 AÑOS": np.random.poisson(12),
            "11-20 AÑOS": np.random.poisson(15),
            "21-30 AÑOS": np.random.poisson(20),
            "31-40 AÑOS": np.random.poisson(18),
            "41-50 AÑOS": np.random.poisson(16),
            "51-59 AÑOS": np.random.poisson(12),
            "60 Y MAS": np.random.poisson(10),
        }

        record = {
            "FECHA": fecha,
            "MUNICIPIO": municipio,
            "VEREDAS": vereda,
            "Efectivas (E)": efectivas,
            "No Efectivas (NE)": no_efectivas,
            "Fallidas (F)": fallidas,
            "Casa renuente": casa_renuente,
            "TPE": tpe,
            "TPVP": tpvp,
            "TPNVP": tpnvp,
            "TPVB": tpvb,
            **edad_data,
        }

        sample_data.append(record)

    return pd.DataFrame(sample_data)


def load_brigadas_data(file_path="data/Resumen.xlsx"):
    """
    Carga los datos de brigadas con manejo robusto de archivos faltantes
    y normalización completa de columnas
    """
    try:
        if not Path(file_path).exists():
            st.warning(f"⚠️ File not found: {file_path}")
            return None

        df = pd.read_excel(
            file_path,
            sheet_name="Vacunacion",
            usecols=lambda x: "fecha" in x.lower() or "municipio" in x.lower(),
        )

        return df if len(df) > 0 else None

    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None


def process_real_brigadas_data(df):
    """
    Procesa datos reales con normalización completa y acceso seguro a columnas
    """
    df_clean = df.copy()

    # Convertir fechas con acceso seguro
    fecha_series = safe_column_access(
        df_clean, ["FECHA", "Fecha", "DATE", "fecha"], pd.NaT
    )
    if not fecha_series.isna().all():
        df_clean["FECHA"] = pd.to_datetime(fecha_series, errors="coerce")

    # Limpiar nombres de municipios y veredas con acceso seguro
    municipio_series = safe_column_access(
        df_clean, ["MUNICIPIO", "Municipio", "MPIO"], "Sin dato"
    )
    df_clean["MUNICIPIO"] = municipio_series.astype(str).str.strip().str.title()

    veredas_series = safe_column_access(
        df_clean, ["VEREDAS", "Veredas", "VEREDA", "Vereda"], "Sin especificar"
    )
    df_clean["VEREDAS"] = veredas_series.fillna("Sin especificar")

    # Normalizar valores numéricos principales con acceso seguro
    main_numeric_columns = [
        ["Efectivas (E)", "EFECTIVAS (E)", "Efectivas(E)", "EFECTIVAS"],
        ["No Efectivas (NE)", "NO EFECTIVAS (NE)", "No Efectivas(NE)", "NO EFECTIVAS"],
        ["Fallidas (F)", "FALLIDAS (F)", "Fallidas(F)", "FALLIDAS"],
        ["Casa renuente", "CASA RENUENTE", "Casa Renuente", "CASAS RENUENTES"],
        ["TPE"],
        ["TPVP"],
        ["TPNVP"],
        ["TPVB"],
    ]

    for col_variations in main_numeric_columns:
        series = safe_column_access(df_clean, col_variations, 0)
        # Usar el primer nombre como estándar
        standard_name = col_variations[0]
        df_clean[standard_name] = pd.to_numeric(series, errors="coerce").fillna(0)

    # Normalizar columnas de grupos de edad
    age_patterns = [
        "< 1 AÑO",
        "1-5 AÑOS",
        "6-10 AÑOS",
        "11-20 AÑOS",
        "21-30 AÑOS",
        "31-40 AÑOS",
        "41-50 AÑOS",
        "51-59 AÑOS",
        "60 Y MAS",
        "60-69 AÑOS",
        "70 AÑOS",
    ]

    for col in df_clean.columns:
        col_normalized = normalize_column_name(col)
        for pattern in age_patterns:
            pattern_normalized = normalize_column_name(pattern)
            if pattern_normalized in col_normalized:
                df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce").fillna(0)
                break

    return df_clean


def calculate_brigadas_metrics(df):
    """
    Calcula métricas principales con acceso seguro a columnas
    """
    if df.empty:
        return create_empty_metrics()

    def safe_sum(column_variations):
        """Suma segura de una columna con variaciones de nombres"""
        return safe_column_access(df, column_variations, 0).sum()

    def safe_nunique(column_variations):
        """Conteo único seguro de una columna con variaciones"""
        return safe_column_access(df, column_variations, "Sin dato").nunique()

    def safe_date_min_max(column_variations):
        """Obtiene min/max de fecha de manera segura"""
        fecha_series = safe_column_access(df, column_variations, pd.NaT)
        if not fecha_series.isna().all():
            return fecha_series.min(), fecha_series.max()
        return None, None

    fecha_inicio, fecha_fin = safe_date_min_max(["FECHA", "Fecha", "DATE"])

    return {
        "total_brigadas": len(df),
        "municipios_visitados": safe_nunique(["MUNICIPIO", "Municipio"]),
        "veredas_visitadas": safe_nunique(["VEREDAS", "Veredas"]),
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "total_efectivas": safe_sum(["Efectivas (E)", "EFECTIVAS (E)", "EFECTIVAS"]),
        "total_no_efectivas": safe_sum(
            ["No Efectivas (NE)", "NO EFECTIVAS (NE)", "NO EFECTIVAS"]
        ),
        "total_fallidas": safe_sum(["Fallidas (F)", "FALLIDAS (F)", "FALLIDAS"]),
        "casas_renuentes": safe_sum(
            ["Casa renuente", "CASA RENUENTE", "CASAS RENUENTES"]
        ),
        "poblacion_encontrada": safe_sum(["TPE"]),
        "poblacion_ya_vacunada": safe_sum(["TPVP"]),
        "poblacion_no_vacuna": safe_sum(["TPNVP"]),
        "poblacion_vacunada_brigada": safe_sum(["TPVB"]),
    }


def create_empty_metrics():
    """Crea métricas vacías por defecto"""
    return {
        "total_brigadas": 0,
        "municipios_visitados": 0,
        "veredas_visitadas": 0,
        "fecha_inicio": None,
        "fecha_fin": None,
        "total_efectivas": 0,
        "total_no_efectivas": 0,
        "total_fallidas": 0,
        "casas_renuentes": 0,
        "poblacion_encontrada": 0,
        "poblacion_ya_vacunada": 0,
        "poblacion_no_vacuna": 0,
        "poblacion_vacunada_brigada": 0,
    }


def create_effectiveness_analysis(df):
    """
    Análisis de efectividad con acceso seguro a columnas
    """
    if df.empty:
        return df

    df_result = df.copy()

    try:
        # Acceso seguro a columnas para cálculos
        efectivas = safe_column_access(
            df_result, ["Efectivas (E)", "EFECTIVAS (E)", "EFECTIVAS"], 0
        )
        no_efectivas = safe_column_access(
            df_result, ["No Efectivas (NE)", "NO EFECTIVAS (NE)", "NO EFECTIVAS"], 0
        )
        fallidas = safe_column_access(
            df_result, ["Fallidas (F)", "FALLIDAS (F)", "FALLIDAS"], 0
        )
        total_intentos = efectivas + no_efectivas + fallidas

        df_result["tasa_efectividad"] = np.where(
            total_intentos > 0, (efectivas / total_intentos * 100).round(2), 0
        )

        tpe = safe_column_access(df_result, ["TPE"], 0)
        tpvb = safe_column_access(df_result, ["TPVB"], 0)
        tpvp = safe_column_access(df_result, ["TPVP"], 0)
        casa_renuente = safe_column_access(
            df_result, ["Casa renuente", "CASA RENUENTE"], 0
        )

        df_result["tasa_aceptacion"] = np.where(tpe > 0, (tpvb / tpe * 100).round(2), 0)
        df_result["resistencia_casa"] = np.where(
            tpe > 0, (casa_renuente / tpe * 100).round(2), 0
        )
        df_result["cobertura_previa"] = np.where(
            tpe > 0, (tpvp / tpe * 100).round(2), 0
        )

        poblacion_susceptible = tpe - tpvp
        df_result["eficiencia_brigada"] = np.where(
            poblacion_susceptible > 0, (tpvb / poblacion_susceptible * 100).round(2), 0
        )

    except Exception as e:
        st.warning(f"⚠️ Error calculando efectividad: {str(e)}")

    return df_result


def show_brigadas_overview(df, colors):
    """
    Muestra resumen general de brigadas con acceso seguro
    """
    st.subheader("📊 Resumen General de Brigadas")

    if df.empty:
        st.warning("⚠️ No hay datos de brigadas para mostrar")
        return

    metrics = calculate_brigadas_metrics(df)

    # Métricas principales en 4 columnas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Brigadas",
            f"{metrics['total_brigadas']:,}".replace(",", "."),
            delta=f"{metrics['municipios_visitados']} municipios",
        )

    with col2:
        st.metric(
            "Población Encontrada",
            f"{metrics['poblacion_encontrada']:,}".replace(",", "."),
            delta=f"{metrics['veredas_visitadas']} veredas",
        )

    with col3:
        total_efectivas = metrics["total_efectivas"]
        total_intentos = (
            metrics["total_efectivas"]
            + metrics["total_no_efectivas"]
            + metrics["total_fallidas"]
        )
        efectividad_global = (
            (total_efectivas / total_intentos * 100) if total_intentos > 0 else 0
        )

        st.metric(
            "Efectividad Global",
            f"{efectividad_global:.1f}%",
            delta=f"{total_efectivas} efectivas",
        )

    with col4:
        poblacion_encontrada = metrics["poblacion_encontrada"]
        poblacion_vacunada = metrics["poblacion_vacunada_brigada"]
        cobertura_brigadas = (
            (poblacion_vacunada / poblacion_encontrada * 100)
            if poblacion_encontrada > 0
            else 0
        )

        st.metric(
            "Cobertura Brigadas",
            f"{cobertura_brigadas:.1f}%",
            delta=f"{poblacion_vacunada} vacunados",
        )


def show_temporal_brigadas_analysis(df, colors):
    """
    Análisis temporal de brigadas con acceso seguro
    """
    st.subheader("📅 Evolución Temporal de Brigadas")

    if df.empty:
        st.warning("⚠️ No hay datos para análisis temporal")
        return

    fecha_series = safe_column_access(df, ["FECHA", "Fecha", "DATE"], pd.NaT)
    if fecha_series.isna().all():
        st.warning("⚠️ No hay datos de fecha válidos para análisis temporal")
        return

    try:
        # Verificar qué columnas están disponibles
        available_cols = []
        possible_cols = [
            ["Efectivas (E)", "EFECTIVAS (E)", "EFECTIVAS"],
            ["No Efectivas (NE)", "NO EFECTIVAS (NE)", "NO EFECTIVAS"],
            ["TPE"],
            ["TPVB"],
        ]

        for col_variations in possible_cols:
            series = safe_column_access(df, col_variations, 0)
            if series.sum() > 0:  # Solo incluir si tiene datos
                col_name = col_variations[0]  # Usar nombre estándar
                available_cols.append(col_name)

        if not available_cols:
            st.warning("⚠️ No hay columnas numéricas para análisis temporal")
            return

        # Crear DataFrame temporal con fecha
        df_temp = df.copy()
        df_temp["FECHA"] = fecha_series

        # Agrupar por fecha solo con columnas disponibles
        agg_dict = {}
        for col_name in available_cols:
            if col_name == "Efectivas (E)":
                agg_dict["Efectivas (E)"] = (
                    safe_column_access(df_temp, ["Efectivas (E)", "EFECTIVAS"], 0)
                    .groupby(df_temp["FECHA"])
                    .sum()
                )
            elif col_name == "No Efectivas (NE)":
                agg_dict["No Efectivas (NE)"] = (
                    safe_column_access(
                        df_temp, ["No Efectivas (NE)", "NO EFECTIVAS"], 0
                    )
                    .groupby(df_temp["FECHA"])
                    .sum()
                )
            elif col_name == "TPE":
                agg_dict["TPE"] = (
                    safe_column_access(df_temp, ["TPE"], 0)
                    .groupby(df_temp["FECHA"])
                    .sum()
                )
            elif col_name == "TPVB":
                agg_dict["TPVB"] = (
                    safe_column_access(df_temp, ["TPVB"], 0)
                    .groupby(df_temp["FECHA"])
                    .sum()
                )

        # Crear temporal_data manualmente
        fechas_unicas = sorted(df_temp["FECHA"].dropna().unique())
        temporal_data = pd.DataFrame({"FECHA": fechas_unicas})

        for col_name in available_cols:
            if col_name in ["Efectivas (E)", "EFECTIVAS"]:
                col_data = []
                for fecha in fechas_unicas:
                    mask = df_temp["FECHA"] == fecha
                    valores = safe_column_access(
                        df_temp[mask], ["Efectivas (E)", "EFECTIVAS"], 0
                    )
                    col_data.append(valores.sum())
                temporal_data["Efectivas (E)"] = col_data
            elif col_name in ["TPE"]:
                col_data = []
                for fecha in fechas_unicas:
                    mask = df_temp["FECHA"] == fecha
                    valores = safe_column_access(df_temp[mask], ["TPE"], 0)
                    col_data.append(valores.sum())
                temporal_data["TPE"] = col_data
            elif col_name in ["TPVB"]:
                col_data = []
                for fecha in fechas_unicas:
                    mask = df_temp["FECHA"] == fecha
                    valores = safe_column_access(df_temp[mask], ["TPVB"], 0)
                    col_data.append(valores.sum())
                temporal_data["TPVB"] = col_data

        # Crear gráfico con las columnas disponibles
        fig = go.Figure()

        color_map = {
            "Efectivas (E)": colors.get("primary", "#7D0F2B"),
            "TPE": colors.get("secondary", "#F2A900"),
            "TPVB": colors.get("success", "#509E2F"),
        }

        for col in temporal_data.columns:
            if col != "FECHA" and col in color_map:
                fig.add_trace(
                    go.Scatter(
                        x=temporal_data["FECHA"],
                        y=temporal_data[col],
                        mode="lines+markers",
                        name=col,
                        line=dict(color=color_map[col], width=3),
                    )
                )

        fig.update_layout(
            title="Evolución Temporal de Brigadas de Vacunación",
            xaxis_title="Fecha",
            yaxis_title="Número de Personas",
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=500,
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error creando gráfico temporal: {str(e)}")

        # Fallback: mostrar tabla básica
        st.info("📊 Mostrando tabla de datos en su lugar:")
        fecha_series = safe_column_access(df, ["FECHA", "Fecha"], pd.NaT)
        if not fecha_series.isna().all():
            fecha_counts = fecha_series.value_counts().reset_index()
            fecha_counts.columns = ["Fecha", "Número de Brigadas"]
            st.dataframe(fecha_counts, use_container_width=True)


def show_territorial_analysis(df, colors):
    """
    Análisis territorial por municipios con acceso seguro
    """
    st.subheader("🗺️ Análisis Territorial")

    if df.empty:
        st.warning("⚠️ No hay datos territoriales para mostrar")
        return

    col1, col2 = st.columns(2)

    with col1:
        try:
            municipio_series = safe_column_access(
                df, ["MUNICIPIO", "Municipio"], "Sin dato"
            )
            tpe_series = safe_column_access(df, ["TPE"], 0)
            tpvb_series = safe_column_access(df, ["TPVB"], 0)
            efectivas_series = safe_column_access(df, ["Efectivas (E)", "EFECTIVAS"], 0)

            if municipio_series.nunique() > 1 and tpe_series.sum() > 0:
                # Crear DataFrame para análisis por municipio
                municipio_data = pd.DataFrame(
                    {
                        "MUNICIPIO": municipio_series,
                        "TPE": tpe_series,
                        "TPVB": tpvb_series,
                        "Efectivas (E)": efectivas_series,
                    }
                )

                municipio_stats = (
                    municipio_data.groupby("MUNICIPIO").sum().reset_index()
                )

                municipio_stats["efectividad"] = np.where(
                    municipio_stats["TPE"] > 0,
                    (municipio_stats["TPVB"] / municipio_stats["TPE"] * 100).round(2),
                    0,
                )

                municipio_stats = municipio_stats.sort_values(
                    "efectividad", ascending=False
                ).head(10)

                fig = px.bar(
                    municipio_stats,
                    x="MUNICIPIO",
                    y="efectividad",
                    title="Top 10 Municipios por Efectividad",
                    color_discrete_sequence=[colors.get("primary", "#7D0F2B")],
                )

                fig.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white", xaxis_tickangle=45
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("💡 Datos insuficientes para análisis por municipio")

                # Mostrar al menos conteo por municipio
                if municipio_series.nunique() > 1:
                    municipio_counts = municipio_series.value_counts().reset_index()
                    municipio_counts.columns = ["Municipio", "Número de Brigadas"]
                    st.dataframe(municipio_counts.head(10), use_container_width=True)

        except Exception as e:
            st.error(f"❌ Error en análisis territorial: {str(e)}")

    with col2:
        try:
            # Distribución de resultados con acceso seguro
            efectivas_total = safe_column_access(
                df, ["Efectivas (E)", "EFECTIVAS"], 0
            ).sum()
            no_efectivas_total = safe_column_access(
                df, ["No Efectivas (NE)", "NO EFECTIVAS"], 0
            ).sum()
            fallidas_total = safe_column_access(
                df, ["Fallidas (F)", "FALLIDAS"], 0
            ).sum()

            if efectivas_total + no_efectivas_total + fallidas_total > 0:
                resultados_data = pd.DataFrame(
                    {
                        "Resultado": ["Efectivas", "No Efectivas", "Fallidas"],
                        "Cantidad": [
                            efectivas_total,
                            no_efectivas_total,
                            fallidas_total,
                        ],
                    }
                )

                fig = px.pie(
                    resultados_data,
                    names="Resultado",
                    values="Cantidad",
                    title="Distribución de Resultados de Brigadas",
                )

                fig.update_layout(plot_bgcolor="white", paper_bgcolor="white")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("💡 Datos de resultados no disponibles")

        except Exception as e:
            st.error(f"❌ Error en gráfico de resultados: {str(e)}")


def show_demographic_brigadas_analysis(df, colors):
    """
    Análisis demográfico de brigadas por grupos de edad con acceso seguro
    """
    st.subheader("👥 Análisis Demográfico por Grupos de Edad")

    if df.empty:
        st.warning("⚠️ No hay datos demográficos para mostrar")
        return

    # Buscar columnas de grupos de edad de manera más flexible
    age_columns = []
    for col in df.columns:
        col_normalized = normalize_column_name(col)
        if any(
            age_pattern in col_normalized
            for age_pattern in ["AÑO", "ANOS", "EDAD", "MAS", "MAYOR"]
        ):
            age_columns.append(col)

    if age_columns:
        st.info(f"📊 Grupos de edad encontrados: {len(age_columns)}")

        age_data = []
        for col in age_columns:
            try:
                numeric_values = pd.to_numeric(df[col], errors="coerce").fillna(0)
                total = numeric_values.sum()

                if total > 0:
                    age_data.append({"Grupo_Edad": col, "Total": int(total)})

            except Exception as e:
                st.warning(f"⚠️ Error procesando columna {col}: {str(e)}")
                continue

        if age_data:
            age_df = pd.DataFrame(age_data)
            age_df = age_df.sort_values("Total", ascending=False)

            try:
                fig = px.bar(
                    age_df,
                    x="Grupo_Edad",
                    y="Total",
                    title="Distribución por Grupos de Edad",
                    color_discrete_sequence=[colors.get("secondary", "#F2A900")],
                )

                fig.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    xaxis_tickangle=45,
                    height=500,
                )

                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(age_df, use_container_width=True)

            except Exception as e:
                st.error(f"❌ Error creando gráfico: {str(e)}")
                st.dataframe(age_df, use_container_width=True)
        else:
            st.info("💡 No se encontraron datos válidos de grupos de edad")
    else:
        st.info("💡 No se encontraron columnas de grupos de edad")

        # Mostrar información de debug
        with st.expander("🔍 Columnas disponibles"):
            st.write("Columnas encontradas en el dataset:")
            for i, col in enumerate(df.columns, 1):
                st.write(f"{i:2d}. {col}")


def test_column_normalization():
    """
    Función de prueba para verificar que la normalización funciona
    """
    st.markdown("### 🧪 Prueba de Normalización de Columnas")

    # Crear DataFrame de prueba con columnas problemáticas
    test_data = {
        " Efectivas (E)": [10, 20, 30],  # Espacio al principio
        "No Efectivas (NE) ": [5, 10, 15],  # Espacio al final
        " Casa renuente ": [1, 2, 3],  # Espacios en ambos lados
        "TPE": [50, 100, 150],  # Normal
        " TPVB ": [25, 50, 75],  # Espacios y mayúsculas
    }

    df_test = pd.DataFrame(test_data)

    st.write("**DataFrame original:**")
    st.write(f"Columnas: {list(df_test.columns)}")
    st.dataframe(df_test)

    # Normalizar
    df_normalized, mapping = normalize_dataframe_columns(df_test)

    st.write("**DataFrame normalizado:**")
    st.write(f"Columnas: {list(df_normalized.columns)}")
    st.dataframe(df_normalized)

    st.write("**Mapeo de columnas:**")
    for standard, actual in mapping.items():
        st.write(f"• {standard} → '{actual}'")

    # Probar acceso seguro
    st.write("**Prueba de acceso seguro:**")
    efectivas = safe_column_access(
        df_normalized, ["Efectivas (E)", "EFECTIVAS (E)", " Efectivas (E)"], 0
    )
    st.write(f"Efectivas encontradas: {efectivas.tolist()}")

    return df_normalized


def show_file_requirements():
    """
    Muestra los requisitos del archivo y cómo estructurarlo
    """
    st.markdown("### 📋 Requisitos del Archivo de Brigadas")

    st.info(
        """
    **Archivo requerido:** `data/Resumen.xlsx`
    
    **Estructura esperada:**
    - **Hoja:** 'Vacunacion'
    - **Columnas mínimas requeridas:**
    """
    )

    required_structure = pd.DataFrame(
        {
            "Columna": [
                "FECHA",
                "MUNICIPIO",
                "VEREDAS",
                "Efectivas (E)",
                "No Efectivas (NE)",
                "Fallidas (F)",
                "TPE",
                "TPVP",
                "TPNVP",
                "TPVB",
                "Casa renuente",
                "< 1 AÑO",
                "1-5 AÑOS",
                "6-10 AÑOS",
                "11-20 AÑOS",
                "21-30 AÑOS",
                "31-40 AÑOS",
                "41-50 AÑOS",
                "51-59 AÑOS",
                "60 Y MAS",
            ],
            "Descripción": [
                "Fecha de la brigada",
                "Nombre del municipio",
                "Nombre de la vereda",
                "Visitas efectivas",
                "Visitas no efectivas",
                "Visitas fallidas",
                "Total población encontrada",
                "Total población ya vacunada",
                "Total población no vacunada",
                "Total población vacunada por brigada",
                "Casas renuentes",
                "Menores de 1 año",
                "1 a 5 años",
                "6 a 10 años",
                "11 a 20 años",
                "21 a 30 años",
                "31 a 40 años",
                "41 a 50 años",
                "51 a 59 años",
                "60 años y más",
            ],
            "Tipo": [
                "Fecha",
                "Texto",
                "Texto",
                "Número",
                "Número",
                "Número",
                "Número",
                "Número",
                "Número",
                "Número",
                "Número",
                "Número",
                "Número",
                "Número",
                "Número",
                "Número",
                "Número",
                "Número",
                "Número",
                "Número",
            ],
        }
    )

    st.dataframe(required_structure, use_container_width=True)


def mostrar_brigadas():
    df_combined, df_aseguramiento, fecha_corte = load_and_combine_data(
        "data/Resumen.xlsx",
        "data/vacunacion_fa.csv",
        "data/Poblacion_aseguramiento.xlsx",
    )

    st.header("Análisis de Brigadas de Emergencia")

    # Solo datos post emergencia
    df_brigadas = df_combined[df_combined["Fecha_Aplicacion"] >= fecha_corte]

    # Métricas de brigadas
    total_brigadas = len(df_brigadas)
    cobertura_total = (total_brigadas / df_aseguramiento["Total"].sum() * 100).round(2)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Vacunados en Brigadas", f"{total_brigadas:,}")
    with col2:
        st.metric("Cobertura Alcanzada", f"{cobertura_total}%")

    # Avance por municipio
    avance_municipal = (
        df_brigadas.groupby("Municipio").size().reset_index(name="Vacunados")
    )
    fig_avance = px.bar(
        avance_municipal.sort_values("Vacunados", ascending=False),
        x="Municipio",
        y="Vacunados",
        title="Avance por Municipio en Brigadas",
    )
    st.plotly_chart(fig_avance)
