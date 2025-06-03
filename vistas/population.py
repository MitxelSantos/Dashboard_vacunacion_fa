"""
vistas/population.py - Vista de análisis de población
Enfocada en distribución por EAPB y métricas de cobertura poblacional
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def show_population_tab(df_population, combined_data, COLORS):
    """Muestra análisis de población con énfasis en cobertura por EAPB"""
    st.header("🏥 Análisis de Población por EAPB")

    if df_population.empty:
        st.warning("No hay datos de población disponibles")
        return

    # Identificar columnas
    eapb_col = None
    municipio_col = None
    poblacion_col = None

    for col in df_population.columns:
        col_upper = str(col).upper()
        if (
            "EAPB" in col_upper
            or "NOMBRE ENTIDAD" in col_upper
            or "ENTIDAD" in col_upper
        ):
            eapb_col = col
        elif "MUNICIPIO" in col_upper:
            municipio_col = col
        elif "TOTAL" in col_upper or "POBLACION" in col_upper:
            poblacion_col = col

    if not all([eapb_col, poblacion_col]):
        st.error(
            "No se pudieron identificar las columnas necesarias en los datos de población"
        )
        return

    # Análisis de estructura poblacional
    col1, col2, col3 = st.columns(3)

    total_poblacion = (
        pd.to_numeric(df_population[poblacion_col], errors="coerce").fillna(0).sum()
    )
    total_registros = len(df_population)
    municipios_unicos = df_population[municipio_col].nunique() if municipio_col else 0
    eapb_unicas = df_population[eapb_col].nunique()

    with col1:
        st.metric("Población Total", f"{total_poblacion:,}")

    with col2:
        st.metric("Municipios Únicos", f"{municipios_unicos}")

    with col3:
        st.metric("EAPB Activas", f"{eapb_unicas}")

    # Distribución por EAPB con porcentajes
    st.subheader("📊 Distribución de Población por EAPB")

    eapb_totals = (
        df_population.groupby(eapb_col)[poblacion_col]
        .sum()
        .sort_values(ascending=False)
    )

    # Calcular porcentajes
    eapb_percentages = (eapb_totals / total_poblacion) * 100

    col1, col2 = st.columns(2)

    with col1:
        # Top 10 EAPB por población (barras horizontales con porcentajes)
        top_eapb = eapb_totals.head(10)
        top_eapb_pct = eapb_percentages.head(10)

        # Crear DataFrame para el gráfico
        top_eapb_data = pd.DataFrame(
            {
                "EAPB": top_eapb.index,
                "Población": top_eapb.values,
                "Porcentaje": top_eapb_pct.values,
            }
        )

        fig = px.bar(
            top_eapb_data,
            y="EAPB",
            x="Porcentaje",
            orientation="h",
            title="Top 10 EAPB por Población (%)",
            color_discrete_sequence=[COLORS["secondary"]],
            text="Porcentaje",
        )

        fig.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>"
            + "Porcentaje: %{x:.1f}%<br>"
            + "Población: %{customdata:,}<extra></extra>",
            customdata=top_eapb_data["Población"],
        )

        fig.update_layout(
            plot_bgcolor=COLORS["white"],
            paper_bgcolor=COLORS["white"],
            height=500,
            yaxis={"categoryorder": "total ascending"},
            xaxis_title="Porcentaje de Población (%)",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Distribución porcentual - gráfico circular
        # Agrupar EAPB pequeñas en "Otras"
        top_8_eapb = eapb_percentages.head(8)
        otras_pct = eapb_percentages.iloc[8:].sum()

        if otras_pct > 0:
            pie_data = top_8_eapb.tolist() + [otras_pct]
            pie_labels = top_8_eapb.index.tolist() + ["Otras EAPB"]
        else:
            pie_data = top_8_eapb.tolist()
            pie_labels = top_8_eapb.index.tolist()

        fig = px.pie(
            values=pie_data,
            names=pie_labels,
            title="Distribución % - EAPB Principal",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )

        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>"
            + "Porcentaje: %{percent}<br>"
            + "Población: %{value:.0f}<extra></extra>",
        )

        fig.update_layout(height=500, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    # Análisis de cobertura por EAPB
    if combined_data["total_general"] > 0:
        st.subheader("📈 Análisis de Cobertura por EAPB")

        # Calcular métricas de cobertura
        cobertura_general = combined_data["total_general"] / total_poblacion * 100
        meta_poblacional = total_poblacion * 0.8
        avance_meta = combined_data["total_general"] / meta_poblacional * 100

        # Mostrar métricas principales
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Cobertura General", f"{cobertura_general:.1f}%")

        with col2:
            st.metric("Avance Meta (80%)", f"{avance_meta:.1f}%")

        with col3:
            total_renuentes = combined_data["barridos_totales"].get(
                "total_renuentes", 0
            )
            if total_renuentes > 0:
                tasa_aceptacion = (
                    combined_data["total_general"]
                    / (combined_data["total_general"] + total_renuentes)
                    * 100
                )
                st.metric("Tasa de Aceptación", f"{tasa_aceptacion:.1f}%")
            else:
                st.metric("Renuentes", "0")

        with col4:
            poblacion_contactada = combined_data["total_general"] + total_renuentes
            pct_contactado = poblacion_contactada / total_poblacion * 100
            st.metric("Población Contactada", f"{pct_contactado:.1f}%")

        # Análisis detallado de cobertura esperada por EAPB
        st.subheader("🎯 Cobertura Esperada vs Real por EAPB")

        # Calcular cobertura esperada por EAPB (proporcional a su población)
        cobertura_esperada_data = []

        for eapb in eapb_totals.head(10).index:
            poblacion_eapb = eapb_totals[eapb]
            porcentaje_poblacion = (poblacion_eapb / total_poblacion) * 100

            # Cobertura esperada proporcional
            vacunados_esperados = combined_data["total_general"] * (
                poblacion_eapb / total_poblacion
            )

            # Cobertura ideal (80% de su población)
            cobertura_ideal = poblacion_eapb * 0.8

            cobertura_esperada_data.append(
                {
                    "EAPB": eapb,
                    "Población": poblacion_eapb,
                    "% Población": porcentaje_poblacion,
                    "Vacunados Esperados": vacunados_esperados,
                    "Cobertura Ideal": cobertura_ideal,
                    "Gap a Ideal": cobertura_ideal - vacunados_esperados,
                }
            )

        df_cobertura = pd.DataFrame(cobertura_esperada_data)

        # Gráfico de brechas de cobertura
        fig = go.Figure()

        # Barras de cobertura esperada
        fig.add_trace(
            go.Bar(
                name="Cobertura Actual Esperada",
                x=df_cobertura["EAPB"],
                y=df_cobertura["Vacunados Esperados"],
                marker_color=COLORS["success"],
                text=[f"{val:,.0f}" for val in df_cobertura["Vacunados Esperados"]],
                textposition="inside",
            )
        )

        # Barras de brecha a cobertura ideal
        fig.add_trace(
            go.Bar(
                name="Brecha a Meta (80%)",
                x=df_cobertura["EAPB"],
                y=df_cobertura["Gap a Ideal"],
                marker_color=COLORS["warning"],
                text=[f"{val:,.0f}" for val in df_cobertura["Gap a Ideal"]],
                textposition="inside",
            )
        )

        fig.update_layout(
            title="Cobertura Actual vs Brecha a Meta por EAPB",
            xaxis_title="EAPB",
            yaxis_title="Personas",
            barmode="stack",
            plot_bgcolor=COLORS["white"],
            paper_bgcolor=COLORS["white"],
            height=500,
        )

        st.plotly_chart(fig, use_container_width=True)

        # Tabla detallada con porcentajes
        st.subheader("📋 Detalle de Cobertura por EAPB")

        # Preparar datos para tabla
        tabla_cobertura = df_cobertura.copy()
        tabla_cobertura["Cobertura Actual %"] = (
            tabla_cobertura["Vacunados Esperados"] / tabla_cobertura["Población"] * 100
        )
        tabla_cobertura["Avance a Meta %"] = (
            tabla_cobertura["Vacunados Esperados"]
            / tabla_cobertura["Cobertura Ideal"]
            * 100
        )

        # Formatear para display
        tabla_display = tabla_cobertura[
            [
                "EAPB",
                "Población",
                "% Población",
                "Cobertura Actual %",
                "Avance a Meta %",
            ]
        ].copy()

        # Redondear valores
        tabla_display["% Población"] = tabla_display["% Población"].round(1)
        tabla_display["Cobertura Actual %"] = tabla_display["Cobertura Actual %"].round(
            1
        )
        tabla_display["Avance a Meta %"] = tabla_display["Avance a Meta %"].round(1)

        # Renombrar columnas
        tabla_display = tabla_display.rename(
            columns={
                "EAPB": "EAPB",
                "Población": "Población Total",
                "% Población": "% del Total",
                "Cobertura Actual %": "Cobertura (%)",
                "Avance a Meta %": "Avance Meta (%)",
            }
        )

        st.dataframe(
            tabla_display,
            use_container_width=True,
            column_config={
                "Población Total": st.column_config.NumberColumn(
                    "Población Total", format="%d"
                ),
                "% del Total": st.column_config.NumberColumn(
                    "% del Total", format="%.1f%%"
                ),
                "Cobertura (%)": st.column_config.NumberColumn(
                    "Cobertura (%)", format="%.1f%%"
                ),
                "Avance Meta (%)": st.column_config.NumberColumn(
                    "Avance Meta (%)", format="%.1f%%"
                ),
            },
        )

    # Análisis de diversidad poblacional
    st.subheader("🏢 Diversidad del Sistema de Aseguramiento")

    if municipio_col:
        # Análisis de EAPB por municipio
        eapb_por_municipio = (
            df_population.groupby(municipio_col)[eapb_col]
            .nunique()
            .sort_values(ascending=False)
        )
        municipios_multiples_eapb = (eapb_por_municipio > 1).sum()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Municipios con Múltiples EAPB", f"{municipios_multiples_eapb}")

        with col2:
            max_eapb_municipio = eapb_por_municipio.max()
            st.metric("Máximo EAPB por Municipio", f"{max_eapb_municipio}")

        with col3:
            promedio_eapb = eapb_por_municipio.mean()
            st.metric("Promedio EAPB/Municipio", f"{promedio_eapb:.1f}")

        # Gráfico de diversidad
        if len(eapb_por_municipio) > 0:
            # Top municipios con más diversidad de EAPB
            top_diversidad = eapb_por_municipio.head(15)

            fig = px.bar(
                x=top_diversidad.values,
                y=top_diversidad.index,
                orientation="h",
                title="Top 15 Municipios - Diversidad de EAPB",
                color_discrete_sequence=[COLORS["accent"]],
                text=top_diversidad.values,
            )

            fig.update_traces(textposition="outside")
            fig.update_layout(
                plot_bgcolor=COLORS["white"],
                paper_bgcolor=COLORS["white"],
                height=500,
                yaxis={"categoryorder": "total ascending"},
                xaxis_title="Número de EAPB",
                yaxis_title="Municipio",
            )

            st.plotly_chart(fig, use_container_width=True)

    # Resumen ejecutivo
    st.subheader("📊 Resumen Ejecutivo - Población")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🎯 Indicadores Clave:**")
        st.markdown(f"• **Población Total:** {total_poblacion:,} personas")
        st.markdown(
            f"• **EAPB más grande:** {eapb_totals.index[0]} ({eapb_percentages.iloc[0]:.1f}%)"
        )
        st.markdown(f"• **Concentración Top 3:** {eapb_percentages.head(3).sum():.1f}%")

        if combined_data["total_general"] > 0:
            st.markdown(f"• **Cobertura Actual:** {cobertura_general:.1f}%")
            st.markdown(f"• **Meta 80%:** {meta_poblacional:,.0f} personas")

    with col2:
        st.markdown("**📈 Oportunidades:**")

        if combined_data["total_general"] > 0:
            pendiente_vacunar = meta_poblacional - combined_data["total_general"]
            porcentaje_pendiente = (pendiente_vacunar / total_poblacion) * 100

            st.markdown(f"• **Pendiente para meta:** {pendiente_vacunar:,.0f} personas")
            st.markdown(f"• **Porcentaje pendiente:** {porcentaje_pendiente:.1f}%")

        st.markdown(
            f"• **Municipios diversos:** {municipios_multiples_eapb} de {municipios_unicos}"
        )
        st.markdown(
            f"• **EAPB menores (<5%):** {len(eapb_percentages[eapb_percentages < 5])}"
        )
