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
    Carga los datasets necesarios para la aplicación desde archivos reales.

    Returns:
        dict: Diccionario con todos los dataframes necesarios.
    """
    # Rutas a los archivos
    poblacion_file = DATA_DIR / "POBLACION.xlsx"
    vacunacion_file = DATA_DIR / "vacunacion_fa.csv"

    # Verificar si los archivos existen
    if not poblacion_file.exists():
        st.error(f"ERROR: Archivo de población no encontrado en {poblacion_file}")
        st.stop()

    if not vacunacion_file.exists():
        st.error(f"ERROR: Archivo de vacunación no encontrado en {vacunacion_file}")
        st.stop()

    # Cargar datos de población
    try:
        municipios_df = pd.read_excel(poblacion_file, sheet_name="Poblacion")
        # Información de diagnóstico silenciosa para no llenar la UI
        print(f"Datos de población cargados: {len(municipios_df)} municipios")
    except Exception as e:
        st.error(f"Error al cargar datos de población: {str(e)}")
        st.stop()

    # Cargar datos de vacunación
    try:
        vacunacion_df = pd.read_csv(vacunacion_file, low_memory=False)
        # Información de diagnóstico silenciosa
        print(f"Datos de vacunación cargados: {len(vacunacion_df)} registros")
    except Exception as e:
        st.error(f"Error al cargar datos de vacunación: {str(e)}")
        st.stop()

    # Crear directorio de datos si no existe
    os.makedirs(DATA_DIR, exist_ok=True)

    # Calcular métricas
    metricas_df = calculate_metrics(municipios_df, vacunacion_df)

    return {
        "municipios": municipios_df,
        "vacunacion": vacunacion_df,
        "metricas": metricas_df,
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

    # Verificar que exista la columna NombreMunicipioResidencia
    if "NombreMunicipioResidencia" not in vacunacion_df.columns:
        print(
            "Error: La columna 'NombreMunicipioResidencia' no existe en los datos de vacunación"
        )
        # Crear columna de vacunados con ceros
        metricas_df["Vacunados"] = 0
    else:
        # Contar vacunados por municipio
        # Limpiar y normalizar nombres a minúsculas para la comparación
        vacunacion_df_clean = vacunacion_df.copy()

        # Rellenar valores NaN y convertir a minúsculas
        vacunacion_df_clean["NombreMunicipioResidencia"] = vacunacion_df_clean[
            "NombreMunicipioResidencia"
        ].fillna("Sin especificar")
        vacunacion_df_clean["NombreMunicipioResidencia"] = (
            vacunacion_df_clean["NombreMunicipioResidencia"].str.strip().str.lower()
        )

        # Normalizar nombre de municipios en datos de población
        metricas_df["DPMP_lower"] = metricas_df["DPMP"].str.strip().str.lower()

        # Contar vacunados por municipio (nombres en minúsculas)
        vacunados_por_municipio = (
            vacunacion_df_clean["NombreMunicipioResidencia"]
            .value_counts()
            .reset_index()
        )
        vacunados_por_municipio.columns = ["Municipio", "Vacunados"]

        # Diagnóstico de la fusión (solo en consola para no llenar la UI)
        municipios_vacunacion = set(vacunados_por_municipio["Municipio"])
        municipios_poblacion = set(metricas_df["DPMP_lower"])
        comunes = municipios_vacunacion.intersection(municipios_poblacion)

        print(f"Municipios en vacunación: {len(municipios_vacunacion)}")
        print(f"Municipios en población: {len(municipios_poblacion)}")
        print(f"Municipios coincidentes: {len(comunes)}")

        # Fusionar con municipios en minúsculas
        metricas_df = pd.merge(
            metricas_df,
            vacunados_por_municipio,
            left_on="DPMP_lower",  # Usando la versión en minúsculas
            right_on="Municipio",
            how="left",
        )

        # Eliminar columna auxiliar
        metricas_df = metricas_df.drop(
            ["DPMP_lower", "Municipio"], axis=1, errors="ignore"
        )

        # Verificar si la fusión funcionó
        if "Vacunados" not in metricas_df.columns:
            print("Error en la fusión: la columna 'Vacunados' no se creó")
            metricas_df["Vacunados"] = 0

    # Rellenar valores NaN con 0
    metricas_df["Vacunados"] = metricas_df["Vacunados"].fillna(0)

    # Calcular cobertura y pendientes para ambas fuentes
    metricas_df["Cobertura_DANE"] = (
        metricas_df["Vacunados"] / metricas_df["DANE"] * 100
    ).round(2)
    metricas_df["Pendientes_DANE"] = metricas_df["DANE"] - metricas_df["Vacunados"]

    metricas_df["Cobertura_SISBEN"] = (
        metricas_df["Vacunados"] / metricas_df["SISBEN"] * 100
    ).round(2)
    metricas_df["Pendientes_SISBEN"] = metricas_df["SISBEN"] - metricas_df["Vacunados"]

    # Información de diagnóstico
    print(f"Total de vacunados calculados: {metricas_df['Vacunados'].sum()}")
    print(
        f"Municipios sin vacunados: {(metricas_df['Vacunados'] == 0).sum()} de {len(metricas_df)}"
    )

    return metricas_df
