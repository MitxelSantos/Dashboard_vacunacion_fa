"""
vistas/geographic.py - Vista de distribución geográfica
Enfocada en análisis territorial y cobertura por municipios
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def show_geographic_tab(combined_data, COLORS):
    """Muestra análisis geográfico con énfasis en cobertura territorial"""
    st.header("🗺️ Distribución Geográfica")

    # Análisis por tipo de intervención
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📍 Concentración de Vacunación Individual")

        # Analizar datos históricos por fecha
        if not combined_data.get("temporal_data", pd.DataFrame()).empty:
            df_hist = combined_data["temporal_data"][
                combined_data["temporal_data"]["fuente"] == "Históricos (PAI)"
            ]

            if not df_hist.empty:
                # Agrupar por fecha para identificar días con mayor actividad
                actividad_por_dia = (
                    df_hist.groupby(df_hist["fecha"].dt.date).size().reset_index()
                )
                actividad_por_dia.columns = ["Fecha", "Vacunados"]
                actividad_por_dia = actividad_por_dia.sort_values(
                    "Vacunados", ascending=False
                )

                # Calcular porcentajes
                total_vacunados_hist = actividad_por_dia["Vacunados"].sum()
                actividad_por_dia["Porcentaje"] = (
                    actividad_por_dia["Vacunados"] / total_vacunados_hist
                ) * 100
                actividad_por_dia["Porcentaje_Acum"] = actividad_por_dia[
                    "Porcentaje"
                ].cumsum()

                # Top 15 días con más actividad
                top_dias = actividad_por_dia.head(15)

                fig = px.bar(
                    top_dias,
                    y="Fecha",
                    x="Porcentaje",
                    orientation="h",
                    title="Top 15 Días - Concentración de Vacunación (%)",
                    color_discrete_sequence=[COLORS["primary"]],
                    text="Porcentaje",
                )

                fig.update_traces(
                    texttemplate="%{text:.1f}%",
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>"
                    + "Porcentaje: %{x:.1f}%<br>"
                    + "Vacunados: %{customdata:,}<extra></extra>",
                    customdata=top_dias["Vacunados"],
                )

                fig.update_layout(
                    plot_bgcolor=COLORS["white"],
                    paper_bgcolor=COLORS["white"],
                    height=500,
                    yaxis={"categoryorder": "total ascending"},
                    xaxis_title="Porcentaje del Total Individual (%)",
                )
                st.plotly_chart(fig, use_container_width=True)

                # Estadísticas de concentración
                st.markdown("**📊 Estadísticas de Concentración:**")
                dias_80_pct = len(
                    actividad_por_dia[actividad_por_dia["Porcentaje_Acum"] <= 80]
                )
                dias_total = len(actividad_por_dia)
                concentracion = (dias_80_pct / dias_total) * 100

                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("80% vacunados en", f"{dias_80_pct} días")
                with col_b:
                    st.metric("Concentración", f"{concentracion:.1f}%")

        else:
            st.info("Datos históricos no disponibles para análisis geográfico")

    with col2:
        st.subheader("🚨 Efectividad de Barridos Territoriales")

        # Analizar datos de barridos
        df_barr = (
            combined_data["temporal_data"][
                combined_data["temporal_data"]["fuente"] == "Barridos (Emergencia)"
            ]
            if not combined_data["temporal_data"].empty
            else pd.DataFrame()
        )

        if not df_barr.empty:
            # Agrupar por fecha para mostrar efectividad de barridos
            barridos_por_dia = (
                df_barr.groupby(df_barr["fecha"].dt.date).size().reset_index()
            )
            barridos_por_dia.columns = ["Fecha", "Vacunas_Aplicadas"]
            barridos_por_dia = barridos_por_dia.sort_values(
                "Vacunas_Aplicadas", ascending=False
            )

            # Calcular porcentajes
            total_vacunas_barridos = barridos_por_dia["Vacunas_Aplicadas"].sum()
            barridos_por_dia["Porcentaje"] = (
                barridos_por_dia["Vacunas_Aplicadas"] / total_vacunas_barridos
            ) * 100
            barridos_por_dia["Porcentaje_Acum"] = barridos_por_dia[
                "Porcentaje"
            ].cumsum()

            # Top 15 días más efectivos
            top_barridos = barridos_por_dia.head(15)

            fig = px.bar(
                top_barridos,
                y="Fecha",
                x="Porcentaje",
                orientation="h",
                title="Top 15 Días - Efectividad de Barridos (%)",
                color_discrete_sequence=[COLORS["warning"]],
                text="Porcentaje",
            )

            fig.update_traces(
                texttemplate="%{text:.1f}%",
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>"
                + "Porcentaje: %{x:.1f}%<br>"
                + "Vacunas: %{customdata:,}<extra></extra>",
                customdata=top_barridos["Vacunas_Aplicadas"],
            )

            fig.update_layout(
                plot_bgcolor=COLORS["white"],
                paper_bgcolor=COLORS["white"],
                height=500,
                yaxis={"categoryorder": "total ascending"},
                xaxis_title="Porcentaje del Total Barridos (%)",
            )
            st.plotly_chart(fig, use_container_width=True)

            # Estadísticas de efectividad
            st.markdown("**📊 Estadísticas de Efectividad:**")
            dias_barridos = len(barridos_por_dia)
            promedio_diario = (
                total_vacunas_barridos / dias_barridos if dias_barridos > 0 else 0
            )

            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Promedio Diario", f"{promedio_diario:.0f} vacunas")
            with col_b:
                st.metric("Días Activos", f"{dias_barridos} días")

        else:
            st.info("Datos de barridos no disponibles para análisis geográfico")

    # Análisis comparativo de eficiencia
    st.subheader("⚖️ Comparación de Eficiencia Territorial")

    if (
        not combined_data["temporal_data"].empty
        and len(combined_data["temporal_data"]["fuente"].unique()) > 1
    ):

        # Comparar eficiencia entre modalidades
        eficiencia_data = []

        for fuente in combined_data["temporal_data"]["fuente"].unique():
            data_fuente = combined_data["temporal_data"][
                combined_data["temporal_data"]["fuente"] == fuente
            ]

            if not data_fuente.empty:
                dias_activos = data_fuente["fecha"].dt.date.nunique()
                total_vacunados = len(data_fuente)
                promedio_diario = (
                    total_vacunados / dias_activos if dias_activos > 0 else 0
                )

                eficiencia_data.append(
                    {
                        "Modalidad": fuente.split("(")[0].strip(),
                        "Total_Vacunados": total_vacunados,
                        "Dias_Activos": dias_activos,
                        "Promedio_Diario": promedio_diario,
                        "Eficiencia_Relativa": 0,  # Se calculará después
                    }
                )

        if len(eficiencia_data) >= 2:
            df_eficiencia = pd.DataFrame(eficiencia_data)

            # Calcular eficiencia relativa (%)
            max_eficiencia = df_eficiencia["Promedio_Diario"].max()
            df_eficiencia["Eficiencia_Relativa"] = (
                df_eficiencia["Promedio_Diario"] / max_eficiencia
            ) * 100

            # Gráfico de comparación
            fig = px.bar(
                df_eficiencia,
                x="Modalidad",
                y="Eficiencia_Relativa",
                title="Eficiencia Relativa por Modalidad (%)",
                color="Modalidad",
                color_discrete_map={
                    "Históricos": COLORS["primary"],
                    "Barridos": COLORS["warning"],
                },
                text="Eficiencia_Relativa",
            )

            fig.update_traces(
                texttemplate="%{text:.1f}%",
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>"
                + "Eficiencia: %{y:.1f}%<br>"
                + "Promedio/día: %{customdata:.0f}<extra></extra>",
                customdata=df_eficiencia["Promedio_Diario"],
            )

            fig.update_layout(
                plot_bgcolor=COLORS["white"],
                paper_bgcolor=COLORS["white"],
                height=400,
                yaxis_title="Eficiencia Relativa (%)",
                showlegend=False,
            )

            st.plotly_chart(fig, use_container_width=True)

            # Tabla de métricas detalladas
            st.markdown("**📋 Métricas Detalladas por Modalidad:**")

            df_display = df_eficiencia.copy()
            df_display = df_display.rename(
                columns={
                    "Modalidad": "Modalidad",
                    "Total_Vacunados": "Total Vacunados",
                    "Dias_Activos": "Días Activos",
                    "Promedio_Diario": "Promedio/Día",
                    "Eficiencia_Relativa": "Eficiencia (%)",
                }
            )

            # Formatear columnas
            df_display["Promedio/Día"] = df_display["Promedio/Día"].round(1)
            df_display["Eficiencia (%)"] = df_display["Eficiencia (%)"].round(1)

            st.dataframe(
                df_display,
                use_container_width=True,
                column_config={
                    "Total Vacunados": st.column_config.NumberColumn(
                        "Total Vacunados", format="%d"
                    ),
                    "Promedio/Día": st.column_config.NumberColumn(
                        "Promedio/Día", format="%.1f"
                    ),
                    "Eficiencia (%)": st.column_config.NumberColumn(
                        "Eficiencia (%)", format="%.1f%%"
                    ),
                },
            )

    # Análisis de cobertura territorial
    st.subheader("🎯 Indicadores de Cobertura Territorial")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Intensidad de cobertura
        total_registros = len(combined_data.get("temporal_data", pd.DataFrame()))
        if total_registros > 0:
            st.metric("Registros Totales", f"{total_registros:,}")

    with col2:
        # Diversidad temporal
        if not combined_data.get("temporal_data", pd.DataFrame()).empty:
            dias_unicos = combined_data["temporal_data"]["fecha"].dt.date.nunique()
            st.metric("Días con Actividad", f"{dias_unicos}")

    with col3:
        # Modalidades activas
        modalidades = (
            len(combined_data.get("temporal_data", pd.DataFrame())["fuente"].unique())
            if not combined_data.get("temporal_data", pd.DataFrame()).empty
            else 0
        )
        st.metric("Modalidades Activas", f"{modalidades}/2")

    with col4:
        # Eficiencia global
        if not combined_data.get("temporal_data", pd.DataFrame()).empty:
            dias_span = combined_data["temporal_data"]["fecha"].dt.date.nunique()
            eficiencia_global = total_registros / dias_span if dias_span > 0 else 0
            st.metric("Eficiencia Global", f"{eficiencia_global:.0f}/día")
