"""
app.py - Dashboard de Vacunación Fiebre Amarilla - Tolima
Versión 2.3 - Limpio, modularizado y con porcentajes en gráficos
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import os
from pathlib import Path

# Importar módulos de Google Drive
try:
    from google_drive_loader import (
        load_vaccination_data,
        load_population_data,
        load_barridos_data,
        load_logo,
    )

    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False

# Importar vistas
from vistas.overview import show_overview_tab
from vistas.temporal import show_temporal_tab
from vistas.geographic import show_geographic_tab
from vistas.population import show_population_tab


# Configuración de página
st.set_page_config(
    page_title="Dashboard Fiebre Amarilla - Tolima",
    page_icon="💉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Colores institucionales del Tolima
COLORS = {
    "primary": "#7D0F2B",
    "secondary": "#F2A900",
    "accent": "#5A4214",
    "success": "#509E2F",
    "warning": "#F7941D",
    "white": "#FFFFFF",
}

# Rangos de edad (11 rangos)
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
    "60-69": "60-69 años",
    "70+": "70 años y más",
}


def calculate_age(fecha_nacimiento, fecha_referencia=None):
    """Calcula la edad en años a partir de la fecha de nacimiento"""
    if pd.isna(fecha_nacimiento):
        return None

    if fecha_referencia is None:
        fecha_referencia = datetime.now()

    try:
        edad = fecha_referencia.year - fecha_nacimiento.year

        if (fecha_referencia.month, fecha_referencia.day) < (
            fecha_nacimiento.month,
            fecha_nacimiento.day,
        ):
            edad -= 1

        return max(0, edad)
    except:
        return None


def classify_age_group(edad):
    """Clasifica una edad en el rango correspondiente"""
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
def load_historical_data():
    """Carga datos históricos de vacunación individual"""
    try:
        # Intentar cargar desde Google Drive primero
        if GOOGLE_DRIVE_AVAILABLE and st.secrets.get("google_drive", {}).get(
            "vacunacion_csv"
        ):
            df = load_vaccination_data()
            if not df.empty:
                if "FA UNICA" in df.columns:
                    df["FA UNICA"] = pd.to_datetime(df["FA UNICA"], errors="coerce")
                if "FechaNacimiento" in df.columns:
                    df["FechaNacimiento"] = pd.to_datetime(
                        df["FechaNacimiento"], errors="coerce"
                    )
                return df

        # Fallback a archivo local
        if os.path.exists("data/vacunacion_fa.csv"):
            df = pd.read_csv("data/vacunacion_fa.csv")
            if not df.empty:
                if "FA UNICA" in df.columns:
                    df["FA UNICA"] = pd.to_datetime(df["FA UNICA"], errors="coerce")
                if "FechaNacimiento" in df.columns:
                    df["FechaNacimiento"] = pd.to_datetime(
                        df["FechaNacimiento"], errors="coerce"
                    )
                return df

    except Exception as e:
        st.error(f"Error cargando datos históricos: {str(e)}")

    return pd.DataFrame()


@st.cache_data
def load_barridos_data():
    """Carga datos de barridos territoriales de emergencia"""
    try:
        # Intentar cargar desde Google Drive primero
        if GOOGLE_DRIVE_AVAILABLE and st.secrets.get("google_drive", {}).get(
            "resumen_barridos_xlsx"
        ):
            df = load_barridos_data()
            if not df.empty:
                if "FECHA" in df.columns:
                    df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")
                return df

        # Fallback a archivo local
        if os.path.exists("data/Resumen.xlsx"):
            try:
                df = pd.read_excel("data/Resumen.xlsx", sheet_name="Vacunacion")
            except:
                try:
                    df = pd.read_excel("data/Resumen.xlsx", sheet_name="Barridos")
                except:
                    df = pd.read_excel("data/Resumen.xlsx", sheet_name=0)

            if not df.empty:
                if "FECHA" in df.columns:
                    df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")
                return df

    except Exception as e:
        st.error(f"Error cargando barridos: {str(e)}")

    return pd.DataFrame()


@st.cache_data
def load_population_data():
    """Carga datos de población por EAPB y municipio"""
    try:
        # Intentar cargar desde Google Drive primero
        if GOOGLE_DRIVE_AVAILABLE and st.secrets.get("google_drive", {}).get(
            "poblacion_xlsx"
        ):
            df = load_population_data()
            if not df.empty:
                return df

        # Fallback a archivo local
        if os.path.exists("data/Poblacion_aseguramiento.xlsx"):
            df = pd.read_excel("data/Poblacion_aseguramiento.xlsx")
            if not df.empty:
                return df

    except Exception as e:
        st.error(f"Error cargando población: {str(e)}")

    return pd.DataFrame()


def detect_age_columns_barridos(df):
    """Detecta columnas de edad por etapa en datos de barridos"""
    age_columns_by_stage = {
        "etapa_1_encontrada": {},
        "etapa_2_previa": {},
        "etapa_3_no_vacunada": {},
        "etapa_4_vacunada_barrido": {},
    }

    total_columns_by_stage = {
        "etapa_1_encontrada": None,
        "etapa_2_previa": None,
        "etapa_3_no_vacunada": None,
        "etapa_4_vacunada_barrido": None,
    }

    rangos_patrones = {
        "<1": ["< 1 AÑO"],
        "1-5": ["1-5 AÑOS"],
        "6-10": ["6-10 AÑOS"],
        "11-20": ["11-20 AÑOS"],
        "21-30": ["21-30 AÑOS"],
        "31-40": ["31-40 AÑOS"],
        "41-50": ["41-50 AÑOS"],
        "51-59": ["51-59 AÑOS"],
        "60+": ["60 Y MAS"],
        "60-69": ["60-69 AÑOS"],
        "70+": ["70 AÑOS Y MAS"],
    }

    total_patterns = {
        "etapa_1_encontrada": ["TPE"],
        "etapa_2_previa": ["TPVP"],
        "etapa_3_no_vacunada": ["TPNVP"],
        "etapa_4_vacunada_barrido": ["TPVB"],
    }

    # Detectar columnas de totales
    for etapa, patterns in total_patterns.items():
        for col_name in df.columns:
            col_str = str(col_name).upper().strip()
            if col_str in patterns:
                total_columns_by_stage[etapa] = col_name
                break

    # Detectar columnas de edad
    for rango, patrones in rangos_patrones.items():
        columnas_encontradas = []

        for col_idx, col_name in enumerate(df.columns):
            col_str = str(col_name).upper().strip()

            for patron in patrones:
                if patron in col_str:
                    if patron == "1-5 AÑOS" and any(
                        conflicto in col_str for conflicto in ["41-50", "51-59"]
                    ):
                        continue
                    if patron == "60 Y MAS" and any(
                        conflicto in col_str
                        for conflicto in ["60-69", "269", "2693", "2694", "2695"]
                    ):
                        continue

                    columnas_encontradas.append((col_idx, col_name))
                    break

        columnas_encontradas.sort(key=lambda x: x[0])

        etapas = [
            "etapa_1_encontrada",
            "etapa_2_previa",
            "etapa_3_no_vacunada",
            "etapa_4_vacunada_barrido",
        ]

        for i, (col_idx, col_name) in enumerate(columnas_encontradas):
            if i < len(etapas):
                age_columns_by_stage[etapas[i]][rango] = col_name

    return age_columns_by_stage, total_columns_by_stage


def process_historical_by_age(df_historical):
    """Procesa datos históricos calculando edades desde fecha de nacimiento"""
    if df_historical.empty:
        return {"total_individual": 0, "por_edad": {}}

    result = {"total_individual": len(df_historical), "por_edad": {}}

    if (
        "FechaNacimiento" in df_historical.columns
        and "FA UNICA" in df_historical.columns
    ):
        df_work = df_historical.copy()
        df_work["edad_vacunacion"] = df_work.apply(
            lambda row: (
                calculate_age(row["FechaNacimiento"], row["FA UNICA"])
                if pd.notna(row["FechaNacimiento"]) and pd.notna(row["FA UNICA"])
                else None
            ),
            axis=1,
        )

        df_work["rango_edad"] = df_work["edad_vacunacion"].apply(classify_age_group)
        age_counts = df_work["rango_edad"].value_counts()

        for rango in RANGOS_EDAD.keys():
            count = age_counts.get(rango, 0)
            result["por_edad"][rango] = {"total": count, "label": RANGOS_EDAD[rango]}

    return result


def process_barridos_totals(df_barridos):
    """Procesa totales de barridos con enfoque en vacunas aplicadas"""
    if df_barridos.empty:
        return {
            "total_vacunados": 0,
            "total_renuentes": 0,
            "por_edad": {},
            "renuentes_por_edad": {},
            "columns_info": {},
        }

    age_columns_by_stage, total_columns_by_stage = detect_age_columns_barridos(
        df_barridos
    )

    totales = {
        "total_vacunados": 0,
        "total_renuentes": 0,
        "por_edad": {},
        "renuentes_por_edad": {},
        "columns_info": {
            "age_columns_by_stage": age_columns_by_stage,
            "total_columns_by_stage": total_columns_by_stage,
        },
    }

    # Procesar Etapa 4 (Vacunados en barrido)
    etapa_4_columns = age_columns_by_stage.get("etapa_4_vacunada_barrido", {})

    for rango, col_name in etapa_4_columns.items():
        if col_name in df_barridos.columns:
            valores_numericos = pd.to_numeric(
                df_barridos[col_name], errors="coerce"
            ).fillna(0)
            total_rango = valores_numericos.sum()

            totales["por_edad"][rango] = {
                "total": total_rango,
                "label": RANGOS_EDAD.get(rango, rango),
                "column": col_name,
            }
            totales["total_vacunados"] += total_rango

    # Consolidar rangos 60+
    total_60_consolidado = 0
    rangos_60_plus = ["60+", "60-69", "70+"]

    for rango_60 in rangos_60_plus:
        if rango_60 in totales["por_edad"]:
            total_60_consolidado += totales["por_edad"][rango_60]["total"]

    if total_60_consolidado > 0:
        totales["por_edad"]["60+"] = {
            "total": total_60_consolidado,
            "label": "60 años y más (consolidado)",
            "column": "consolidado",
        }
        # Remover subrangos
        for rango_sub in ["60-69", "70+"]:
            if rango_sub in totales["por_edad"]:
                del totales["por_edad"][rango_sub]

    # Procesar Etapa 3 (Renuentes)
    etapa_3_columns = age_columns_by_stage.get("etapa_3_no_vacunada", {})
    for rango, col_name in etapa_3_columns.items():
        if col_name in df_barridos.columns:
            valores_numericos = pd.to_numeric(
                df_barridos[col_name], errors="coerce"
            ).fillna(0)
            total_rango = valores_numericos.sum()

            totales["renuentes_por_edad"][rango] = {
                "total": total_rango,
                "label": RANGOS_EDAD.get(rango, rango),
                "column": col_name,
            }
            totales["total_renuentes"] += total_rango

    # Consolidar renuentes 60+
    total_renuentes_60_consolidado = 0
    for rango_60 in rangos_60_plus:
        if rango_60 in totales["renuentes_por_edad"]:
            total_renuentes_60_consolidado += totales["renuentes_por_edad"][rango_60][
                "total"
            ]

    if total_renuentes_60_consolidado > 0:
        totales["renuentes_por_edad"]["60+"] = {
            "total": total_renuentes_60_consolidado,
            "label": "60 años y más (consolidado)",
            "column": "consolidado",
        }
        for rango_sub in ["60-69", "70+"]:
            if rango_sub in totales["renuentes_por_edad"]:
                del totales["renuentes_por_edad"][rango_sub]

    return totales


def determine_cutoff_date(df_barridos, df_historical):
    """Determina fechas de corte y rangos temporales"""
    fechas_info = {
        "fecha_corte": None,
        "fecha_mas_reciente_historicos_usada": None,
        "total_historicos_usados": 0,
        "rango_historicos_completo": None,
        "rango_barridos": None,
    }

    # Fecha de corte (más antigua de barridos)
    if not df_barridos.empty and "FECHA" in df_barridos.columns:
        fechas_barridos = df_barridos["FECHA"].dropna()
        if len(fechas_barridos) > 0:
            fechas_info["fecha_corte"] = fechas_barridos.min().to_pydatetime()
            fechas_info["rango_barridos"] = (
                fechas_barridos.min().to_pydatetime(),
                fechas_barridos.max().to_pydatetime(),
            )

    # Procesar históricos según fecha de corte
    if not df_historical.empty and "FA UNICA" in df_historical.columns:
        fechas_historicos = df_historical["FA UNICA"].dropna()

        if len(fechas_historicos) > 0:
            fechas_info["rango_historicos_completo"] = (
                fechas_historicos.min().to_pydatetime(),
                fechas_historicos.max().to_pydatetime(),
            )

            if fechas_info["fecha_corte"]:
                fecha_corte_pd = pd.Timestamp(fechas_info["fecha_corte"])
                historicos_antes_corte = fechas_historicos[
                    fechas_historicos < fecha_corte_pd
                ]

                if len(historicos_antes_corte) > 0:
                    fechas_info["fecha_mas_reciente_historicos_usada"] = (
                        historicos_antes_corte.max().to_pydatetime()
                    )
                    fechas_info["total_historicos_usados"] = len(historicos_antes_corte)
                else:
                    fechas_info["fecha_mas_reciente_historicos_usada"] = (
                        fechas_historicos.max().to_pydatetime()
                    )
                    fechas_info["total_historicos_usados"] = len(fechas_historicos)
            else:
                fechas_info["fecha_mas_reciente_historicos_usada"] = (
                    fechas_historicos.max().to_pydatetime()
                )
                fechas_info["total_historicos_usados"] = len(fechas_historicos)

    # Mostrar información de fechas de corte (MANTENER)
    if fechas_info["fecha_corte"]:
        st.success(
            f"📅 **Fecha de corte (inicio barridos):** {fechas_info['fecha_corte'].strftime('%d/%m/%Y')}"
        )

    if fechas_info["fecha_mas_reciente_historicos_usada"]:
        st.info(
            f"📅 **Último histórico usado:** {fechas_info['fecha_mas_reciente_historicos_usada'].strftime('%d/%m/%Y')} ({fechas_info['total_historicos_usados']:,} registros)"
        )

    if fechas_info["rango_historicos_completo"]:
        inicio, fin = fechas_info["rango_historicos_completo"]
        st.info(
            f"📊 **Rango completo históricos:** {inicio.strftime('%d/%m/%Y')} - {fin.strftime('%d/%m/%Y')}"
        )

    if fechas_info["rango_barridos"]:
        inicio, fin = fechas_info["rango_barridos"]
        st.info(
            f"🚨 **Período barridos:** {inicio.strftime('%d/%m/%Y')} - {fin.strftime('%d/%m/%Y')}"
        )

    return fechas_info


def combine_vaccination_data(df_historical, df_barridos, fechas_info):
    """Combina datos históricos PAI y barridos con lógica corregida"""
    combined_data = {
        "temporal_data": pd.DataFrame(),
        "historical_processed": {},
        "barridos_totales": {},
        "total_individual": 0,
        "total_barridos": 0,
        "total_general": 0,
        "fechas_info": fechas_info,
    }

    # Procesar datos históricos PAI
    if not df_historical.empty:
        fecha_corte = fechas_info.get("fecha_corte")

        if fecha_corte and "FA UNICA" in df_historical.columns:
            fecha_corte_pd = pd.Timestamp(fecha_corte)
            mask_pre = df_historical["FA UNICA"] < fecha_corte_pd
            df_pre = df_historical[mask_pre].copy()
        else:
            df_pre = df_historical.copy()

        combined_data["historical_processed"] = process_historical_by_age(df_pre)
        combined_data["total_individual"] = combined_data["historical_processed"][
            "total_individual"
        ]

        if "FA UNICA" in df_pre.columns:
            df_hist_temporal = df_pre[df_pre["FA UNICA"].notna()].copy()
            df_hist_temporal["fecha"] = df_hist_temporal["FA UNICA"]
            df_hist_temporal["fuente"] = "Históricos (PAI)"
            df_hist_temporal["tipo"] = "individual"
            combined_data["temporal_data"] = df_hist_temporal[
                ["fecha", "fuente", "tipo"]
            ].copy()

    # Procesar datos de barridos
    if not df_barridos.empty:
        combined_data["barridos_totales"] = process_barridos_totals(df_barridos)
        combined_data["total_barridos"] = combined_data["barridos_totales"][
            "total_vacunados"
        ]

        if "FECHA" in df_barridos.columns:
            barridos_temporales = []
            age_columns_by_stage, _ = detect_age_columns_barridos(df_barridos)
            etapa_4_cols = age_columns_by_stage.get("etapa_4_vacunada_barrido", {})

            for _, row in df_barridos.iterrows():
                if pd.notna(row.get("FECHA")):
                    vacunas_aplicadas = 0
                    for col in etapa_4_cols.values():
                        if col in df_barridos.columns:
                            valor = pd.to_numeric(row[col], errors="coerce")
                            if pd.notna(valor):
                                vacunas_aplicadas += int(valor)

                    if vacunas_aplicadas > 0:
                        registros_a_crear = min(vacunas_aplicadas, 100)
                        for _ in range(registros_a_crear):
                            barridos_temporales.append(
                                {
                                    "fecha": row["FECHA"],
                                    "fuente": "Barridos (Emergencia)",
                                    "tipo": "barrido",
                                }
                            )

            if barridos_temporales:
                df_barr_temporal = pd.DataFrame(barridos_temporales)
                combined_data["temporal_data"] = pd.concat(
                    [combined_data["temporal_data"], df_barr_temporal],
                    ignore_index=True,
                )

    combined_data["total_general"] = (
        combined_data["total_individual"] + combined_data["total_barridos"]
    )

    return combined_data


def main():
    """Función principal con carga secuencial y timeout"""
    st.title("🏥 Dashboard de Vacunación Fiebre Amarilla")
    st.markdown("**Departamento del Tolima - Barridos Territoriales**")

    # Sidebar
    with st.sidebar:
        # ... tu código de sidebar existente ...
        pass

    # CARGA SECUENCIAL CON PROGRESO TOTAL
    st.markdown("### 📥 Cargando datos necesarios...")

    total_progress = st.progress(0)
    overall_status = st.empty()

    # 1. Cargar históricos (40% del progreso)
    overall_status.text("1/3 Cargando datos históricos de vacunación...")
    df_historical = load_historical_data()
    total_progress.progress(0.33)

    # 2. Cargar población (30% del progreso)
    overall_status.text("2/3 Cargando datos de población...")
    df_population = load_population_data()
    total_progress.progress(0.66)

    # 3. Cargar barridos (30% del progreso)
    overall_status.text("3/3 Cargando datos de barridos...")
    df_barridos = load_barridos_data()
    total_progress.progress(1.0)

    # Limpiar progreso
    overall_status.text("✅ Todos los datos cargados")
    time.sleep(1)
    total_progress.empty()
    overall_status.empty()

    # Verificar que se cargaron datos críticos
    if df_historical.empty and df_barridos.empty:
        st.error(
            "❌ No se pudieron cargar datos críticos. Revisa tu conexión y permisos."
        )
        st.stop()

    # Determinar fechas de corte (mantener solo estos mensajes)
    fechas_info = determine_cutoff_date(df_barridos, df_historical)

    # Combinar datos
    combined_data = combine_vaccination_data(df_historical, df_barridos, fechas_info)

    # Estado de datos (simplificado)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status = "✅" if combined_data["total_individual"] > 0 else "❌"
        st.markdown(
            f"{status} **Individual:** {combined_data['total_individual']:,} vacunados"
        )

    with col2:
        status = "✅" if combined_data["total_barridos"] > 0 else "❌"
        st.markdown(
            f"{status} **Barridos:** {combined_data['total_barridos']:,} vacunas aplicadas"
        )

    with col3:
        status = "✅" if not df_population.empty else "❌"
        municipios_count = "47 municipios" if not df_population.empty else "Sin datos"
        st.markdown(f"{status} **Población:** {municipios_count}")

    with col4:
        if (
            not df_historical.empty
            and "NombreMunicipioResidencia" in df_historical.columns
        ):
            municipios_unicos = df_historical["NombreMunicipioResidencia"].nunique()
            status_mun = "✅" if municipios_unicos == 47 else "⚠️"
            st.markdown(f"{status_mun} **Municipios detectados:** {municipios_unicos}")
        else:
            st.markdown("❌ **Municipios:** No detectados")

    st.markdown("---")

    # Tabs principales
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Resumen", "📅 Temporal", "🗺️ Geográfico", "🏥 Población"]
    )

    with tab1:
        show_overview_tab(
            combined_data, df_population, fechas_info, COLORS, RANGOS_EDAD
        )

    with tab2:
        show_temporal_tab(combined_data, COLORS)

    with tab3:
        show_geographic_tab(combined_data, COLORS)

    with tab4:
        show_population_tab(df_population, combined_data, COLORS)

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #7D0F2B;'>"
        "<small>Dashboard de Vacunación v2.3 - Secretaría de Salud del Tolima</small><br>"
        "<small>Modularizado y optimizado</small>"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
