import pandas as pd
import numpy as np
from pathlib import Path
import streamlit as st
import os
import requests
from io import BytesIO

# Directorio de datos
DATA_DIR = Path(__file__).parent.parent.parent / "data"

@st.cache_data(ttl=3600)
def load_datasets():
    """
    Carga los datasets desde Google Drive o localmente si están disponibles.
    
    Returns:
        dict: Diccionario con todos los dataframes necesarios.
    """
    # Verificar si estamos en Streamlit Cloud o en desarrollo local
    is_local = os.path.exists(DATA_DIR / "POBLACION.xlsx")
    
    if is_local:
        # Si estamos en desarrollo local, cargar archivos directamente
        st.success("Cargando datos desde archivos locales")
        
        # Cargar datos de población
        poblacion_file = DATA_DIR / "POBLACION.xlsx"
        municipios_df = pd.read_excel(poblacion_file, sheet_name="Poblacion")
        
        # Cargar datos de vacunación
        vacunacion_file = DATA_DIR / "vacunacion_fa.csv"
        if vacunacion_file.exists():
            vacunacion_df = pd.read_csv(vacunacion_file)
        else:
            st.error(f"El archivo {vacunacion_file} no existe")
            return None
    else:
        # Si estamos en Streamlit Cloud, cargar archivos desde Google Drive
        st.info("Cargando datos desde Google Drive")
        
        # Obtener IDs de Google Drive desde los secretos
        try:
            # Acceder a secretos de Streamlit
            google_drive_secrets = st.secrets["google_drive"]
            poblacion_file_id = google_drive_secrets["poblacion_file_id"]
            vacunacion_file_id = google_drive_secrets["vacunacion_file_id"]
        except Exception as e:
            st.error(f"Error al obtener secretos: {str(e)}")
            st.error("Por favor, configure los secretos en Streamlit Cloud")
            return None
        
        # Descargar archivos de Google Drive
        try:
            # Función para descargar un archivo de Google Drive
            def download_file_from_google_drive(file_id):
                URL = f"https://drive.google.com/uc?export=download&id={file_id}"
                session = requests.Session()
                response = session.get(URL)
                return BytesIO(response.content)
            
            # Descargar y cargar datos de población
            poblacion_bytes = download_file_from_google_drive(poblacion_file_id)
            municipios_df = pd.read_excel(poblacion_bytes, sheet_name="Poblacion")
            
            # Descargar y cargar datos de vacunación
            vacunacion_bytes = download_file_from_google_drive(vacunacion_file_id)
            vacunacion_df = pd.read_csv(vacunacion_bytes)
            
            st.success("Datos cargados correctamente desde Google Drive")
        except Exception as e:
            st.error(f"Error al descargar archivos: {str(e)}")
            return None
    
    # Calcular métricas
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
    
    # Calcular cobertura y pendientes para ambas fuentes
    metricas_df['Cobertura_DANE'] = (metricas_df['Vacunados'] / metricas_df['DANE'] * 100).round(2)
    metricas_df['Pendientes_DANE'] = metricas_df['DANE'] - metricas_df['Vacunados']
    
    metricas_df['Cobertura_SISBEN'] = (metricas_df['Vacunados'] / metricas_df['SISBEN'] * 100).round(2)
    metricas_df['Pendientes_SISBEN'] = metricas_df['SISBEN'] - metricas_df['Vacunados']
    
    return {
        "municipios": municipios_df,
        "vacunacion": vacunacion_df,
        "metricas": metricas_df
    }