import pandas as pd
import numpy as np


def normalize_municipality_names(df, col="Municipio"):
    """Normaliza nombres de municipios"""
    if col not in df.columns:
        return df
    
    df_clean = df.copy()
    df_clean[col] = df_clean[col].str.upper().str.strip()
    return df_clean


def clean_dates(df, date_cols):
    """Limpia columnas de fechas"""
    df_clean = df.copy()
    for col in date_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_datetime(df_clean[col], errors="coerce")
    return df_clean


def clean_age(df, birth_col, ref_date=None, new_col="Edad"):
    """Calcula edad basada en fecha de nacimiento"""
    if birth_col not in df.columns:
        return df
        
    df_clean = df.copy()
    if ref_date is None:
        ref_date = pd.Timestamp.today()
    
    df_clean[new_col] = (
        (ref_date - pd.to_datetime(df_clean[birth_col], errors="coerce")).dt.days // 365
    ).astype("Int64")
    return df_clean


def apply_filters(data, filters):
    """
    Aplica filtros a los datos del dashboard
    
    Args:
        data: Diccionario con DataFrames o DataFrame individual
        filters: Diccionario con filtros a aplicar
    
    Returns:
        Datos filtrados en el mismo formato de entrada
    """
    try:
        # Si data es un diccionario, procesamos cada DataFrame
        if isinstance(data, dict):
            filtered_data = {}
            
            # Procesar cada DataFrame en el diccionario
            for key, df in data.items():
                if isinstance(df, pd.DataFrame) and not df.empty:
                    filtered_data[key] = _apply_filters_to_dataframe(df, filters)
                else:
                    filtered_data[key] = df
            
            return filtered_data
        
        # Si data es un DataFrame, aplicar filtros directamente
        elif isinstance(data, pd.DataFrame):
            return _apply_filters_to_dataframe(data, filters)
        
        # Si no es ninguno de los anteriores, retornar sin cambios
        else:
            return data
            
    except Exception as e:
        print(f"Error aplicando filtros: {str(e)}")
        return data


def _apply_filters_to_dataframe(df, filters):
    """
    Aplica filtros a un DataFrame individual
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df
    
    if not isinstance(filters, dict) or not filters:
        return df
    
    filtered_df = df.copy()
    
    try:
        # Aplicar filtros por columna
        for col, val in filters.items():
            if val is None or val == "Todos" or val == "":
                continue
                
            if col in filtered_df.columns:
                # Filtro por valor exacto
                if isinstance(val, (str, int, float)):
                    filtered_df = filtered_df[filtered_df[col] == val]
                # Filtro por lista de valores
                elif isinstance(val, (list, tuple)):
                    filtered_df = filtered_df[filtered_df[col].isin(val)]
                # Filtro por rango (para fechas o números)
                elif isinstance(val, dict) and 'min' in val and 'max' in val:
                    if val['min'] is not None:
                        filtered_df = filtered_df[filtered_df[col] >= val['min']]
                    if val['max'] is not None:
                        filtered_df = filtered_df[filtered_df[col] <= val['max']]
        
        return filtered_df
        
    except Exception as e:
        print(f"Error filtrando DataFrame: {str(e)}")
        return df


def create_metrics_dataframe(df_vacunacion, df_poblacion=None, fuente_poblacion="DANE"):
    """
    Crea DataFrame de métricas combinando vacunación y población
    
    Args:
        df_vacunacion: DataFrame con datos de vacunación
        df_poblacion: DataFrame con datos de población (opcional)
        fuente_poblacion: Fuente de datos de población
    
    Returns:
        DataFrame con métricas por municipio
    """
    try:
        if df_vacunacion is None or df_vacunacion.empty:
            return pd.DataFrame()
        
        # Buscar columna de municipio en vacunación
        municipio_col = None
        for col in ['NombreMunicipioResidencia', 'Municipio', 'MUNICIPIO']:
            if col in df_vacunacion.columns:
                municipio_col = col
                break
        
        if municipio_col is None:
            return pd.DataFrame()
        
        # Crear métricas básicas de vacunación
        metricas = df_vacunacion.groupby(municipio_col).agg({
            df_vacunacion.columns[0]: 'count'  # Contar registros
        }).reset_index()
        
        metricas.columns = ['DPMP', 'Vacunados']
        
        # Si hay datos de población, calcular cobertura
        if df_poblacion is not None and not df_poblacion.empty:
            try:
                # Buscar columna de municipio en población
                pop_municipio_col = None
                for col in ['DPMP', 'Municipio', 'MUNICIPIO']:
                    if col in df_poblacion.columns:
                        pop_municipio_col = col
                        break
                
                if pop_municipio_col and fuente_poblacion in df_poblacion.columns:
                    # Normalizar nombres para mejor matching
                    metricas_norm = normalize_municipality_names(metricas.copy(), 'DPMP')
                    poblacion_norm = normalize_municipality_names(df_poblacion.copy(), pop_municipio_col)
                    
                    # Fusionar datos
                    metricas_combined = pd.merge(
                        metricas_norm,
                        poblacion_norm[['DPMP', fuente_poblacion]].groupby('DPMP')[fuente_poblacion].sum().reset_index(),
                        on='DPMP',
                        how='left'
                    )
                    
                    # Calcular cobertura
                    metricas_combined[fuente_poblacion] = metricas_combined[fuente_poblacion].fillna(0)
                    metricas_combined[f'Cobertura_{fuente_poblacion}'] = np.where(
                        metricas_combined[fuente_poblacion] > 0,
                        (metricas_combined['Vacunados'] / metricas_combined[fuente_poblacion] * 100).round(2),
                        0
                    )
                    
                    return metricas_combined
                    
            except Exception as e:
                print(f"Error calculando cobertura: {str(e)}")
        
        # Si no hay datos de población o hay error, retornar métricas básicas
        metricas[fuente_poblacion] = 1000  # Valor por defecto
        metricas[f'Cobertura_{fuente_poblacion}'] = 0
        
        return metricas
        
    except Exception as e:
        print(f"Error creando métricas: {str(e)}")
        return pd.DataFrame()


def prepare_dashboard_data(df_vacunacion, df_poblacion=None, fuente_poblacion="DANE"):
    """
    Prepara los datos para el dashboard en el formato esperado
    
    Args:
        df_vacunacion: DataFrame con datos de vacunación
        df_poblacion: DataFrame con datos de población
        fuente_poblacion: Fuente de población a usar
    
    Returns:
        Diccionario con datos preparados para el dashboard
    """
    try:
        # Crear estructura de datos esperada por las vistas
        dashboard_data = {
            'vacunacion': df_vacunacion if df_vacunacion is not None else pd.DataFrame(),
            'poblacion': df_poblacion if df_poblacion is not None else pd.DataFrame(),
            'metricas': create_metrics_dataframe(df_vacunacion, df_poblacion, fuente_poblacion)
        }
        
        return dashboard_data
        
    except Exception as e:
        print(f"Error preparando datos para dashboard: {str(e)}")
        return {
            'vacunacion': pd.DataFrame(),
            'poblacion': pd.DataFrame(),
            'metricas': pd.DataFrame()
        }