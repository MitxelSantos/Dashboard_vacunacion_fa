import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from src.visualization.charts import create_bar_chart, create_pie_chart


def normalize_insurance_data(df):
    """
    Normaliza los datos de aseguramiento reemplazando valores NaN con "Sin dato"
    """
    df_clean = df.copy()

    # Columnas a normalizar
    columns_to_clean = [
        "NombreAseguradora",
        "RegimenAfiliacion",
        "NombreMunicipioResidencia",
    ]

    for col in columns_to_clean:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna("Sin dato")
            df_clean[col] = df_clean[col].replace(
                ["", "nan", "NaN", "null", "NULL"], "Sin dato"
            )

    return df_clean


def create_eapb_municipality_heatmap(data, colors):
    """
    Crea un heatmap/gráfico de distribución de EAPB por municipio
    """
    try:
        # Crear tabla cruzada entre municipios y EAPB
        pivot_data = pd.crosstab(
            data["NombreMunicipioResidencia"], data["NombreAseguradora"], margins=False
        )

        # Convertir a porcentajes por fila (por municipio)
        pivot_pct = pivot_data.div(pivot_data.sum(axis=1), axis=0) * 100

        # Seleccionar top 10 municipios con más vacunados para mejor visualización
        top_municipios = data["NombreMunicipioResidencia"].value_counts().head(10).index
        pivot_pct_filtered = pivot_pct.loc[pivot_pct.index.intersection(top_municipios)]

        # Seleccionar top 8 EAPB para evitar sobrecarga visual
        top_eapb = data["NombreAseguradora"].value_counts().head(8).index
        pivot_pct_final = pivot_pct_filtered[
            pivot_pct_filtered.columns.intersection(top_eapb)
        ]

        if pivot_pct_final.empty:
            return None

        # Crear heatmap
        fig = go.Figure(
            data=go.Heatmap(
                z=pivot_pct_final.values,
                x=pivot_pct_final.columns,
                y=pivot_pct_final.index,
                colorscale="RdYlBu_r",
                hovertemplate="Municipio: %{y}<br>EAPB: %{x}<br>Porcentaje: %{z:.1f}%<extra></extra>",
                colorbar=dict(title="% de Vacunados"),
            )
        )

        fig.update_layout(
            title="Distribución de EAPB por Municipio (Top 10 municipios y 8 EAPB principales)",
            xaxis_title="EAPB",
            yaxis_title="Municipio",
            height=600,
            plot_bgcolor="white",
            paper_bgcolor="white",
        )

        # Rotar etiquetas del eje X para mejor legibilidad
        fig.update_xaxes(tickangle=45)

        return fig
    except Exception as e:
        st.error(f"Error creando heatmap: {str(e)}")
        return None


def create_eapb_coverage_by_municipality(data, metricas_data, fuente_poblacion, colors):
    """
    Crea gráfico de cobertura por EAPB en cada municipio
    """
    try:
        # Verificar que tenemos datos suficientes
        if len(data) == 0 or len(metricas_data) == 0:
            return None

        # Contar vacunados por EAPB y municipio
        eapb_municipio = (
            data.groupby(["NombreMunicipioResidencia", "NombreAseguradora"])
            .size()
            .reset_index()
        )
        eapb_municipio.columns = ["Municipio", "EAPB", "Vacunados"]

        # Preparar datos de métricas para fusión
        # Usar normalización de nombres de municipios
        from src.data.normalize import normalize_municipality_names

        # Normalizar nombres en ambos datasets
        metricas_norm = normalize_municipality_names(metricas_data.copy(), "DPMP")
        eapb_municipio_norm = normalize_municipality_names(
            eapb_municipio.copy(), "Municipio"
        )

        # Fusionar con datos de población usando nombres normalizados
        eapb_municipio_merged = pd.merge(
            eapb_municipio_norm,
            metricas_norm[["DPMP", "DPMP_norm", fuente_poblacion]],
            left_on="Municipio_norm",
            right_on="DPMP_norm",
            how="left",
        )

        # Eliminar registros sin población
        eapb_municipio_valid = eapb_municipio_merged.dropna(subset=[fuente_poblacion])

        if len(eapb_municipio_valid) == 0:
            return None

        # Calcular cobertura por EAPB por municipio
        # Evitar división por cero
        eapb_municipio_valid["Cobertura"] = np.where(
            eapb_municipio_valid[fuente_poblacion] > 0,
            (
                eapb_municipio_valid["Vacunados"]
                / eapb_municipio_valid[fuente_poblacion]
                * 100
            ).round(2),
            0,
        )

        # Filtrar para visualización: top municipios y EAPB
        top_municipios = data["NombreMunicipioResidencia"].value_counts().head(6).index
        top_eapb = data["NombreAseguradora"].value_counts().head(5).index

        filtered_data = eapb_municipio_valid[
            (eapb_municipio_valid["Municipio"].isin(top_municipios))
            & (eapb_municipio_valid["EAPB"].isin(top_eapb))
        ].copy()

        if len(filtered_data) == 0:
            return None

        # Crear gráfico de barras agrupadas
        fig = px.bar(
            filtered_data,
            x="Municipio",
            y="Cobertura",
            color="EAPB",
            title=f"Cobertura por EAPB en Municipios Principales (Población {fuente_poblacion})",
            labels={"Cobertura": "Cobertura (%)", "Municipio": "Municipio"},
            height=500,
            barmode="group",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )

        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis_tickangle=45,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )

        # Añadir valores en las barras solo si no hay demasiados datos
        if len(filtered_data) < 30:
            fig.update_traces(texttemplate="%{y:.1f}%", textposition="outside")

        return fig

    except Exception as e:
        return None


def show(data, filters, colors, fuente_poblacion="DANE"):
    """
    Muestra la página de aseguramiento del dashboard.
    VERSIÓN MEJORADA: Incluye análisis detallado de EAPB por municipio.

    Args:
        data (dict): Diccionario con los dataframes
        filters (dict): Filtros seleccionados
        colors (dict): Colores institucionales
        fuente_poblacion (str): Fuente de datos de población ("DANE" o "SISBEN")
    """
    st.title("Aseguramiento")

    # Aplicar filtros a los datos
    from src.data.preprocessor import apply_filters

    filtered_data = apply_filters(data, filters, fuente_poblacion)

    # Normalizar datos de aseguramiento
    filtered_data["vacunacion"] = normalize_insurance_data(filtered_data["vacunacion"])

    # =====================================================================
    # SECCIÓN 1: ANÁLISIS GENERAL DE RÉGIMEN Y ASEGURADORAS
    # =====================================================================
    st.subheader("Distribución General por Régimen y Aseguradoras")

    # Dividir en dos columnas
    col1, col2 = st.columns(2)

    # Gráfico de distribución por régimen
    with col1:
        try:
            # Agrupar por régimen
            regimen_counts = (
                filtered_data["vacunacion"]["RegimenAfiliacion"]
                .value_counts()
                .reset_index()
            )
            regimen_counts.columns = ["RegimenAfiliacion", "Vacunados"]

            # Calcular porcentajes
            regimen_counts["Porcentaje"] = (
                regimen_counts["Vacunados"] / regimen_counts["Vacunados"].sum() * 100
            ).round(1)

            # Crear gráfico
            fig_regimen = create_bar_chart(
                data=regimen_counts,
                x="RegimenAfiliacion",
                y="Vacunados",
                title="Distribución por régimen de afiliación",
                color=colors["primary"],
                height=400,
            )

            st.plotly_chart(fig_regimen, use_container_width=True)

            # Mostrar estadísticas
            st.info(
                f"""
            **Régimen predominante:** {regimen_counts.iloc[0]['RegimenAfiliacion']} 
            ({regimen_counts.iloc[0]['Porcentaje']:.1f}%)
            """
            )

        except Exception as e:
            st.error(f"Error al crear gráfico de distribución por régimen: {str(e)}")

    # Gráfico de distribución por aseguradora (Top 10)
    with col2:
        try:
            # Agrupar por aseguradora
            aseguradora_counts = (
                filtered_data["vacunacion"]["NombreAseguradora"]
                .value_counts()
                .reset_index()
            )
            aseguradora_counts.columns = ["NombreAseguradora", "Vacunados"]

            # Tomar las 10 principales aseguradoras
            top_aseguradoras = aseguradora_counts.head(10)

            # Crear gráfico
            fig_aseguradora = create_bar_chart(
                data=top_aseguradoras,
                x="NombreAseguradora",
                y="Vacunados",
                title="Top 10 EAPB/Aseguradoras",
                color=colors["secondary"],
                height=400,
            )

            st.plotly_chart(fig_aseguradora, use_container_width=True)

            # Mostrar estadísticas
            total_aseguradoras = len(aseguradora_counts)
            concentracion_top5 = (
                top_aseguradoras.head(5)["Vacunados"].sum()
                / top_aseguradoras["Vacunados"].sum()
                * 100
            )

            st.info(
                f"""
            **Total de EAPB:** {total_aseguradoras}  
            **Concentración Top 5:** {concentracion_top5:.1f}%
            """
            )

        except Exception as e:
            st.error(
                f"Error al crear gráfico de distribución por aseguradora: {str(e)}"
            )

    # =====================================================================
    # SECCIÓN 2: ANÁLISIS DETALLADO DE EAPB POR MUNICIPIO (NUEVA SECCIÓN)
    # =====================================================================
    st.subheader("📍 Distribución y Cobertura de EAPB por Municipio")

    st.markdown(
        """
    Esta sección muestra cómo se distribuyen las diferentes EAPB en cada municipio 
    y su contribución a la cobertura de vacunación.
    """
    )

    # Heatmap de distribución EAPB por municipio
    try:
        fig_heatmap = create_eapb_municipality_heatmap(
            filtered_data["vacunacion"], colors
        )
        if fig_heatmap:
            st.plotly_chart(fig_heatmap, use_container_width=True)

            st.markdown(
                """
            **Interpretación del Heatmap:** 
            - Colores más intensos indican mayor concentración de vacunados de esa EAPB en el municipio
            - Permite identificar patrones de distribución territorial de las aseguradoras
            """
            )
        else:
            st.warning("No se pudo generar el heatmap de distribución")

    except Exception as e:
        st.error(f"Error al crear heatmap de EAPB por municipio: {str(e)}")

    # Gráfico de cobertura por EAPB por municipio
    try:
        fig_coverage = create_eapb_coverage_by_municipality(
            filtered_data["vacunacion"],
            filtered_data["metricas"],
            fuente_poblacion,
            colors,
        )

        if fig_coverage:
            st.plotly_chart(fig_coverage, use_container_width=True)

            st.markdown(
                """
            **Interpretación de Cobertura por EAPB:** 
            - Muestra qué tan efectiva es cada EAPB en la vacunación por municipio
            - Permite identificar EAPB con mejor desempeño en diferentes territorios
            """
            )
        else:
            st.warning(
                "⚠️ No hay datos suficientes para mostrar el gráfico de cobertura por EAPB"
            )

    except Exception as e:
        st.error(f"Error al crear gráfico de cobertura por EAPB: {str(e)}")

    # =====================================================================
    # SECCIÓN 3: ANÁLISIS CRUZADO RÉGIMEN-MUNICIPIO
    # =====================================================================
    st.subheader("Análisis Cruzado: Régimen por Municipio")

    try:
        # Crear tabla cruzada
        regimen_municipio = pd.crosstab(
            filtered_data["vacunacion"]["NombreMunicipioResidencia"],
            filtered_data["vacunacion"]["RegimenAfiliacion"],
            margins=True,
            margins_name="Total",
        )

        # Mostrar tabla
        st.dataframe(regimen_municipio, use_container_width=True)

        # Gráfico de los municipios principales por régimen
        if st.checkbox("Mostrar gráfico de municipios principales por régimen"):
            # Obtener los 8 municipios con más vacunados
            top_municipios = (
                regimen_municipio.sort_values(by="Total", ascending=False)
                .head(9)  # 8 + Total
                .index[:-1]  # Excluir Total
            )

            # Filtrar datos para esos municipios
            top_data = filtered_data["vacunacion"][
                filtered_data["vacunacion"]["NombreMunicipioResidencia"].isin(
                    top_municipios
                )
            ]

            # Contar por municipio y régimen
            top_counts = (
                top_data.groupby(["NombreMunicipioResidencia", "RegimenAfiliacion"])
                .size()
                .reset_index()
            )
            top_counts.columns = ["Municipio", "Regimen", "Vacunados"]

            # Crear gráfico
            fig = px.bar(
                top_counts,
                x="Municipio",
                y="Vacunados",
                color="Regimen",
                title="Distribución por régimen en los municipios principales",
                height=500,
                barmode="group",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )

            # Personalizar diseño
            fig.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(l=10, r=10, t=40, b=10),
                title={"y": 0.98, "x": 0.5, "xanchor": "center", "yanchor": "top"},
                title_font=dict(size=16),
                legend_title="Régimen",
                xaxis_tickangle=45,
            )

            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error al crear análisis cruzado régimen-municipio: {str(e)}")

    # =====================================================================
    # SECCIÓN 4: ANÁLISIS DETALLADO POR ASEGURADORA ESPECÍFICA
    # =====================================================================
    st.subheader("🔍 Análisis Detallado por EAPB/Aseguradora")

    # Seleccionar aseguradora para análisis detallado
    try:
        # Obtener lista de aseguradoras (excluyendo "Sin dato")
        aseguradoras_lista = list(
            filtered_data["vacunacion"]["NombreAseguradora"]
            .value_counts()
            .drop("Sin dato", errors="ignore")
            .index
        )
        aseguradoras = ["Todas"] + sorted(aseguradoras_lista)

        aseguradora_seleccionada = st.selectbox(
            "Seleccione una EAPB/Aseguradora para análisis detallado:",
            options=aseguradoras,
        )

        if aseguradora_seleccionada != "Todas":
            # Filtrar datos para la aseguradora seleccionada
            datos_aseguradora = filtered_data["vacunacion"][
                filtered_data["vacunacion"]["NombreAseguradora"]
                == aseguradora_seleccionada
            ]

            if len(datos_aseguradora) == 0:
                st.warning(
                    f"No hay datos disponibles para la EAPB {aseguradora_seleccionada}"
                )
            else:
                # Métricas principales
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    total_vacunados = len(datos_aseguradora)
                    porcentaje = (
                        total_vacunados / len(filtered_data["vacunacion"]) * 100
                    )
                    st.metric(
                        label="Total vacunados",
                        value=f"{total_vacunados:,}".replace(",", "."),
                        delta=f"{porcentaje:.1f}% del total",
                    )

                with col2:
                    # Distribución por sexo/género
                    if "Sexo" in datos_aseguradora.columns:
                        dist_sexo = (
                            datos_aseguradora["Sexo"]
                            .fillna("Sin dato")
                            .value_counts()
                            .to_dict()
                        )
                        predominante = max(dist_sexo, key=dist_sexo.get)
                        st.metric("Género predominante", f"{predominante}")
                    else:
                        st.metric("Distribución por género", "No disponible")

                with col3:
                    # Distribución por régimen
                    if "RegimenAfiliacion" in datos_aseguradora.columns:
                        dist_regimen = (
                            datos_aseguradora["RegimenAfiliacion"]
                            .fillna("Sin dato")
                            .value_counts()
                            .to_dict()
                        )
                        regimen_principal = max(dist_regimen, key=dist_regimen.get)
                        st.metric("Régimen principal", f"{regimen_principal}")
                    else:
                        st.metric("Distribución por régimen", "No disponible")

                with col4:
                    # Número de municipios donde opera
                    municipios_operacion = datos_aseguradora[
                        "NombreMunicipioResidencia"
                    ].nunique()
                    st.metric("Municipios de operación", f"{municipios_operacion}")

                # Gráficos específicos de la aseguradora
                col_left, col_right = st.columns(2)

                with col_left:
                    # Distribución por municipio
                    municipio_counts = (
                        datos_aseguradora["NombreMunicipioResidencia"]
                        .fillna("Sin dato")
                        .value_counts()
                        .reset_index()
                    )
                    municipio_counts.columns = ["Municipio", "Vacunados"]

                    # Top 10 municipios
                    top_municipios_aseg = municipio_counts.head(10)

                    fig_municipios = create_bar_chart(
                        data=top_municipios_aseg,
                        x="Municipio",
                        y="Vacunados",
                        title=f"Distribución territorial - {aseguradora_seleccionada}",
                        color=colors["accent"],
                        height=400,
                    )

                    st.plotly_chart(fig_municipios, use_container_width=True)

                with col_right:
                    # Distribución por grupo de edad (si existe)
                    if "Grupo_Edad" in datos_aseguradora.columns:
                        edad_counts = (
                            datos_aseguradora["Grupo_Edad"]
                            .fillna("Sin dato")
                            .value_counts()
                            .reset_index()
                        )
                        edad_counts.columns = ["Grupo_Edad", "Vacunados"]

                        fig_edad_aseg = create_pie_chart(
                            data=edad_counts,
                            names="Grupo_Edad",
                            values="Vacunados",
                            title=f"Distribución etaria - {aseguradora_seleccionada}",
                            color_map={},
                            height=400,
                        )

                        st.plotly_chart(fig_edad_aseg, use_container_width=True)
                    else:
                        st.info("Datos de grupo de edad no disponibles para esta EAPB")

                # Análisis de cobertura por municipio para esta EAPB
                st.markdown(
                    f"### Cobertura de {aseguradora_seleccionada} por Municipio"
                )

                # Calcular cobertura por municipio para esta EAPB específica
                cobertura_aseg = (
                    datos_aseguradora.groupby("NombreMunicipioResidencia")
                    .size()
                    .reset_index()
                )
                cobertura_aseg.columns = ["Municipio", "Vacunados_EAPB"]

                # Fusionar con datos de población
                cobertura_aseg = pd.merge(
                    cobertura_aseg,
                    filtered_data["metricas"][["DPMP", fuente_poblacion]],
                    left_on="Municipio",
                    right_on="DPMP",
                    how="left",
                )

                # Calcular cobertura de esta EAPB específica
                cobertura_aseg["Cobertura_EAPB"] = (
                    cobertura_aseg["Vacunados_EAPB"]
                    / cobertura_aseg[fuente_poblacion]
                    * 100
                ).round(2)

                # Mostrar top 10 municipios por cobertura de esta EAPB
                top_cobertura_eapb = cobertura_aseg.nlargest(10, "Cobertura_EAPB")

                if len(top_cobertura_eapb) > 0:
                    fig_cob_eapb = create_bar_chart(
                        data=top_cobertura_eapb,
                        x="Municipio",
                        y="Cobertura_EAPB",
                        title=f"Top 10 municipios por cobertura de {aseguradora_seleccionada}",
                        color=colors["warning"],
                        height=400,
                        formatter="%{y:.2f}%",
                    )

                    st.plotly_chart(fig_cob_eapb, use_container_width=True)
                else:
                    st.info(
                        "No hay datos suficientes para mostrar cobertura por municipio"
                    )

    except Exception as e:
        st.error(f"Error en análisis detallado por aseguradora: {str(e)}")

    # =====================================================================
    # SECCIÓN 5: INSIGHTS Y RECOMENDACIONES
    # =====================================================================
    st.markdown("---")
    st.subheader("💡 Insights del Análisis de Aseguramiento")

    try:
        # Calcular algunos insights automáticos
        total_eapb = len(filtered_data["vacunacion"]["NombreAseguradora"].unique())
        eapb_principal = (
            filtered_data["vacunacion"]["NombreAseguradora"].value_counts().index[0]
        )
        participacion_principal = (
            filtered_data["vacunacion"]["NombreAseguradora"].value_counts().iloc[0]
            / len(filtered_data["vacunacion"])
            * 100
        )

        regimen_principal = (
            filtered_data["vacunacion"]["RegimenAfiliacion"].value_counts().index[0]
        )
        participacion_regimen = (
            filtered_data["vacunacion"]["RegimenAfiliacion"].value_counts().iloc[0]
            / len(filtered_data["vacunacion"])
            * 100
        )

        insights_aseguramiento = [
            f"🏥 **{total_eapb} EAPB diferentes** participan en la vacunación",
            f"📊 **{eapb_principal}** es la EAPB con mayor participación ({participacion_principal:.1f}%)",
            f"🎯 **Régimen {regimen_principal}** representa el {participacion_regimen:.1f}% de los vacunados",
        ]

        # Calcular concentración (índice Herfindahl simple)
        participaciones = filtered_data["vacunacion"]["NombreAseguradora"].value_counts(
            normalize=True
        )
        hhi = (participaciones**2).sum()

        if hhi > 0.25:
            insights_aseguramiento.append(
                "⚠️ **Alta concentración** en pocas EAPB - considerar diversificación"
            )
        else:
            insights_aseguramiento.append(
                "✅ **Distribución balanceada** entre diferentes EAPB"
            )

        # Mostrar insights
        for insight in insights_aseguramiento:
            st.markdown(f"- {insight}")

    except Exception as e:
        st.warning(f"No se pudieron calcular todos los insights: {str(e)}")
