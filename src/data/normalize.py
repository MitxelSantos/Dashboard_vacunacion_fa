"""
Funciones para normalizar nombres de municipios y otros datos
para asegurar consistencia en todo el sistema.
"""

import pandas as pd
import unicodedata


def normalize_municipality_names(df, column_name):
    """
    Normaliza los nombres de municipios de manera consistente en todo el sistema.

    Args:
        df (pd.DataFrame): DataFrame con columna de municipios
        column_name (str): Nombre de la columna que contiene los municipios

    Returns:
        pd.DataFrame: DataFrame con nombres normalizados
    """
    # Crear copia para no modificar el original
    df_clean = df.copy()

    # Verificar si la columna original es categórica
    is_categorical = pd.api.types.is_categorical_dtype(df_clean[column_name])

    if is_categorical:
        # Convertir a string para evitar problemas con categorías
        df_clean[column_name] = df_clean[column_name].astype(str)

    # Crear versión normalizada usando astype(str) para garantizar compatibilidad
    df_clean[f"{column_name}_norm"] = (
        df_clean[column_name].astype(str).fillna("Sin especificar")
    )

    # Normalizar quitando acentos y convirtiendo a minúsculas
    df_clean[f"{column_name}_norm"] = df_clean[f"{column_name}_norm"].apply(
        lambda text: unicodedata.normalize("NFKD", str(text))
        .encode("ASCII", "ignore")
        .decode("ASCII")
        .lower()
        .strip()
    )

    # Aplicar mapeo de nombres alternativos
    name_mapping = {
        "san sebastian de mariquita": "mariquita",
        "armero guayabal": "armero",
    }

    # Aplicar mapeo
    for alt_name, std_name in name_mapping.items():
        mask = df_clean[f"{column_name}_norm"] == alt_name
        if mask.any():
            df_clean.loc[mask, f"{column_name}_norm"] = std_name

    return df_clean
