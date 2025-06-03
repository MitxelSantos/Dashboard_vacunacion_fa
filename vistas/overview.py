"""
vistas/overview.py - Vista de resumen general
Enfocada en mostrar porcentajes y métricas principales
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def show_overview_tab(combined_data, df_population, fechas_info, COLORS, RANGOS_EDAD):
    """Muestra la vista general del dashboard con énfasis en porcentajes"""
    st.header("📊 Resumen General")

    # Calcular población total
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

    # Métricas principales con porcentajes
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        individual_count = combined_data["total_individual"]
        if total_population > 0:
            individual_pct = (individual_count / total_population) * 100
            st.metric(
                "PAI (Históricos)",
                f"{individual_pct:.1f}%",
                delta=f"{individual_count:,} vacunados",
            )
        else:
            st.metric("PAI (Históricos)", f"{individual_count:,}")

    with col2:
        barridos_count = combined_data["total_barridos"]
        if total_population > 0:
            barridos_pct = (barridos_count / total_population) * 100
            st.metric(
                "Barridos (Nuevas)",
                f"{barridos_pct:.1f}%",
                delta=f"{barridos_count:,} vacunados",
            )
        else:
            st.metric("Barridos (Nuevas)", f"{barridos_count:,}")

    with col3:
        total_vacunados = combined_data["total_general"]
        if total_population > 0:
            cobertura_total = (total_vacunados / total_population) * 100
            st.metric(
                "Cobertura Total",
                f"{cobertura_total:.1f}%",
                delta=f"{total_vacunados:,} vacunados",
            )
        else:
            st.metric("Total Vacunados", f"{total_vacunados:,}")

    with col4:
        if total_population > 0:
            meta = total_population * 0.8
            avance_meta = (total_vacunados / meta) * 100
            st.metric(
                "Avance Meta (80%)", f"{avance_meta:.1f}%", delta=f"Meta: {meta:,.0f}"
            )
        else:
            st.metric("Población Total", f"{total_population:,}")

    # Gráficos principales con porcentajes
    col1, col2 = st.columns(2)

    with col1:
        # Distribución porcentual por modalidad
        if total_population > 0:
            individual_pct = (
                combined_data["total_individual"] / total_population
            ) * 100
            barridos_pct = (combined_data["total_barridos"] / total_population) * 100
            sin_vacunar_pct = 100 - individual_pct - barridos_pct

            modalidades_data = {
                "Modalidad": ["Individual (PAI)", "Barridos", "Sin Vacunar"],
                "Porcentaje": [individual_pct, barridos_pct, sin_vacunar_pct],
                "Cantidad": [
                    combined_data["total_individual"],
                    combined_data["total_barridos"],
                    total_population - combined_data["total_general"],
                ],
            }

            fig = px.bar(
                modalidades_data,
                x="Modalidad",
                y="Porcentaje",
                title="Distribución de Cobertura (%)",
                color="Modalidad",
                color_discrete_map={
                    "Individual (PAI)": COLORS["primary"],
                    "Barridos": COLORS["warning"],
                    "Sin Vacunar": COLORS["accent"],
                },
                text="Porcentaje",
            )

            # Personalizar el texto en las barras
            fig.update_traces(
                texttemplate="%{text:.1f}%<br>%{customdata:,}",
                textposition="inside",
                customdata=modalidades_data["Cantidad"],
            )

            fig.update_layout(
                plot_bgcolor=COLORS["white"],
                paper_bgcolor=COLORS["white"],
                height=400,
                yaxis_title="Porcentaje de Población (%)",
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Fallback sin población
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
        # Gráfico de cobertura y contacto poblacional
        total_renuentes = combined_data["barridos_totales"].get("total_renuentes", 0)
        total_vacunados = combined_data["total_general"]

        if total_population > 0:
            contactados = total_vacunados + total_renuentes
            sin_contactar = max(0, total_population - contactados)

            # Calcular porcentajes
            vacunados_pct = (total_vacunados / total_population) * 100
            renuentes_pct = (total_renuentes / total_population) * 100
            sin_contactar_pct = (sin_contactar / total_population) * 100

            # Datos para gráfico circular
            cobertura_data = {
                "Categoría": ["Vacunados", "Renuentes", "Sin Contactar"],
                "Porcentaje": [vacunados_pct, renuentes_pct, sin_contactar_pct],
                "Cantidad": [total_vacunados, total_renuentes, sin_contactar],
            }

            fig = px.pie(
                cobertura_data,
                values="Porcentaje",
                names="Categoría",
                title="Estado de Contacto Poblacional (%)",
                color_discrete_map={
                    "Vacunados": COLORS["success"],
                    "Renuentes": "#FF6B6B",
                    "Sin Contactar": "#D3D3D3",
                },
            )

            # Personalizar el texto
            fig.update_traces(
                textposition="inside",
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>"
                + "Porcentaje: %{percent}<br>"
                + "Cantidad: %{customdata:,}<extra></extra>",
                customdata=cobertura_data["Cantidad"],
            )

            fig.update_layout(height=400, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

        else:
            # Fallback: distribución por edad de barridos
            if combined_data["barridos_totales"].get("por_edad"):
                rangos_data = combined_data["barridos_totales"]["por_edad"]
                total_barridos = sum(data["total"] for data in rangos_data.values())

                if total_barridos > 0:
                    labels = [RANGOS_EDAD.get(k, k) for k in rangos_data.keys()]
                    values = [data["total"] for data in rangos_data.values()]
                    percentages = [(v / total_barridos) * 100 for v in values]

                    fig = px.pie(
                        values=percentages,
                        names=labels,
                        title="Distribución Barridos por Edad (%)",
                        color_discrete_sequence=px.colors.qualitative.Set3,
                    )
                    fig.update_traces(textposition="inside", textinfo="percent+label")
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

    # Tabla detallada por rangos de edad con porcentajes
    st.subheader("📊 Detalle por Rangos de Edad")

    age_detail_data = []
    total_general = combined_data["total_general"]

    for rango, label in RANGOS_EDAD.items():
        individual = 0
        barridos = 0

        if combined_data["historical_processed"].get("por_edad", {}).get(rango):
            individual = combined_data["historical_processed"]["por_edad"][rango][
                "total"
            ]

        if combined_data["barridos_totales"].get("por_edad", {}).get(rango):
            barridos = combined_data["barridos_totales"]["por_edad"][rango]["total"]

        total_rango = individual + barridos

        if total_rango > 0:  # Solo mostrar rangos con datos
            pct_del_total = (
                (total_rango / total_general * 100) if total_general > 0 else 0
            )
            pct_individual = (individual / total_rango * 100) if total_rango > 0 else 0
            pct_barridos = (barridos / total_rango * 100) if total_rango > 0 else 0

            age_detail_data.append(
                {
                    "Rango de Edad": label,
                    "Total": total_rango,
                    "% del Total General": f"{pct_del_total:.1f}%",
                    "Individual": individual,
                    "% Individual": f"{pct_individual:.1f}%",
                    "Barridos": barridos,
                    "% Barridos": f"{pct_barridos:.1f}%",
                }
            )

    if age_detail_data:
        df_detail = pd.DataFrame(age_detail_data)

        # Configurar el estilo de la tabla
        st.dataframe(
            df_detail,
            use_container_width=True,
            column_config={
                "Total": st.column_config.NumberColumn("Total", format="%d"),
                "Individual": st.column_config.NumberColumn("Individual", format="%d"),
                "Barridos": st.column_config.NumberColumn("Barridos", format="%d"),
            },
        )

        # Métricas resumen
        st.markdown("### 📈 Métricas Resumen")
        col1, col2, col3 = st.columns(3)

        with col1:
            if total_population > 0:
                tasa_aceptacion = (
                    (total_general / (total_general + total_renuentes) * 100)
                    if (total_general + total_renuentes) > 0
                    else 0
                )
                st.metric("Tasa de Aceptación", f"{tasa_aceptacion:.1f}%")

        with col2:
            rangos_con_datos = len(age_detail_data)
            st.metric("Rangos con Datos", f"{rangos_con_datos}/11")

        with col3:
            if total_population > 0:
                poblacion_contactada = total_general + total_renuentes
                pct_contactado = poblacion_contactada / total_population * 100
                st.metric("Población Contactada", f"{pct_contactado:.1f}%")

    else:
        st.info("No hay datos detallados por edad disponibles")
