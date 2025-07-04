"""
vistas/temporal.py - Análisis temporal con separación PRE vs DURANTE
VERSIÓN CORREGIDA - Fix para error .dt accessor con manejo robusto de fechas
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


def safe_date_comparison(date_series, cutoff_date, operation="less"):
    """Realiza comparación de fechas de forma segura"""
    try:
        if cutoff_date is None:
            return pd.Series([False] * len(date_series))
        
        # Convertir fecha de corte a timestamp
        if isinstance(cutoff_date, datetime):
            cutoff_timestamp = pd.Timestamp(cutoff_date)
        elif isinstance(cutoff_date, pd.Timestamp):
            cutoff_timestamp = cutoff_date
        else:
            cutoff_timestamp = pd.Timestamp(cutoff_date)
        
        # Limpiar la serie de fechas - CONVERSIÓN ROBUSTA
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
        return pd.Series([False] * len(date_series))


def safe_group_by_date(df, date_column):
    """
    Agrupa por fecha de forma segura, manejando conversiones
    """
    try:
        # Asegurar que la columna es datetime
        df_clean = df[df[date_column].notna()].copy()
        
        if df_clean.empty:
            return pd.DataFrame(columns=["Fecha", "Count"])
        
        # Forzar conversión a datetime
        df_clean[date_column] = pd.to_datetime(df_clean[date_column], errors='coerce')
        
        # Eliminar filas donde la conversión falló
        df_clean = df_clean[df_clean[date_column].notna()]
        
        if df_clean.empty:
            return pd.DataFrame(columns=["Fecha", "Count"])
        
        # Ahora sí podemos usar .dt.date de forma segura
        grouped = df_clean.groupby(df_clean[date_column].dt.date).size().reset_index()
        grouped.columns = ["Fecha", "Count"]
        grouped["Fecha"] = pd.to_datetime(grouped["Fecha"])
        
        return grouped.sort_values("Fecha")
        
    except Exception as e:
        st.error(f"Error agrupando por fecha: {str(e)}")
        return pd.DataFrame(columns=["Fecha", "Count"])


def show_temporal_tab(combined_data, df_individual, df_barridos, COLORS):
    """Muestra análisis temporal con separación clara PRE vs DURANTE emergencia"""
    st.header("📅 Análisis Temporal - Combinación Sin Duplicados")

    fecha_corte = combined_data.get("fecha_corte")

    if fecha_corte:
        # Convertir timestamp a datetime para evitar errores con Plotly
        if hasattr(fecha_corte, 'to_pydatetime'):
            fecha_corte_dt = fecha_corte.to_pydatetime()
        elif isinstance(fecha_corte, pd.Timestamp):
            fecha_corte_dt = fecha_corte.to_pydatetime()
        else:
            fecha_corte_dt = fecha_corte
            
        st.success(
            f"🎯 **Fecha de corte:** {fecha_corte_dt.strftime('%d/%m/%Y')} - Inicio de emergencia sanitaria"
        )

        # Mostrar evolución PRE-emergencia
        show_pre_emergency_evolution(df_individual, fecha_corte_dt, COLORS)

        # Mostrar evolución DURANTE emergencia
        show_during_emergency_evolution(df_barridos, fecha_corte_dt, COLORS)

        # Mostrar comparación temporal combinada
        show_combined_temporal_analysis(df_individual, df_barridos, fecha_corte_dt, COLORS)

    else:
        st.warning("⚠️ No se pudo determinar fecha de corte")
        # Mostrar análisis básico sin corte
        show_basic_temporal_analysis(df_individual, df_barridos, COLORS)


def show_pre_emergency_evolution(df_individual, fecha_corte_dt, COLORS):
    """Muestra evolución PRE-emergencia (vacunación individual)"""
    st.subheader("🏥 Período PRE-Emergencia (Vacunación Individual)")

    if df_individual.empty or "FA UNICA" not in df_individual.columns:
        st.warning("⚠️ No hay datos de vacunación individual disponibles")
        return

    # Convertir fecha_corte_dt a timestamp para comparación
    if isinstance(fecha_corte_dt, datetime):
        fecha_corte_ts = pd.Timestamp(fecha_corte_dt)
    else:
        fecha_corte_ts = fecha_corte_dt

    # Filtrar solo datos PRE-emergencia usando comparación segura
    mask_pre = safe_date_comparison(df_individual["FA UNICA"], fecha_corte_ts, "less")
    df_pre = df_individual[mask_pre].copy()

    if df_pre.empty:
        st.info(
            f"ℹ️ No hay vacunación individual antes de {fecha_corte_dt.strftime('%d/%m/%Y')}"
        )
        return

    # Agrupar por fecha usando función segura
    daily_pre = safe_group_by_date(df_pre, "FA UNICA")
    
    if daily_pre.empty:
        st.info("ℹ️ No hay fechas válidas en datos PRE-emergencia")
        return

    daily_pre.columns = ["Fecha", "Vacunados"]
    daily_pre["Acumulado"] = daily_pre["Vacunados"].cumsum()

    col1, col2 = st.columns(2)

    with col1:
        # Gráfico diario PRE-emergencia
        fig = px.bar(
            daily_pre,
            x="Fecha",
            y="Vacunados",
            title="Vacunación Diaria PRE-Emergencia",
            color_discrete_sequence=[COLORS["primary"]],
        )

        # Agregar línea vertical usando shapes
        fig.add_shape(
            type="line",
            x0=fecha_corte_dt,
            x1=fecha_corte_dt,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(color="red", width=2, dash="dash"),
        )

        # Agregar anotación
        fig.add_annotation(
            x=fecha_corte_dt,
            y=0.9,
            yref="paper",
            text="Inicio Emergencia",
            showarrow=True,
            arrowhead=2,
            arrowcolor="red",
            bgcolor="white",
            bordercolor="red",
        )

        fig.update_layout(
            plot_bgcolor=COLORS["white"], 
            paper_bgcolor=COLORS["white"], 
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Gráfico acumulado PRE-emergencia
        fig_acum = px.line(
            daily_pre,
            x="Fecha",
            y="Acumulado",
            title="Vacunación Acumulada PRE-Emergencia",
            color_discrete_sequence=[COLORS["primary"]],
        )

        # Agregar línea vertical usando shapes
        fig_acum.add_shape(
            type="line",
            x0=fecha_corte_dt,
            x1=fecha_corte_dt,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(color="red", width=2, dash="dash"),
        )
        
        # Agregar anotación
        fig_acum.add_annotation(
            x=fecha_corte_dt,
            y=0.9,
            yref="paper",
            text="Inicio Emergencia",
            showarrow=True,
            arrowhead=2,
            arrowcolor="red",
            bgcolor="white",
            bordercolor="red",
        )

        fig_acum.update_layout(
            plot_bgcolor=COLORS["white"], 
            paper_bgcolor=COLORS["white"], 
            height=400
        )

        st.plotly_chart(fig_acum, use_container_width=True)

    # Estadísticas PRE-emergencia
    total_dias_pre = len(daily_pre)
    promedio_diario_pre = daily_pre["Vacunados"].mean()
    total_vacunados_pre = daily_pre["Vacunados"].sum()
    fecha_inicio_pre = daily_pre["Fecha"].min()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Días con Vacunación", f"{total_dias_pre}")

    with col2:
        st.metric("Promedio Diario", f"{promedio_diario_pre:.0f}")

    with col3:
        st.metric("Total PRE-Emergencia", f"{total_vacunados_pre:,}")

    with col4:
        # Calcular duración usando timedelta
        if isinstance(fecha_inicio_pre, pd.Timestamp):
            fecha_inicio_dt = fecha_inicio_pre.to_pydatetime()
        else:
            fecha_inicio_dt = fecha_inicio_pre

        duracion_pre = (fecha_corte_dt - fecha_inicio_dt).days
        st.metric("Duración Período", f"{duracion_pre} días")


def show_during_emergency_evolution(df_barridos, fecha_corte_dt, COLORS):
    """Muestra evolución DURANTE emergencia (barridos territoriales)"""
    st.subheader("🚨 Período DURANTE Emergencia (Barridos Territoriales)")

    if df_barridos.empty or "FECHA" not in df_barridos.columns:
        st.warning("⚠️ No hay datos de barridos disponibles")
        return

    # Convertir fecha_corte_dt a timestamp para comparación
    if isinstance(fecha_corte_dt, datetime):
        fecha_corte_ts = pd.Timestamp(fecha_corte_dt)
    else:
        fecha_corte_ts = fecha_corte_dt

    # Filtrar solo datos DURANTE emergencia usando comparación segura
    mask_durante = safe_date_comparison(df_barridos["FECHA"], fecha_corte_ts, "greater_equal")
    df_durante = df_barridos[mask_durante].copy()

    if df_durante.empty:
        st.info(f"ℹ️ No hay barridos desde {fecha_corte_dt.strftime('%d/%m/%Y')}")
        return

    # Detectar columnas de TPVB (vacunados en barrido)
    vacunados_cols = []
    age_patterns = [
        "<1",
        "1-5",
        "6-10",
        "11-20",
        "21-30",
        "31-40",
        "41-50",
        "51-59",
        "60",
    ]

    for age_pattern in age_patterns:
        found_cols = []
        for col in df_durante.columns:
            if age_pattern in str(col):
                found_cols.append(col)

        # Tomar la 4ta columna (índice 3) como TPVB
        if len(found_cols) >= 4:
            vacunados_cols.append(found_cols[3])

    if not vacunados_cols:
        st.warning("⚠️ No se encontraron columnas de TPVB en barridos")
        return

    # Calcular vacunados por día
    daily_durante = []

    # Asegurar que FECHA esté en formato datetime
    df_durante["FECHA"] = pd.to_datetime(df_durante["FECHA"], errors='coerce')
    df_durante = df_durante[df_durante["FECHA"].notna()]

    for _, row in df_durante.iterrows():
        fecha = row["FECHA"]
        if pd.isna(fecha):
            continue
            
        total_vacunados = 0
        total_barridos = 1

        for col in vacunados_cols:
            if col in df_durante.columns:
                valor = pd.to_numeric(row[col], errors="coerce")
                if pd.notna(valor):
                    total_vacunados += valor

        if total_vacunados > 0:
            daily_durante.append(
                {
                    "Fecha": fecha,
                    "Vacunados": total_vacunados,
                    "Barridos": total_barridos,
                }
            )

    if not daily_durante:
        st.warning("⚠️ No se encontraron vacunados en barridos")
        return

    df_durante_daily = pd.DataFrame(daily_durante)
    df_durante_daily = (
        df_durante_daily.groupby("Fecha")
        .agg({"Vacunados": "sum", "Barridos": "sum"})
        .reset_index()
    )
    df_durante_daily = df_durante_daily.sort_values("Fecha")

    # Calcular acumulado
    df_durante_daily["Acumulado"] = df_durante_daily["Vacunados"].cumsum()

    col1, col2 = st.columns(2)

    with col1:
        # Gráfico diario DURANTE emergencia
        fig = px.bar(
            df_durante_daily,
            x="Fecha",
            y="Vacunados",
            title="Vacunación Diaria DURANTE Emergencia",
            color_discrete_sequence=[COLORS["warning"]],
        )

        fig.update_layout(
            plot_bgcolor=COLORS["white"], 
            paper_bgcolor=COLORS["white"], 
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Gráfico acumulado DURANTE emergencia
        fig_acum = px.line(
            df_durante_daily,
            x="Fecha",
            y="Acumulado",
            title="Vacunación Acumulada DURANTE Emergencia",
            color_discrete_sequence=[COLORS["warning"]],
        )

        fig_acum.update_layout(
            plot_bgcolor=COLORS["white"], 
            paper_bgcolor=COLORS["white"], 
            height=400
        )

        st.plotly_chart(fig_acum, use_container_width=True)

    # Estadísticas DURANTE emergencia
    total_dias_durante = len(df_durante_daily)
    total_barridos_realizados = df_durante_daily["Barridos"].sum()
    promedio_diario_durante = df_durante_daily["Vacunados"].mean()
    total_vacunados_durante = df_durante_daily["Vacunados"].sum()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Días con Barridos", f"{total_dias_durante}")

    with col2:
        st.metric("Total Barridos", f"{total_barridos_realizados}")

    with col3:
        st.metric("Promedio/Día", f"{promedio_diario_durante:.0f}")

    with col4:
        st.metric("Total DURANTE", f"{total_vacunados_durante:,}")


def show_combined_temporal_analysis(df_individual, df_barridos, fecha_corte_dt, COLORS):
    """Muestra análisis temporal combinado con línea de corte"""
    st.subheader("⚖️ Análisis Temporal Combinado")

    # Convertir fecha_corte_dt a timestamp para comparaciones
    if isinstance(fecha_corte_dt, datetime):
        fecha_corte_ts = pd.Timestamp(fecha_corte_dt)
    else:
        fecha_corte_ts = fecha_corte_dt

    # Preparar datos PRE-emergencia usando función segura
    if "FA UNICA" in df_individual.columns:
        mask_pre = safe_date_comparison(df_individual["FA UNICA"], fecha_corte_ts, "less")
        df_pre = df_individual[mask_pre]

        if not df_pre.empty:
            pre_daily = safe_group_by_date(df_pre, "FA UNICA")
            if not pre_daily.empty:
                pre_daily.columns = ["Fecha", "Individual"]
            else:
                pre_daily = pd.DataFrame(columns=["Fecha", "Individual"])
        else:
            pre_daily = pd.DataFrame(columns=["Fecha", "Individual"])
    else:
        pre_daily = pd.DataFrame(columns=["Fecha", "Individual"])

    # Preparar datos DURANTE emergencia (simplificado)
    if "FECHA" in df_barridos.columns:
        mask_durante = safe_date_comparison(df_barridos["FECHA"], fecha_corte_ts, "greater_equal")
        df_durante = df_barridos[mask_durante]

        if not df_durante.empty:
            durante_daily = safe_group_by_date(df_durante, "FECHA")
            if not durante_daily.empty:
                durante_daily.columns = ["Fecha", "Barridos_Realizados"]
            else:
                durante_daily = pd.DataFrame(columns=["Fecha", "Barridos_Realizados"])
        else:
            durante_daily = pd.DataFrame(columns=["Fecha", "Barridos_Realizados"])
    else:
        durante_daily = pd.DataFrame(columns=["Fecha", "Barridos_Realizados"])

    # Crear gráfico temporal combinado
    fig = go.Figure()

    # Agregar datos PRE-emergencia
    if not pre_daily.empty:
        fig.add_trace(
            go.Scatter(
                x=pre_daily["Fecha"],
                y=pre_daily["Individual"],
                mode="lines+markers",
                name="PRE-Emergencia (Individual)",
                line=dict(color=COLORS["primary"], width=3),
                fill="tonexty",
            )
        )

    # Agregar datos DURANTE emergencia
    if not durante_daily.empty:
        fig.add_trace(
            go.Scatter(
                x=durante_daily["Fecha"],
                y=durante_daily["Barridos_Realizados"],
                mode="lines+markers",
                name="DURANTE Emergencia (Barridos)",
                line=dict(color=COLORS["warning"], width=3),
                yaxis="y2",
            )
        )

    # Agregar línea vertical usando shapes
    fig.add_shape(
        type="line",
        x0=fecha_corte_dt,
        x1=fecha_corte_dt,
        y0=0,
        y1=1,
        yref="paper",
        line=dict(color="red", width=3, dash="dash"),
    )

    # Agregar anotación
    fig.add_annotation(
        x=fecha_corte_dt,
        y=0.95,
        yref="paper",
        text="INICIO EMERGENCIA",
        showarrow=True,
        arrowhead=2,
        arrowcolor="red",
        bgcolor="white",
        bordercolor="red",
        font=dict(color="red", size=12),
    )

    fig.update_layout(
        title="Evolución Temporal: PRE vs DURANTE Emergencia",
        xaxis_title="Fecha",
        yaxis_title="Vacunación Individual",
        yaxis2=dict(title="Barridos Realizados", overlaying="y", side="right"),
        plot_bgcolor=COLORS["white"],
        paper_bgcolor=COLORS["white"],
        height=500,
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True)

    # Resumen comparativo
    st.markdown("**📊 Resumen Comparativo:**")

    col1, col2, col3 = st.columns(3)

    with col1:
        if not pre_daily.empty:
            fecha_inicio = pre_daily["Fecha"].min()
            if isinstance(fecha_inicio, pd.Timestamp):
                fecha_inicio_dt = fecha_inicio.to_pydatetime()
            else:
                fecha_inicio_dt = fecha_inicio

            # Calcular fecha fin del período PRE
            from datetime import timedelta

            fecha_fin_pre = fecha_corte_dt - timedelta(days=1)

            periodo_pre = f"{fecha_inicio_dt.strftime('%d/%m/%Y')} - {fecha_fin_pre.strftime('%d/%m/%Y')}"
            total_pre = pre_daily["Individual"].sum()
            st.metric(
                "Período PRE-Emergencia", periodo_pre, delta=f"{total_pre:,} vacunados"
            )

    with col2:
        if not durante_daily.empty:
            fecha_max = durante_daily["Fecha"].max()
            if isinstance(fecha_max, pd.Timestamp):
                fecha_max_dt = fecha_max.to_pydatetime()
            else:
                fecha_max_dt = fecha_max

            periodo_durante = f"{fecha_corte_dt.strftime('%d/%m/%Y')} - {fecha_max_dt.strftime('%d/%m/%Y')}"
            total_barridos = durante_daily["Barridos_Realizados"].sum()
            st.metric(
                "Período DURANTE Emergencia",
                periodo_durante,
                delta=f"{total_barridos} barridos",
            )

    with col3:
        total_combinado = pre_daily["Individual"].sum() if not pre_daily.empty else 0
        st.metric(
            "TOTAL REAL Combinado", f"{total_combinado:,}", delta="Sin duplicados"
        )


def show_basic_temporal_analysis(df_individual, df_barridos, COLORS):
    """Muestra análisis temporal básico cuando no hay fecha de corte"""
    st.subheader("📅 Análisis Temporal Básico")

    st.info("💡 Sin fecha de corte definida - mostrando datos completos")

    # Análisis básico de individuales
    if not df_individual.empty and "FA UNICA" in df_individual.columns:
        # Usar función segura para obtener fechas válidas
        fechas_convertidas = pd.to_datetime(df_individual["FA UNICA"], errors='coerce')
        df_ind_valid = df_individual[fechas_convertidas.notna()]
        
        if not df_ind_valid.empty:
            fecha_min_ind = fechas_convertidas.min()
            fecha_max_ind = fechas_convertidas.max()
            total_ind = len(df_ind_valid)

            st.metric(
                "Vacunación Individual",
                f"{fecha_min_ind.strftime('%d/%m/%Y')} - {fecha_max_ind.strftime('%d/%m/%Y')}",
                delta=f"{total_ind:,} vacunados",
            )

    # Análisis básico de barridos
    if not df_barridos.empty and "FECHA" in df_barridos.columns:
        # Usar función segura para obtener fechas válidas
        fechas_convertidas = pd.to_datetime(df_barridos["FECHA"], errors='coerce')
        df_barr_valid = df_barridos[fechas_convertidas.notna()]
        
        if not df_barr_valid.empty:
            fecha_min_barr = fechas_convertidas.min()
            fecha_max_barr = fechas_convertidas.max()
            total_barr = len(df_barr_valid)

            st.metric(
                "Barridos Territoriales",
                f"{fecha_min_barr.strftime('%d/%m/%Y')} - {fecha_max_barr.strftime('%d/%m/%Y')}",
                delta=f"{total_barr} barridos",
            )