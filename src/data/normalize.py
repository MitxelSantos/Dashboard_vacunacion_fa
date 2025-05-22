"""
Funciones para normalizar nombres de municipios y otros datos
para asegurar consistencia en todo el sistema.
Versión mejorada con manejo unificado de valores NaN como "Sin dato"
y normalización de géneros.
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
        df_clean[column_name].astype(str).fillna("Sin dato")
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


def normalize_gender_values(df, column_name):
    """
    Normaliza los valores de género a las tres categorías estándar:
    - Masculino
    - Femenino  
    - No Binario (para todo lo demás)
    - Sin dato (para valores NaN o vacíos)

    Args:
        df (pd.DataFrame): DataFrame con columna de género/sexo
        column_name (str): Nombre de la columna que contiene los valores de género

    Returns:
        pd.DataFrame: DataFrame con valores de género normalizados
    """
    df_clean = df.copy()
    
    def normalize_single_gender(value):
        """Normaliza un valor individual de género"""
        if pd.isna(value) or str(value).lower().strip() in ['nan', '', 'none', 'null', 'na']:
            return "Sin dato"
        
        value_str = str(value).lower().strip()
        
        if value_str in ['masculino', 'm', 'masc', 'hombre', 'h', 'male', '1']:
            return "Masculino"
        elif value_str in ['femenino', 'f', 'fem', 'mujer', 'female', '2']:
            return "Femenino"
        else:
            # Todas las demás clasificaciones van a "No Binario"
            return "No Binario"
    
    # Aplicar la normalización
    df_clean[f"{column_name}_normalized"] = df_clean[column_name].apply(normalize_single_gender)
    
    return df_clean


def normalize_nan_values(df, columns_to_clean=None, replacement="Sin dato"):
    """
    Normaliza todos los valores NaN en las columnas especificadas o en todo el DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame a limpiar
        columns_to_clean (list): Lista de columnas a limpiar. Si es None, limpia todas.
        replacement (str): Valor de reemplazo para NaN
        
    Returns:
        pd.DataFrame: DataFrame con valores NaN normalizados
    """
    df_clean = df.copy()
    
    # Si no se especifican columnas, usar todas las columnas de tipo object/string
    if columns_to_clean is None:
        columns_to_clean = df_clean.select_dtypes(include=['object', 'string']).columns.tolist()
    
    # Normalizar cada columna especificada
    for col in columns_to_clean:
        if col in df_clean.columns:
            # Convertir a string si es categórica
            if pd.api.types.is_categorical_dtype(df_clean[col]):
                df_clean[col] = df_clean[col].astype(str)
            
            # Reemplazar diversos tipos de valores vacíos/nulos
            df_clean[col] = df_clean[col].fillna(replacement)
            df_clean[col] = df_clean[col].replace(
                ["", "nan", "NaN", "null", "NULL", "None", "NONE", "na", "NA"], 
                replacement
            )
            
            # Limpiar espacios en blanco que podrían considerarse como vacíos
            df_clean[col] = df_clean[col].apply(
                lambda x: replacement if str(x).strip() == "" else x
            )
    
    return df_clean


def normalize_age_groups(df, age_column, age_group_column=None):
    """
    Normaliza los grupos de edad basándose en la edad numérica.
    
    Args:
        df (pd.DataFrame): DataFrame con datos de edad
        age_column (str): Nombre de la columna con las edades numéricas
        age_group_column (str): Nombre de la columna donde guardar los grupos (opcional)
        
    Returns:
        pd.DataFrame: DataFrame con grupos de edad normalizados
    """
    df_clean = df.copy()
    
    if age_group_column is None:
        age_group_column = f"{age_column}_group"
    
    def categorize_age(age):
        """Categoriza la edad en grupos estándar"""
        try:
            age_num = float(age)
            if pd.isna(age_num):
                return "Sin dato"
            elif age_num < 5:
                return "0-4"
            elif age_num < 15:
                return "5-14"
            elif age_num < 20:
                return "15-19"
            elif age_num < 30:
                return "20-29"
            elif age_num < 40:
                return "30-39"
            elif age_num < 50:
                return "40-49"
            elif age_num < 60:
                return "50-59"
            elif age_num < 70:
                return "60-69"
            elif age_num < 80:
                return "70-79"
            else:
                return "80+"
        except (ValueError, TypeError):
            return "Sin dato"
    
    # Aplicar la categorización
    df_clean[age_group_column] = df_clean[age_column].apply(categorize_age)
    
    return df_clean


def comprehensive_data_normalization(df):
    """
    Aplica todas las normalizaciones necesarias a un DataFrame de manera integral.
    
    Args:
        df (pd.DataFrame): DataFrame a normalizar
        
    Returns:
        pd.DataFrame: DataFrame completamente normalizado
    """
    df_normalized = df.copy()
    
    # 1. Normalizar valores NaN en columnas categóricas comunes
    categorical_columns = [
        'GrupoEtnico', 'RegimenAfiliacion', 'NombreAseguradora', 
        'NombreMunicipioResidencia', 'NombreDptoResidencia',
        'Desplazado', 'Discapacitado', 'TipoIdentificacion'
    ]
    
    existing_categorical = [col for col in categorical_columns if col in df_normalized.columns]
    if existing_categorical:
        df_normalized = normalize_nan_values(df_normalized, existing_categorical)
    
    # 2. Normalizar géneros si existe la columna
    gender_columns = ['Sexo', 'Genero']
    for gender_col in gender_columns:
        if gender_col in df_normalized.columns:
            df_normalized = normalize_gender_values(df_normalized, gender_col)
            # Reemplazar la columna original con la normalizada
            df_normalized[gender_col] = df_normalized[f"{gender_col}_normalized"]
            df_normalized = df_normalized.drop(f"{gender_col}_normalized", axis=1)
            break
    
    # 3. Normalizar grupos de edad si existe la columna de edad
    if 'Edad_Vacunacion' in df_normalized.columns:
        if 'Grupo_Edad' not in df_normalized.columns:
            df_normalized = normalize_age_groups(df_normalized, 'Edad_Vacunacion', 'Grupo_Edad')
        else:
            # Si ya existe Grupo_Edad pero tiene valores inconsistentes, regenerar
            df_normalized = normalize_age_groups(df_normalized, 'Edad_Vacunacion', 'Grupo_Edad_New')
            # Reemplazar solo si la nueva versión tiene menos "Sin dato"
            if (df_normalized['Grupo_Edad_New'] == 'Sin dato').sum() < (df_normalized['Grupo_Edad'] == 'Sin dato').sum():
                df_normalized['Grupo_Edad'] = df_normalized['Grupo_Edad_New']
            df_normalized = df_normalized.drop('Grupo_Edad_New', axis=1)
    
    # 4. Normalizar nombres de municipios si existe la columna
    if 'NombreMunicipioResidencia' in df_normalized.columns:
        df_normalized = normalize_municipality_names(df_normalized, 'NombreMunicipioResidencia')
    
    return df_normalized


def get_standardized_categories():
    """
    Retorna las categorías estandarizadas para cada tipo de variable demográfica.
    
    Returns:
        dict: Diccionario con las categorías estándar para cada variable
    """
    return {
        'genero': ['Masculino', 'Femenino', 'No Binario', 'Sin dato'],
        'grupos_edad': ['0-4', '5-14', '15-19', '20-29', '30-39', '40-49', 
                       '50-59', '60-69', '70-79', '80+', 'Sin dato'],
        'regimen': ['Contributivo', 'Subsidiado', 'Especial', 'No asegurado', 'Sin dato'],
        'grupo_etnico': ['Mestizo', 'Afrodescendiente', 'Indígena', 'Blanco', 
                        'Gitano', 'Palenquero', 'Raizal', 'Otro', 'Sin dato'],
        'desplazado': ['Sí', 'No', 'Sin dato'],
        'discapacitado': ['Sí', 'No', 'Sin dato']
    }
