import pandas as pd
import numpy as np


def normalize_gender_values(value):
    """
    Normaliza los valores de género de manera comprehensiva
    """
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


def normalize_categorical_values(df, columns_to_normalize=None):
    """
    Normaliza valores categóricos reemplazando NaN y valores vacíos con "Sin dato"
    """
    df_clean = df.copy()
    
    if columns_to_normalize is None:
        # Definir columnas categóricas por defecto
        columns_to_normalize = [
            'GrupoEtnico', 'RegimenAfiliacion', 'NombreAseguradora', 
            'NombreMunicipioResidencia', 'NombreDptoResidencia',
            'Desplazado', 'Discapacitado', 'TipoIdentificacion', 'Grupo_Edad'
        ]
    
    # Filtrar solo las columnas que existen en el DataFrame
    existing_columns = [col for col in columns_to_normalize if col in df_clean.columns]
    
    for col in existing_columns:
        # Convertir a string si es categórica
        if pd.api.types.is_categorical_dtype(df_clean[col]):
            df_clean[col] = df_clean[col].astype(str)
        
        # Reemplazar diversos tipos de valores vacíos/nulos
        df_clean[col] = df_clean[col].fillna("Sin dato")
        df_clean[col] = df_clean[col].replace(
            ["", "nan", "NaN", "null", "NULL", "None", "NONE", "na", "NA", "#N/A", "N/A"], 
            "Sin dato"
        )
        
        # Limpiar espacios en blanco que podrían considerarse como vacíos
        df_clean[col] = df_clean[col].apply(
            lambda x: "Sin dato" if str(x).strip() == "" else str(x).strip()
        )
    
    return df_clean


def normalize_boolean_values(df, boolean_columns=None):
    """
    Normaliza valores booleanos a formato estándar Sí/No/Sin dato
    """
    df_clean = df.copy()
    
    if boolean_columns is None:
        boolean_columns = ['Desplazado', 'Discapacitado']
    
    # Filtrar solo las columnas que existen
    existing_boolean_columns = [col for col in boolean_columns if col in df_clean.columns]
    
    def normalize_boolean(value):
        if pd.isna(value) or str(value).lower().strip() in ['nan', '', 'none', 'null', 'na', 'sin dato']:
            return "Sin dato"
        
        value_str = str(value).lower().strip()
        if value_str in ['true', '1', 'si', 'sí', 'yes', 'y']:
            return "Sí"
        elif value_str in ['false', '0', 'no', 'n']:
            return "No"
        else:
            return "Sin dato"
    
    for col in existing_boolean_columns:
        df_clean[col] = df_clean[col].apply(normalize_boolean)
    
    return df_clean


def apply_filters(data, filters, fuente_poblacion="DANE"):
    """
    Aplica los filtros seleccionados a los datos.
    VERSIÓN MEJORADA: Incluye normalización comprehensiva de datos antes del filtrado.

    Args:
        data (dict): Diccionario con los dataframes
        filters (dict): Filtros seleccionados
        fuente_poblacion (str): Fuente de datos de población ("DANE" o "SISBEN")

    Returns:
        dict: Diccionario con los dataframes filtrados y normalizados
    """
    # Importar la función de normalización
    from src.data.normalize import normalize_municipality_names

    # Crear copias para no modificar los originales
    filtered_data = {
        "municipios": data["municipios"].copy(),
        "vacunacion": data["vacunacion"].copy(),
        "metricas": data["metricas"].copy(),
    }

    # =====================================================================
    # PASO 1: NORMALIZACIÓN COMPREHENSIVA DE DATOS
    # =====================================================================
    
    # Normalizar datos de vacunación antes del filtrado
    vacunacion_df = filtered_data["vacunacion"]

    # Convertir columnas categóricas a strings para evitar errores
    for col in vacunacion_df.columns:
        if pd.api.types.is_categorical_dtype(vacunacion_df[col]):
            vacunacion_df[col] = vacunacion_df[col].astype(str)

    # Aplicar normalización de valores categóricos
    vacunacion_df = normalize_categorical_values(vacunacion_df)
    
    # Aplicar normalización de valores booleanos
    vacunacion_df = normalize_boolean_values(vacunacion_df)
    
    # Normalizar géneros específicamente
    gender_columns = ['Sexo', 'Genero']
    for col in gender_columns:
        if col in vacunacion_df.columns:
            vacunacion_df[col] = vacunacion_df[col].apply(normalize_gender_values)

    # =====================================================================
    # PASO 2: APLICACIÓN DE FILTROS
    # =====================================================================
    
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

    # Mapeo mejorado de filtros con manejo de géneros normalizados
    column_mapping = {
        "grupo_edad": "Grupo_Edad",
        "sexo": "Genero" if "Genero" in vacunacion_df.columns else "Sexo",
        "grupo_etnico": "GrupoEtnico",
        "regimen": "RegimenAfiliacion",
        "aseguradora": "NombreAseguradora",
    }

    # Aplicar cada filtro solo si la columna existe
    for filter_key, column_name in column_mapping.items():
        if column_name in vacunacion_df.columns and filters[filter_key] != "Todos":
            
            # Caso especial para género: normalizar el valor del filtro también
            if filter_key == "sexo":
                filter_value_normalized = normalize_gender_values(filters[filter_key])
                # Filtrar usando el valor normalizado
                vacunacion_df = vacunacion_df[
                    vacunacion_df[column_name] == filter_value_normalized
                ]
            else:
                # Para otros filtros, usar comparación insensible a mayúsculas/minúsculas
                # pero considerando que ya hemos normalizado los datos
                
                # Crear versión temporal para comparación
                vacunacion_df.loc[:, f"{column_name}_lower"] = (
                    vacunacion_df[column_name]
                    .astype(str)
                    .str.lower()
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

    # =====================================================================
    # PASO 3: RECÁLCULO DE MÉTRICAS
    # =====================================================================
    
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
        cols_to_drop = ["DPMP_norm", "Municipio_norm"]
        for col in cols_to_drop:
            if col in metricas_df.columns:
                metricas_df = metricas_df.drop(col, axis=1)

        # Manejar columnas duplicadas de Vacunados
        if "Vacunados_y" in metricas_df.columns:
            metricas_df["Vacunados"] = metricas_df["Vacunados_y"]
            metricas_df = metricas_df.drop("Vacunados_y", axis=1)
        
        if "Vacunados_x" in metricas_df.columns:
            if "Vacunados" not in metricas_df.columns:
                metricas_df["Vacunados"] = metricas_df["Vacunados_x"]
            metricas_df = metricas_df.drop("Vacunados_x", axis=1)

        # Si la fusión falló y no hay vacunados, preservar los valores originales o crear con ceros
        if "Vacunados" not in metricas_df.columns:
            if "Vacunados" in filtered_data["metricas"].columns:
                metricas_df["Vacunados"] = filtered_data["metricas"]["Vacunados"]
            else:
                metricas_df["Vacunados"] = 0

        # Rellenar valores NaN
        metricas_df["Vacunados"] = metricas_df["Vacunados"].fillna(0)

        # Recalcular métricas con protección contra división por cero
        # Para DANE
        metricas_df["Cobertura_DANE"] = np.where(
            metricas_df["DANE"] > 0,
            (metricas_df["Vacunados"] / metricas_df["DANE"] * 100).round(2),
            0
        )
        metricas_df["Pendientes_DANE"] = np.maximum(
            metricas_df["DANE"] - metricas_df["Vacunados"], 0
        )

        # Para SISBEN
        metricas_df["Cobertura_SISBEN"] = np.where(
            metricas_df["SISBEN"] > 0,
            (metricas_df["Vacunados"] / metricas_df["SISBEN"] * 100).round(2),
            0
        )
        metricas_df["Pendientes_SISBEN"] = np.maximum(
            metricas_df["SISBEN"] - metricas_df["Vacunados"], 0
        )

        # Actualizar el dataframe de métricas
        filtered_data["metricas"] = metricas_df

    # =====================================================================
    # PASO 4: VALIDACIÓN FINAL Y LIMPIEZA
    # =====================================================================
    
    # Validar que los DataFrames resultantes tengan sentido
    if len(filtered_data["vacunacion"]) == 0:
        # Si no hay datos después del filtrado, informar al usuario
        # pero mantener la estructura para evitar errores
        st.warning("⚠️ Los filtros aplicados no devolvieron ningún resultado. Mostrando estructura vacía.")
    
    # Asegurar que las columnas de métricas existan
    required_metric_columns = [
        "Vacunados", "Cobertura_DANE", "Pendientes_DANE", 
        "Cobertura_SISBEN", "Pendientes_SISBEN"
    ]
    
    for col in required_metric_columns:
        if col not in filtered_data["metricas"].columns:
            if "Vacunados" in col:
                filtered_data["metricas"][col] = 0
            elif "Cobertura" in col:
                filtered_data["metricas"][col] = 0.0
            elif "Pendientes" in col:
                # Calcular pendientes basándose en la fuente correspondiente
                if "DANE" in col and "DANE" in filtered_data["metricas"].columns:
                    filtered_data["metricas"][col] = filtered_data["metricas"]["DANE"]
                elif "SISBEN" in col and "SISBEN" in filtered_data["metricas"].columns:
                    filtered_data["metricas"][col] = filtered_data["metricas"]["SISBEN"]
                else:
                    filtered_data["metricas"][col] = 0

    return filtered_data


def get_filter_values_normalized(data):
    """
    Obtiene los valores únicos normalizados para cada filtro.
    Útil para poblar los selectores de filtros en la interfaz.
    
    Args:
        data (dict): Diccionario con los dataframes
        
    Returns:
        dict: Diccionario con valores únicos normalizados para cada filtro
    """
    vacunacion_df = data["vacunacion"].copy()
    
    # Normalizar datos antes de extraer valores únicos
    vacunacion_df = normalize_categorical_values(vacunacion_df)
    vacunacion_df = normalize_boolean_values(vacunacion_df)
    
    # Normalizar géneros
    gender_columns = ['Sexo', 'Genero']
    for col in gender_columns:
        if col in vacunacion_df.columns:
            vacunacion_df[col] = vacunacion_df[col].apply(normalize_gender_values)
    
    # Extraer valores únicos normalizados
    filter_values = {}
    
    # Municipios
    if "NombreMunicipioResidencia" in vacunacion_df.columns:
        municipios = sorted(vacunacion_df["NombreMunicipioResidencia"].dropna().unique())
        filter_values["municipios"] = [m for m in municipios if m != "Sin dato"]
    
    # Grupos de edad
    if "Grupo_Edad" in vacunacion_df.columns:
        grupos_edad = vacunacion_df["Grupo_Edad"].dropna().unique()
        # Ordenar grupos de edad lógicamente
        orden_grupos = ["0-4", "5-14", "15-19", "20-29", "30-39", 
                       "40-49", "50-59", "60-69", "70-79", "80+"]
        grupos_ordenados = [g for g in orden_grupos if g in grupos_edad]
        grupos_otros = sorted([g for g in grupos_edad if g not in orden_grupos and g != "Sin dato"])
        filter_values["grupos_edad"] = grupos_ordenados + grupos_otros
    
    # Géneros (usar orden específico)
    gender_col = "Genero" if "Genero" in vacunacion_df.columns else "Sexo"
    if gender_col in vacunacion_df.columns:
        generos = vacunacion_df[gender_col].unique()
        # Orden específico para géneros
        orden_generos = ["Masculino", "Femenino", "No Binario"]
        generos_ordenados = [g for g in orden_generos if g in generos]
        filter_values["generos"] = generos_ordenados
    
    # Grupos étnicos
    if "GrupoEtnico" in vacunacion_df.columns:
        grupos_etnicos = sorted(vacunacion_df["GrupoEtnico"].dropna().unique())
        filter_values["grupos_etnicos"] = [g for g in grupos_etnicos if g != "Sin dato"]
    
    # Regímenes
    if "RegimenAfiliacion" in vacunacion_df.columns:
        regimenes = sorted(vacunacion_df["RegimenAfiliacion"].dropna().unique())
        filter_values["regimenes"] = [r for r in regimenes if r != "Sin dato"]
    
    # Aseguradoras
    if "NombreAseguradora" in vacunacion_df.columns:
        aseguradoras = sorted(vacunacion_df["NombreAseguradora"].dropna().unique())
        filter_values["aseguradoras"] = [a for a in aseguradoras if a != "Sin dato"]
    
    return filter_values


def validate_data_quality(data):
    """
    Valida la calidad de los datos y reporta estadísticas de completitud.
    
    Args:
        data (dict): Diccionario con los dataframes
        
    Returns:
        dict: Reporte de calidad de datos
    """
    vacunacion_df = data["vacunacion"].copy()
    total_records = len(vacunacion_df)
    
    quality_report = {
        "total_records": total_records,
        "completeness": {},
        "data_quality_score": 0,
        "issues": []
    }
    
    # Columnas críticas para evaluar
    critical_columns = [
        'NombreMunicipioResidencia', 'Sexo', 'Grupo_Edad', 
        'GrupoEtnico', 'RegimenAfiliacion', 'FA UNICA'
    ]
    
    completeness_scores = []
    
    for col in critical_columns:
        if col in vacunacion_df.columns:
            # Contar registros completos (no NaN, no vacíos, no "Sin dato")
            complete_records = vacunacion_df[
                (~vacunacion_df[col].isna()) & 
                (vacunacion_df[col] != "Sin dato") &
                (vacunacion_df[col].astype(str).str.strip() != "") &
                (~vacunacion_df[col].astype(str).str.lower().isin(['nan', 'null', 'none']))
            ]
            
            completeness_pct = (len(complete_records) / total_records * 100) if total_records > 0 else 0
            quality_report["completeness"][col] = completeness_pct
            completeness_scores.append(completeness_pct)
            
            # Identificar problemas
            if completeness_pct < 80:
                quality_report["issues"].append(f"Baja completitud en {col}: {completeness_pct:.1f}%")
            elif completeness_pct < 95:
                quality_report["issues"].append(f"Completitud moderada en {col}: {completeness_pct:.1f}%")
    
    # Calcular score general de calidad
    if completeness_scores:
        quality_report["data_quality_score"] = np.mean(completeness_scores)
    
    # Evaluaciones adicionales
    # Verificar duplicados por documento
    if "Documento" in vacunacion_df.columns:
        duplicates = vacunacion_df["Documento"].duplicated().sum()
        if duplicates > 0:
            quality_report["issues"].append(f"Se encontraron {duplicates} posibles duplicados por documento")
    
    # Verificar fechas válidas
    if "FA UNICA" in vacunacion_df.columns:
        try:
            fechas_validas = pd.to_datetime(vacunacion_df["FA UNICA"], errors="coerce").notna().sum()
            fechas_invalidas = total_records - fechas_validas
            if fechas_invalidas > 0:
                quality_report["issues"].append(f"Se encontraron {fechas_invalidas} fechas inválidas")
        except:
            quality_report["issues"].append("No se pudo validar el formato de fechas")
    
    return quality_report