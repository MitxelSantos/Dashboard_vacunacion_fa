"""
app.py - Dashboard de Vacunación Fiebre Amarilla - Tolima
Versión 2.4 - Corregida con arquitectura robusta de carga
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import os
import time
from pathlib import Path

# Importar módulos de Google Drive con manejo de errores mejorado
try:
    from google_drive_loader import (
        load_vaccination_data,
        load_population_data,
        load_barridos_data,
        load_logo,
        load_from_drive,
        validate_secrets,
    )

    GOOGLE_DRIVE_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ Google Drive no disponible: {str(e)}")
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


def show_system_status():
    """Muestra el estado del sistema de carga"""
    st.markdown("### 🔍 Estado del Sistema")

    # Verificar Google Drive
    if GOOGLE_DRIVE_AVAILABLE:
        valid, message = validate_secrets()
        if valid:
            st.success("✅ Google Drive: Configurado correctamente")
        else:
            st.warning(f"⚠️ Google Drive: {message}")
    else:
        st.error("❌ Google Drive: No disponible")

    # Verificar archivos locales
    local_files = {
        "Vacunación": Path("data/vacunacion_fa.csv"),
        "Población": Path("data/Poblacion_aseguramiento.xlsx"),
        "Barridos": Path("data/Resumen.xlsx"),
        "Logo": Path("assets/images/logo_gobernacion.png"),
    }

    st.markdown("**Archivos Locales:**")
    for name, path in local_files.items():
        if path.exists():
            size = path.stat().st_size
            st.success(f"✅ {name}: Disponible ({size:,} bytes)")
        else:
            st.error(f"❌ {name}: No encontrado")


@st.cache_data(ttl=3600)  # Cache por 1 hora
def load_historical_data():
    """
    Carga datos históricos de vacunación individual con arquitectura robusta
    """
    try:
        # Verificar archivo local primero
        local_file = Path("data/vacunacion_fa.csv")

        if local_file.exists():
            st.info("📁 Usando archivo local de vacunación")
            df = pd.read_csv(
                local_file, low_memory=False, encoding="utf-8", on_bad_lines="skip"
            )
        elif GOOGLE_DRIVE_AVAILABLE:
            st.info("☁️ Descargando datos de vacunación desde Google Drive...")
            df = load_vaccination_data()
        else:
            st.error("❌ No se puede acceder a datos de vacunación")
            return pd.DataFrame()

        # Procesar fechas si el DataFrame no está vacío
        if not df.empty:
            if "FA UNICA" in df.columns:
                df["FA UNICA"] = pd.to_datetime(df["FA UNICA"], errors="coerce")
            if "FechaNacimiento" in df.columns:
                df["FechaNacimiento"] = pd.to_datetime(
                    df["FechaNacimiento"], errors="coerce"
                )

            st.success(f"✅ Datos de vacunación cargados: {len(df):,} registros")
            return df
        else:
            st.warning("⚠️ No se encontraron datos de vacunación")
            return pd.DataFrame()

    except Exception as e:
        st.error(f"❌ Error cargando datos históricos: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_barridos_data_cached():
    """
    Carga datos de barridos territoriales con arquitectura robusta
    """
    try:
        # Verificar archivo local primero
        local_file = Path("data/Resumen.xlsx")

        if local_file.exists():
            st.info("📁 Usando archivo local de barridos")
            try:
                df = pd.read_excel(local_file, sheet_name="Vacunacion")
            except:
                try:
                    df = pd.read_excel(local_file, sheet_name="Barridos")
                except:
                    df = pd.read_excel(local_file, sheet_name=0)
        elif GOOGLE_DRIVE_AVAILABLE:
            st.info("☁️ Descargando datos de barridos desde Google Drive...")
            df = load_barridos_data()
        else:
            st.error("❌ No se puede acceder a datos de barridos")
            return pd.DataFrame()

        # Procesar fechas si el DataFrame no está vacío
        if not df.empty:
            if "FECHA" in df.columns:
                df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")

            st.success(f"✅ Datos de barridos cargados: {len(df):,} registros")
            return df
        else:
            st.warning("⚠️ No se encontraron datos de barridos")
            return pd.DataFrame()

    except Exception as e:
        st.error(f"❌ Error cargando barridos: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_population_data_cached():
    """
    Carga datos de población con arquitectura robusta
    """
    try:
        # Verificar archivo local primero
        local_file = Path("data/Poblacion_aseguramiento.xlsx")

        if local_file.exists():
            st.info("📁 Usando archivo local de población")
            df = pd.read_excel(local_file)
        elif GOOGLE_DRIVE_AVAILABLE:
            st.info("☁️ Descargando datos de población desde Google Drive...")
            df = load_population_data()
        else:
            st.error("❌ No se puede acceder a datos de población")
            return pd.DataFrame()

        if not df.empty:
            st.success(f"✅ Datos de población cargados: {len(df):,} registros")
            return df
        else:
            st.warning("⚠️ No se encontraron datos de población")
            return pd.DataFrame()

    except Exception as e:
        st.error(f"❌ Error cargando población: {str(e)}")
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
    """
    Función principal con carga secuencial mejorada y manejo robusto de errores
    """
    st.title("🏥 Dashboard de Vacunación Fiebre Amarilla")
    st.markdown("**Departamento del Tolima - Barridos Territoriales**")

    # Sidebar con logo y configuración
    with st.sidebar:
        # Logo de la Gobernación
        logo_path = None
        try:
            if GOOGLE_DRIVE_AVAILABLE:
                logo_path = load_logo()
            else:
                local_logo = Path("assets/images/logo_gobernacion.png")
                if local_logo.exists():
                    logo_path = str(local_logo)
        except:
            pass

        if logo_path and Path(logo_path).exists():
            st.image(logo_path, width=150, caption="Secretaría de Salud del Tolima")
        else:
            st.info("💡 Logo no encontrado")

        st.title("Dashboard Vacunación")
        st.subheader("Fiebre Amarilla")

        # Información del sistema
        if st.checkbox("🔍 Estado del Sistema"):
            show_system_status()

        st.markdown("---")
        st.markdown("**Desarrollado por:**")
        st.markdown("Ing. José Miguel Santos")
        st.markdown("Secretaría de Salud del Tolima © 2025")

    # CARGA SECUENCIAL CON PROGRESO Y VALIDACIÓN
    st.markdown("### 📥 Cargando datos necesarios...")

    # Verificar disponibilidad inicial
    with st.spinner("Inicializando sistema de carga..."):
        if GOOGLE_DRIVE_AVAILABLE:
            st.info("✅ Google Drive disponible")
        else:
            st.warning(
                "⚠️ Google Drive no disponible - usando archivos locales únicamente"
            )

    # Contenedor para el progreso
    progress_container = st.container()

    with progress_container:
        total_progress = st.progress(0)
        overall_status = st.empty()

        # 1. Cargar datos históricos (33% del progreso)
        overall_status.text("1/3 Cargando datos históricos de vacunación...")
        df_historical = load_historical_data()
        total_progress.progress(0.33)

        # 2. Cargar datos de población (66% del progreso)
        overall_status.text("2/3 Cargando datos de población...")
        df_population = load_population_data_cached()
        total_progress.progress(0.66)

        # 3. Cargar datos de barridos (100% del progreso)
        overall_status.text("3/3 Cargando datos de barridos...")
        df_barridos = load_barridos_data_cached()
        total_progress.progress(1.0)

        # Limpiar progreso
        time.sleep(1)
        total_progress.empty()
        overall_status.empty()

    # Validación de datos críticos
    st.markdown("### 📊 Validación de Datos")

    validation_results = []

    # Validar datos históricos
    if not df_historical.empty:
        validation_results.append("✅ **Datos históricos:** OK")
        if "FechaNacimiento" in df_historical.columns:
            validation_results.append("  ├─ ✅ Columna FechaNacimiento disponible")
        else:
            validation_results.append("  ├─ ⚠️ Falta columna FechaNacimiento")
    else:
        validation_results.append("❌ **Datos históricos:** Sin datos")

    # Validar datos de barridos
    if not df_barridos.empty:
        validation_results.append("✅ **Datos de barridos:** OK")
    else:
        validation_results.append("❌ **Datos de barridos:** Sin datos")

    # Validar datos de población
    if not df_population.empty:
        validation_results.append("✅ **Datos de población:** OK")
    else:
        validation_results.append("❌ **Datos de población:** Sin datos")

    # Mostrar resultados de validación
    for result in validation_results:
        st.markdown(result)

    # Verificar que tengamos datos mínimos para continuar
    if df_historical.empty and df_barridos.empty:
        st.error("❌ Sin datos suficientes para mostrar el dashboard")
        st.markdown(
            """
        ### 🔧 Posibles soluciones:
        1. **Verificar conexión a Google Drive** - Revisa los secretos en Streamlit Cloud
        2. **Subir archivos localmente** - Coloca los archivos en la carpeta `data/`
        3. **Verificar permisos** - Asegúrate de que los archivos en Drive sean accesibles
        4. **Contactar administrador** - Si el problema persiste
        """
        )

        # Mostrar información de debug
        with st.expander("🔍 Información de depuración"):
            st.write("**Google Drive disponible:**", GOOGLE_DRIVE_AVAILABLE)
            if GOOGLE_DRIVE_AVAILABLE:
                valid, message = validate_secrets()
                st.write("**Configuración válida:**", valid)
                st.write("**Mensaje:**", message)

        return

    # Si llegamos aquí, tenemos datos suficientes para continuar
    st.success("🎉 ¡Datos cargados exitosamente! Procesando dashboard...")

    # Determinar fechas de corte
    fechas_info = determine_cutoff_date(df_barridos, df_historical)

    # Mostrar información de fechas de corte
    if fechas_info.get("fecha_corte"):
        st.success(
            f"📅 **Fecha de corte (inicio barridos):** {fechas_info['fecha_corte'].strftime('%d/%m/%Y')}"
        )

    if fechas_info.get("fecha_mas_reciente_historicos_usada"):
        st.info(
            f"📅 **Último histórico usado:** {fechas_info['fecha_mas_reciente_historicos_usada'].strftime('%d/%m/%Y')} ({fechas_info['total_historicos_usados']:,} registros)"
        )

    if fechas_info.get("rango_historicos_completo"):
        inicio, fin = fechas_info["rango_historicos_completo"]
        st.info(
            f"📊 **Rango completo históricos:** {inicio.strftime('%d/%m/%Y')} - {fin.strftime('%d/%m/%Y')}"
        )

    if fechas_info.get("rango_barridos"):
        inicio, fin = fechas_info["rango_barridos"]
        st.info(
            f"🚨 **Período barridos:** {inicio.strftime('%d/%m/%Y')} - {fin.strftime('%d/%m/%Y')}"
        )

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
        try:
            show_overview_tab(
                combined_data, df_population, fechas_info, COLORS, RANGOS_EDAD
            )
        except Exception as e:
            st.error(f"❌ Error en vista Resumen: {str(e)}")

    with tab2:
        try:
            show_temporal_tab(combined_data, COLORS)
        except Exception as e:
            st.error(f"❌ Error en vista Temporal: {str(e)}")

    with tab3:
        try:
            show_geographic_tab(combined_data, COLORS)
        except Exception as e:
            st.error(f"❌ Error en vista Geográfico: {str(e)}")

    with tab4:
        try:
            show_population_tab(df_population, combined_data, COLORS)
        except Exception as e:
            st.error(f"❌ Error en vista Población: {str(e)}")

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #7D0F2B;'>"
        "<small>Dashboard de Vacunación v2.4 - Secretaría de Salud del Tolima</small><br>"
        "<small>Arquitectura robusta con carga mejorada</small>"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
