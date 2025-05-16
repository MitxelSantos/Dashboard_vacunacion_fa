import pandas as pd
import os
from pathlib import Path
import streamlit as st

# Constante global para el directorio de datos
DATA_DIR = Path(__file__).parent.parent.parent / "data"

@st.cache_data(ttl=3600)  # Caché por 1 hora
def load_datasets():
    """
    Carga todos los datasets necesarios para la aplicación.
    
    Returns:
        dict: Diccionario con todos los dataframes necesarios.
    """
    # Rutas absolutas a los archivos
    poblacion_file = DATA_DIR / "POBLACION.xlsx"
    vacunacion_file = DATA_DIR / "vacunacion_fa.csv"
    
    # Verificar que los archivos existan
    if not poblacion_file.exists():
        raise FileNotFoundError(f"El archivo {poblacion_file} no existe")
    
    if not vacunacion_file.exists():
        raise FileNotFoundError(f"El archivo {vacunacion_file} no existe")
    
    # Cargar datos de población
    municipios_df = pd.read_excel(
        poblacion_file,
        sheet_name="Poblacion"
    )
    
    # Cargar datos de vacunación
    vacunacion_df = pd.read_csv(vacunacion_file)
    
    # Calcular métricas agregadas para ambas fuentes
    metricas_dane_df = calculate_metrics(municipios_df, vacunacion_df, "DANE")
    metricas_sisben_df = calculate_metrics(municipios_df, vacunacion_df, "SISBEN")
    
    # Crear un diccionario único de métricas que incluya ambas fuentes
    metricas_df = municipios_df.copy()
    
    # Contar vacunados por municipio
    vacunados_por_municipio = vacunacion_df['NombreMunicipioResidencia'].value_counts().reset_index()
    vacunados_por_municipio.columns = ['Municipio', 'Vacunados']
    
    # Fusionar con datos de población
    metricas_df = pd.merge(
        metricas_df,
        vacunados_por_municipio,
        left_on='DPMP',
        right_on='Municipio',
        how='left'
    )
    
    # Rellenar valores NaN
    metricas_df['Vacunados'].fillna(0, inplace=True)
    
    # Calcular cobertura para ambas fuentes
    metricas_df['Cobertura_DANE'] = (metricas_df['Vacunados'] / metricas_df['DANE'] * 100).round(2)
    metricas_df['Pendientes_DANE'] = metricas_df['DANE'] - metricas_df['Vacunados']
    
    metricas_df['Cobertura_SISBEN'] = (metricas_df['Vacunados'] / metricas_df['SISBEN'] * 100).round(2)
    metricas_df['Pendientes_SISBEN'] = metricas_df['SISBEN'] - metricas_df['Vacunados']
    
    return {
        "municipios": municipios_df,
        "vacunacion": vacunacion_df,
        "metricas": metricas_df
    }

def calculate_metrics(municipios_df, vacunacion_df, fuente="DANE"):
    """
    Calcula métricas agregadas para el dashboard basado en la fuente de población elegida.
    
    Args:
        municipios_df (pd.DataFrame): DataFrame con datos de municipios
        vacunacion_df (pd.DataFrame): DataFrame con datos de vacunación
        fuente (str): Fuente de datos de población ("DANE" o "SISBEN")
        
    Returns:
        pd.DataFrame: DataFrame con métricas calculadas
    """
    # Contar vacunados por municipio
    vacunados_por_municipio = vacunacion_df['NombreMunicipioResidencia'].value_counts().reset_index()
    vacunados_por_municipio.columns = ['Municipio', 'Vacunados']
    
    # Fusionar con datos de población
    metricas_df = pd.merge(
        municipios_df,
        vacunados_por_municipio,
        left_on='DPMP',
        right_on='Municipio',
        how='left'
    )
    
    # Rellenar valores NaN
    metricas_df['Vacunados'].fillna(0, inplace=True)
    
    # Calcular cobertura y pendientes según la fuente seleccionada
    metricas_df[f'Cobertura_{fuente}'] = (metricas_df['Vacunados'] / metricas_df[fuente] * 100).round(2)
    metricas_df[f'Pendientes_{fuente}'] = metricas_df[fuente] - metricas_df['Vacunados']
    
    return metricas_df