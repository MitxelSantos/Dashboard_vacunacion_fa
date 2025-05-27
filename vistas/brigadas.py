"""
vistas/brigadas.py - ARCHIVO COMPLETO
Vista de Brigadas Territoriales para el Dashboard de Vacunación
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta


def load_brigadas_data(file_path="data/Resumen.xlsx"):
    """
    Carga y procesa los datos de brigadas de vacunación
    """
    try:
        # Leer la hoja de Vacunacion
        df = pd.read_excel(file_path, sheet_name="Vacunacion")

        # Convertir fecha
        df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")

        # Limpiar nombres de municipios y veredas
        df["MUNICIPIO"] = df["MUNICIPIO"].astype(str).str.strip().str.title()
        df["VEREDAS"] = df["VEREDAS"].fillna("Sin especificar")

        # Normalizar valores numéricos principales
        numeric_columns = [
            "Efectivas (E)",
            "No Efectivas (NE)",
            "Fallidas (F)",
            "Casa renuente",
            "TPE",
            "TPVP",
            "TPNVP",
            "TPVB",
        ]

        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        return df

    except Exception as e:
        st.error(f"Error cargando datos de brigadas: {str(e)}")
        return pd.DataFrame()


def calculate_brigadas_metrics(df):
    """
    Calcula métricas principales de las brigadas
    """
    if df.empty:
        return {}

    return {
        "total_brigadas": len(df),
        "municipios_visitados": (
            df["MUNICIPIO"].nunique() if "MUNICIPIO" in df.columns else 0
        ),
        "veredas_visitadas": df["VEREDAS"].nunique() if "VEREDAS" in df.columns else 0,
        "fecha_inicio": df["FECHA"].min() if "FECHA" in df.columns else None,
        "fecha_fin": df["FECHA"].max() if "FECHA" in df.columns else None,
        "total_efectivas": (
            df["Efectivas (E)"].sum() if "Efectivas (E)" in df.columns else 0
        ),
        "total_no_efectivas": (
            df["No Efectivas (NE)"].sum() if "No Efectivas (NE)" in df.columns else 0
        ),
        "total_fallidas": (
            df["Fallidas (F)"].sum() if "Fallidas (F)" in df.columns else 0
        ),
        "casas_renuentes": (
            df["Casa renuente"].sum() if "Casa renuente" in df.columns else 0
        ),
        "poblacion_encontrada": df["TPE"].sum() if "TPE" in df.columns else 0,
        "poblacion_ya_vacunada": df["TPVP"].sum() if "TPVP" in df.columns else 0,
        "poblacion_no_vacuna": df["TPNVP"].sum() if "TPNVP" in df.columns else 0,
        "poblacion_vacunada_brigada": df["TPVB"].sum() if "TPVB" in df.columns else 0,
    }


def create_effectiveness_analysis(df):
    """
    Análisis de efectividad de las brigadas
    """
    if df.empty:
        return df

    try:
        # Calcular tasas de efectividad
        efectivas = df.get("Efectivas (E)", 0)
        no_efectivas = df.get("No Efectivas (NE)", 0)
        fallidas = df.get("Fallidas (F)", 0)
        total_intentos = efectivas + no_efectivas + fallidas

        df["tasa_efectividad"] = np.where(
            total_intentos > 0, (efectivas / total_intentos * 100).round(2), 0
        )

        tpe = df.get("TPE", 0)
        tpvb = df.get("TPVB", 0)

        df["tasa_aceptacion"] = np.where(tpe > 0, (tpvb / tpe * 100).round(2), 0)

        casa_renuente = df.get("Casa renuente", 0)
        df["resistencia_casa"] = np.where(
            tpe > 0, (casa_renuente / tpe * 100).round(2), 0
        )

    except Exception as e:
        st.warning(f"Error calculando efectividad: {str(e)}")

    return df


def show_brigadas_overview(df, colors):
    """
    Muestra resumen general de brigadas
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
    Análisis temporal de brigadas
    """
    st.subheader("📅 Evolución Temporal de Brigadas")

    if df.empty or "FECHA" not in df.columns:
        st.warning("⚠️ No hay datos temporales para mostrar")
        return

    try:
        # Agregar por fecha
        temporal_data = (
            df.groupby("FECHA")
            .agg(
                {
                    "Efectivas (E)": "sum",
                    "No Efectivas (NE)": "sum",
                    "Fallidas (F)": "sum",
                    "TPE": "sum",
                    "TPVB": "sum",
                }
            )
            .reset_index()
        )

        # Crear gráfico de evolución temporal
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=temporal_data["FECHA"],
                y=temporal_data["Efectivas (E)"],
                mode="lines+markers",
                name="Vacunaciones Efectivas",
                line=dict(color=colors.get("primary", "#7D0F2B"), width=3),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=temporal_data["FECHA"],
                y=temporal_data["TPE"],
                mode="lines+markers",
                name="Población Encontrada",
                line=dict(
                    color=colors.get("secondary", "#F2A900"), width=2, dash="dash"
                ),
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
        st.error(f"Error creando gráfico temporal: {str(e)}")


def show_territorial_analysis(df, colors):
    """
    Análisis territorial por municipios y veredas
    """
    st.subheader("🗺️ Análisis Territorial")

    if df.empty:
        st.warning("⚠️ No hay datos territoriales para mostrar")
        return

    col1, col2 = st.columns(2)

    with col1:
        try:
            # Top municipios por efectividad
            if "MUNICIPIO" in df.columns and "TPE" in df.columns:
                municipio_stats = (
                    df.groupby("MUNICIPIO")
                    .agg({"Efectivas (E)": "sum", "TPE": "sum", "TPVB": "sum"})
                    .reset_index()
                )

                municipio_stats["efectividad"] = np.where(
                    municipio_stats["TPE"] > 0,
                    (municipio_stats["TPVB"] / municipio_stats["TPE"] * 100).round(2),
                    0,
                )
                municipio_stats = municipio_stats.sort_values(
                    "efectividad", ascending=False
                ).head(10)

                # Crear gráfico simple
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
                st.info("Datos de municipios no disponibles")

        except Exception as e:
            st.error(f"Error en análisis territorial: {str(e)}")

    with col2:
        try:
            # Distribución de resultados
            total_efectivas = (
                df["Efectivas (E)"].sum() if "Efectivas (E)" in df.columns else 0
            )
            total_no_efectivas = (
                df["No Efectivas (NE)"].sum()
                if "No Efectivas (NE)" in df.columns
                else 0
            )
            total_fallidas = (
                df["Fallidas (F)"].sum() if "Fallidas (F)" in df.columns else 0
            )

            if total_efectivas + total_no_efectivas + total_fallidas > 0:
                resultados_data = pd.DataFrame(
                    {
                        "Resultado": ["Efectivas", "No Efectivas", "Fallidas"],
                        "Cantidad": [
                            total_efectivas,
                            total_no_efectivas,
                            total_fallidas,
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
                st.info("Datos de resultados no disponibles")

        except Exception as e:
            st.error(f"Error en gráfico de resultados: {str(e)}")


def show_demographic_brigadas_analysis(df, colors):
    """
    Análisis demográfico de brigadas por grupos de edad
    """
    st.subheader("👥 Análisis Demográfico por Grupos de Edad")

    if df.empty:
        st.warning("⚠️ No hay datos demográficos para mostrar")
        return

    # Buscar columnas de grupos de edad
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
    ]

    found_age_columns = []
    for pattern in age_patterns:
        if pattern in df.columns:
            found_age_columns.append(pattern)

    if found_age_columns:
        st.info(f"📊 Grupos de edad encontrados: {len(found_age_columns)}")

        # Crear análisis básico
        age_data = []
        for col in found_age_columns:
            total = df[col].sum()
            age_data.append({"Grupo_Edad": col, "Total": total})

        if age_data:
            age_df = pd.DataFrame(age_data)
            fig = px.bar(
                age_df,
                x="Grupo_Edad",
                y="Total",
                title="Distribución por Grupos de Edad",
                color_discrete_sequence=[colors.get("secondary", "#F2A900")],
            )

            fig.update_layout(
                plot_bgcolor="white", paper_bgcolor="white", xaxis_tickangle=45
            )

            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("💡 No se encontraron columnas de grupos de edad en los datos")


def show(data, filters, colors, fuente_poblacion="DANE"):
    """
    Vista principal de Brigadas Territoriales

    ESTA ES LA FUNCIÓN PRINCIPAL QUE DEBE EXISTIR
    """
    st.title("📍 Brigadas Territoriales")
    st.markdown(
        """
    Esta vista analiza los datos de las brigadas de vacunación casa a casa,
    mostrando efectividad, cobertura territorial y análisis demográfico.
    """
    )

    # Cargar datos de brigadas
    df_brigadas = load_brigadas_data()

    if df_brigadas.empty:
        st.error("❌ No se pudieron cargar los datos de brigadas")
        st.info(
            "💡 Asegúrate de que el archivo 'Resumen.xlsx' esté en la carpeta 'data/'"
        )
        st.info("📄 El archivo debe tener una hoja llamada 'Vacunacion'")

        # Mostrar información de debug
        with st.expander("🔍 Información de Debug"):
            st.write("Estructura esperada del archivo:")
            st.code(
                """
            data/
            └── Resumen.xlsx
                └── Hoja: Vacunacion
                    ├── FECHA
                    ├── MUNICIPIO  
                    ├── VEREDAS
                    ├── Efectivas (E)
                    ├── TPE, TPVP, TPNVP, TPVB
                    └── ... (otras columnas)
            """
            )
        return

    # Calcular efectividad
    df_brigadas = create_effectiveness_analysis(df_brigadas)

    # Filtros específicos para brigadas
    st.sidebar.subheader("Filtros de Brigadas")

    # Filtro por municipio
    if "MUNICIPIO" in df_brigadas.columns:
        municipios_brigadas = ["Todos"] + sorted(
            df_brigadas["MUNICIPIO"].dropna().unique().tolist()
        )
        municipio_brigada = st.sidebar.selectbox(
            "Municipio de Brigada:", municipios_brigadas
        )
    else:
        municipio_brigada = "Todos"
        st.sidebar.info("Filtro de municipio no disponible")

    # Filtro por rango de fechas
    if "FECHA" in df_brigadas.columns and not df_brigadas["FECHA"].isna().all():
        fecha_min = df_brigadas["FECHA"].min().date()
        fecha_max = df_brigadas["FECHA"].max().date()

        fecha_inicio = st.sidebar.date_input(
            "Fecha inicio:", value=fecha_min, min_value=fecha_min, max_value=fecha_max
        )

        fecha_fin = st.sidebar.date_input(
            "Fecha fin:", value=fecha_max, min_value=fecha_min, max_value=fecha_max
        )
    else:
        st.sidebar.warning("Filtros de fecha no disponibles")
        fecha_inicio = None
        fecha_fin = None

    # Aplicar filtros
    df_filtered = df_brigadas.copy()

    if municipio_brigada != "Todos" and "MUNICIPIO" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["MUNICIPIO"] == municipio_brigada]

    if fecha_inicio and fecha_fin and "FECHA" in df_filtered.columns:
        df_filtered = df_filtered[
            (df_filtered["FECHA"].dt.date >= fecha_inicio)
            & (df_filtered["FECHA"].dt.date <= fecha_fin)
        ]

    if df_filtered.empty:
        st.warning("⚠️ No hay datos con los filtros seleccionados")
        return

    st.success(f"✅ Datos cargados: {len(df_filtered)} brigadas")

    # Mostrar análisis
    show_brigadas_overview(df_filtered, colors)

    st.markdown("---")
    show_temporal_brigadas_analysis(df_filtered, colors)

    st.markdown("---")
    show_territorial_analysis(df_filtered, colors)

    st.markdown("---")
    show_demographic_brigadas_analysis(df_filtered, colors)

    # Tabla detallada básica
    st.subheader("📋 Datos de Brigadas")

    # Mostrar columnas disponibles
    with st.expander("📝 Columnas disponibles en los datos"):
        st.write(f"Total de columnas: {len(df_filtered.columns)}")
        for i, col in enumerate(df_filtered.columns, 1):
            st.write(f"{i:2d}. {col}")

    # Mostrar tabla básica
    display_columns = ["FECHA", "MUNICIPIO", "VEREDAS"]
    numeric_columns = ["Efectivas (E)", "TPE", "TPVB", "tasa_efectividad"]

    available_columns = [
        col for col in display_columns + numeric_columns if col in df_filtered.columns
    ]

    if available_columns:
        st.dataframe(df_filtered[available_columns].head(20), use_container_width=True)
    else:
        st.dataframe(df_filtered.head(20), use_container_width=True)

    # Insights finales
    st.markdown("---")
    st.subheader("💡 Insights de Brigadas")

    insights = [
        f"📊 **{len(df_filtered)} brigadas** analizadas con los filtros aplicados",
        f"🗺️ **{df_filtered['MUNICIPIO'].nunique() if 'MUNICIPIO' in df_filtered.columns else 0} municipios** diferentes visitados",
        f"📅 **Período**: {df_filtered['FECHA'].min().strftime('%d/%m/%Y') if 'FECHA' in df_filtered.columns and not df_filtered['FECHA'].isna().all() else 'No disponible'} - {df_filtered['FECHA'].max().strftime('%d/%m/%Y') if 'FECHA' in df_filtered.columns and not df_filtered['FECHA'].isna().all() else 'No disponible'}",
    ]

    for insight in insights:
        st.markdown(f"- {insight}")
