"""
vistas/overview.py - Vista de resumen con lógica temporal
Enfocada en combinación sin duplicados
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def show_overview_tab(combined_data, COLORS, RANGOS_EDAD):
    """Muestra resumen general con lógica de combinación temporal"""
    st.header("📊 Resumen General - Datos Combinados Sin Duplicados")

    # Métricas principales con lógica temporal
    show_main_metrics_temporal(combined_data, COLORS)

    # Distribución por rangos de edad (combinada)
    show_combined_age_distribution(combined_data, COLORS, RANGOS_EDAD)

    # Análisis de períodos
    show_periods_analysis(combined_data, COLORS)

    # Análisis territorial si hay población
    if combined_data["population"]["por_municipio"]:
        show_territorial_summary_combined(combined_data, COLORS)


def show_main_metrics_temporal(combined_data, COLORS):
    """Muestra métricas principales con lógica temporal"""
    col1, col2, col3, col4 = st.columns(4)

    total_pre = combined_data["total_individual_pre"]
    total_barridos = combined_data["total_barridos"]
    total_renuentes = combined_data["total_renuentes"]
    total_real = combined_data["total_real_combinado"]

    with col1:
        st.metric(
            "🏥 PRE-Emergencia",
            f"{total_pre:,}",
            delta="Individual sin duplicados" if total_pre > 0 else "Sin datos",
        )

    with col2:
        st.metric(
            "🚨 DURANTE Emergencia",
            f"{total_barridos:,}",
            delta="Barridos territoriales" if total_barridos > 0 else "Sin datos",
        )

    with col3:
        st.metric(
            "📈 TOTAL REAL",
            f"{total_real:,}",
            delta="Combinado sin duplicados" if total_real > 0 else "Sin datos",
        )

    with col4:
        # Mostrar tasa de aceptación
        if total_renuentes > 0:
            total_contactados = total_real + total_renuentes
            tasa_aceptacion = (total_real / total_contactados) * 100
            st.metric(
                "✅ Tasa de Aceptación",
                f"{tasa_aceptacion:.1f}%",
                delta=f"{total_renuentes:,} renuentes",
            )
        else:
            # Mostrar distribución PRE vs DURANTE
            if total_real > 0:
                prop_pre = (total_pre / total_real) * 100
                st.metric(
                    "📊 % PRE-Emergencia", f"{prop_pre:.1f}%", delta=f"del total real"
                )

    # Información de fecha de corte
    if combined_data.get("fecha_corte"):
        fecha_corte = combined_data["fecha_corte"]
        st.success(
            f"🎯 **Fecha de corte:** {fecha_corte.strftime('%d/%m/%Y')} - Inicio de la emergencia sanitaria"
        )


def show_combined_age_distribution(combined_data, COLORS, RANGOS_EDAD):
    """Muestra distribución combinada por rangos de edad"""
    st.subheader("👥 Distribución por Rangos de Edad (Combinada Sin Duplicados)")

    # Preparar datos combinados por edad
    individual_edad = combined_data["individual_pre"]["por_edad"]
    barridos_edad = combined_data["barridos"]["vacunados_barrido"]["por_edad"]

    age_data = []
    for rango in RANGOS_EDAD.keys():
        individual_count = individual_edad.get(rango, 0)
        barridos_count = barridos_edad.get(rango, 0)
        total_rango = individual_count + barridos_count

        if total_rango > 0:  # Solo mostrar rangos con datos
            age_data.append(
                {
                    "Rango": rango,
                    "Descripción": RANGOS_EDAD[rango],
                    "PRE-Emergencia": individual_count,
                    "DURANTE Emergencia": barridos_count,
                    "Total Real": total_rango,
                    "% del Total": (
                        (total_rango / combined_data["total_real_combinado"] * 100)
                        if combined_data["total_real_combinado"] > 0
                        else 0
                    ),
                }
            )

    if not age_data:
        st.warning("⚠️ No se encontraron datos de distribución por edad")
        return

    df_age = pd.DataFrame(age_data)
    df_age = df_age.sort_values("Total Real", ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        # Gráfico de barras apiladas temporal
        fig = px.bar(
            df_age,
            x="Rango",
            y=["PRE-Emergencia", "DURANTE Emergencia"],
            title="Vacunación por Período y Rango de Edad",
            color_discrete_map={
                "PRE-Emergencia": COLORS["primary"],
                "DURANTE Emergencia": COLORS["warning"],
            },
        )

        fig.update_layout(
            plot_bgcolor=COLORS["white"],
            paper_bgcolor=COLORS["white"],
            height=400,
            xaxis_title="Rango de Edad",
            yaxis_title="Cantidad de Vacunados",
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Gráfico circular de distribución total
        fig_pie = px.pie(
            df_age,
            values="Total Real",
            names="Descripción",
            title="Distribución % Total Real por Edad",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )

        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(height=400)

        st.plotly_chart(fig_pie, use_container_width=True)

    # Tabla resumen
    st.markdown("**📋 Resumen por Rangos de Edad (Datos Reales Sin Duplicados):**")

    # Preparar tabla para mostrar
    tabla_display = df_age[
        [
            "Descripción",
            "PRE-Emergencia",
            "DURANTE Emergencia",
            "Total Real",
            "% del Total",
        ]
    ].copy()
    tabla_display["% del Total"] = tabla_display["% del Total"].round(1)

    # Agregar fila de totales
    fila_total = {
        "Descripción": "**TOTAL GENERAL**",
        "PRE-Emergencia": df_age["PRE-Emergencia"].sum(),
        "DURANTE Emergencia": df_age["DURANTE Emergencia"].sum(),
        "Total Real": df_age["Total Real"].sum(),
        "% del Total": 100.0,
    }
    tabla_display = pd.concat(
        [tabla_display, pd.DataFrame([fila_total])], ignore_index=True
    )

    st.dataframe(
        tabla_display,
        use_container_width=True,
        column_config={
            "Descripción": st.column_config.TextColumn("Rango de Edad"),
            "PRE-Emergencia": st.column_config.NumberColumn(
                "PRE-Emergencia", format="%d"
            ),
            "DURANTE Emergencia": st.column_config.NumberColumn(
                "DURANTE Emergencia", format="%d"
            ),
            "Total Real": st.column_config.NumberColumn("Total Real", format="%d"),
            "% del Total": st.column_config.NumberColumn(
                "% del Total", format="%.1f%%"
            ),
        },
        hide_index=True,
    )


def show_periods_analysis(combined_data, COLORS):
    """Muestra análisis de períodos temporales"""
    st.subheader("⏰ Análisis de Períodos")

    total_pre = combined_data["total_individual_pre"]
    total_barridos = combined_data["total_barridos"]
    total_real = combined_data["total_real_combinado"]

    if total_real == 0:
        st.warning("⚠️ No hay datos para analizar períodos")
        return

    # Calcular proporciones
    prop_pre = (total_pre / total_real) * 100
    prop_durante = (total_barridos / total_real) * 100

    col1, col2 = st.columns(2)

    with col1:
        # Gráfico de comparación temporal
        periodos = ["PRE-Emergencia\n(Individual)", "DURANTE Emergencia\n(Barridos)"]
        valores = [total_pre, total_barridos]

        fig = go.Figure(
            data=[
                go.Bar(
                    x=periodos,
                    y=valores,
                    text=[
                        f"{val:,}<br>({prop:.1f}%)"
                        for val, prop in zip(valores, [prop_pre, prop_durante])
                    ],
                    textposition="auto",
                    marker_color=[COLORS["primary"], COLORS["warning"]],
                )
            ]
        )

        fig.update_layout(
            title="Comparación de Períodos",
            xaxis_title="Período",
            yaxis_title="Cantidad de Vacunados",
            plot_bgcolor=COLORS["white"],
            paper_bgcolor=COLORS["white"],
            height=400,
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Gráfico de dona temporal
        fig_donut = go.Figure(
            data=[
                go.Pie(
                    labels=periodos,
                    values=valores,
                    hole=0.4,
                    marker_colors=[COLORS["primary"], COLORS["warning"]],
                    textinfo="percent+label",
                )
            ]
        )

        fig_donut.update_layout(
            title="Proporción Temporal",
            height=400,
            annotations=[
                dict(
                    text=f"Total Real<br>{total_real:,}",
                    x=0.5,
                    y=0.5,
                    font_size=16,
                    showarrow=False,
                )
            ],
        )

        st.plotly_chart(fig_donut, use_container_width=True)

    # Insights estratégicos temporales
    st.markdown("**🎯 Análisis Estratégico Temporal:**")

    insights = []

    if prop_pre > 60:
        insights.append(
            "✅ **Respuesta temprana efectiva:** La mayoría de vacunación ocurrió antes de la emergencia"
        )
    elif prop_durante > 60:
        insights.append(
            "🚨 **Intervención de emergencia crucial:** Los barridos fueron fundamentales para la cobertura"
        )
    else:
        insights.append(
            "⚖️ **Respuesta equilibrada:** Combinación efectiva de estrategias PRE y DURANTE emergencia"
        )

    if total_barridos > total_pre:
        insights.append(
            "📍 **Intensificación exitosa:** Los barridos superaron la vacunación pre-emergencia"
        )

    # Mostrar insights
    for insight in insights:
        st.markdown(insight)


def show_territorial_summary_combined(combined_data, COLORS):
    """Muestra resumen territorial con datos combinados"""
    st.subheader("🗺️ Resumen Territorial (Datos Combinados)")

    total_poblacion = combined_data["population"]["total"]
    total_vacunados = combined_data["total_real_combinado"]

    if total_poblacion == 0:
        return

    # Calcular métricas territoriales
    cobertura_real = (total_vacunados / total_poblacion) * 100
    meta_80 = total_poblacion * 0.8
    avance_meta = (total_vacunados / meta_80) * 100
    faltante_meta = max(0, meta_80 - total_vacunados)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Población Asegurada", f"{total_poblacion:,}")

    with col2:
        st.metric("Cobertura Real Combinada", f"{cobertura_real:.1f}%")

    with col3:
        st.metric("Avance Meta 80%", f"{avance_meta:.1f}%")

    with col4:
        st.metric("Faltante para Meta", f"{faltante_meta:,.0f}")

    # Análisis de municipios
    municipios_con_datos = len(combined_data["population"]["por_municipio"])

    st.markdown(
        f"**📊 Análisis de {municipios_con_datos} municipios con población asegurada registrada**"
    )

    # Mostrar concentración poblacional
    poblacion_municipios = combined_data["population"]["por_municipio"]
    top_5_poblacion = sorted(
        poblacion_municipios.items(), key=lambda x: x[1], reverse=True
    )[:5]

    if top_5_poblacion:
        st.markdown("**🏘️ Top 5 Municipios por Población Asegurada:**")
        for i, (municipio, poblacion) in enumerate(top_5_poblacion, 1):
            pct_total = (poblacion / total_poblacion) * 100

            # Calcular vacunados combinados del municipio
            individual_mun = combined_data["individual_pre"]["por_municipio"].get(
                municipio, 0
            )
            barridos_mun = combined_data["barridos"]["vacunados_barrido"][
                "por_municipio"
            ].get(municipio, 0)
            total_mun = individual_mun + barridos_mun
            cobertura_mun = (total_mun / poblacion) * 100 if poblacion > 0 else 0

            st.write(
                f"{i}. **{municipio}**: {poblacion:,} hab. ({pct_total:.1f}%) - Cobertura: {cobertura_mun:.1f}%"
            )
