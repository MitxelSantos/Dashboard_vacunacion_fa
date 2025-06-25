"""
vistas/temporal.py - Análisis temporal con separación PRE vs DURANTE
<<<<<<< HEAD
VERSIÓN CORREGIDA FINAL - Fix completo para TypeError con Timestamps
=======
<<<<<<< HEAD
VERSIÓN CORREGIDA FINAL - Fix completo para TypeError con Timestamps
=======
Enfocado en mostrar la fecha de corte y evitar duplicados
VERSIÓN CORREGIDA - Fix para TypeError con Timestamps
>>>>>>> 473c13cb41e69bac105a2353395993231aa3b7ac
>>>>>>> d869af22d548c4c79736db9cea6c80fc64dc2272
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


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

        if hasattr(fecha_corte, "to_pydatetime"):
            fecha_corte_dt = fecha_corte.to_pydatetime()
        elif isinstance(fecha_corte, pd.Timestamp):
            fecha_corte_dt = fecha_corte.to_pydatetime()
        else:
            fecha_corte_dt = fecha_corte

        st.success(

            f"🎯 **Fecha de corte:** {fecha_corte_dt.strftime('%d/%m/%Y')} - Inicio de emergencia sanitaria"

            f"🎯 **Fecha de corte:** {fecha_corte.strftime('%d/%m/%Y')} - Inicio de emergencia sanitaria"

        )

        # Mostrar evolución PRE-emergencia
        show_pre_emergency_evolution(df_individual, fecha_corte_dt, COLORS)

        # Mostrar evolución DURANTE emergencia
        show_during_emergency_evolution(df_barridos, fecha_corte_dt, COLORS)

        # Mostrar comparación temporal combinada
<<<<<<< HEAD
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

    # Filtrar solo datos PRE-emergencia
    df_pre = df_individual[
<<<<<<< HEAD
        (df_individual["FA UNICA"].notna()) & (df_individual["FA UNICA"] < fecha_corte_ts)
=======
        (df_individual["FA UNICA"].notna())
        & (df_individual["FA UNICA"] < fecha_corte_ts)
>>>>>>> 473c13cb41e69bac105a2353395993231aa3b7ac
    ].copy()

    if df_pre.empty:
        st.info(
            f"ℹ️ No hay vacunación individual antes de {fecha_corte_dt.strftime('%d/%m/%Y')}"
        )
        return

    # Agrupar por fecha
    daily_pre = df_pre.groupby(df_pre["FA UNICA"].dt.date).size().reset_index()
    daily_pre.columns = ["Fecha", "Vacunados"]
    daily_pre["Fecha"] = pd.to_datetime(daily_pre["Fecha"])
    daily_pre = daily_pre.sort_values("Fecha")

    # Calcular acumulado
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

<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> d869af22d548c4c79736db9cea6c80fc64dc2272
        # Agregar línea vertical usando shapes (más robusto)
        fig.add_shape(
            type="line",
            x0=fecha_corte_dt,
            x1=fecha_corte_dt,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(color="red", width=2, dash="dash"),
        )
<<<<<<< HEAD

=======
        
>>>>>>> d869af22d548c4c79736db9cea6c80fc64dc2272
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
<<<<<<< HEAD
=======
        )

        fig.update_layout(
            plot_bgcolor=COLORS["white"], 
            paper_bgcolor=COLORS["white"], 
            height=400
=======
        # Agregar línea vertical de fecha de corte (convertida a string para Plotly)
        fig.add_vline(
            x=fecha_corte_dt.strftime("%Y-%m-%d"),
            line_dash="dash",
            line_color="red",
            annotation_text="Inicio Emergencia",
>>>>>>> d869af22d548c4c79736db9cea6c80fc64dc2272
        )

        fig.update_layout(
            plot_bgcolor=COLORS["white"], paper_bgcolor=COLORS["white"], height=400
>>>>>>> 473c13cb41e69bac105a2353395993231aa3b7ac
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

<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> d869af22d548c4c79736db9cea6c80fc64dc2272
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
<<<<<<< HEAD

=======
        
>>>>>>> d869af22d548c4c79736db9cea6c80fc64dc2272
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
<<<<<<< HEAD
=======
        )

        fig_acum.update_layout(
            plot_bgcolor=COLORS["white"], 
            paper_bgcolor=COLORS["white"], 
            height=400
=======
        # Agregar línea vertical de fecha de corte (convertida a string para Plotly)
        fig_acum.add_vline(
            x=fecha_corte_dt.strftime("%Y-%m-%d"),
            line_dash="dash",
            line_color="red",
            annotation_text="Inicio Emergencia",
>>>>>>> d869af22d548c4c79736db9cea6c80fc64dc2272
        )

        fig_acum.update_layout(
            plot_bgcolor=COLORS["white"], paper_bgcolor=COLORS["white"], height=400
>>>>>>> 473c13cb41e69bac105a2353395993231aa3b7ac
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
<<<<<<< HEAD
        
=======

>>>>>>> 473c13cb41e69bac105a2353395993231aa3b7ac
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

    # Filtrar solo datos DURANTE emergencia
    df_durante = df_barridos[
        (df_barridos["FECHA"].notna()) & (df_barridos["FECHA"] >= fecha_corte_ts)
    ].copy()

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

    for _, row in df_durante.iterrows():
        fecha = row["FECHA"]
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
<<<<<<< HEAD
            plot_bgcolor=COLORS["white"], 
            paper_bgcolor=COLORS["white"], 
            height=400
=======
            plot_bgcolor=COLORS["white"], paper_bgcolor=COLORS["white"], height=400
>>>>>>> 473c13cb41e69bac105a2353395993231aa3b7ac
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
<<<<<<< HEAD
            plot_bgcolor=COLORS["white"], 
            paper_bgcolor=COLORS["white"], 
            height=400
=======
            plot_bgcolor=COLORS["white"], paper_bgcolor=COLORS["white"], height=400
>>>>>>> 473c13cb41e69bac105a2353395993231aa3b7ac
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

    # Preparar datos PRE-emergencia
    if "FA UNICA" in df_individual.columns:
        df_pre = df_individual[
            (df_individual["FA UNICA"].notna())
            & (df_individual["FA UNICA"] < fecha_corte_ts)
        ]

        if not df_pre.empty:
            pre_daily = df_pre.groupby(df_pre["FA UNICA"].dt.date).size().reset_index()
            pre_daily.columns = ["Fecha", "Individual"]
            pre_daily["Fecha"] = pd.to_datetime(pre_daily["Fecha"])
        else:
            pre_daily = pd.DataFrame(columns=["Fecha", "Individual"])
    else:
        pre_daily = pd.DataFrame(columns=["Fecha", "Individual"])

    # Preparar datos DURANTE emergencia (simplificado)
    if "FECHA" in df_barridos.columns:
        df_durante = df_barridos[
            (df_barridos["FECHA"].notna()) & (df_barridos["FECHA"] >= fecha_corte_ts)
        ]

        if not df_durante.empty:
            durante_daily = df_durante.groupby("FECHA").size().reset_index()
            durante_daily.columns = ["Fecha", "Barridos_Realizados"]
            durante_daily["Fecha"] = pd.to_datetime(durante_daily["Fecha"])
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

<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> d869af22d548c4c79736db9cea6c80fc64dc2272
    # Agregar línea vertical usando shapes (más robusto)
    fig.add_shape(
        type="line",
        x0=fecha_corte_dt,
        x1=fecha_corte_dt,
        y0=0,
        y1=1,
        yref="paper",
        line=dict(color="red", width=3, dash="dash"),
    )
<<<<<<< HEAD

=======
    
>>>>>>> d869af22d548c4c79736db9cea6c80fc64dc2272
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
<<<<<<< HEAD
=======
=======
    # Agregar línea vertical de fecha de corte (convertida a string para Plotly)
    fig.add_vline(
        x=fecha_corte_dt.strftime("%Y-%m-%d"),
        line_dash="dash",
        line_color="red",
        line_width=3,
        annotation_text="INICIO EMERGENCIA",
        annotation_position="top",
>>>>>>> 473c13cb41e69bac105a2353395993231aa3b7ac
>>>>>>> d869af22d548c4c79736db9cea6c80fc64dc2272
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
<<<<<<< HEAD
            fecha_inicio = pre_daily['Fecha'].min()
=======
            fecha_inicio = pre_daily["Fecha"].min()
>>>>>>> 473c13cb41e69bac105a2353395993231aa3b7ac
            if isinstance(fecha_inicio, pd.Timestamp):
                fecha_inicio_dt = fecha_inicio.to_pydatetime()
            else:
                fecha_inicio_dt = fecha_inicio
<<<<<<< HEAD
            
            # Calcular fecha fin del período PRE
            from datetime import timedelta
            fecha_fin_pre = fecha_corte_dt - timedelta(days=1)
            
=======

            # Calcular fecha fin del período PRE
            from datetime import timedelta

            fecha_fin_pre = fecha_corte_dt - timedelta(days=1)

>>>>>>> 473c13cb41e69bac105a2353395993231aa3b7ac
            periodo_pre = f"{fecha_inicio_dt.strftime('%d/%m/%Y')} - {fecha_fin_pre.strftime('%d/%m/%Y')}"
            total_pre = pre_daily["Individual"].sum()
            st.metric(
                "Período PRE-Emergencia", periodo_pre, delta=f"{total_pre:,} vacunados"
            )

    with col2:
        if not durante_daily.empty:
<<<<<<< HEAD
            fecha_max = durante_daily['Fecha'].max()
=======
            fecha_max = durante_daily["Fecha"].max()
>>>>>>> 473c13cb41e69bac105a2353395993231aa3b7ac
            if isinstance(fecha_max, pd.Timestamp):
                fecha_max_dt = fecha_max.to_pydatetime()
            else:
                fecha_max_dt = fecha_max
<<<<<<< HEAD
                
=======

>>>>>>> 473c13cb41e69bac105a2353395993231aa3b7ac
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
        df_ind_valid = df_individual[df_individual["FA UNICA"].notna()]
        if not df_ind_valid.empty:
            fecha_min_ind = df_ind_valid["FA UNICA"].min()
            fecha_max_ind = df_ind_valid["FA UNICA"].max()
            total_ind = len(df_ind_valid)

            st.metric(
                "Vacunación Individual",
                f"{fecha_min_ind.strftime('%d/%m/%Y')} - {fecha_max_ind.strftime('%d/%m/%Y')}",
                delta=f"{total_ind:,} vacunados",
            )

    # Análisis básico de barridos
    if not df_barridos.empty and "FECHA" in df_barridos.columns:
        df_barr_valid = df_barridos[df_barridos["FECHA"].notna()]
        if not df_barr_valid.empty:
            fecha_min_barr = df_barr_valid["FECHA"].min()
            fecha_max_barr = df_barr_valid["FECHA"].max()
            total_barr = len(df_barr_valid)

            st.metric(
                "Barridos Territoriales",
                f"{fecha_min_barr.strftime('%d/%m/%Y')} - {fecha_max_barr.strftime('%d/%m/%Y')}",
                delta=f"{total_barr} barridos",
<<<<<<< HEAD
            )
=======
            )
>>>>>>> 473c13cb41e69bac105a2353395993231aa3b7ac
