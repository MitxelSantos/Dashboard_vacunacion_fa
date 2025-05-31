"""
app.py - Dashboard de Vacunación Fiebre Amarilla - Tolima
Versión corregida con rangos de edad correctos y cálculo de edad desde fecha de nacimiento
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import os
from pathlib import Path

# Configuración de página
st.set_page_config(
    page_title="Dashboard Fiebre Amarilla - Tolima",
    page_icon="💉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Colores institucionales del Tolima
COLORS = {
    "primary": "#7D0F2B",  # Vinotinto institucional
    "secondary": "#F2A900",  # Amarillo dorado
    "accent": "#5A4214",  # Marrón dorado
    "success": "#509E2F",  # Verde
    "warning": "#F7941D",  # Naranja
    "white": "#FFFFFF",
}

# Rangos de edad correctos para análisis
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


def calculate_age(fecha_nacimiento, fecha_referencia=None):
    """
    Calcula la edad en años a partir de la fecha de nacimiento

    Args:
        fecha_nacimiento: Fecha de nacimiento (datetime)
        fecha_referencia: Fecha de referencia para calcular edad (default: hoy)

    Returns:
        int: Edad en años
    """
    if pd.isna(fecha_nacimiento):
        return None

    if fecha_referencia is None:
        fecha_referencia = datetime.now()

    try:
        edad = fecha_referencia.year - fecha_nacimiento.year

        # Ajustar si no ha llegado el cumpleaños este año
        if (fecha_referencia.month, fecha_referencia.day) < (
            fecha_nacimiento.month,
            fecha_nacimiento.day,
        ):
            edad -= 1

        return max(0, edad)  # No permitir edades negativas
    except:
        return None


def classify_age_group(edad):
    """
    Clasifica una edad en el rango correspondiente

    Args:
        edad: Edad en años (int)

    Returns:
        str: Código del rango de edad
    """
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
    else:  # 60 y más
        return "60+"


@st.cache_data
def load_barridos_data():
    """Carga datos de barridos territoriales de emergencia"""
    try:
        if os.path.exists("data/Resumen.xlsx"):
            # Intentar diferentes hojas
            try:
                df = pd.read_excel("data/Resumen.xlsx", sheet_name="Barridos")
            except:
                try:
                    df = pd.read_excel("data/Resumen.xlsx", sheet_name="Vacunacion")
                except:
                    # Si no existe, usar la primera hoja
                    df = pd.read_excel("data/Resumen.xlsx", sheet_name=0)

            if not df.empty:
                # Convertir fechas
                if "FECHA" in df.columns:
                    df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")

                st.info(f"🔍 **Barridos cargados:** {len(df)} registros")
                st.info(f"📊 **Columnas disponibles:** {list(df.columns)}")

                return df

    except Exception as e:
        st.error(f"Error cargando barridos: {str(e)}")
    return pd.DataFrame()


@st.cache_data
def load_historical_data():
    """Carga datos históricos de vacunación individual"""
    try:
        if os.path.exists("data/vacunacion_fa.csv"):
            df = pd.read_csv("data/vacunacion_fa.csv")

            if not df.empty:
                # Convertir fechas
                if "FA UNICA" in df.columns:
                    df["FA UNICA"] = pd.to_datetime(df["FA UNICA"], errors="coerce")

                if "FechaNacimiento" in df.columns:
                    df["FechaNacimiento"] = pd.to_datetime(
                        df["FechaNacimiento"], errors="coerce"
                    )

                st.info(f"🔍 **Históricos cargados:** {len(df)} registros individuales")
                return df

    except Exception as e:
        st.error(f"Error cargando datos históricos: {str(e)}")
    return pd.DataFrame()


@st.cache_data
def load_population_data():
    """Carga datos de población por EAPB y municipio"""
    try:
        if os.path.exists("data/Poblacion_aseguramiento.xlsx"):
            df = pd.read_excel("data/Poblacion_aseguramiento.xlsx")

            if not df.empty:
                st.info(f"🔍 **Población cargada:** {len(df)} registros EAPB-Municipio")
                return df

    except Exception as e:
        st.error(f"Error cargando población: {str(e)}")
    return pd.DataFrame()


def detect_age_columns_barridos(df):
    """Detecta EXACTAMENTE 11 rangos de edad por cada una de las 4 etapas"""
    age_columns_by_stage = {
        "etapa_1_encontrada": {},  # Población encontrada
        "etapa_2_previa": {},  # Vacunada previamente
        "etapa_3_no_vacunada": {},  # No vacunada encontrada
        "etapa_4_vacunada_barrido": {},  # Vacunada en barrido
    }

    # Rangos estándar esperados (11 rangos)
    rangos_estandar = [
        "<1",
        "1-5",
        "6-10",
        "11-20",
        "21-30",
        "31-40",
        "41-50",
        "51-59",
        "60+",
    ]

    # Patrones específicos para cada rango
    patrones_busqueda = {
        "<1": ["< 1 AÑO"],
        "1-5": ["1-5 AÑOS"],
        "6-10": ["6-10 AÑOS"],
        "11-20": ["11-20 AÑOS"],
        "21-30": ["21-30 AÑOS"],
        "31-40": ["31-40 AÑOS"],
        "41-50": ["41-50 AÑOS"],
        "51-59": ["51-59 AÑOS"],
        "60+": ["60 Y MAS"],
    }

    # Detectar columnas por etapa con patrones exactos
    for rango, patrones in patrones_busqueda.items():
        for patron in patrones:

            # Etapa 1: Sin sufijo (base)
            col_etapa1 = None
            for col in df.columns:
                if str(col).strip() == patron:
                    col_etapa1 = col
                    break
            if col_etapa1:
                age_columns_by_stage["etapa_1_encontrada"][rango] = col_etapa1

            # Etapa 2: Sufijo "2"
            col_etapa2 = None
            for col in df.columns:
                if str(col).strip() == f"{patron}2":
                    col_etapa2 = col
                    break
            if col_etapa2:
                age_columns_by_stage["etapa_2_previa"][rango] = col_etapa2

            # Etapa 3: Sufijos específicos por rango
            sufijos_etapa3 = {
                "< 1 AÑO": "3",
                "1-5 AÑOS": "11",
                "6-10 AÑOS": "12",
                "11-20 AÑOS": "13",
                "21-30 AÑOS": "14",
                "31-40 AÑOS": "15",
                "41-50 AÑOS": "16",
                "51-59 AÑOS": "17",
                "60 Y MAS": "18",
            }

            if patron in sufijos_etapa3:
                sufijo = sufijos_etapa3[patron]
                col_etapa3 = None
                for col in df.columns:
                    if str(col).strip() == f"{patron}{sufijo}":
                        col_etapa3 = col
                        break
                if col_etapa3:
                    age_columns_by_stage["etapa_3_no_vacunada"][rango] = col_etapa3

            # Etapa 4: Sufijos específicos por rango
            sufijos_etapa4 = {
                "< 1 AÑO": "4",
                "1-5 AÑOS": "21",
                "6-10 AÑOS": "21",  # Nota: mismo sufijo que 1-5
                "11-20 AÑOS": "22",
                "21-30 AÑOS": "23",
                "31-40 AÑOS": "24",
                "41-50 AÑOS": "25",
                "51-59 AÑOS": "26",
                "60 Y MAS": "182",
            }

            if patron in sufijos_etapa4:
                sufijo = sufijos_etapa4[patron]
                col_etapa4 = None
                for col in df.columns:
                    # Para 6-10 AÑOS con sufijo 21, necesitamos ser más específicos
                    if patron == "6-10 AÑOS" and sufijo == "21":
                        if str(col).strip() == "6-10 AÑOS21":
                            col_etapa4 = col
                            break
                    else:
                        if str(col).strip() == f"{patron}{sufijo}":
                            col_etapa4 = col
                            break
                if col_etapa4:
                    age_columns_by_stage["etapa_4_vacunada_barrido"][rango] = col_etapa4

    # Detectar columnas de consolidación 60+ (60-69, 70+)
    columns_to_consolidate = {
        "etapa_1_encontrada": [],
        "etapa_2_previa": [],
        "etapa_3_no_vacunada": [],
        "etapa_4_vacunada_barrido": [],
    }

    # Patrones de consolidación específicos
    consolidation_mappings = {
        "60-69 AÑOS27": "etapa_1_encontrada",
        "70 AÑOS Y MAS269": "etapa_1_encontrada",
        "60-69 AÑOS272": "etapa_2_previa",
        "70 AÑOS Y MAS2693": "etapa_3_no_vacunada",
        "60-69 AÑOS273": "etapa_3_no_vacunada",
        "70 AÑOS Y MAS2694": "etapa_4_vacunada_barrido",
        "60-69 AÑOS274": "etapa_4_vacunada_barrido",
        "70 AÑOS Y MAS2695": "etapa_1_encontrada",  # Corregir si es necesario
    }

    for col in df.columns:
        col_str = str(col).strip()
        if col_str in consolidation_mappings:
            etapa = consolidation_mappings[col_str]
            columns_to_consolidate[etapa].append(col)

    # Mostrar resumen de detección exacta
    st.success("🎯 **Detección exacta por etapa:**")
    etapa_labels = {
        "etapa_1_encontrada": "Población encontrada",
        "etapa_2_previa": "Vacunada previamente",
        "etapa_3_no_vacunada": "No vacunada encontrada",
        "etapa_4_vacunada_barrido": "Vacunada en barrido",
    }

    for etapa, columns in age_columns_by_stage.items():
        label = etapa_labels[etapa]
        count = len(columns)
        status = "✅" if count == 9 else "⚠️"
        st.write(f"{status} **{label}:** {count}/9 rangos detectados")

        # Mostrar rangos faltantes
        rangos_encontrados = set(columns.keys())
        rangos_faltantes = set(rangos_estandar) - rangos_encontrados
        if rangos_faltantes:
            st.write(f"   Faltantes: {list(rangos_faltantes)}")

    # Mostrar consolidación
    total_consolidacion = sum(len(cols) for cols in columns_to_consolidate.values())
    if total_consolidacion > 0:
        st.info(
            f"🔄 **Columnas de consolidación 60+:** {total_consolidacion} detectadas"
        )

    return age_columns_by_stage, columns_to_consolidate


def process_historical_by_age(df_historical):
    """Procesa datos históricos calculando edades desde fecha de nacimiento"""
    if df_historical.empty:
        return {"total_individual": 0, "por_edad": {}}

    result = {"total_individual": len(df_historical), "por_edad": {}}

    # Calcular edades si tenemos fecha de nacimiento
    if (
        "FechaNacimiento" in df_historical.columns
        and "FA UNICA" in df_historical.columns
    ):

        # Calcular edad al momento de la vacunación
        df_work = df_historical.copy()
        df_work["edad_vacunacion"] = df_work.apply(
            lambda row: (
                calculate_age(row["FechaNacimiento"], row["FA UNICA"])
                if pd.notna(row["FechaNacimiento"]) and pd.notna(row["FA UNICA"])
                else None
            ),
            axis=1,
        )

        # Clasificar en rangos
        df_work["rango_edad"] = df_work["edad_vacunacion"].apply(classify_age_group)

        # Contar por rango
        age_counts = df_work["rango_edad"].value_counts()

        for rango in RANGOS_EDAD.keys():
            count = age_counts.get(rango, 0)
            result["por_edad"][rango] = {"total": count, "label": RANGOS_EDAD[rango]}

        # Información de debug
        edades_validas = df_work["edad_vacunacion"].notna().sum()
        st.info(
            f"📊 **Edades calculadas:** {edades_validas} de {len(df_work)} registros"
        )

        if edades_validas > 0:
            edad_min = df_work["edad_vacunacion"].min()
            edad_max = df_work["edad_vacunacion"].max()
            edad_promedio = df_work["edad_vacunacion"].mean()
            st.info(
                f"📈 **Rango de edades:** {edad_min:.0f} - {edad_max:.0f} años (promedio: {edad_promedio:.1f})"
            )

    else:
        st.warning("⚠️ No se encontró columna 'FechaNacimiento' para calcular edades")

    return result


def process_barridos_totals(df_barridos):
    """Procesa totales de barridos enfocándose en vacunados (Etapa 4) y renuentes (Etapa 3)"""
    if df_barridos.empty:
        return {
            "total_vacunados": 0,
            "total_renuentes": 0,
            "por_edad": {},
            "renuentes_por_edad": {},
            "columns_info": {},
        }

    # Detectar columnas de edad por etapa
    age_columns_by_stage, columns_to_consolidate = detect_age_columns_barridos(
        df_barridos
    )

    st.info("🎯 **Enfoque en datos relevantes:**")
    st.write("• **Etapa 4 (Vacunados en barrido):** Nueva vacunación realizada")
    st.write("• **Etapa 3 (No vacunados):** Renuentes/Rechazos para ajustar cobertura")

    # Mostrar columnas detectadas solo para etapas relevantes
    etapas_relevantes = ["etapa_4_vacunada_barrido", "etapa_3_no_vacunada"]
    for etapa in etapas_relevantes:
        if age_columns_by_stage.get(etapa):
            etapa_label = (
                "Vacunados en barrido"
                if etapa == "etapa_4_vacunada_barrido"
                else "Renuentes/No vacunados"
            )
            st.write(
                f"🔍 **{etapa_label}:** {len(age_columns_by_stage[etapa])} rangos detectados"
            )

    totales = {
        "total_vacunados": 0,  # Solo etapa 4
        "total_renuentes": 0,  # Solo etapa 3
        "por_edad": {},  # Vacunados por edad (etapa 4)
        "renuentes_por_edad": {},  # Renuentes por edad (etapa 3)
        "columns_info": {
            "age_columns_by_stage": age_columns_by_stage,
            "columns_to_consolidate": columns_to_consolidate,
        },
    }

    # Procesar SOLO Etapa 4 (Vacunados en barrido) - DATO PRINCIPAL
    etapa_4_columns = age_columns_by_stage.get("etapa_4_vacunada_barrido", {})
    for rango, col_name in etapa_4_columns.items():
        if col_name in df_barridos.columns:
            valores_numericos = pd.to_numeric(
                df_barridos[col_name], errors="coerce"
            ).fillna(0)
            total_rango = valores_numericos.sum()

            totales["por_edad"][rango] = {
                "total": total_rango,
                "label": RANGOS_EDAD[rango],
                "column": col_name,
            }
            totales["total_vacunados"] += total_rango

    # Procesar Etapa 3 (No vacunados/Renuentes) - PARA ANÁLISIS DE COBERTURA
    etapa_3_columns = age_columns_by_stage.get("etapa_3_no_vacunada", {})
    for rango, col_name in etapa_3_columns.items():
        if col_name in df_barridos.columns:
            valores_numericos = pd.to_numeric(
                df_barridos[col_name], errors="coerce"
            ).fillna(0)
            total_rango = valores_numericos.sum()

            totales["renuentes_por_edad"][rango] = {
                "total": total_rango,
                "label": RANGOS_EDAD[rango],
                "column": col_name,
            }
            totales["total_renuentes"] += total_rango

    # Consolidar columnas adicionales en 60+ SOLO para etapas relevantes
    for etapa_nombre in ["etapa_4_vacunada_barrido", "etapa_3_no_vacunada"]:
        consolidation_cols = columns_to_consolidate.get(etapa_nombre, [])
        if consolidation_cols:
            total_consolidado = 0
            for col in consolidation_cols:
                if col in df_barridos.columns:
                    valores_numericos = pd.to_numeric(
                        df_barridos[col], errors="coerce"
                    ).fillna(0)
                    total_consolidado += valores_numericos.sum()

            if total_consolidado > 0:
                if etapa_nombre == "etapa_4_vacunada_barrido":
                    # Agregar a vacunados
                    if "60+" in totales["por_edad"]:
                        totales["por_edad"]["60+"]["total"] += total_consolidado
                    else:
                        totales["por_edad"]["60+"] = {
                            "total": total_consolidado,
                            "label": RANGOS_EDAD["60+"],
                            "column": "consolidado",
                        }
                    totales["total_vacunados"] += total_consolidado

                elif etapa_nombre == "etapa_3_no_vacunada":
                    # Agregar a renuentes
                    if "60+" in totales["renuentes_por_edad"]:
                        totales["renuentes_por_edad"]["60+"][
                            "total"
                        ] += total_consolidado
                    else:
                        totales["renuentes_por_edad"]["60+"] = {
                            "total": total_consolidado,
                            "label": RANGOS_EDAD["60+"],
                            "column": "consolidado",
                        }
                    totales["total_renuentes"] += total_consolidado

    # Mostrar resumen enfocado
    st.success("✅ **Datos procesados (enfoque correcto):**")
    st.write(
        f"• **Nueva vacunación (Barridos):** {totales['total_vacunados']:,.0f} personas"
    )
    st.write(
        f"• **Renuentes/No vacunados:** {totales['total_renuentes']:,.0f} personas"
    )
    st.write(f"• **Lógica:** PAI + Barridos = Total vacunados")
    st.write(f"• **Cobertura ajustada:** Considerando renuentes en denominador")

    return totales


def determine_cutoff_date(df_barridos):
    """Determina la fecha de corte automáticamente"""
    if df_barridos.empty or "FECHA" not in df_barridos.columns:
        return None

    # Buscar la fecha MÁS ANTIGUA en barridos (inicio de emergencia)
    fechas_validas = df_barridos["FECHA"].dropna()
    if len(fechas_validas) > 0:
        fecha_corte = fechas_validas.min()
        st.success(
            f"📅 **Fecha de corte determinada:** {fecha_corte.strftime('%d/%m/%Y')}"
        )
        st.info(
            f"• **Pre-emergencia:** Vacunación individual antes del {fecha_corte.strftime('%d/%m/%Y')}"
        )
        st.info(
            f"• **Emergencia:** Barridos territoriales desde el {fecha_corte.strftime('%d/%m/%Y')}"
        )
        return fecha_corte
    return None


def combine_vaccination_data(df_historical, df_barridos, fecha_corte):
    """Combina datos históricos PAI y barridos con lógica corregida"""
    combined_data = {
        "pre_emergencia": pd.DataFrame(),
        "emergencia": pd.DataFrame(),
        "historical_processed": {},
        "barridos_totales": {},
        "total_individual": 0,  # PAI (históricos)
        "total_barridos": 0,  # Solo nueva vacunación (Etapa 4)
        "total_general": 0,  # PAI + Barridos
    }

    # Procesar datos históricos PAI (toda la data histórica es válida)
    if not df_historical.empty:
        if fecha_corte and "FA UNICA" in df_historical.columns:
            # Si hay fecha de corte, tomar solo antes del corte
            mask_pre = df_historical["FA UNICA"] < fecha_corte
            df_pre = df_historical[mask_pre].copy()
        else:
            # Si no hay fecha de corte, usar todos los datos históricos
            df_pre = df_historical.copy()

        df_pre["periodo"] = "pre_emergencia"
        combined_data["pre_emergencia"] = df_pre

        # Procesar por rangos de edad
        combined_data["historical_processed"] = process_historical_by_age(df_pre)
        combined_data["total_individual"] = combined_data["historical_processed"][
            "total_individual"
        ]

    # Procesar datos de barridos (enfoque en nueva vacunación)
    if not df_barridos.empty:
        df_emerg = df_barridos.copy()
        df_emerg["periodo"] = "emergencia"
        combined_data["emergencia"] = df_emerg

        # Procesar con lógica corregida (solo Etapa 4 + Etapa 3)
        combined_data["barridos_totales"] = process_barridos_totals(df_barridos)
        combined_data["total_barridos"] = combined_data["barridos_totales"][
            "total_vacunados"
        ]

    # Total general = PAI + Nueva vacunación de barridos
    combined_data["total_general"] = (
        combined_data["total_individual"] + combined_data["total_barridos"]
    )

    st.success("✅ **Lógica integrada PAI + Barridos:**")
    st.write(
        f"• **PAI (registros históricos):** {combined_data['total_individual']:,} vacunados"
    )
    st.write(
        f"• **Barridos (nueva vacunación):** {combined_data['total_barridos']:,} vacunados"
    )
    st.write(f"• **TOTAL INTEGRADO:** {combined_data['total_general']:,} vacunados")

    total_renuentes = combined_data["barridos_totales"].get("total_renuentes", 0)
    if total_renuentes > 0:
        st.write(f"• **Renuentes identificados:** {total_renuentes:,} personas")
        tasa_aceptacion = (
            combined_data["total_general"]
            / (combined_data["total_general"] + total_renuentes)
        ) * 100
        st.write(f"• **Tasa de aceptación:** {tasa_aceptacion:.1f}%")

    return combined_data


def show_overview_tab(combined_data, df_population, fecha_corte):
    """Muestra la vista general del dashboard con datos combinados"""
    st.header("📊 Resumen General")

    # Información de división temporal
    if fecha_corte:
        st.info(
            f"🔄 **División temporal:** Corte el {fecha_corte.strftime('%d/%m/%Y')} (inicio de barridos)"
        )

    # Métricas principales corregidas (población fija)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "PAI (Históricos)",
            f"{combined_data['total_individual']:,}".replace(",", "."),
            delta="Vacunación previa registrada",
        )

    with col2:
        st.metric(
            "Barridos (Nueva vacunación)",
            f"{combined_data['total_barridos']:,}".replace(",", "."),
            delta="Vacunación en terreno",
        )

    with col3:
        # Población FIJA (no restar renuentes)
        total_population = 0
        if not df_population.empty:
            pop_column = None
            for col in df_population.columns:
                if any(
                    keyword in str(col).upper()
                    for keyword in ["TOTAL", "POBLACION", "POBLACIÓN"]
                ):
                    pop_column = col
                    break

            if pop_column:
                try:
                    total_population = (
                        pd.to_numeric(df_population[pop_column], errors="coerce")
                        .fillna(0)
                        .sum()
                    )
                except:
                    total_population = 0

        if total_population > 0:
            st.metric(
                "Población Total (Fija)", f"{total_population:,}".replace(",", ".")
            )
            st.caption("Base EAPB sin ajustes")
        else:
            st.metric("Población Total", "Calculando...")

    with col4:
        total_vacunados = combined_data["total_general"]
        if total_population > 0:
            cobertura = total_vacunados / total_population * 100
            st.metric("Cobertura Total", f"{cobertura:.2f}%")
            st.caption("(PAI + Barridos) / Población")
        else:
            st.metric("Total Vacunados", f"{total_vacunados:,}".replace(",", "."))

    # Gráficos principales
    col1, col2 = st.columns(2)

    with col1:
        # Comparación por modalidad
        modalidades_data = {
            "Modalidad": ["Individual", "Barridos"],
            "Vacunados": [
                combined_data["total_individual"],
                combined_data["total_barridos"],
            ],
        }

        fig = px.bar(
            modalidades_data,
            x="Modalidad",
            y="Vacunados",
            title="Vacunación por Modalidad",
            color="Modalidad",
            color_discrete_map={
                "Individual": COLORS["primary"],
                "Barridos": COLORS["warning"],
            },
        )
        fig.update_layout(
            plot_bgcolor=COLORS["white"], paper_bgcolor=COLORS["white"], height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Gráfico de cobertura con triple segmento
        total_renuentes = combined_data["barridos_totales"].get("total_renuentes", 0)
        total_vacunados = combined_data["total_general"]

        if total_population > 0:
            # Calcular segmentos
            contactados = total_vacunados + total_renuentes
            sin_contactar = max(0, total_population - contactados)

            # Datos para gráfico de barras segmentado
            segmentos_data = {
                "Categoría": ["Población del Tolima"],
                "Vacunados": [total_vacunados],
                "Renuentes": [total_renuentes],
                "Sin contactar": [sin_contactar],
            }

            # Crear DataFrame para plotly
            df_segmentos = pd.DataFrame(segmentos_data)

            fig = go.Figure()

            # Agregar cada segmento
            fig.add_trace(
                go.Bar(
                    name="Vacunados (PAI + Barridos)",
                    x=df_segmentos["Categoría"],
                    y=df_segmentos["Vacunados"],
                    marker_color="#2E8B57",  # Verde
                )
            )

            fig.add_trace(
                go.Bar(
                    name="Renuentes",
                    x=df_segmentos["Categoría"],
                    y=df_segmentos["Renuentes"],
                    marker_color="#FF6B6B",  # Rojo
                )
            )

            fig.add_trace(
                go.Bar(
                    name="Sin contactar",
                    x=df_segmentos["Categoría"],
                    y=df_segmentos["Sin contactar"],
                    marker_color="#D3D3D3",  # Gris
                )
            )

            fig.update_layout(
                title="Cobertura y Contacto Poblacional",
                barmode="stack",
                height=400,
                showlegend=True,
                yaxis_title="Número de personas",
            )

            st.plotly_chart(fig, use_container_width=True)

            # Mostrar porcentajes
            if total_population > 0:
                st.caption(
                    f"Vacunados: {(total_vacunados/total_population*100):.1f}% | "
                    f"Renuentes: {(total_renuentes/total_population*100):.1f}% | "
                    f"Sin contactar: {(sin_contactar/total_population*100):.1f}%"
                )

        else:
            # Fallback: distribución por edad de barridos
            if combined_data["barridos_totales"].get("por_edad"):
                rangos_data = combined_data["barridos_totales"]["por_edad"]

                labels = [RANGOS_EDAD.get(k, k) for k in rangos_data.keys()]
                values = [data["total"] for data in rangos_data.values()]

                fig = px.pie(
                    values=values,
                    names=labels,
                    title="Nueva Vacunación por Edad - Barridos",
                    color_discrete_sequence=px.colors.qualitative.Set3,
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Datos de población en procesamiento...")

    # Tabla detallada por rangos de edad
    st.subheader("📊 Detalle por Rangos de Edad")

    age_detail_data = []
    for rango, label in RANGOS_EDAD.items():
        individual = 0
        barridos = 0

        if combined_data["historical_processed"].get("por_edad", {}).get(rango):
            individual = combined_data["historical_processed"]["por_edad"][rango][
                "total"
            ]

        if combined_data["barridos_totales"].get("por_edad", {}).get(rango):
            barridos = combined_data["barridos_totales"]["por_edad"][rango]["total"]

        total = individual + barridos

        if total > 0:  # Solo mostrar rangos con datos
            age_detail_data.append(
                {
                    "Rango de Edad": label,
                    "Individual": individual,
                    "Barridos": barridos,
                    "Total": total,
                    "% del Total": (
                        f"{(total / combined_data['total_general'] * 100):.1f}%"
                        if combined_data["total_general"] > 0
                        else "0%"
                    ),
                }
            )

    if age_detail_data:
        df_detail = pd.DataFrame(age_detail_data)
        st.dataframe(df_detail, use_container_width=True)
    else:
        st.info("No hay datos detallados por edad disponibles")

    # Análisis detallado enfocado en datos relevantes
    st.subheader("📊 Análisis Integral: PAI + Barridos + Renuencia")

    # Crear tabla integral
    integral_data = []
    total_renuentes_data = combined_data["barridos_totales"].get(
        "renuentes_por_edad", {}
    )

    for rango, label in RANGOS_EDAD.items():
        pai_vacunados = 0
        barridos_vacunados = 0
        renuentes = 0

        # PAI (históricos)
        if combined_data["historical_processed"].get("por_edad", {}).get(rango):
            pai_vacunados = combined_data["historical_processed"]["por_edad"][rango][
                "total"
            ]

        # Barridos (nueva vacunación)
        if combined_data["barridos_totales"].get("por_edad", {}).get(rango):
            barridos_vacunados = combined_data["barridos_totales"]["por_edad"][rango][
                "total"
            ]

        # Renuentes
        if total_renuentes_data.get(rango):
            renuentes = total_renuentes_data[rango]["total"]

        total_vacunados_rango = pai_vacunados + barridos_vacunados

        if total_vacunados_rango > 0 or renuentes > 0:  # Mostrar rangos con datos
            integral_data.append(
                {
                    "Rango de Edad": label,
                    "PAI (Históricos)": pai_vacunados,
                    "Barridos (Nuevos)": barridos_vacunados,
                    "Total Vacunados": total_vacunados_rango,
                    "Renuentes": renuentes,
                    "% Renuencia": (
                        f"{(renuentes / (total_vacunados_rango + renuentes) * 100):.1f}%"
                        if (total_vacunados_rango + renuentes) > 0
                        else "0%"
                    ),
                }
            )

    if integral_data:
        df_integral = pd.DataFrame(integral_data)
        st.dataframe(df_integral, use_container_width=True)

        # Métricas de análisis integral
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_pai = combined_data["total_individual"]
            st.metric("Total PAI", f"{total_pai:,.0f}")
            st.caption("Vacunación histórica registrada")

        with col2:
            total_barridos_nuevos = combined_data["total_barridos"]
            st.metric("Total Barridos", f"{total_barridos_nuevos:,.0f}")
            st.caption("Nueva vacunación en terreno")

        with col3:
            total_renuentes = combined_data["barridos_totales"].get(
                "total_renuentes", 0
            )
            st.metric("Total Renuentes", f"{total_renuentes:,.0f}")
            st.caption("Rechazos documentados")

        with col4:
            total_contactado = combined_data["total_general"] + total_renuentes
            if total_contactado > 0:
                tasa_aceptacion = (
                    combined_data["total_general"] / total_contactado
                ) * 100
                st.metric("Tasa Aceptación", f"{tasa_aceptacion:.1f}%")
                st.caption("Vacunados / Total contactado")
            else:
                st.metric("Tasa Aceptación", "N/A")

        # Análisis de eficiencia con población fija
        st.subheader("📈 Análisis de Eficiencia Real")

        if total_population > 0:
            col1, col2, col3 = st.columns(3)

            with col1:
                cobertura_pai = (total_pai / total_population) * 100
                st.metric("Cobertura PAI", f"{cobertura_pai:.2f}%")
                st.caption("Históricos / Población total")

            with col2:
                cobertura_total = (
                    combined_data["total_general"] / total_population
                ) * 100
                st.metric("Cobertura Total", f"{cobertura_total:.2f}%")
                st.caption("(PAI + Barridos) / Población total")

            with col3:
                incremento_cobertura = (
                    combined_data["total_barridos"] / total_population
                ) * 100
                st.metric("Incremento por Barridos", f"+{incremento_cobertura:.2f}%")
                st.caption("Solo nueva vacunación")

        # Análisis de contacto (sin afectar denominador)
        total_contactados = combined_data["total_general"] + total_renuentes
        if total_contactados > 0:
            col1, col2, col3 = st.columns(3)

            with col1:
                tasa_aceptacion = (
                    combined_data["total_general"] / total_contactados
                ) * 100
                st.metric("Tasa de Aceptación", f"{tasa_aceptacion:.1f}%")
                st.caption("Vacunados / Total contactado")

            with col2:
                if total_population > 0:
                    cobertura_contacto = (total_contactados / total_population) * 100
                    st.metric("Cobertura de Contacto", f"{cobertura_contacto:.1f}%")
                    st.caption("Contactados / Población total")

            with col3:
                if total_renuentes > 0 and total_population > 0:
                    tasa_renuencia = (total_renuentes / total_population) * 100
                    st.metric("Tasa de Renuencia", f"{tasa_renuencia:.2f}%")
                    st.caption("Renuentes / Población total")

        # Información metodológica real
        with st.expander("ℹ️ Metodología Implementada (Sin Simulaciones)"):
            st.write("**Fuentes de datos reales:**")
            st.write("• **PAI:** Registros históricos individuales completos")
            st.write(
                "• **Barridos:** Solo Etapa 4 (nueva vacunación) de todas las columnas"
            )
            st.write(
                "• **Renuentes:** Etapa 3 (para análisis de aceptación, no afecta denominador)"
            )
            st.write("• **Población:** Base EAPB completa y fija")
            st.write("")
            st.write("**Cálculos aplicados:**")
            st.write("• **Cobertura Total = (PAI + Barridos) / Población Total × 100**")
            st.write(
                "• **Tasa Aceptación = Vacunados / (Vacunados + Renuentes) × 100**"
            )
            st.write("• **Población NO se ajusta por renuentes (permanece fija)**")
            st.write(
                "• **Gráfico de barras: Segmentos apilados (Vacunados/Renuentes/Sin contactar)**"
            )
    else:
        st.info("Datos en procesamiento - Verficando detección de etapas relevantes")


def show_temporal_tab(combined_data, fecha_corte):
    """Muestra análisis temporal"""
    st.header("📅 Análisis Temporal")

    if fecha_corte:
        st.info(
            f"📅 **Fecha de corte:** {fecha_corte.strftime('%d/%m/%Y')} - Inicio de barridos territoriales"
        )

    # Análisis de vacunación individual (pre-emergencia)
    if (
        not combined_data["pre_emergencia"].empty
        and "FA UNICA" in combined_data["pre_emergencia"].columns
    ):
        st.subheader("📈 Período Pre-emergencia (Vacunación Individual)")

        df_temporal = combined_data["pre_emergencia"][
            combined_data["pre_emergencia"]["FA UNICA"].notna()
        ].copy()

        if not df_temporal.empty:
            # Evolución diaria
            daily_data = (
                df_temporal.groupby(df_temporal["FA UNICA"].dt.date)
                .size()
                .reset_index()
            )
            daily_data.columns = ["Fecha", "Vacunados"]
            daily_data["Fecha"] = pd.to_datetime(daily_data["Fecha"])

            fig = px.line(
                daily_data,
                x="Fecha",
                y="Vacunados",
                title="Evolución Diaria - Vacunación Individual",
                color_discrete_sequence=[COLORS["primary"]],
            )
            fig.update_layout(
                plot_bgcolor=COLORS["white"], paper_bgcolor=COLORS["white"], height=400
            )
            st.plotly_chart(fig, use_container_width=True)

            # Estadísticas temporales
            col1, col2, col3 = st.columns(3)

            with col1:
                fecha_inicio = daily_data["Fecha"].min()
                fecha_fin = daily_data["Fecha"].max()
                duracion = (fecha_fin - fecha_inicio).days + 1
                st.metric("Duración Pre-emergencia", f"{duracion} días")

            with col2:
                promedio_diario = daily_data["Vacunados"].mean()
                st.metric("Promedio Diario", f"{promedio_diario:.1f}")

            with col3:
                max_dia = daily_data.loc[daily_data["Vacunados"].idxmax()]
                st.metric("Día Pico", f"{max_dia['Vacunados']} vac")
                st.caption(f"Fecha: {max_dia['Fecha'].strftime('%d/%m/%Y')}")

    # Análisis de barridos (emergencia)
    if (
        not combined_data["emergencia"].empty
        and "FECHA" in combined_data["emergencia"].columns
    ):
        st.subheader("🚨 Período de Emergencia (Barridos Territoriales)")

        df_barridos_temporal = combined_data["emergencia"][
            combined_data["emergencia"]["FECHA"].notna()
        ].copy()

        if not df_barridos_temporal.empty:
            # Barridos por día
            barridos_daily = (
                df_barridos_temporal.groupby(df_barridos_temporal["FECHA"].dt.date)
                .size()
                .reset_index()
            )
            barridos_daily.columns = ["Fecha", "Barridos"]
            barridos_daily["Fecha"] = pd.to_datetime(barridos_daily["Fecha"])

            fig = px.bar(
                barridos_daily,
                x="Fecha",
                y="Barridos",
                title="Barridos Territoriales por Día",
                color_discrete_sequence=[COLORS["warning"]],
            )
            fig.update_layout(
                plot_bgcolor=COLORS["white"], paper_bgcolor=COLORS["white"], height=400
            )
            st.plotly_chart(fig, use_container_width=True)

            # Estadísticas de barridos
            col1, col2, col3 = st.columns(3)

            with col1:
                total_barridos = len(df_barridos_temporal)
                st.metric("Total Barridos", total_barridos)

            with col2:
                if "MUNICIPIO" in df_barridos_temporal.columns:
                    municipios_barridos = df_barridos_temporal["MUNICIPIO"].nunique()
                    st.metric("Municipios Cubiertos", municipios_barridos)

            with col3:
                if "VEREDAS" in df_barridos_temporal.columns:
                    veredas_barridos = df_barridos_temporal["VEREDAS"].nunique()
                    st.metric("Veredas Visitadas", veredas_barridos)


def show_geographic_tab(combined_data):
    """Muestra análisis geográfico incluyendo veredas"""
    st.header("🗺️ Distribución Geográfica")

    col1, col2 = st.columns(2)

    with col1:
        # Vacunación individual por municipio
        if (
            not combined_data["pre_emergencia"].empty
            and "NombreMunicipioResidencia" in combined_data["pre_emergencia"].columns
        ):

            st.subheader("📍 Vacunación Individual por Municipio")

            municipios_hist = (
                combined_data["pre_emergencia"]["NombreMunicipioResidencia"]
                .value_counts()
                .reset_index()
            )
            municipios_hist.columns = ["Municipio", "Vacunados"]

            top_municipios = municipios_hist.head(15)

            fig = px.bar(
                top_municipios,
                x="Vacunados",
                y="Municipio",
                orientation="h",
                title="Top 15 Municipios - Vacunación Individual",
                color_discrete_sequence=[COLORS["primary"]],
            )
            fig.update_layout(
                plot_bgcolor=COLORS["white"],
                paper_bgcolor=COLORS["white"],
                height=500,
                yaxis={"categoryorder": "total ascending"},
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Barridos por municipio
        if (
            not combined_data["emergencia"].empty
            and "MUNICIPIO" in combined_data["emergencia"].columns
        ):

            st.subheader("🚨 Barridos por Municipio")

            municipios_barr = (
                combined_data["emergencia"]["MUNICIPIO"].value_counts().reset_index()
            )
            municipios_barr.columns = ["Municipio", "Barridos"]

            top_barridos = municipios_barr.head(15)

            fig = px.bar(
                top_barridos,
                x="Barridos",
                y="Municipio",
                orientation="h",
                title="Top 15 Municipios - Barridos Territoriales",
                color_discrete_sequence=[COLORS["warning"]],
            )
            fig.update_layout(
                plot_bgcolor=COLORS["white"],
                paper_bgcolor=COLORS["white"],
                height=500,
                yaxis={"categoryorder": "total ascending"},
            )
            st.plotly_chart(fig, use_container_width=True)

    # Análisis de veredas
    if (
        not combined_data["emergencia"].empty
        and "VEREDAS" in combined_data["emergencia"].columns
    ):

        st.subheader("🏘️ Análisis de Veredas Visitadas")

        veredas_data = (
            combined_data["emergencia"]["VEREDAS"].value_counts().reset_index()
        )
        veredas_data.columns = ["Vereda", "Barridos"]

        # Mostrar métricas de veredas
        col1, col2, col3 = st.columns(3)

        with col1:
            total_veredas = len(veredas_data)
            st.metric("Veredas Visitadas", total_veredas)

        with col2:
            if not veredas_data.empty:
                avg_barridos = veredas_data["Barridos"].mean()
                st.metric("Promedio Barridos/Vereda", f"{avg_barridos:.1f}")

        with col3:
            if not veredas_data.empty:
                max_barridos = veredas_data["Barridos"].max()
                st.metric("Máximo Barridos/Vereda", max_barridos)

        # Top veredas
        if len(veredas_data) > 0:
            top_veredas = veredas_data.head(20)

            fig = px.bar(
                top_veredas,
                x="Barridos",
                y="Vereda",
                orientation="h",
                title="Top 20 Veredas - Barridos Territoriales",
                color_discrete_sequence=[COLORS["accent"]],
            )
            fig.update_layout(
                plot_bgcolor=COLORS["white"],
                paper_bgcolor=COLORS["white"],
                height=600,
                yaxis={"categoryorder": "total ascending"},
            )
            st.plotly_chart(fig, use_container_width=True)


def show_population_tab(df_population, combined_data):
    """Muestra análisis de población considerando múltiples EAPB por municipio"""
    st.header("🏥 Análisis de Población por EAPB")

    if df_population.empty:
        st.warning("No hay datos de población disponibles")
        return

    # Análisis de estructura de población
    eapb_col = None
    municipio_col = None

    # Buscar columnas correctas
    for col in df_population.columns:
        if (
            "EAPB" in str(col).upper()
            or "NOMBRE ENTIDAD" in str(col).upper()
            or "ENTIDAD" in str(col).upper()
        ):
            eapb_col = col
        elif "MUNICIPIO" in str(col).upper():
            municipio_col = col

    if eapb_col:
        col1, col2, col3 = st.columns(3)

        with col1:
            total_registros = len(df_population)
            st.metric("Registros EAPB-Municipio", total_registros)

        with col2:
            if municipio_col:
                municipios_unicos = df_population[municipio_col].nunique()
                st.metric("Municipios Únicos", municipios_unicos)

        with col3:
            eapb_unicas = df_population[eapb_col].nunique()
            st.metric("EAPB Únicas", eapb_unicas)

    # Distribución por EAPB
    if (
        "EAPB" in df_population.columns or "Nombre Entidad" in df_population.columns
    ) and (
        "Total" in df_population.columns
        or "POBLACION" in df_population.columns
        or "Total general" in df_population.columns
    ):
        # Identificar columnas correctas
        eapb_col = None
        pop_col = None

        for col in df_population.columns:
            if (
                "EAPB" in str(col).upper()
                or "NOMBRE ENTIDAD" in str(col).upper()
                or "ENTIDAD" in str(col).upper()
            ):
                eapb_col = col
            elif "TOTAL" in str(col).upper() or "POBLACION" in str(col).upper():
                pop_col = col

        if eapb_col and pop_col:

            st.subheader("Distribución de Población por EAPB")

            eapb_totals = (
                df_population.groupby(eapb_col)[pop_col]
                .sum()
                .sort_values(ascending=False)
            )

        col1, col2 = st.columns(2)

        with col1:
            # Top 10 EAPB
            top_eapb = eapb_totals.head(10)

            fig = px.bar(
                x=top_eapb.values,
                y=top_eapb.index,
                orientation="h",
                title="Top 10 EAPB por Población",
                color_discrete_sequence=[COLORS["secondary"]],
            )
            fig.update_layout(
                plot_bgcolor=COLORS["white"],
                paper_bgcolor=COLORS["white"],
                height=400,
                yaxis={"categoryorder": "total ascending"},
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Distribución porcentual
            fig = px.pie(
                values=eapb_totals.head(8).values,
                names=eapb_totals.head(8).index,
                title="Distribución % - Top 8 EAPB",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        # Análisis de cobertura por EAPB si hay datos de vacunación
        if combined_data["total_general"] > 0:
            st.subheader("📊 Análisis de Cobertura")

            col1, col2 = st.columns(2)

            with col1:
                total_pop = eapb_totals.sum()
                cobertura_general = (
                    (combined_data["total_general"] / total_pop * 100)
                    if total_pop > 0
                    else 0
                )
                st.metric("Cobertura General", f"{cobertura_general:.2f}%")

            with col2:
                poblacion_objetivo = total_pop * 0.8  # Ejemplo: 80% población objetivo
                if poblacion_objetivo > 0:
                    avance_meta = (
                        combined_data["total_general"] / poblacion_objetivo * 100
                    )
                    st.metric("Avance Meta (80%)", f"{avance_meta:.1f}%")


def main():
    """Función principal del dashboard"""
    # Título principal
    st.title("🏥 Dashboard de Vacunación Fiebre Amarilla")
    st.markdown("**Departamento del Tolima - Barridos Territoriales**")

    # Sidebar con información
    with st.sidebar:
        # Mostrar logo si existe
        logo_path = "assets/images/logo_gobernacion.png"
        if os.path.exists(logo_path):
            st.image(logo_path, width=200)
        else:
            st.warning("Logo no encontrado en assets/images/logo_gobernacion.png")
            # Fallback con imagen de placeholder
            st.image(
                "https://via.placeholder.com/200x100/7D0F2B/FFFFFF?text=TOLIMA",
                width=200,
            )

        st.markdown("---")
        st.markdown("### ℹ️ Información del Sistema")
        st.markdown("- **Fuente 1:** PAI (Históricos)")
        st.markdown("- **Fuente 2:** Barridos (Nueva vacunación)")
        st.markdown("- **Población:** Base EAPB ajustada")
        st.markdown("- **Análisis:** Cobertura + Renuencia")
        st.markdown("- **Período:** 2024-2025")
        st.markdown("---")

        # Mostrar rangos de edad
        st.markdown("### 📊 Rangos de Edad")
        for code, label in RANGOS_EDAD.items():
            st.markdown(f"- **{code}:** {label}")
        st.markdown("---")

        # Información metodológica
        st.markdown("### 🔬 Metodología")
        st.markdown("**Sistema integrado:**")
        st.markdown("• PAI: Vacunación histórica")
        st.markdown("• Barridos: Solo nueva vacunación")
        st.markdown("• Renuentes: Para ajustar cobertura")
        st.markdown("• **Total = PAI + Barridos**")
        st.markdown("---")

        # Control de actualización
        if st.button("🔄 Actualizar Datos"):
            st.cache_data.clear()
            st.rerun()

        # Debug toggle
        show_debug = st.checkbox("🔍 Mostrar información de debug")

    # Cargar datos
    with st.spinner("Cargando datos..."):
        if show_debug:
            st.markdown("### 🔍 Debug Information")
            df_historical = load_historical_data()
            df_barridos = load_barridos_data()
            df_population = load_population_data()
        else:
            # Cargar silenciosamente
            try:
                # Datos históricos individuales
                df_historical = (
                    pd.read_csv("data/vacunacion_fa.csv")
                    if os.path.exists("data/vacunacion_fa.csv")
                    else pd.DataFrame()
                )
                if not df_historical.empty:
                    if "FA UNICA" in df_historical.columns:
                        df_historical["FA UNICA"] = pd.to_datetime(
                            df_historical["FA UNICA"], errors="coerce"
                        )
                    if "FechaNacimiento" in df_historical.columns:
                        df_historical["FechaNacimiento"] = pd.to_datetime(
                            df_historical["FechaNacimiento"], errors="coerce"
                        )

                # Datos de barridos
                if os.path.exists("data/Resumen.xlsx"):
                    try:
                        df_barridos = pd.read_excel(
                            "data/Resumen.xlsx", sheet_name="Barridos"
                        )
                    except:
                        try:
                            df_barridos = pd.read_excel(
                                "data/Resumen.xlsx", sheet_name="Vacunacion"
                            )
                        except:
                            df_barridos = pd.read_excel(
                                "data/Resumen.xlsx", sheet_name=0
                            )

                    if "FECHA" in df_barridos.columns:
                        df_barridos["FECHA"] = pd.to_datetime(
                            df_barridos["FECHA"], errors="coerce"
                        )
                else:
                    df_barridos = pd.DataFrame()

                # Datos de población
                df_population = (
                    pd.read_excel("data/Poblacion_aseguramiento.xlsx")
                    if os.path.exists("data/Poblacion_aseguramiento.xlsx")
                    else pd.DataFrame()
                )

            except Exception as e:
                st.error(f"Error cargando datos: {str(e)}")
                df_historical = df_barridos = df_population = pd.DataFrame()

    # Determinar fecha de corte y combinar datos
    fecha_corte = determine_cutoff_date(df_barridos)
    combined_data = combine_vaccination_data(df_historical, df_barridos, fecha_corte)

    # Estado de datos
    col1, col2, col3 = st.columns(3)

    with col1:
        status = "✅" if combined_data["total_individual"] > 0 else "❌"
        st.markdown(
            f"{status} **Individual:** {combined_data['total_individual']} registros"
        )

    with col2:
        status = "✅" if combined_data["total_barridos"] > 0 else "❌"
        st.markdown(
            f"{status} **Barridos:** {combined_data['total_barridos']} vacunados"
        )

    with col3:
        status = "✅" if not df_population.empty else "❌"
        st.markdown(f"{status} **Población:** {len(df_population)} registros EAPB")

    st.markdown("---")

    # Tabs principales
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Resumen", "📅 Temporal", "🗺️ Geográfico", "🏥 Población"]
    )

    with tab1:
        show_overview_tab(combined_data, df_population, fecha_corte)

    with tab2:
        show_temporal_tab(combined_data, fecha_corte)

    with tab3:
        show_geographic_tab(combined_data)

    with tab4:
        show_population_tab(df_population, combined_data)

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #7D0F2B;'>"
        "<small>Dashboard de Vacunación - Secretaría de Salud del Tolima</small>"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
