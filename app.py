"""
app.py - Dashboard de Vacunación Fiebre Amarilla - Tolima
Versión 2.2 - Estructura corregida: 11 rangos + totales, detección por posición,
enfoque en vacunas aplicadas, fechas completas, municipios correctos
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

# Rangos de edad actualizados (11 rangos)
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
                df = pd.read_excel("data/Resumen.xlsx", sheet_name="Vacunacion")
            except:
                try:
                    df = pd.read_excel("data/Resumen.xlsx", sheet_name="Barridos")
                except:
                    # Si no existe, usar la primera hoja
                    df = pd.read_excel("data/Resumen.xlsx", sheet_name=0)

            if not df.empty:
                # Convertir fechas
                if "FECHA" in df.columns:
                    df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")

                st.info(f"🔍 **Barridos cargados:** {len(df)} registros")
                st.info(f"📊 **Columnas disponibles:** {len(df.columns)} columnas")

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
    """Detecta 11 rangos + 1 total = 12 columnas por etapa (ESTRUCTURA REAL)"""
    age_columns_by_stage = {
        "etapa_1_encontrada": {},
        "etapa_2_previa": {},
        "etapa_3_no_vacunada": {},
        "etapa_4_vacunada_barrido": {},
    }

    # Columnas de totales por etapa
    total_columns_by_stage = {
        "etapa_1_encontrada": None,  # TPE
        "etapa_2_previa": None,  # TPVP
        "etapa_3_no_vacunada": None,  # TPNVP
        "etapa_4_vacunada_barrido": None,  # TPVB
    }

    # 11 rangos base exactos
    rangos_patrones = {
        "<1": ["< 1 AÑO"],
        "1-5": ["1-5 AÑOS"],
        "6-10": ["6-10 AÑOS"],
        "11-20": ["11-20 AÑOS"],
        "21-30": ["21-30 AÑOS"],
        "31-40": ["31-40 AÑOS"],
        "41-50": ["41-50 AÑOS"],
        "51-59": ["51-59 AÑOS"],
        "60+": ["60 Y MAS"],  # Rango principal 60+
        "60-69": ["60-69 AÑOS"],  # Rango específico 60-69
        "70+": ["70 AÑOS Y MAS"],  # Rango específico 70+
    }

    # Detectar columnas de totales primero
    total_patterns = {
        "etapa_1_encontrada": ["TPE"],
        "etapa_2_previa": ["TPVP"],
        "etapa_3_no_vacunada": ["TPNVP"],
        "etapa_4_vacunada_barrido": ["TPVB"],
    }

    for etapa, patterns in total_patterns.items():
        for col_name in df.columns:
            col_str = str(col_name).upper().strip()
            if col_str in patterns:
                total_columns_by_stage[etapa] = col_name
                break

    # Para cada rango, encontrar TODAS sus variaciones y ordenarlas por posición
    for rango, patrones in rangos_patrones.items():
        columnas_encontradas = []

        # Buscar todas las columnas que contengan EXACTAMENTE este patrón
        for col_idx, col_name in enumerate(df.columns):
            col_str = str(col_name).upper().strip()

            for patron in patrones:
                # Verificación EXACTA del patrón
                if patron in col_str:
                    # Evitar confusiones entre rangos similares
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

        # Ordenar por posición en el DataFrame
        columnas_encontradas.sort(key=lambda x: x[0])

        # Asignar a etapas basándose en orden de aparición
        etapas = [
            "etapa_1_encontrada",
            "etapa_2_previa",
            "etapa_3_no_vacunada",
            "etapa_4_vacunada_barrido",
        ]

        for i, (col_idx, col_name) in enumerate(columnas_encontradas):
            if i < len(etapas):  # Solo asignar las primeras 4
                age_columns_by_stage[etapas[i]][rango] = col_name

    # Mostrar resumen de detección (CORREGIDO: 11 rangos + 1 total)
    st.success("🎯 **Detección por posición (11 rangos + 1 total = 12 columnas):**")
    etapa_labels = {
        "etapa_1_encontrada": "Etapa 1 - Población encontrada (TPE)",
        "etapa_2_previa": "Etapa 2 - Vacunada previamente (TPVP)",
        "etapa_3_no_vacunada": "Etapa 3 - No vacunada encontrada (TPNVP)",
        "etapa_4_vacunada_barrido": "Etapa 4 - Vacunada en barrido (TPVB)",
    }

    for etapa, columns in age_columns_by_stage.items():
        label = etapa_labels[etapa]
        count = len(columns)
        total_col = total_columns_by_stage[etapa]

        status = "✅" if count == 11 and total_col else "⚠️"
        total_status = f" + Total: {total_col}" if total_col else " + Total: ❌"

        st.write(f"{status} **{label}:** {count}/11 rangos{total_status}")

        # Mostrar rangos faltantes
        rangos_encontrados = set(columns.keys())
        rangos_esperados = set(rangos_patrones.keys())
        rangos_faltantes = rangos_esperados - rangos_encontrados
        if rangos_faltantes:
            st.write(f"   Rangos faltantes: {list(rangos_faltantes)}")

        # Mostrar algunos ejemplos
        if count > 0:
            ejemplos = list(columns.values())[:3]
            st.write(f"   Ejemplos: {ejemplos}")

    # Información sobre consolidación 60+
    st.info("📊 **Manejo de rangos 60+:**")
    st.write("• **60 Y MAS:** Rango principal 60+")
    st.write("• **60-69 AÑOS:** Subgrupo específico 60-69")
    st.write("• **70 AÑOS Y MAS:** Subgrupo específico 70+")
    st.write("• Todos se suman para el total 60+ en el dashboard")

    return age_columns_by_stage, total_columns_by_stage


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
    """Procesa totales de barridos con 11 rangos + consolidación 60+"""
    if df_barridos.empty:
        return {
            "total_vacunados": 0,
            "total_renuentes": 0,
            "por_edad": {},
            "renuentes_por_edad": {},
            "columns_info": {},
        }

    # Detectar columnas de edad por etapa (actualizada)
    age_columns_by_stage, total_columns_by_stage = detect_age_columns_barridos(
        df_barridos
    )

    st.info("🎯 **Enfoque en datos relevantes (11 rangos):**")
    st.write("• **Etapa 4 (TPVB):** Nueva vacunación realizada")
    st.write("• **Etapa 3 (TPNVP):** Renuentes/Rechazos para ajustar cobertura")

    totales = {
        "total_vacunados": 0,  # Solo etapa 4
        "total_renuentes": 0,  # Solo etapa 3
        "por_edad": {},  # Vacunados por edad (etapa 4)
        "renuentes_por_edad": {},  # Renuentes por edad (etapa 3)
        "columns_info": {
            "age_columns_by_stage": age_columns_by_stage,
            "total_columns_by_stage": total_columns_by_stage,
        },
    }

    # Procesar SOLO Etapa 4 (Vacunados en barrido) - DATO PRINCIPAL
    etapa_4_columns = age_columns_by_stage.get("etapa_4_vacunada_barrido", {})

    # Procesar los 11 rangos base
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

    # Consolidar rangos 60+ (60 Y MAS + 60-69 AÑOS + 70 AÑOS Y MAS)
    total_60_consolidado = 0
    rangos_60_plus = ["60+", "60-69", "70+"]

    for rango_60 in rangos_60_plus:
        if rango_60 in totales["por_edad"]:
            total_60_consolidado += totales["por_edad"][rango_60]["total"]

    # Actualizar el rango 60+ consolidado
    if total_60_consolidado > 0:
        totales["por_edad"]["60+"] = {
            "total": total_60_consolidado,
            "label": "60 años y más (consolidado)",
            "column": "consolidado",
        }
        # Remover subrangos para evitar doble conteo en visualizaciones
        for rango_sub in ["60-69", "70+"]:
            if rango_sub in totales["por_edad"]:
                del totales["por_edad"][rango_sub]

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
                "label": RANGOS_EDAD.get(rango, rango),
                "column": col_name,
            }
            totales["total_renuentes"] += total_rango

    # Consolidar renuentes 60+ también
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
        # Remover subrangos
        for rango_sub in ["60-69", "70+"]:
            if rango_sub in totales["renuentes_por_edad"]:
                del totales["renuentes_por_edad"][rango_sub]

    # Usar columna de total si está disponible
    total_etapa_4 = total_columns_by_stage.get("etapa_4_vacunada_barrido")
    if total_etapa_4 and total_etapa_4 in df_barridos.columns:
        total_verificacion = (
            pd.to_numeric(df_barridos[total_etapa_4], errors="coerce").fillna(0).sum()
        )
        st.info(
            f"✅ **Verificación con {total_etapa_4}:** {total_verificacion:,.0f} (calculado: {totales['total_vacunados']:,.0f})"
        )

    # Mostrar resumen enfocado
    st.success("✅ **Datos procesados (11 rangos + consolidación 60+):**")
    st.write(
        f"• **Nueva vacunación (Barridos):** {totales['total_vacunados']:,.0f} personas"
    )
    st.write(
        f"• **Renuentes/No vacunados:** {totales['total_renuentes']:,.0f} personas"
    )
    st.write(f"• **Rangos procesados:** {len(totales['por_edad'])} (consolidados)")

    return totales


def determine_cutoff_date(df_barridos, df_historical):
    """Determina fechas de corte y rangos temporales"""
    fechas_info = {
        "fecha_corte": None,
        "fecha_mas_reciente_historicos_usada": None,  # ANTES del corte
        "total_historicos_usados": 0,
        "rango_historicos_completo": None,
        "rango_barridos": None,
    }

    # Fecha de corte (más antigua de barridos) - CONVERTIR A DATETIME PYTHON
    if not df_barridos.empty and "FECHA" in df_barridos.columns:
        fechas_barridos = df_barridos["FECHA"].dropna()
        if len(fechas_barridos) > 0:
            # Convertir a datetime de Python para compatibilidad con plotly
            fechas_info["fecha_corte"] = fechas_barridos.min().to_pydatetime()
            fechas_info["rango_barridos"] = (
                fechas_barridos.min().to_pydatetime(),
                fechas_barridos.max().to_pydatetime(),
            )

    # Procesar históricos según fecha de corte
    if not df_historical.empty and "FA UNICA" in df_historical.columns:
        fechas_historicos = df_historical["FA UNICA"].dropna()

        if len(fechas_historicos) > 0:
            # Rango completo de históricos - CONVERTIR A DATETIME PYTHON
            fechas_info["rango_historicos_completo"] = (
                fechas_historicos.min().to_pydatetime(),
                fechas_historicos.max().to_pydatetime(),
            )

            # Si hay fecha de corte, filtrar históricos ANTES del corte
            if fechas_info["fecha_corte"]:
                # Convertir fecha_corte de vuelta a pandas timestamp para comparación
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
                    # Si no hay históricos antes del corte, usar todos
                    fechas_info["fecha_mas_reciente_historicos_usada"] = (
                        fechas_historicos.max().to_pydatetime()
                    )
                    fechas_info["total_historicos_usados"] = len(fechas_historicos)
            else:
                # Sin fecha de corte, usar todos los históricos
                fechas_info["fecha_mas_reciente_historicos_usada"] = (
                    fechas_historicos.max().to_pydatetime()
                )
                fechas_info["total_historicos_usados"] = len(fechas_historicos)

    # Mostrar información completa
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
        "fechas_info": fechas_info,  # Mantener info de fechas
    }

    # Procesar datos históricos PAI (ANTES de la fecha de corte)
    if not df_historical.empty:
        fecha_corte = fechas_info.get("fecha_corte")

        if fecha_corte and "FA UNICA" in df_historical.columns:
            # Convertir fecha_corte a pandas timestamp para comparación
            fecha_corte_pd = pd.Timestamp(fecha_corte)
            # Filtrar solo registros ANTES del corte
            mask_pre = df_historical["FA UNICA"] < fecha_corte_pd
            df_pre = df_historical[mask_pre].copy()
            st.info(
                f"📊 Registros históricos usados: {len(df_pre):,} de {len(df_historical):,} (antes del corte)"
            )
        else:
            # Si no hay fecha de corte, usar todos los datos históricos
            df_pre = df_historical.copy()

        # Procesar por rangos de edad
        combined_data["historical_processed"] = process_historical_by_age(df_pre)
        combined_data["total_individual"] = combined_data["historical_processed"][
            "total_individual"
        ]

        # Preparar datos temporales
        if "FA UNICA" in df_pre.columns:
            df_hist_temporal = df_pre[df_pre["FA UNICA"].notna()].copy()
            df_hist_temporal["fecha"] = df_hist_temporal["FA UNICA"]
            df_hist_temporal["fuente"] = "Históricos (PAI)"
            df_hist_temporal["tipo"] = "individual"
            combined_data["temporal_data"] = df_hist_temporal[
                ["fecha", "fuente", "tipo"]
            ].copy()

    # Procesar datos de barridos (enfoque en vacunas aplicadas)
    if not df_barridos.empty:
        combined_data["barridos_totales"] = process_barridos_totals(df_barridos)
        combined_data["total_barridos"] = combined_data["barridos_totales"][
            "total_vacunados"
        ]

        # Preparar datos temporales de barridos
        if "FECHA" in df_barridos.columns:
            barridos_temporales = []

            # Obtener columnas de etapa 4 (vacunas aplicadas)
            age_columns_by_stage, _ = detect_age_columns_barridos(df_barridos)
            etapa_4_cols = age_columns_by_stage.get("etapa_4_vacunada_barrido", {})

            for _, row in df_barridos.iterrows():
                if pd.notna(row.get("FECHA")):
                    # Contar vacunas aplicadas en este barrido
                    vacunas_aplicadas = 0
                    for col in etapa_4_cols.values():
                        if col in df_barridos.columns:
                            valor = pd.to_numeric(row[col], errors="coerce")
                            if pd.notna(valor):
                                vacunas_aplicadas += int(valor)

                    # Crear registros temporales proporcionales a vacunas aplicadas
                    if vacunas_aplicadas > 0:
                        # Limitar a 100 registros por barrido para performance
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

    # Total general = PAI + Nueva vacunación de barridos
    combined_data["total_general"] = (
        combined_data["total_individual"] + combined_data["total_barridos"]
    )

    st.success("✅ **Lógica integrada PAI + Barridos (CORREGIDA):**")
    st.write(
        f"• **PAI (antes del corte):** {combined_data['total_individual']:,} vacunados"
    )
    st.write(
        f"• **Barridos (vacunas aplicadas):** {combined_data['total_barridos']:,} vacunados"
    )
    st.write(f"• **TOTAL INTEGRADO:** {combined_data['total_general']:,} vacunados")

    return combined_data


def show_overview_tab(combined_data, df_population, fechas_info):
    """Muestra la vista general del dashboard con datos combinados (CORREGIDO)"""
    st.header("📊 Resumen General")

    # Información de división temporal (CORREGIDO)
    if fechas_info.get("fecha_corte"):
        fecha_corte_str = fechas_info["fecha_corte"].strftime("%d/%m/%Y")
        st.info(
            f"🔄 **División temporal:** Corte el {fecha_corte_str} (inicio de barridos)"
        )

    if fechas_info.get("fecha_mas_reciente_historicos_usada"):
        fecha_hist_str = fechas_info["fecha_mas_reciente_historicos_usada"].strftime(
            "%d/%m/%Y"
        )
        registros_usados = fechas_info.get("total_historicos_usados", 0)
        st.info(
            f"📊 **Último histórico usado:** {fecha_hist_str} ({registros_usados:,} registros antes del corte)"
        )

    # Métricas principales corregidas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "PAI (Históricos)",
            f"{combined_data['total_individual']:,}".replace(",", "."),
            delta="Vacunación previa registrada",
        )

    with col2:
        st.metric(
            "Barridos (Vacunas aplicadas)",
            f"{combined_data['total_barridos']:,}".replace(",", "."),
            delta="Nueva vacunación en terreno",
        )

    with col3:
        # Población FIJA
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
                "Población Total (47 municipios)",
                f"{total_population:,}".replace(",", "."),
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


def show_temporal_tab(combined_data):
    """Muestra análisis temporal mejorado con gráfico combinado"""
    st.header("📅 Análisis Temporal")

    fechas_info = combined_data.get("fechas_info", {})

    # Mostrar información de fechas
    col1, col2 = st.columns(2)

    with col1:
        if fechas_info.get("rango_historicos_completo"):
            inicio, fin = fechas_info["rango_historicos_completo"]
            st.info(
                f"📊 **Históricos (PAI):**\n{inicio.strftime('%d/%m/%Y')} - {fin.strftime('%d/%m/%Y')}"
            )

    with col2:
        if fechas_info.get("rango_barridos"):
            inicio, fin = fechas_info["rango_barridos"]
            st.info(
                f"🚨 **Barridos:**\n{inicio.strftime('%d/%m/%Y')} - {fin.strftime('%d/%m/%Y')}"
            )

    # Gráfico temporal combinado
    if not combined_data["temporal_data"].empty:
        st.subheader("📈 Evolución Temporal por Fuente de Datos")

        df_temporal = combined_data["temporal_data"].copy()

        # Agregar por fecha y fuente
        daily_summary = (
            df_temporal.groupby([df_temporal["fecha"].dt.date, "fuente"])
            .size()
            .reset_index()
        )
        daily_summary.columns = ["Fecha", "Fuente", "Vacunados"]
        daily_summary["Fecha"] = pd.to_datetime(daily_summary["Fecha"])

        # Crear gráfico con colores diferenciados
        fig = px.line(
            daily_summary,
            x="Fecha",
            y="Vacunados",
            color="Fuente",
            title="Vacunación por Día - Históricos vs Barridos",
            color_discrete_map={
                "Históricos (PAI)": COLORS["primary"],
                "Barridos (Emergencia)": COLORS["warning"],
            },
        )

        # Agregar línea vertical en fecha de corte - VERSIÓN CORREGIDA
        if fechas_info.get("fecha_corte"):
            try:
                # Convertir a string ISO para máxima compatibilidad
                fecha_corte = fechas_info["fecha_corte"]
                if hasattr(fecha_corte, "strftime"):
                    fecha_corte_str = fecha_corte.strftime("%Y-%m-%d")
                else:
                    fecha_corte_str = str(fecha_corte)

                # Usar add_shape en lugar de add_vline para mayor control
                fig.add_shape(
                    type="line",
                    x0=fecha_corte_str,
                    x1=fecha_corte_str,
                    y0=0,
                    y1=1,
                    yref="paper",
                    line=dict(color="red", width=2, dash="dash"),
                )

                # Agregar anotación separadamente
                fig.add_annotation(
                    x=fecha_corte_str,
                    y=0.95,
                    yref="paper",
                    text="Inicio Barridos",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor="red",
                    font=dict(color="red"),
                    bgcolor="white",
                    bordercolor="red",
                    borderwidth=1,
                )

            except Exception as e:
                st.warning(f"No se pudo agregar línea de fecha de corte: {str(e)}")

        fig.update_layout(
            plot_bgcolor=COLORS["white"], paper_bgcolor=COLORS["white"], height=500
        )

        st.plotly_chart(fig, use_container_width=True)

        # Estadísticas comparativas
        st.subheader("📊 Estadísticas Comparativas")

        col1, col2, col3 = st.columns(3)

        with col1:
            historicos_dias = daily_summary[
                daily_summary["Fuente"] == "Históricos (PAI)"
            ]
            if not historicos_dias.empty:
                promedio_hist = historicos_dias["Vacunados"].mean()
                st.metric("Promedio Diario Históricos", f"{promedio_hist:.1f}")

        with col2:
            barridos_dias = daily_summary[
                daily_summary["Fuente"] == "Barridos (Emergencia)"
            ]
            if not barridos_dias.empty:
                promedio_barr = barridos_dias["Vacunados"].mean()
                st.metric("Promedio Diario Barridos", f"{promedio_barr:.1f}")

        with col3:
            if not historicos_dias.empty and not barridos_dias.empty:
                incremento = ((promedio_barr - promedio_hist) / promedio_hist) * 100
                st.metric("Incremento de Ritmo", f"{incremento:+.1f}%")
    else:
        st.info("No hay datos temporales disponibles para mostrar")


def show_geographic_tab(combined_data):
    """Muestra análisis geográfico con conteo correcto de municipios"""
    st.header("🗺️ Distribución Geográfica")

    col1, col2 = st.columns(2)

    with col1:
        # Vacunación individual por municipio (CORREGIDO)
        if (
            combined_data.get("historical_processed", {})
            and not combined_data.get("temporal_data", pd.DataFrame()).empty
        ):
            st.subheader("📍 Vacunación Individual por Municipio")

            # Obtener datos históricos desde temporal_data
            df_hist = combined_data["temporal_data"][
                combined_data["temporal_data"]["fuente"] == "Históricos (PAI)"
            ]

            if not df_hist.empty:
                # Agrupar por fecha para contar municipios únicos por día
                municipios_por_dia = (
                    df_hist.groupby(df_hist["fecha"].dt.date).size().reset_index()
                )
                municipios_por_dia.columns = ["Fecha", "Vacunados"]

                # Tomar top fechas con más vacunaciones
                top_fechas = municipios_por_dia.nlargest(15, "Vacunados")

                fig = px.bar(
                    top_fechas,
                    x="Vacunados",
                    y="Fecha",
                    orientation="h",
                    title="Top 15 Días - Vacunación Individual",
                    color_discrete_sequence=[COLORS["primary"]],
                )
                fig.update_layout(
                    plot_bgcolor=COLORS["white"],
                    paper_bgcolor=COLORS["white"],
                    height=500,
                    yaxis={"categoryorder": "total ascending"},
                )
                st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("Datos históricos no disponibles para análisis geográfico")

    with col2:
        # Barridos por municipio (enfoque en vacunas aplicadas)
        barridos_data = combined_data.get("barridos_totales", {})
        if barridos_data.get("columns_info"):
            st.subheader("🚨 Vacunas Aplicadas por Barridos")

            # Obtener datos de barridos desde temporal_data
            df_barr = combined_data["temporal_data"][
                combined_data["temporal_data"]["fuente"] == "Barridos (Emergencia)"
            ]

            if not df_barr.empty:
                # Agrupar por fecha para mostrar vacunas aplicadas
                vacunas_por_dia = (
                    df_barr.groupby(df_barr["fecha"].dt.date).size().reset_index()
                )
                vacunas_por_dia.columns = ["Fecha", "Vacunas_Aplicadas"]

                # Tomar top fechas con más vacunas aplicadas
                top_vacunas = vacunas_por_dia.nlargest(15, "Vacunas_Aplicadas")

                fig = px.bar(
                    top_vacunas,
                    x="Vacunas_Aplicadas",
                    y="Fecha",
                    orientation="h",
                    title="Top 15 Días - Vacunas Aplicadas en Barridos",
                    color_discrete_sequence=[COLORS["warning"]],
                )
                fig.update_layout(
                    plot_bgcolor=COLORS["white"],
                    paper_bgcolor=COLORS["white"],
                    height=500,
                    yaxis={"categoryorder": "total ascending"},
                )
                st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("Datos de barridos no disponibles para análisis geográfico")


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
    """Función principal del dashboard corregida"""
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
        st.markdown("- **Fuente 1:** PAI (Históricos individuales)")
        st.markdown("- **Fuente 2:** Barridos (Vacunas aplicadas)")
        st.markdown("- **Población:** Base EAPB (47 municipios)")
        st.markdown("- **Análisis:** Cobertura + Renuencia")
        st.markdown("- **Período:** 2024-2025")
        st.markdown("---")

        # Mostrar rangos de edad
        st.markdown("### 📊 Rangos de Edad (11 rangos)")
        for code, label in RANGOS_EDAD.items():
            st.markdown(f"- **{code}:** {label}")
        st.markdown("---")

        # Información metodológica actualizada
        st.markdown("### 🔬 Metodología v2.2")
        st.markdown("**Sistema integrado:**")
        st.markdown("• **PAI:** Vacunación histórica individual")
        st.markdown("• **Barridos:** Solo vacunas aplicadas (Etapa 4)")
        st.markdown("• **Municipios:** 47 únicos (sin EAPB)")
        st.markdown("• **Temporal:** Colores por fuente de datos")
        st.markdown("• **Detección:** Por posición (11 rangos + totales)")
        st.markdown("• **Total = PAI + Vacunas de Barridos**")
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
                            "data/Resumen.xlsx", sheet_name="Vacunacion"
                        )
                    except:
                        try:
                            df_barridos = pd.read_excel(
                                "data/Resumen.xlsx", sheet_name="Barridos"
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

    # Determinar fechas de corte y rangos temporales (FUNCIÓN CORREGIDA)
    fechas_info = determine_cutoff_date(df_barridos, df_historical)

    # Combinar datos con información temporal completa (FUNCIÓN CORREGIDA)
    combined_data = combine_vaccination_data(df_historical, df_barridos, fechas_info)

    # Estado de datos con información corregida
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
        # Verificar conteo real de municipios
        if (
            not df_historical.empty
            and "NombreMunicipioResidencia" in df_historical.columns
        ):
            municipios_unicos = df_historical["NombreMunicipioResidencia"].nunique()
            status_mun = "✅" if municipios_unicos == 47 else "⚠️"
            st.markdown(f"{status_mun} **Municipios detectados:** {municipios_unicos}")
        else:
            st.markdown("❌ **Municipios:** No detectados")

    # Mostrar información de fechas de forma prominente
    if fechas_info.get("fecha_corte") or fechas_info.get(
        "fecha_mas_reciente_historicos_usada"
    ):
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            if fechas_info.get("fecha_mas_reciente_historicos_usada"):
                fecha_str = fechas_info["fecha_mas_reciente_historicos_usada"].strftime(
                    "%d/%m/%Y"
                )
                st.info(f"📅 **Último registro histórico usado:** {fecha_str}")

        with col2:
            if fechas_info.get("fecha_corte"):
                fecha_str = fechas_info["fecha_corte"].strftime("%d/%m/%Y")
                st.success(f"🚨 **Inicio de barridos:** {fecha_str}")

    st.markdown("---")

    # Tabs principales
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Resumen", "📅 Temporal", "🗺️ Geográfico", "🏥 Población"]
    )

    with tab1:
        show_overview_tab(combined_data, df_population, fechas_info)

    with tab2:
        show_temporal_tab(combined_data)

    with tab3:
        show_geographic_tab(combined_data)

    with tab4:
        show_population_tab(df_population, combined_data)

    # Footer actualizado
    st.markdown("---")

    # Información técnica del dashboard
    with st.expander("ℹ️ Información Técnica del Dashboard v2.2"):
        st.markdown("### 📊 **Especificaciones Técnicas:**")
        st.markdown(
            "- **Fuente PAI:** Registros individuales con cálculo de edad desde fecha de nacimiento"
        )
        st.markdown("- **Fuente Barridos:** Solo Etapa 4 (vacunas realmente aplicadas)")
        st.markdown("- **Detección:** Por posición, 11 rangos + totales por etapa")
        st.markdown(
            "- **Municipios:** 47 únicos, filtrado para excluir nombres de EAPB"
        )
        st.markdown("- **Temporal:** Diferenciación por colores según fuente")
        st.markdown("- **Población:** Base fija sin restar renuentes")

        st.markdown("### 🎯 **Rangos de Edad (11 rangos):**")
        st.markdown(
            "< 1, 1-5, 6-10, 11-20, 21-30, 31-40, 41-50, 51-59, 60+, 60-69, 70+ años"
        )

        st.markdown("### 📈 **Métricas Calculadas:**")
        st.markdown("- **Cobertura Total:** (PAI + Barridos) / Población × 100")
        st.markdown(
            "- **Tasa de Aceptación:** Vacunados / (Vacunados + Renuentes) × 100"
        )
        st.markdown("- **Incremento por Barridos:** Solo vacunas nuevas aplicadas")

        st.markdown("### 🔧 **Estructura de Datos:**")
        st.markdown("- **Etapa 1:** TPE (Total Población Encontrada)")
        st.markdown("- **Etapa 2:** TPVP (Total Población Vacunada Previamente)")
        st.markdown("- **Etapa 3:** TPNVP (Total Población No Vacunada Previamente)")
        st.markdown("- **Etapa 4:** TPVB (Total Población Vacunada en Barrido)")

    st.markdown(
        "<div style='text-align: center; color: #7D0F2B;'>"
        "<small>Dashboard de Vacunación v2.2 - Secretaría de Salud del Tolima</small><br>"
        "<small>Estructura completa: 11 rangos + totales + detección por posición</small>"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
