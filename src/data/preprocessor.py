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
    # Importar la función de normalización
    from src.data.normalize import normalize_municipality_names

    # Crear copias para no modificar los originales
    filtered_data = {
        "municipios": data["municipios"].copy(),
        "vacunacion": data["vacunacion"].copy(),
        "metricas": data["metricas"].copy(),
    }

    # Filtrar vacunación
    vacunacion_df = filtered_data["vacunacion"]

    # Aplicar cada filtro en secuencia
    # Primero manejar el filtro de municipio (caso especial)
    if (
        filters["municipio"] != "Todos"
        and "NombreMunicipioResidencia" in vacunacion_df.columns
    ):
        # Mapeo de nombres alternativos para filtrado
        municipality_map = {
            "Mariquita": [
                "San Sebastian De Mariquita",
                "San Sebastián De Mariquita",
                "San Sebastian de Mariquita",
                "San Sebastián de Mariquita",
            ],
            "Armero": ["Armero Guayabal", "ARMERO GUAYABAL"],
        }

        # Verificar si el municipio seleccionado tiene nombres alternativos
        alt_names = municipality_map.get(filters["municipio"], [])

        if alt_names:
            # Crear máscara para incluir tanto el nombre normal como los alternativos
            mask = (
                vacunacion_df["NombreMunicipioResidencia"].str.lower()
                == filters["municipio"].lower()
            )
            for alt in alt_names:
                mask = mask | (
                    vacunacion_df["NombreMunicipioResidencia"].str.lower()
                    == alt.lower()
                )

            # Aplicar filtro con la máscara expandida
            vacunacion_df = vacunacion_df[mask]
        else:
            # Filtro normal para otros municipios
            vacunacion_df = vacunacion_df[
                vacunacion_df["NombreMunicipioResidencia"].str.lower()
                == filters["municipio"].lower()
            ]

    # Aplicar el resto de los filtros
    # Normalizar columnas para filtros
    column_mapping = {
        "grupo_edad": "Grupo_Edad",
        "sexo": "Sexo",
        "grupo_etnico": "GrupoEtnico",
        "regimen": "RegimenAfiliacion",
        "aseguradora": "NombreAseguradora",
    }

    # Aplicar cada filtro solo si la columna existe
    for filter_key, column_name in column_mapping.items():
        if column_name in vacunacion_df.columns and filters[filter_key] != "Todos":
            # Normalizar los valores para comparación insensible a mayúsculas/minúsculas
            vacunacion_df[f"{column_name}_lower"] = (
                vacunacion_df[column_name].fillna("Sin especificar").str.lower()
            )
            filter_value_lower = filters[filter_key].lower()

            # Filtrar usando la versión normalizada
            vacunacion_df = vacunacion_df[
                vacunacion_df[f"{column_name}_lower"] == filter_value_lower
            ]

            # Eliminar columna temporal
            vacunacion_df = vacunacion_df.drop(f"{column_name}_lower", axis=1)

    # Actualizar el dataframe de vacunación filtrado
    filtered_data["vacunacion"] = vacunacion_df

    # Recalcular métricas para datos filtrados
    if "NombreMunicipioResidencia" in vacunacion_df.columns:
        # Usar nombres normalizados
        vacunacion_df_clean = normalize_municipality_names(
            vacunacion_df, "NombreMunicipioResidencia"
        )

        # Normalizar nombres en metricas
        metricas_df = normalize_municipality_names(filtered_data["metricas"], "DPMP")

        # Contar vacunados por municipio (versión normalizada)
        vacunados_por_municipio = (
            vacunacion_df_clean.groupby("NombreMunicipioResidencia_norm")
            .size()
            .reset_index()
        )
        vacunados_por_municipio.columns = ["Municipio_norm", "Vacunados"]

        # Fusionar por nombre normalizado
        metricas_df = pd.merge(
            metricas_df,
            vacunados_por_municipio,
            left_on="DPMP_norm",
            right_on="Municipio_norm",
            how="left",
        )

        # Eliminar columnas auxiliares
        metricas_df = metricas_df.drop(
            ["DPMP_norm", "Municipio_norm"], axis=1, errors="ignore"
        )

        # Si ya hay una columna Vacunados, actualizar en lugar de duplicar
        if "Vacunados_y" in metricas_df.columns:
            metricas_df["Vacunados"] = metricas_df["Vacunados_y"]
            metricas_df = metricas_df.drop("Vacunados_y", axis=1)

        # Si la fusión falló y no hay vacunados, preservar los valores originales
        if "Vacunados" not in metricas_df.columns:
            if "Vacunados" in filtered_data["metricas"].columns:
                metricas_df["Vacunados"] = filtered_data["metricas"]["Vacunados"]
            else:
                metricas_df["Vacunados"] = 0

        # Rellenar valores NaN
        metricas_df["Vacunados"] = metricas_df["Vacunados"].fillna(0)

        # Recalcular métricas
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
