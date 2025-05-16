import pandas as pd
import numpy as np


def apply_filters(data, filters, fuente_poblacion="DANE"):
    """
    Aplica los filtros seleccionados a los datos.

    Args:
        data (dict): Diccionario con los dataframes
        filters (dict): Filtros seleccionados
        fuente_poblacion (str): Fuente de datos de población ("DANE" o "SISBEN")

    Returns:
        dict: Diccionario con los dataframes filtrados
    """
    # Crear copias para no modificar los originales
    filtered_data = {
        "municipios": data["municipios"].copy(),
        "vacunacion": data["vacunacion"].copy(),
        "metricas": data["metricas"].copy(),
    }

    # Filtrar vacunación
    vacunacion_df = filtered_data["vacunacion"]

    # Aplicar filtro de municipio
    if filters["municipio"] != "Todos":
        vacunacion_df = vacunacion_df[
            vacunacion_df["NombreMunicipioResidencia"] == filters["municipio"]
        ]

    # Aplicar filtro de grupo de edad
    if filters["grupo_edad"] != "Todos":
        vacunacion_df = vacunacion_df[
            vacunacion_df["Grupo_Edad"] == filters["grupo_edad"]
        ]

    # Aplicar filtro de sexo
    if filters["sexo"] != "Todos":
        vacunacion_df = vacunacion_df[vacunacion_df["Sexo"] == filters["sexo"]]

    # Aplicar filtro de grupo étnico
    if filters["grupo_etnico"] != "Todos":
        vacunacion_df = vacunacion_df[
            vacunacion_df["GrupoEtnico"] == filters["grupo_etnico"]
        ]

    # Aplicar filtro de régimen
    if filters["regimen"] != "Todos":
        vacunacion_df = vacunacion_df[
            vacunacion_df["RegimenAfiliacion"] == filters["regimen"]
        ]

    # Aplicar filtro de aseguradora
    if filters["aseguradora"] != "Todos":
        vacunacion_df = vacunacion_df[
            vacunacion_df["NombreAseguradora"] == filters["aseguradora"]
        ]

    # Actualizar el dataframe de vacunación filtrado
    filtered_data["vacunacion"] = vacunacion_df

    # Recalcular métricas si se aplicaron filtros
    if any(v != "Todos" for v in filters.values()):
        # Contar vacunados por municipio después de aplicar filtros
        vacunados_por_municipio = (
            vacunacion_df["NombreMunicipioResidencia"].value_counts().reset_index()
        )
        vacunados_por_municipio.columns = ["Municipio", "Vacunados"]

        # Fusionar con datos de municipios
        metricas_df = pd.merge(
            filtered_data["municipios"],
            vacunados_por_municipio,
            left_on="DPMP",
            right_on="Municipio",
            how="left",
        )

        # Rellenar valores NaN
        metricas_df["Vacunados"] = metricas_df["Vacunados"].fillna(0)

        # Recalcular cobertura y pendientes para ambas fuentes
        metricas_df["Cobertura_DANE"] = (
            metricas_df["Vacunados"] / metricas_df["DANE"] * 100
        ).round(2)
        metricas_df["Pendientes_DANE"] = metricas_df["DANE"] - metricas_df["Vacunados"]

        metricas_df["Cobertura_SISBEN"] = (
            metricas_df["Vacunados"] / metricas_df["SISBEN"] * 100
        ).round(2)
        metricas_df["Pendientes_SISBEN"] = (
            metricas_df["SISBEN"] - metricas_df["Vacunados"]
        )

        # Actualizar el dataframe de métricas
        filtered_data["metricas"] = metricas_df

    return filtered_data
