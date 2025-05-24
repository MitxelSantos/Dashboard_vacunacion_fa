"""
Normalizador de nombres de EAPB/Aseguradoras
VERSIÓN MEJORADA con nuevos mapeos del usuario
Desarrollado para el Dashboard de Vacunación - Fiebre Amarilla del Tolima
"""

import pandas as pd
import numpy as np
import streamlit as st


def normalize_eapb_names(
    df, column_name="NombreAseguradora", mapping=None, create_backup=True
):
    """
    Normaliza nombres de EAPB usando un mapeo definido

    Args:
        df: DataFrame con los datos
        column_name: Nombre de la columna con EAPB
        mapping: Diccionario de mapeo {nombre_original: nombre_canónico}
        create_backup: Si crear una columna de respaldo con los nombres originales

    Returns:
        DataFrame con columna normalizada
    """
    if mapping is None:
        try:
            from .eapb_mappings import ALL_EAPB_MAPPINGS

            mapping = ALL_EAPB_MAPPINGS
        except ImportError:
            return df

    df_clean = df.copy()

    # Verificar que la columna existe
    if column_name not in df_clean.columns:
        return df_clean

    # Crear respaldo si se solicita
    if create_backup and f"{column_name}_original" not in df_clean.columns:
        df_clean[f"{column_name}_original"] = df_clean[column_name].copy()

    # Normalizar valores NaN primero
    df_clean[column_name] = df_clean[column_name].fillna("Sin dato")

    # Contador de cambios
    cambios_realizados = 0
    registros_afectados = 0

    # Aplicar mapeo
    for nombre_original, nombre_canonico in mapping.items():
        # Contar registros que serán afectados
        mask = df_clean[column_name] == nombre_original
        num_registros = mask.sum()

        if num_registros > 0:
            df_clean.loc[mask, column_name] = nombre_canonico
            cambios_realizados += 1
            registros_afectados += num_registros

    return df_clean


def apply_eapb_normalization_to_data(data):
    """
    Aplica normalización de EAPB a los datos del dashboard

    Args:
        data: Diccionario con los dataframes del dashboard

    Returns:
        Diccionario con datos normalizados
    """
    if "vacunacion" not in data:
        return data

    df = data["vacunacion"].copy()

    if "NombreAseguradora" not in df.columns:
        return data

    try:
        # Aplicar normalización
        df_normalized = normalize_eapb_names(df, "NombreAseguradora")

        # Actualizar los datos
        data["vacunacion"] = df_normalized

        return data

    except Exception as e:
        return data


def get_normalization_report(df, column_name="NombreAseguradora"):
    """
    Genera un reporte de la normalización aplicada
    VERSIÓN MEJORADA: Con más detalles estadísticos

    Args:
        df: DataFrame con datos normalizados
        column_name: Nombre de la columna de EAPB

    Returns:
        Diccionario con estadísticas del reporte
    """
    backup_column = f"{column_name}_original"

    if backup_column not in df.columns:
        return {"error": "No se encontró columna de respaldo para generar reporte"}

    # Comparar valores originales vs normalizados
    changes = df[df[column_name] != df[backup_column]]

    if len(changes) == 0:
        return {"message": "No se realizaron cambios en la normalización"}

    # Estadísticas de cambios
    changes_summary = changes.groupby([backup_column, column_name]).size().reset_index()
    changes_summary.columns = ["Original", "Normalizado", "Registros"]
    changes_summary = changes_summary.sort_values("Registros", ascending=False)

    # Calcular concentración antes y después
    original_concentration = (
        df[backup_column].value_counts().head(5).sum() / len(df) * 100
    )
    normalized_concentration = (
        df[column_name].value_counts().head(5).sum() / len(df) * 100
    )

    report = {
        "total_changes": len(changes),
        "unique_mappings": len(changes_summary),
        "changes_detail": changes_summary.to_dict("records"),
        "original_unique": df[backup_column].nunique(),
        "normalized_unique": df[column_name].nunique(),
        "reduction_percentage": (
            (df[backup_column].nunique() - df[column_name].nunique())
            / df[backup_column].nunique()
            * 100
        ),
        "original_concentration": original_concentration,
        "normalized_concentration": normalized_concentration,
        "top_normalized": df[column_name].value_counts().head(10).to_dict(),
    }

    return report


def validate_eapb_mapping():
    """
    Valida que los mapeos de EAPB sean consistentes
    """
    try:
        from .eapb_mappings import ALL_EAPB_MAPPINGS, get_eapb_stats

        # Verificar específicamente los nuevos mapeos del usuario
        nuevos_mapeos_usuario = {
            "COMFENALCO VALLE E.P.S.-CM": "COMFENALCO VALLE EPS",
            "COOSALUD EPS S.A.Contributivo": "COOSALUD ESS EPS-S",
            "Colmédica": "Colmédica medicina prepagada",
            "EPS SURA": "Salud Sura",
            "EPS Y MEDICINA PREPAGADA SURAMERICANA S.A-CM": "Salud Sura",
            "SANITAS S.A. E.P.S.-CM": "SANITAS EPS",
            "SAVIA SALUD E.P.S.": "SAVIA SALUD EPS Subsidiado",
            "Salud Coomeva": "COOMEVA EPS SA",
        }

        # Validación silenciosa
        nuevos_encontrados = 0
        for original, esperado in nuevos_mapeos_usuario.items():
            if original in ALL_EAPB_MAPPINGS:
                actual = ALL_EAPB_MAPPINGS[original]
                if actual == esperado:
                    nuevos_encontrados += 1

        # Validar que no hay mapeos circulares
        circular_mappings = []
        for original, canonical in ALL_EAPB_MAPPINGS.items():
            if canonical in ALL_EAPB_MAPPINGS:
                circular_mappings.append(
                    (original, canonical, ALL_EAPB_MAPPINGS[canonical])
                )

        return len(circular_mappings) == 0 and nuevos_encontrados == len(
            nuevos_mapeos_usuario
        )

    except ImportError:
        return False
    except Exception as e:
        return False


def create_eapb_mapping_summary(df, column_name="NombreAseguradora"):
    """
    Crea un resumen visual de los mapeos aplicados para Streamlit

    Args:
        df: DataFrame con datos normalizados
        column_name: Nombre de la columna de EAPB

    Returns:
        DataFrame resumen para mostrar en Streamlit
    """
    backup_column = f"{column_name}_original"

    if backup_column not in df.columns:
        return pd.DataFrame({"Error": ["No hay columna de respaldo disponible"]})

    # Crear resumen de mapeos
    mapeo_summary = (
        df[df[column_name] != df[backup_column]]
        .groupby([backup_column, column_name])
        .size()
        .reset_index()
    )
    mapeo_summary.columns = ["EAPB_Original", "EAPB_Normalizada", "Registros_Afectados"]
    mapeo_summary = mapeo_summary.sort_values("Registros_Afectados", ascending=False)

    # Añadir porcentajes
    total_records = len(df)
    mapeo_summary["Porcentaje"] = (
        mapeo_summary["Registros_Afectados"] / total_records * 100
    ).round(2)

    return mapeo_summary


if __name__ == "__main__":
    # Ejecutar validaciones silenciosamente
    validate_eapb_mapping()
