import pandas as pd
import numpy as np
from pathlib import Path
import streamlit as st
import os

# Directorio de datos
DATA_DIR = Path(__file__).parent.parent.parent / "data"

@st.cache_data(ttl=3600)
def load_datasets():
    """
    Carga los datasets necesarios para la aplicación o genera datos simulados si no están disponibles.
    
    Returns:
        dict: Diccionario con todos los dataframes necesarios.
    """
    # Rutas a los archivos
    poblacion_file = DATA_DIR / "POBLACION.xlsx"
    vacunacion_file = DATA_DIR / "vacunacion_fa.csv"
    
    # Verificar si los archivos existen
    files_exist = poblacion_file.exists() and vacunacion_file.exists()
    
    if files_exist:
        # Si los archivos existen, cargarlos
        st.success("Datos reales cargados correctamente.")
        
        # Cargar datos de población
        municipios_df = pd.read_excel(poblacion_file, sheet_name="Poblacion")
        
        # Cargar datos de vacunación
        vacunacion_df = pd.read_csv(vacunacion_file)
        
    else:
        # Si los archivos no existen, mostrar mensaje y usar datos simulados
        st.warning("""
        ⚠️ **Modo Demostración**: Se están usando datos simulados porque los archivos reales no están disponibles.
        
        En un entorno de producción, deberías proporcionar:
        - `data/POBLACION.xlsx`: Datos reales de población
        - `data/vacunacion_fa.csv`: Datos reales de vacunación
        """)
        
        # Generar datos simulados de población
        municipios = [
            "Ibagué", "Espinal", "Chaparral", "Mariquita", "Melgar", "Líbano", 
            "Ortega", "Guamo", "Fresno", "Flandes", "Honda", "Rovira", "San Luis",
            "Alvarado", "Cajamarca", "Venadillo", "Planadas", "Alpujarra", "Suárez"
        ]
        
        dane_values = [498535, 68779, 50174, 35999, 35646, 33916, 31093, 30907, 29623, 27639, 
                       23274, 20512, 11695, 8477, 17896, 11854, 25779, 4140, 3460]
        
        sisben_values = [332581, 74236, 52632, 34990, 33583, 35608, 20943, 32592, 32076, 22497, 
                         19602, 28060, 16118, 10073, 18126, 14297, 27713, 4674, 4419]
        
        codigos_dane = ["73001", "73268", "73168", "73443", "73449", "73411", "73504", "73319", 
                         "73283", "73275", "73349", "73624", "73678", "73026", "73124", "73861", 
                         "73555", "73024", "73770"]
        
        # Crear DataFrame de municipios simulado
        municipios_df = pd.DataFrame({
            "DPMP": municipios,
            "SISBEN": sisben_values,
            "DANE": dane_values,
            "CODMUN/\r\nDIVIPOLA/COD DANE": codigos_dane
        })
        
        # Generar datos simulados de vacunación
        np.random.seed(42)  # Para reproducibilidad
        n_registros = 5000
        
        # Tipos de identificación
        tipos_id = ['CC', 'TI', 'RC', 'CE', 'PA']
        
        # Nombres y apellidos simulados
        nombres = ['Juan', 'María', 'Pedro', 'Ana', 'Luis', 'Sofía', 'Carlos', 'Laura']
        apellidos = ['García', 'Rodríguez', 'López', 'Martínez', 'González', 'Pérez']
        
        # Sexos
        sexos = ['Masculino', 'Femenino']
        
        # Grupos de edad
        grupos_edad = ['0-4', '5-14', '15-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+']
        
        # Grupos étnicos
        grupos_etnicos = ['Indígena', 'Afrocolombiano', 'ROM', 'Raizal', 'Palenquero', 'Ninguno']
        prob_etnicos = [0.05, 0.03, 0.01, 0.01, 0.01, 0.89]
        
        # Estatus
        estatus = [True, False]
        
        # Regímenes
        regimenes = ['Contributivo', 'Subsidiado', 'Excepción', 'Especial', 'No asegurado']
        
        # Aseguradoras
        aseguradoras = ['Nueva EPS', 'Salud Total', 'Sanitas', 'Medimás', 'Famisanar', 'Coomeva', 'Sura', 'Otros']
        
        # Crear datos simulados
        data = {
            'IdPaciente': [f'ID{i:06d}' for i in range(1, n_registros + 1)],
            'TipoIdentificacion': np.random.choice(tipos_id, n_registros),
            'Documento': [str(np.random.randint(10000000, 99999999)) for _ in range(n_registros)],
            'PrimerNombre': np.random.choice(nombres, n_registros),
            'PrimerApellido': np.random.choice(apellidos, n_registros),
            'Sexo': np.random.choice(sexos, n_registros),
            'FechaNacimiento': pd.date_range(start='1940-01-01', end='2023-12-31', periods=n_registros),
            'NombreMunicipioNacimiento': np.random.choice(municipios, n_registros),
            'NombreDptoNacimiento': ['Tolima'] * n_registros,
            'NombreMunicipioResidencia': np.random.choice(municipios, n_registros),
            'NombreDptoResidencia': ['Tolima'] * n_registros,
            'GrupoEtnico': np.random.choice(grupos_etnicos, n_registros, p=prob_etnicos),
            'Desplazado': np.random.choice(estatus, n_registros),
            'Discapacitado': np.random.choice(estatus, n_registros),
            'RegimenAfiliacion': np.random.choice(regimenes, n_registros),
            'NombreAseguradora': np.random.choice(aseguradoras, n_registros),
            'FA UNICA': ['Si'] * n_registros,
            'Grupo_Edad': np.random.choice(grupos_edad, n_registros),
            'Edad_Vacunacion': np.random.randint(0, 90, n_registros),
        }
        
        # Crear DataFrame de vacunación simulado
        vacunacion_df = pd.DataFrame(data)
    
    # Calcular métricas
    metricas_df = calculate_metrics(municipios_df, vacunacion_df)
    
    # Crear directorio de datos si no existe
    os.makedirs(DATA_DIR, exist_ok=True)
    
    return {
        "municipios": municipios_df,
        "vacunacion": vacunacion_df,
        "metricas": metricas_df
    }

def calculate_metrics(municipios_df, vacunacion_df):
    """
    Calcula métricas agregadas para el dashboard.
    
    Args:
        municipios_df (pd.DataFrame): DataFrame con datos de municipios
        vacunacion_df (pd.DataFrame): DataFrame con datos de vacunación
        
    Returns:
        pd.DataFrame: DataFrame con métricas calculadas
    """
    # Crear copia para no modificar el original
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
    
    return metricas_df