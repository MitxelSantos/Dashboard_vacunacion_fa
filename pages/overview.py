import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from src.visualization.charts import (
    create_bar_chart,
    create_pie_chart,
    create_scatter_plot,
)


def show(data, filters, colors, fuente_poblacion="DANE"):
    """
    Muestra la página de visión general del dashboard.

    Args:
        data (dict): Diccionario con los dataframes
        filters (dict): Filtros seleccionados
        colors (dict): Colores institucionales
        fuente_poblacion (str): Fuente de datos de población ("DANE" o "SISBEN")
    """
    st.title("Visión General")

    # Aplicar filtros a los datos
    from src.data.preprocessor import apply_filters

    filtered_data = apply_filters(data, filters, fuente_poblacion)

    # Verificar que las columnas existan en los dataframes
    if fuente_poblacion not in filtered_data["metricas"].columns:
        st.error(
            f"Columna '{fuente_poblacion}' no encontrada en los datos. Usando 'DANE' como alternativa."
        )
        fuente_poblacion = "DANE"

    if "Vacunados" not in filtered_data["metricas"].columns:
        st.error("Columna 'Vacunados' no encontrada en los datos.")
        # Crear columna de vacunados
        filtered_data["metricas"]["Vacunados"] = 0

    # Resumen de métricas
    st.subheader(
        f"Resumen de Vacunación - Fiebre Amarilla (Población {fuente_poblacion})"
    )

    # Métricas para comparar ambas fuentes
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### Métricas basadas en población {fuente_poblacion}")

        # Calcular métricas seleccionadas
        total_poblacion = filtered_data["metricas"][fuente_poblacion].sum()
        total_vacunados = filtered_data["metricas"]["Vacunados"].sum()
        cobertura = (
            (total_vacunados / total_poblacion * 100) if total_poblacion > 0 else 0
        )
        pendientes = total_poblacion - total_vacunados

        # Mostrar métricas en columnas
        col1_1, col1_2, col1_3, col1_4 = st.columns(4)

        with col1_1:
            st.metric(
                label="Población Total", value=f"{total_poblacion:,}".replace(",", ".")
            )

        with col1_2:
            st.metric(label="Vacunados", value=f"{total_vacunados:,}".replace(",", "."))

        with col1_3:
            st.metric(label="Cobertura", value=f"{cobertura:.2f}%")

        with col1_4:
            st.metric(label="Pendientes", value=f"{pendientes:,}".replace(",", "."))

    with col2:
        # Mostrar comparativa entre DANE y SISBEN
        st.markdown("### Comparativa DANE vs SISBEN")

        # Verificar que ambas columnas existan
        if (
            "DANE" not in filtered_data["metricas"].columns
            or "SISBEN" not in filtered_data["metricas"].columns
        ):
            st.error("Faltan columnas necesarias para la comparativa DANE vs SISBEN")
        else:
            # Preparar datos para la comparativa
            comparativa = {
                "Fuente": ["DANE", "SISBEN"],
                "Población Total": [
                    filtered_data["metricas"]["DANE"].sum(),
                    filtered_data["metricas"]["SISBEN"].sum(),
                ],
                "Cobertura (%)": [
                    (
                        (
                            filtered_data["metricas"]["Vacunados"].sum()
                            / filtered_data["metricas"]["DANE"].sum()
                            * 100
                        )
                        if filtered_data["metricas"]["DANE"].sum() > 0
                        else 0
                    ),
                    (
                        (
                            filtered_data["metricas"]["Vacunados"].sum()
                            / filtered_data["metricas"]["SISBEN"].sum()
                            * 100
                        )
                        if filtered_data["metricas"]["SISBEN"].sum() > 0
                        else 0
                    ),
                ],
            }

            comparativa_df = pd.DataFrame(comparativa)

            # Mostrar la tabla
            st.dataframe(
                comparativa_df.style.format(
                    {"Población Total": "{:,.0f}", "Cobertura (%)": "{:.2f}%"}
                ),
                use_container_width=True,
            )

            # Crear gráfico de barras para comparar coberturas
            fig = create_bar_chart(
                data=comparativa_df,
                x="Fuente",
                y="Cobertura (%)",
                title="Cobertura según fuente de población",
                color=colors["primary"],
                height=250,
            )

            st.plotly_chart(fig, use_container_width=True)

    # Dividir en dos columnas para los gráficos principales
    col_left, col_right = st.columns(2)

    # Gráfico de cobertura por municipio (Top 10)
    with col_left:
        # Determinar qué columna de cobertura usar según la fuente
        cobertura_col = f"Cobertura_{fuente_poblacion}"

        # Verificar que la columna exista
        if cobertura_col not in filtered_data["metricas"].columns:
            st.error(
                f"Columna '{cobertura_col}' no encontrada en los datos. No se puede mostrar gráfico de cobertura por municipio."
            )
        else:
            # Ordenar municipios por cobertura
            top_municipios = (
                filtered_data["metricas"]
                .sort_values(by=cobertura_col, ascending=False)
                .head(10)
            )

            # Crear gráfico
            fig_mun = create_bar_chart(
                data=top_municipios,
                x=cobertura_col,
                y="DPMP",
                title=f"Cobertura por municipio (Top 10) - {fuente_poblacion}",
                color=colors["primary"],
                height=400,
                horizontal=True,
                formatter="%{x:.1f}%",
            )

            st.plotly_chart(fig_mun, use_container_width=True)

    # Gráfico de distribución por grupos de edad
    with col_right:
        # Verificar que Grupo_Edad exista
        if "Grupo_Edad" not in filtered_data["vacunacion"].columns:
            st.error(
                "Columna 'Grupo_Edad' no encontrada en los datos. No se puede mostrar distribución por grupo de edad."
            )
        else:
            # Agrupar por grupo de edad
            edad_counts = (
                filtered_data["vacunacion"]["Grupo_Edad"].value_counts().reset_index()
            )
            edad_counts.columns = ["Grupo_Edad", "Vacunados"]

            # Ordenar por grupos de edad (para mantener el orden correcto)
            try:
                orden_grupos = [
                    "0-4",
                    "5-14",
                    "15-19",
                    "20-29",
                    "30-39",
                    "40-49",
                    "50-59",
                    "60-69",
                    "70-79",
                    "80+",
                ]
                edad_counts["Grupo_Edad"] = pd.Categorical(
                    edad_counts["Grupo_Edad"], categories=orden_grupos, ordered=True
                )
                edad_counts = edad_counts.sort_values("Grupo_Edad")
            except:
                # Si falla la categorización (por ejemplo, si los grupos son diferentes), usar orden alfabético
                edad_counts = edad_counts.sort_values("Grupo_Edad")

            # Crear gráfico
            fig_edad = create_bar_chart(
                data=edad_counts,
                x="Grupo_Edad",
                y="Vacunados",
                title="Distribución por grupos de edad",
                color=colors["secondary"],
                height=400,
            )

            st.plotly_chart(fig_edad, use_container_width=True)

    # Añadir gráfico de dispersión para comparar DANE vs SISBEN
    if (
        "DANE" in filtered_data["metricas"].columns
        and "SISBEN" in filtered_data["metricas"].columns
    ):
        st.subheader("Comparativa DANE vs SISBEN por municipio")

        # Crear gráfico de dispersión
        fig_scatter = create_scatter_plot(
            data=filtered_data["metricas"],
            x="DANE",
            y="SISBEN",
            title="Relación entre población DANE y SISBEN por municipio",
            color=colors["accent"],
            hover_data=["DPMP", "Vacunados", "Cobertura_DANE", "Cobertura_SISBEN"],
            height=500,
        )

        st.plotly_chart(fig_scatter, use_container_width=True)

        st.markdown(
            """
        **Interpretación:** Los puntos por encima de la línea diagonal indican municipios donde la población SISBEN 
        es mayor que la reportada por el DANE. Los puntos por debajo indican lo contrario.
        """
        )

    # División en 3 columnas para gráficos de pastel
    st.subheader("Distribución demográfica de vacunados")
    col1, col2, col3 = st.columns(3)

    # Gráfico de distribución por sexo
    with col1:
        if "Sexo" in filtered_data["vacunacion"].columns:
            # Agrupar por sexo
            sexo_counts = (
                filtered_data["vacunacion"]["Sexo"].value_counts().reset_index()
            )
            sexo_counts.columns = ["Sexo", "Vacunados"]

            # Mapa de colores para sexo
            color_map_sexo = {
                "Masculino": colors["primary"],
                "Femenino": colors["secondary"],
                "MASCULINO": colors["primary"],
                "FEMENINO": colors["secondary"],
                "masculino": colors["primary"],
                "femenino": colors["secondary"],
            }

            # Crear gráfico
            fig_sexo = create_pie_chart(
                data=sexo_counts,
                names="Sexo",
                values="Vacunados",
                title="Distribución por sexo",
                color_map=color_map_sexo,
                height=350,
            )

            st.plotly_chart(fig_sexo, use_container_width=True)
        else:
            st.error("Columna 'Sexo' no encontrada en los datos.")

    # Gráfico de distribución por etnia
    with col2:
        if "GrupoEtnico" in filtered_data["vacunacion"].columns:
            # Agrupar por grupo étnico
            etnia_counts = (
                filtered_data["vacunacion"]["GrupoEtnico"].value_counts().reset_index()
            )
            etnia_counts.columns = ["GrupoEtnico", "Vacunados"]

            # Crear gráfico
            fig_etnia = create_pie_chart(
                data=etnia_counts,
                names="GrupoEtnico",
                values="Vacunados",
                title="Distribución por grupo étnico",
                color_map={},  # Colores automáticos
                height=350,
            )

            st.plotly_chart(fig_etnia, use_container_width=True)
        else:
            st.error("Columna 'GrupoEtnico' no encontrada en los datos.")

    # Gráfico de distribución por régimen
    with col3:
        if "RegimenAfiliacion" in filtered_data["vacunacion"].columns:
            # Agrupar por régimen
            regimen_counts = (
                filtered_data["vacunacion"]["RegimenAfiliacion"]
                .value_counts()
                .reset_index()
            )
            regimen_counts.columns = ["RegimenAfiliacion", "Vacunados"]

            # Crear gráfico
            fig_regimen = create_pie_chart(
                data=regimen_counts,
                names="RegimenAfiliacion",
                values="Vacunados",
                title="Distribución por régimen",
                color_map={},  # Colores automáticos
                height=350,
            )

            st.plotly_chart(fig_regimen, use_container_width=True)
        else:
            st.error("Columna 'RegimenAfiliacion' no encontrada en los datos.")
