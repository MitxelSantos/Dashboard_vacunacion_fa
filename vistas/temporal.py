"""
vistas/temporal.py - Vista de análisis temporal
Enfocada en tendencias y evolución temporal
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def show_temporal_tab(combined_data, COLORS):
    """Muestra análisis temporal con énfasis en tendencias porcentuales"""
    st.header("📅 Análisis Temporal")

    fechas_info = combined_data.get("fechas_info", {})

    # Mostrar información de fechas (sin cambios)
    col1, col2 = st.columns(2)

    with col1:
        if fechas_info.get("rango_historicos_completo"):
            inicio, fin = fechas_info["rango_historicos_completo"]
            st.info(f"📊 **Históricos (PAI):**\n{inicio.strftime('%d/%m/%Y')} - {fin.strftime('%d/%m/%Y')}")

    with col2:
        if fechas_info.get("rango_barridos"):
            inicio, fin = fechas_info["rango_barridos"]
            st.info(f"🚨 **Barridos:**\n{inicio.strftime('%d/%m/%Y')} - {fin.strftime('%d/%m/%Y')}")

    # Gráfico temporal combinado
    if not combined_data["temporal_data"].empty:
        st.subheader("📈 Evolución Temporal Acumulada")

        df_temporal = combined_data["temporal_data"].copy()

        # Crear datos diarios con acumulados y porcentajes
        daily_summary = (
            df_temporal.groupby([df_temporal["fecha"].dt.date, "fuente"])
            .size()
            .reset_index()
        )
        daily_summary.columns = ["Fecha", "Fuente", "Vacunados_Dia"]
        daily_summary["Fecha"] = pd.to_datetime(daily_summary["Fecha"])

        # Calcular acumulados por fuente
        daily_summary = daily_summary.sort_values(['Fuente', 'Fecha'])
        daily_summary['Vacunados_Acumulado'] = daily_summary.groupby('Fuente')['Vacunados_Dia'].cumsum()

        # Calcular porcentaje acumulado del total general
        total_general = combined_data["total_general"]
        daily_summary['Porcentaje_Acumulado'] = (daily_summary['Vacunados_Acumulado'] / total_general) * 100

        # Crear gráfico con dos y-axis
        fig = go.Figure()

        # Agregar líneas por fuente
        for fuente in daily_summary['Fuente'].unique():
            data_fuente = daily_summary[daily_summary['Fuente'] == fuente]
            
            color = COLORS["primary"] if "Históricos" in fuente else COLORS["warning"]
            
            # Línea de porcentaje acumulado
            fig.add_trace(
                go.Scatter(
                    x=data_fuente["Fecha"],
                    y=data_fuente["Porcentaje_Acumulado"],
                    mode='lines+markers',
                    name=f"{fuente} (% Acum.)",
                    line=dict(color=color, width=3),
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                  'Fecha: %{x}<br>' +
                                  'Porcentaje: %{y:.1f}%<br>' +
                                  'Acumulado: %{customdata:,}<extra></extra>',
                    customdata=data_fuente["Vacunados_Acumulado"]
                )
            )

        # Agregar línea vertical en fecha de corte
        if fechas_info.get("fecha_corte"):
            try:
                fecha_corte = fechas_info["fecha_corte"]
                fecha_corte_str = fecha_corte.strftime('%Y-%m-%d')
                
                fig.add_shape(
                    type="line",
                    x0=fecha_corte_str,
                    x1=fecha_corte_str,
                    y0=0,
                    y1=100,
                    line=dict(color="red", width=2, dash="dash"),
                )
                
                fig.add_annotation(
                    x=fecha_corte_str,
                    y=90,
                    text="Inicio Barridos",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor="red",
                    font=dict(color="red"),
                    bgcolor="white",
                    bordercolor="red",
                    borderwidth=1
                )
                
            except Exception:
                pass

        fig.update_layout(
            title="Evolución Porcentual Acumulada de Vacunación",
            xaxis_title="Fecha",
            yaxis_title="Porcentaje Acumulado (%)",
            plot_bgcolor=COLORS["white"],
            paper_bgcolor=COLORS["white"],
            height=500,
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Gráfico de velocidad diaria (barras)
        st.subheader("📊 Velocidad de Vacunación Diaria")
        
        # Calcular métricas diarias
        daily_summary_for_bars = daily_summary.copy()
        
        fig_bars = px.bar(
            daily_summary_for_bars,
            x="Fecha",
            y="Vacunados_Dia",
            color="Fuente",
            title="Vacunaciones por Día",
            color_discrete_map={
                "Históricos (PAI)": COLORS["primary"],
                "Barridos (Emergencia)": COLORS["warning"],
            },
            text="Vacunados_Dia"
        )
        
        fig_bars.update_traces(textposition="outside")
        fig_bars.update_layout(
            plot_bgcolor=COLORS["white"],
            paper_bgcolor=COLORS["white"],
            height=400,
            yaxis_title="Vacunados por Día"
        )
        
        st.plotly_chart(fig_bars, use_container_width=True)

        # Estadísticas comparativas con porcentajes
        st.subheader("📊 Estadísticas Comparativas")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            historicos_dias = daily_summary[daily_summary["Fuente"] == "Históricos (PAI)"]
            if not historicos_dias.empty:
                promedio_hist = historicos_dias["Vacunados_Dia"].mean()
                total_dias_hist = len(historicos_dias)
                st.metric(
                    "Promedio Diario Históricos", 
                    f"{promedio_hist:.0f}",
                    delta=f"{total_dias_hist} días"
                )

        with col2:
            barridos_dias = daily_summary[daily_summary["Fuente"] == "Barridos (Emergencia)"]
            if not barridos_dias.empty:
                promedio_barr = barridos_dias["Vacunados_Dia"].mean()
                total_dias_barr = len(barridos_dias)
                st.metric(
                    "Promedio Diario Barridos", 
                    f"{promedio_barr:.0f}",
                    delta=f"{total_dias_barr} días"
                )

        with col3:
            if not historicos_dias.empty and not barridos_dias.empty:
                incremento = ((promedio_barr - promedio_hist) / promedio_hist) * 100
                st.metric(
                    "Incremento de Velocidad", 
                    f"{incremento:+.1f}%",
                    delta="vs Históricos"
                )

        with col4:
            # Eficiencia (vacunados por día activo)
            if not daily_summary.empty:
                dias_activos = daily_summary["Fecha"].nunique()
                vacunados_total = daily_summary["Vacunados_Dia"].sum()
                eficiencia = vacunados_total / dias_activos if dias_activos > 0 else 0
                st.metric(
                    "Eficiencia General",
                    f"{eficiencia:.0f}/día",
                    delta=f"{dias_activos} días activos"
                )

        # Análisis de tendencias
        st.subheader("📈 Análisis de Tendencias")
        
        # Calcular tendencias para cada fuente
        tendencias = {}
        for fuente in daily_summary['Fuente'].unique():
            data_fuente = daily_summary[daily_summary['Fuente'] == fuente].sort_values('Fecha')
            if len(data_fuente) >= 5:  # Mínimo 5 puntos para tendencia
                # Calcular pendiente usando regresión lineal simple
                x = range(len(data_fuente))
                y = data_fuente['Vacunados_Dia'].values
                
                n = len(x)
                sum_x = sum(x)
                sum_y = sum(y)
                sum_xy = sum(xi * yi for xi, yi in zip(x, y))
                sum_x2 = sum(xi * xi for xi in x)
                
                if n * sum_x2 - sum_x * sum_x != 0:
                    pendiente = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                    tendencias[fuente] = pendiente
                else:
                    tendencias[fuente] = 0

        col1, col2 = st.columns(2)
        
        for i, (fuente, pendiente) in enumerate(tendencias.items()):
            with col1 if i % 2 == 0 else col2:
                if pendiente > 0:
                    trend_icon = "📈"
                    trend_text = "Creciente"
                    delta_color = "normal"
                elif pendiente < 0:
                    trend_icon = "📉"
                    trend_text = "Decreciente"
                    delta_color = "inverse"
                else:
                    trend_icon = "➡️"
                    trend_text = "Estable"
                    delta_color = "normal"
                
                st.metric(
                    f"{trend_icon} Tendencia {fuente.split('(')[0].strip()}",
                    trend_text,
                    delta=f"{pendiente:+.1f} vacunas/día"
                )

    else:
        st.info("No hay datos temporales disponibles para mostrar")