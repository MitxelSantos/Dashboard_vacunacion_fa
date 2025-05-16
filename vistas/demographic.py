import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from src.visualization.charts import create_bar_chart, create_pie_chart


def show(data, filters, colors, fuente_poblacion="DANE"):
    """
    Muestra la página de perfil demográfico del dashboard.

    Args:
        data (dict): Diccionario con los dataframes
        filters (dict): Filtros seleccionados
        colors (dict): Colores institucionales
        fuente_poblacion (str): Fuente de datos de población ("DANE" o "SISBEN")
    """
    st.title("Perfil Demográfico")

    # Aplicar filtros a los datos
    from src.data.preprocessor import apply_filters

    filtered_data = apply_filters(data, filters, fuente_poblacion)

    # Determinar qué columna de cobertura usar según la fuente
    cobertura_col = f"Cobertura_{fuente_poblacion}"

    # Dividir en dos columnas
    col1, col2 = st.columns(2)

    # Gráfico de cobertura por grupos de edad
    with col1:
        # Verificar que Grupo_Edad exista
        if "Grupo_Edad" not in filtered_data["vacunacion"].columns:
            st.error("Columna 'Grupo_Edad' no encontrada en los datos.")
        else:
            # Agrupar por grupo de edad
            try:
                # Verificar si hay datos de edad
                if len(filtered_data["vacunacion"]) > 0:
                    # Asegurarse de que los datos estén en formato string y sin espacios
                    filtered_data["vacunacion"]["Grupo_Edad"] = filtered_data[
                        "vacunacion"
                    ]["Grupo_Edad"].astype(str)
                    filtered_data["vacunacion"]["Grupo_Edad"] = filtered_data[
                        "vacunacion"
                    ]["Grupo_Edad"].str.strip()
                    filtered_data["vacunacion"]["Grupo_Edad"] = filtered_data[
                        "vacunacion"
                    ]["Grupo_Edad"].replace("nan", "Sin especificar")

                    # Normalizar los valores de Grupo_Edad
                    filtered_data["vacunacion"]["Grupo_Edad"] = filtered_data[
                        "vacunacion"
                    ]["Grupo_Edad"].fillna("Sin especificar")

                    # Agrupar por grupo de edad
                    edad_counts = (
                        filtered_data["vacunacion"]["Grupo_Edad"]
                        .value_counts()
                        .reset_index()
                    )
                    edad_counts.columns = ["Grupo_Edad", "Vacunados"]

                    # Definir orden de los grupos de edad
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

                    # Verificar si todos los grupos están presentes
                    grupos_presentes = set(edad_counts["Grupo_Edad"])
                    grupos_orden = [g for g in orden_grupos if g in grupos_presentes]

                    # Si hay grupos en el orden predefinido, usarlos
                    if grupos_orden:
                        edad_counts["Grupo_Edad"] = pd.Categorical(
                            edad_counts["Grupo_Edad"],
                            categories=grupos_orden
                            + [g for g in grupos_presentes if g not in grupos_orden],
                            ordered=True,
                        )
                        edad_counts = edad_counts.sort_values("Grupo_Edad")

                    # Crear gráfico
                    fig_edad = create_bar_chart(
                        data=edad_counts,
                        x="Grupo_Edad",
                        y="Vacunados",
                        title="Distribución por grupos de edad",
                        color=colors["primary"],
                        height=400,
                    )

                    st.plotly_chart(fig_edad, use_container_width=True)
                else:
                    st.info(
                        "No hay datos disponibles para mostrar la distribución por grupos de edad."
                    )
            except Exception as e:
                st.error(
                    f"Error al crear gráfico de distribución por grupos de edad: {str(e)}"
                )

    # Gráfico de distribución por género (antes sexo)
    with col2:
        # Verificar si existe Genero o usar Sexo como fallback
        if "Genero" in filtered_data["vacunacion"].columns:
            genero_col = "Genero"
        elif "Sexo" in filtered_data["vacunacion"].columns:
            genero_col = "Sexo"
            # Normalizar los valores de sexo a las categorías de género
            filtered_data["vacunacion"]["Genero_Normalizado"] = filtered_data[
                "vacunacion"
            ][genero_col].apply(
                lambda x: (
                    "MASCULINO"
                    if str(x).lower()
                    in ["masculino", "m", "masc", "hombre", "h", "male"]
                    else (
                        "FEMENINO"
                        if str(x).lower() in ["femenino", "f", "fem", "mujer", "female"]
                        else (
                            "NO BINARIO"
                            if str(x).lower()
                            in ["no binario", "nb", "otro", "other", "non-binary"]
                            else "Sin especificar"
                        )
                    )
                )
            )
            genero_col = "Genero_Normalizado"
        else:
            st.error("No se encontró columna de Género o Sexo en los datos.")
            genero_col = None

        if genero_col:
            try:
                # Asegurarse de que no hay valores nulos
                filtered_data["vacunacion"][genero_col] = filtered_data["vacunacion"][
                    genero_col
                ].fillna("Sin especificar")

                # Agrupar por género
                genero_counts = (
                    filtered_data["vacunacion"][genero_col].value_counts().reset_index()
                )
                genero_counts.columns = ["Genero", "Vacunados"]

                # Crear gráfico
                fig_genero = create_pie_chart(
                    data=genero_counts,
                    names="Genero",
                    values="Vacunados",
                    title="Distribución por género",
                    color_map={},
                    height=400,
                )

                st.plotly_chart(fig_genero, use_container_width=True)
            except Exception as e:
                st.error(f"Error al crear gráfico de distribución por género: {str(e)}")

    # Gráfico de distribución por grupo étnico
    st.subheader("Distribución por grupo étnico")

    # Verificar que GrupoEtnico exista
    if "GrupoEtnico" not in filtered_data["vacunacion"].columns:
        st.error("Columna 'GrupoEtnico' no encontrada en los datos.")
    else:
        try:
            # Normalizar los valores de GrupoEtnico
            filtered_data["vacunacion"]["GrupoEtnico"] = filtered_data["vacunacion"][
                "GrupoEtnico"
            ].fillna("Sin especificar")

            # Agrupar por grupo étnico
            etnia_counts = (
                filtered_data["vacunacion"]["GrupoEtnico"].value_counts().reset_index()
            )
            etnia_counts.columns = ["GrupoEtnico", "Vacunados"]

            # Crear gráfico
            fig_etnia = create_bar_chart(
                data=etnia_counts,
                x="GrupoEtnico",
                y="Vacunados",
                title="Distribución por grupo étnico",
                color=colors["accent"],
                height=400,
            )

            st.plotly_chart(fig_etnia, use_container_width=True)
        except Exception as e:
            st.error(
                f"Error al crear gráfico de distribución por grupo étnico: {str(e)}"
            )

    # Análisis de factores de vulnerabilidad
    st.subheader("Factores de vulnerabilidad")

    col1, col2 = st.columns(2)

    # Gráfico de desplazados
    with col1:
        if "Desplazado" in filtered_data["vacunacion"].columns:
            try:
                # Normalizar los valores de Desplazado
                filtered_data["vacunacion"]["Desplazado"] = filtered_data["vacunacion"][
                    "Desplazado"
                ].fillna("No")

                # Convertir valores booleanos a texto si es necesario
                if filtered_data["vacunacion"]["Desplazado"].dtype == bool:
                    filtered_data["vacunacion"]["Desplazado"] = filtered_data[
                        "vacunacion"
                    ]["Desplazado"].map({True: "Sí", False: "No"})

                # Agrupar por Desplazado
                desplazado_counts = (
                    filtered_data["vacunacion"]["Desplazado"]
                    .value_counts()
                    .reset_index()
                )
                desplazado_counts.columns = ["Desplazado", "Vacunados"]

                # Crear gráfico
                fig_desplazado = create_pie_chart(
                    data=desplazado_counts,
                    names="Desplazado",
                    values="Vacunados",
                    title="Distribución por condición de desplazamiento",
                    color_map={},
                    height=350,
                )

                st.plotly_chart(fig_desplazado, use_container_width=True)
            except Exception as e:
                st.error(
                    f"Error al crear gráfico de distribución por condición de desplazamiento: {str(e)}"
                )
        else:
            st.info("No se encontraron datos sobre condición de desplazamiento")

    # Gráfico de discapacitados
    with col2:
        if "Discapacitado" in filtered_data["vacunacion"].columns:
            try:
                # Normalizar los valores de Discapacitado
                filtered_data["vacunacion"]["Discapacitado"] = filtered_data[
                    "vacunacion"
                ]["Discapacitado"].fillna("No")

                # Convertir valores booleanos a texto si es necesario
                if filtered_data["vacunacion"]["Discapacitado"].dtype == bool:
                    filtered_data["vacunacion"]["Discapacitado"] = filtered_data[
                        "vacunacion"
                    ]["Discapacitado"].map({True: "Sí", False: "No"})

                # Agrupar por Discapacitado
                discapacitado_counts = (
                    filtered_data["vacunacion"]["Discapacitado"]
                    .value_counts()
                    .reset_index()
                )
                discapacitado_counts.columns = ["Discapacitado", "Vacunados"]

                # Crear gráfico
                fig_discapacitado = create_pie_chart(
                    data=discapacitado_counts,
                    names="Discapacitado",
                    values="Vacunados",
                    title="Distribución por condición de discapacidad",
                    color_map={},
                    height=350,
                )

                st.plotly_chart(fig_discapacitado, use_container_width=True)
            except Exception as e:
                st.error(
                    f"Error al crear gráfico de distribución por condición de discapacidad: {str(e)}"
                )
        else:
            st.info("No se encontraron datos sobre condición de discapacidad")

    # Tabla de datos demográficos
    st.subheader("Datos demográficos detallados")

    # Verificar que exista la columna de grupo de edad
    if "Grupo_Edad" in filtered_data["vacunacion"].columns:
        # Verificar si existe Genero o usar Sexo como fallback
        if "Genero" in filtered_data["vacunacion"].columns:
            demo_genero_col = "Genero"
        elif "Sexo" in filtered_data["vacunacion"].columns:
            demo_genero_col = "Sexo"
        else:
            demo_genero_col = None

        # Agrupar por grupo de edad y género/sexo
        if demo_genero_col and st.checkbox(
            "Mostrar tabla cruzada por grupo de edad y género"
        ):
            try:
                # Normalizar los valores
                filtered_data["vacunacion"]["Grupo_Edad"] = filtered_data["vacunacion"][
                    "Grupo_Edad"
                ].fillna("Sin especificar")
                filtered_data["vacunacion"][demo_genero_col] = filtered_data[
                    "vacunacion"
                ][demo_genero_col].fillna("Sin especificar")

                # Crear tabla cruzada
                tabla_cruzada = pd.crosstab(
                    filtered_data["vacunacion"]["Grupo_Edad"],
                    filtered_data["vacunacion"][demo_genero_col],
                    margins=True,
                    margins_name="Total",
                )

                # Definir orden de los grupos de edad
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

                # Ordenar por grupos de edad si todos están presentes
                if all(grupo in tabla_cruzada.index for grupo in orden_grupos):
                    tabla_cruzada = tabla_cruzada.reindex(orden_grupos + ["Total"])

                st.dataframe(tabla_cruzada, use_container_width=True)
            except Exception as e:
                st.error(f"Error al crear tabla cruzada: {str(e)}")
    else:
        st.error("Columna 'Grupo_Edad' no encontrada en los datos.")
