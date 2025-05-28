"""
src/data/brigadas_loader.py - VERSIÓN CORREGIDA
"""

import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path
import os
from datetime import datetime
import re
import unicodedata


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
        ],
        "TPVP": [
            "TPVP",
            "T.P.V.P",
            "TOTAL POBLACION VACUNADA PREVIA",
            " TPVP",
            "TPVP ",
            " TPVP ",
        ],
        "TPNVP": [
            "TPNVP",
            "T.P.N.V.P",
            "TOTAL POBLACION NO VACUNADA",
            " TPNVP",
            "TPNVP ",
            " TPNVP ",
        ],
        "TPVB": [
            "TPVB",
            "T.P.V.B",
            "TOTAL POBLACION VACUNADA BRIGADA",
            " TPVB",
            "TPVB ",
            " TPVB ",
        ],
        "CASA_RENUENTE": [
            "Casa renuente",
            "CASA RENUENTE",
            "CASAS RENUENTES",
            "RENUENTE",
            " Casa renuente",
            "Casa renuente ",
            " CASA RENUENTE ",
        ],
        # Información básica
        "FECHA": ["FECHA", "Date", "DATE", "Fecha", " FECHA", "FECHA ", " FECHA "],
        "MUNICIPIO": [
            "MUNICIPIO",
            "Municipio",
            "MPIO",
            " MUNICIPIO",
            "MUNICIPIO ",
            " MUNICIPIO ",
        ],
        "VEREDAS": [
            "VEREDAS",
            "Veredas",
            "VEREDA",
            "Vereda",
            " VEREDAS",
            "VEREDAS ",
            " VEREDAS ",
        ],
    }


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
            # Buscar coincidencia exacta (case insensitive)
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

        # Buscar coincidencia sin importar espacios
        for df_col in df.columns:
            if str(df_col).strip() == str(col_name).strip():
                return df[df_col]

        # Buscar coincidencia case-insensitive
        for df_col in df.columns:
            if str(df_col).strip().upper() == str(col_name).strip().upper():
                return df[df_col]

    # Si no se encuentra, devolver serie con valor por defecto
    return pd.Series([default_value] * len(df), index=df.index)


def load_brigadas_excel(file_path="data/Resumen.xlsx"):
    """
    Carga el archivo Excel de brigadas con normalización completa
    """
    try:
        full_path = Path(file_path)

        if not full_path.exists():
            st.warning(f"⚠️ Archivo no encontrado: {file_path}")
            return {}

        excel_data = {}

        with pd.ExcelFile(full_path) as excel_file:
            st.info(f"📄 Hojas encontradas: {', '.join(excel_file.sheet_names)}")

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(full_path, sheet_name=sheet_name)

                # NORMALIZAR COLUMNAS INMEDIATAMENTE
                df, column_mapping = normalize_dataframe_columns(df)

                excel_data[sheet_name] = df
                st.success(
                    f"✅ Cargada hoja '{sheet_name}': {len(df)} filas, {len(df.columns)} columnas"
                )

                # Mostrar mapeo de columnas si es la hoja de Vacunacion
                if sheet_name == "Vacunacion" and column_mapping:
                    st.info("🔄 **Columnas mapeadas:**")
                    for standard, actual in column_mapping.items():
                        st.write(f"  • {standard} → '{actual}'")

        return excel_data

    except Exception as e:
        st.error(f"❌ Error cargando Excel de brigadas: {str(e)}")
        return {}


def process_brigadas_data(df):
    """
    Procesa y normaliza los datos de brigadas con acceso seguro a columnas
    """
    if df.empty:
        return df

    df_clean = df.copy()

    try:
        # Normalizar columnas primero
        df_clean, column_mapping = normalize_dataframe_columns(df_clean)

        # Convertir fecha con acceso seguro
        fecha_series = safe_column_access(
            df_clean, ["FECHA", "Fecha", "DATE", "fecha"], pd.NaT
        )
        if not fecha_series.isna().all():
            df_clean["FECHA"] = pd.to_datetime(fecha_series, errors="coerce")

        # Limpiar y normalizar nombres con acceso seguro
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
            [
                "No Efectivas (NE)",
                "NO EFECTIVAS (NE)",
                "No Efectivas(NE)",
                "NO EFECTIVAS",
            ],
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

        # Normalizar todas las columnas de grupos de edad con acceso seguro
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

        age_columns = []
        for col in df_clean.columns:
            col_normalized = normalize_column_name(col)
            for pattern in age_patterns:
                pattern_normalized = normalize_column_name(pattern)
                if pattern_normalized in col_normalized:
                    age_columns.append(col)
                    break

        for col in age_columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce").fillna(0)

        # Calcular métricas derivadas con acceso seguro
        df_clean = calculate_derived_metrics_safe(df_clean)

        st.success(f"✅ Datos procesados: {len(df_clean)} brigadas")
        return df_clean

    except Exception as e:
        st.error(f"❌ Error procesando datos: {str(e)}")
        return df


def calculate_derived_metrics_safe(df):
    """
    Calcula métricas derivadas con acceso seguro a columnas
    """
    df_calc = df.copy()

    try:
        # Acceso seguro a columnas para tasa de efectividad
        efectivas = safe_column_access(
            df_calc, ["Efectivas (E)", "EFECTIVAS (E)", "Efectivas", "EFECTIVAS"], 0
        )
        no_efectivas = safe_column_access(
            df_calc,
            ["No Efectivas (NE)", "NO EFECTIVAS (NE)", "No Efectivas", "NO EFECTIVAS"],
            0,
        )
        fallidas = safe_column_access(
            df_calc, ["Fallidas (F)", "FALLIDAS (F)", "Fallidas", "FALLIDAS"], 0
        )

        total_intentos = efectivas + no_efectivas + fallidas
        df_calc["tasa_efectividad"] = np.where(
            total_intentos > 0, (efectivas / total_intentos * 100).round(2), 0
        )

        # Acceso seguro para otras métricas
        tpe = safe_column_access(df_calc, ["TPE", "T.P.E"], 0)
        tpvb = safe_column_access(df_calc, ["TPVB", "T.P.V.B"], 0)
        tpvp = safe_column_access(df_calc, ["TPVP", "T.P.V.P"], 0)
        casa_renuente = safe_column_access(
            df_calc, ["Casa renuente", "CASA RENUENTE", "Casa Renuente"], 0
        )

        # Tasa de aceptación
        df_calc["tasa_aceptacion"] = np.where(tpe > 0, (tpvb / tpe * 100).round(2), 0)

        # Tasa de resistencia
        df_calc["tasa_resistencia"] = np.where(
            tpe > 0, (casa_renuente / tpe * 100).round(2), 0
        )

        # Cobertura previa
        df_calc["cobertura_previa"] = np.where(tpe > 0, (tpvp / tpe * 100).round(2), 0)

        # Eficiencia de la brigada
        poblacion_susceptible = tpe - tpvp
        df_calc["eficiencia_brigada"] = np.where(
            poblacion_susceptible > 0, (tpvb / poblacion_susceptible * 100).round(2), 0
        )

    except Exception as e:
        st.warning(f"⚠️ Error calculando métricas derivadas: {str(e)}")

    return df_calc


def create_brigadas_summary_safe(df):
    """
    Crea un resumen ejecutivo con acceso seguro a columnas
    """
    if df.empty:
        return {}

    try:
        # Acceso seguro a columnas de fecha
        fecha_series = safe_column_access(df, ["FECHA", "Fecha", "DATE"], pd.NaT)
        if not fecha_series.isna().all():
            fecha_inicio = fecha_series.min()
            fecha_fin = fecha_series.max()
            duracion_campana = (
                (fecha_fin - fecha_inicio).days + 1
                if pd.notna(fecha_inicio) and pd.notna(fecha_fin)
                else 0
            )
        else:
            fecha_inicio = fecha_fin = None
            duracion_campana = 0

        # Métricas de cobertura con acceso seguro
        total_brigadas = len(df)
        municipios_visitados = safe_column_access(
            df, ["MUNICIPIO", "Municipio"], "Sin dato"
        ).nunique()
        veredas_visitadas = safe_column_access(
            df, ["VEREDAS", "Veredas"], "Sin dato"
        ).nunique()

        # Métricas de población con acceso seguro
        poblacion_total_encontrada = safe_column_access(df, ["TPE"], 0).sum()
        poblacion_ya_vacunada = safe_column_access(df, ["TPVP"], 0).sum()
        poblacion_vacunada_brigada = safe_column_access(df, ["TPVB"], 0).sum()
        poblacion_resistente = safe_column_access(df, ["TPNVP"], 0).sum()

        # Métricas de efectividad con acceso seguro
        total_efectivas = safe_column_access(
            df, ["Efectivas (E)", "EFECTIVAS"], 0
        ).sum()
        total_no_efectivas = safe_column_access(
            df, ["No Efectivas (NE)", "NO EFECTIVAS"], 0
        ).sum()
        total_fallidas = safe_column_access(df, ["Fallidas (F)", "FALLIDAS"], 0).sum()
        total_intentos = total_efectivas + total_no_efectivas + total_fallidas
        efectividad_global = (
            (total_efectivas / total_intentos * 100) if total_intentos > 0 else 0
        )

        return {
            "periodo": {
                "inicio": fecha_inicio,
                "fin": fecha_fin,
                "duracion_dias": duracion_campana,
            },
            "cobertura": {
                "total_brigadas": total_brigadas,
                "municipios_visitados": municipios_visitados,
                "veredas_visitadas": veredas_visitadas,
            },
            "poblacion": {
                "encontrada": poblacion_total_encontrada,
                "ya_vacunada": poblacion_ya_vacunada,
                "vacunada_brigada": poblacion_vacunada_brigada,
                "resistente": poblacion_resistente,
                "cobertura_previa_pct": (
                    (poblacion_ya_vacunada / poblacion_total_encontrada * 100)
                    if poblacion_total_encontrada > 0
                    else 0
                ),
                "cobertura_brigada_pct": (
                    (poblacion_vacunada_brigada / poblacion_total_encontrada * 100)
                    if poblacion_total_encontrada > 0
                    else 0
                ),
            },
            "efectividad": {
                "efectividad_global_pct": efectividad_global,
                "total_efectivas": total_efectivas,
                "total_intentos": total_intentos,
            },
        }

    except Exception as e:
        st.error(f"❌ Error creando resumen: {str(e)}")
        return {}


@st.cache_data(ttl=3600)
def load_brigadas_for_dashboard():
    """
    Función principal para cargar datos de brigadas con normalización completa
    """
    try:
        st.info("🔄 Cargando datos de brigadas...")

        # Cargar Excel con normalización
        excel_data = load_brigadas_excel()

        if not excel_data:
            st.warning("⚠️ No se encontraron datos de brigadas")
            return None

        # Procesar hoja de Vacunacion con normalización
        if "Vacunacion" in excel_data:
            df_brigadas = process_brigadas_data(excel_data["Vacunacion"])

            if df_brigadas.empty:
                st.warning("⚠️ No se pudieron procesar los datos de brigadas")
                return None

        else:
            st.error("❌ No se encontró la hoja 'Vacunacion' en el archivo Excel")
            return None

        # Crear resumen ejecutivo con acceso seguro
        resumen = create_brigadas_summary_safe(df_brigadas)

        result = {
            "brigadas_data": df_brigadas,
            "excel_raw": excel_data,
            "resumen_ejecutivo": resumen,
        }

        st.success(
            f"✅ Datos de brigadas cargados exitosamente: {len(df_brigadas)} registros"
        )

        return result

    except Exception as e:
        st.error(f"❌ Error cargando datos de brigadas: {str(e)}")
        return None
