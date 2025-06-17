"""
vistas/temporal.py - Análisis temporal con separación PRE vs DURANTE
Enfocado en mostrar la fecha de corte y evitar duplicados
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def show_temporal_tab(combined_data, df_individual, df_barridos, COLORS):
    """Muestra análisis temporal con separación clara PRE vs DURANTE emergencia"""
    st.header("📅 Análisis Temporal - Combinación Sin Duplicados")

    fecha_corte = combined_data.get("fecha_corte")

    if fecha_corte:
        st.success(
            f"🎯 **Fecha de corte:** {fecha_corte.strftime('%d/%m/%Y')} - Inicio de emergencia sanitaria"
        )

        # Mostrar evolución PRE-emergencia
        show_pre_emergency_evolution(df_individual, fecha_corte, COLORS)

        # Mostrar evolución DURANTE emergencia
        show_during_emergency_evolution(df_barridos, fecha_corte, COLORS)

        # Mostrar comparación temporal combinada
        show_combined_temporal_analysis(df_individual, df_barridos, fecha_corte, COLORS)

    else:
        st.warning("⚠️ No se pudo determinar fecha de corte")
        # Mostrar análisis básico sin corte
        show_basic_temporal_analysis(df_individual, df_barridos, COLORS)


def show_pre_emergency_evolution(df_individual, fecha_corte, COLORS):
    """Muestra evolución PRE-emergencia (vacunación individual)"""
    st.subheader("🏥 Período PRE-Emergencia (Vacunación Individual)")

    if df_individual.empty or "FA UNICA" not in df_individual.columns:
        st.warning("⚠️ No hay datos de vacunación individual disponibles")
        return

    # Filtrar solo datos PRE-emergencia
    df_pre = df_individual[
        (df_individual["FA UNICA"].notna()) & (df_individual["FA UNICA"] < fecha_corte)
    ].copy()

    if df_pre.empty:
        st.info(
            f"ℹ️ No hay vacunación individual antes de {fecha_corte.strftime('%d/%m/%Y')}"
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

        # Agregar línea vertical de fecha de corte
        fig.add_vline(
            x=fecha_corte,
            line_dash="dash",
            line_color="red",
            annotation_text="Inicio Emergencia",
        )

        fig.update_layout(
            plot_bgcolor=COLORS["white"], paper_bgcolor=COLORS["white"], height=400
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

        # Agregar línea vertical de fecha de corte
        fig_acum.add_vline(
            x=fecha_corte,
            line_dash="dash",
            line_color="red",
            annotation_text="Inicio Emergencia",
        )

        fig_acum.update_layout(
            plot_bgcolor=COLORS["white"], paper_bgcolor=COLORS["white"], height=400
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
        duracion_pre = (fecha_corte - fecha_inicio_pre).days
        st.metric("Duración Período", f"{duracion_pre} días")


def show_during_emergency_evolution(df_barridos, fecha_corte, COLORS):
    """Muestra evolución DURANTE emergencia (barridos territoriales)"""
    st.subheader("🚨 Período DURANTE Emergencia (Barridos Territoriales)")

    if df_barridos.empty or "FECHA" not in df_barridos.columns:
        st.warning("⚠️ No hay datos de barridos disponibles")
        return

    # Filtrar solo datos DURANTE emergencia
    df_durante = df_barridos[
        (df_barridos["FECHA"].notna()) & (df_barridos["FECHA"] >= fecha_corte)
    ].copy()

    if df_durante.empty:
        st.info(f"ℹ️ No hay barridos desde {fecha_corte.strftime('%d/%m/%Y')}")
        return

    # Detectar columnas de vacunados en barrido (4ta sección)
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

        # Tomar la 4ta columna (índice 3) como vacunados en barrido
        if len(found_cols) >= 4:
            vacunados_cols.append(found_cols[3])

    if not vacunados_cols:
        st.warning("⚠️ No se encontraron columnas de vacunados en barridos")
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
            plot_bgcolor=COLORS["white"], paper_bgcolor=COLORS["white"], height=400
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
            plot_bgcolor=COLORS["white"], paper_bgcolor=COLORS["white"], height=400
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


def show_combined_temporal_analysis(df_individual, df_barridos, fecha_corte, COLORS):
    """Muestra análisis temporal combinado con línea de corte"""
    st.subheader("⚖️ Análisis Temporal Combinado")

    # Preparar datos PRE-emergencia
    if "FA UNICA" in df_individual.columns:
        df_pre = df_individual[
            (df_individual["FA UNICA"].notna())
            & (df_individual["FA UNICA"] < fecha_corte)
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
            (df_barridos["FECHA"].notna()) & (df_barridos["FECHA"] >= fecha_corte)
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

    # Agregar línea vertical de fecha de corte
    fig.add_vline(
        x=fecha_corte,
        line_dash="dash",
        line_color="red",
        line_width=3,
        annotation_text="INICIO EMERGENCIA",
        annotation_position="top",
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
            periodo_pre = f"{pre_daily['Fecha'].min().strftime('%d/%m/%Y')} - {(fecha_corte - pd.Timedelta(days=1)).strftime('%d/%m/%Y')}"
            total_pre = pre_daily["Individual"].sum()
            st.metric(
                "Período PRE-Emergencia", periodo_pre, delta=f"{total_pre:,} vacunados"
            )

    with col2:
        if not durante_daily.empty:
            periodo_durante = f"{fecha_corte.strftime('%d/%m/%Y')} - {durante_daily['Fecha'].max().strftime('%d/%m/%Y')}"
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
            )
