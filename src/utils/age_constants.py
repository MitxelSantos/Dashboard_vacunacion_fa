"""
Constantes para rangos de edad estandarizados
Dashboard de Vacunación - Fiebre Amarilla del Tolima
"""

# Rangos de edad estándar para vacunación fiebre amarilla
AGE_RANGES = [
    "Menor de 1 año",
    "1 a 4 años",
    "5 a 9 años",
    "10 a 19 años",
    "20 a 29 años",
    "30 a 39 años",
    "40 a 49 años",
    "50 a 59 años",
    "60 a 69 años",
    "70 años o más",
]

# Orden completo incluyendo "Sin dato"
AGE_RANGES_WITH_MISSING = AGE_RANGES + ["Sin dato"]


def categorize_age(age):
    """
    Función centralizada para categorizar edades

    Args:
        age: Edad numérica

    Returns:
        str: Grupo de edad correspondiente
    """
    try:
        age_num = float(age)
        if pd.isna(age_num):
            return "Sin dato"
        elif age_num < 1:
            return "Menor de 1 año"
        elif age_num < 5:
            return "1 a 4 años"
        elif age_num < 10:
            return "5 a 9 años"
        elif age_num < 20:
            return "10 a 19 años"
        elif age_num < 30:
            return "20 a 29 años"
        elif age_num < 40:
            return "30 a 39 años"
        elif age_num < 50:
            return "40 a 49 años"
        elif age_num < 60:
            return "50 a 59 años"
        elif age_num < 70:
            return "60 a 69 años"
        else:  # 70 años o más
            return "70 años o más"
    except (ValueError, TypeError):
        return "Sin dato"


def get_age_order(include_missing=True):
    """
    Retorna el orden estándar de grupos de edad

    Args:
        include_missing (bool): Si incluir "Sin dato" al final

    Returns:
        list: Lista ordenada de grupos de edad
    """
    return AGE_RANGES_WITH_MISSING if include_missing else AGE_RANGES


def sort_age_groups_dataframe(df, age_column):
    """
    Ordena un DataFrame por grupos de edad en el orden estándar

    Args:
        df (pd.DataFrame): DataFrame con datos
        age_column (str): Nombre de la columna con grupos de edad

    Returns:
        pd.DataFrame: DataFrame ordenado
    """
    import pandas as pd

    # Obtener grupos presentes en los datos
    grupos_presentes = set(df[age_column].unique())
    grupos_orden = [g for g in AGE_RANGES_WITH_MISSING if g in grupos_presentes]

    # Añadir grupos no contemplados al final
    grupos_orden.extend([g for g in grupos_presentes if g not in grupos_orden])

    try:
        # Aplicar orden categórico
        df[age_column] = pd.Categorical(
            df[age_column], categories=grupos_orden, ordered=True
        )
        return df.sort_values(age_column)
    except:
        # Si falla, usar orden alfabético
        return df.sort_values(age_column)


# Mapeo para compatibilidad con rangos anteriores (si es necesario)
OLD_TO_NEW_MAPPING = {
    "0-4": "1 a 4 años",  # Aproximación
    "5-14": "5 a 9 años",  # Aproximación
    "15-19": "10 a 19 años",  # Aproximación
    "20-29": "20 a 29 años",
    "30-39": "30 a 39 años",
    "40-49": "40 a 49 años",
    "50-59": "50 a 59 años",
    "60-69": "60 a 69 años",
    "70-79": "70 años o más",
    "80+": "70 años o más",
}


def migrate_old_age_groups(old_group):
    """
    Migra grupos de edad antiguos al nuevo sistema

    Args:
        old_group (str): Grupo de edad en formato anterior

    Returns:
        str: Grupo de edad en nuevo formato
    """
    return OLD_TO_NEW_MAPPING.get(old_group, old_group)
