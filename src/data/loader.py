import pandas as pd
import numpy as np
from pathlib import Path
import streamlit as st
import os
import time
import io
import traceback

# Intenta importar las bibliotecas de Google con manejo de errores
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload

    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False
    st.warning(
        "⚠️ Las APIs de Google no están disponibles. Se usarán solo archivos locales."
    )

# Directorio de datos
DATA_DIR = Path(__file__).parent.parent.parent / "data"
ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"
IMAGES_DIR = ASSETS_DIR / "images"

# Asegurar que las carpetas existan
DATA_DIR.mkdir(exist_ok=True, parents=True)
ASSETS_DIR.mkdir(exist_ok=True, parents=True)
IMAGES_DIR.mkdir(exist_ok=True, parents=True)


def download_file_with_timeout(drive_service, file_id, destination_path, timeout=60):
    """
    Descarga un archivo de Google Drive con tiempo de espera máximo.

    Args:
        drive_service: Servicio de Google Drive
        file_id (str): ID del archivo en Google Drive
        destination_path (Path): Ruta local donde guardar el archivo
        timeout (int): Tiempo máximo de espera en segundos

    Returns:
        bool: True si la descarga fue exitosa, False en caso contrario
    """
    try:
        start_time = time.time()
        request = drive_service.files().get_media(fileId=file_id)

        # Asegurar que el directorio existe
        destination_path.parent.mkdir(exist_ok=True, parents=True)

        with open(destination_path, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                # Verificar tiempo de espera
                if time.time() - start_time > timeout:
                    print(f"Tiempo de espera excedido al descargar {file_id}")
                    return False

                status, done = downloader.next_chunk()
                print(f"Descarga {int(status.progress() * 100)}%")

        print(f"Archivo descargado exitosamente: {destination_path}")
        return True
    except Exception as e:
        print(f"Error al descargar archivo {file_id}: {str(e)}")
        traceback.print_exc()  # Imprimir stack trace completo
        return False


def load_from_drive():
    """
    Descarga archivos de Google Drive usando la cuenta de servicio.
    """
    if not GOOGLE_APIS_AVAILABLE:
        return False

    # Verificar si tenemos secretos configurados
    if "google_drive" not in st.secrets or "gcp_service_account" not in st.secrets:
        print("No se encontraron secretos de Google Drive configurados")
        return False

    try:
        # Crear credenciales
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/drive.readonly"],
        )

        # Construir servicio de Drive
        drive_service = build("drive", "v3", credentials=credentials)

        # Verificar conexión - intentar listar archivos
        response = drive_service.files().list(pageSize=1).execute()
        if "files" not in response:
            st.error("Error al conectar con Google Drive. Verificar permisos.")
            return False

        # Descargar archivos con timeout
        success = True

        # Descargar archivo de población
        if "poblacion_xlsx" in st.secrets["google_drive"]:
            poblacion_path = DATA_DIR / "POBLACION.xlsx"
            if not download_file_with_timeout(
                drive_service,
                st.secrets["google_drive"]["poblacion_xlsx"],
                poblacion_path,
            ):
                success = False

        # Descargar archivo de vacunación
        if "vacunacion_csv" in st.secrets["google_drive"]:
            vacunacion_path = DATA_DIR / "vacunacion_fa.csv"
            if not download_file_with_timeout(
                drive_service,
                st.secrets["google_drive"]["vacunacion_csv"],
                vacunacion_path,
            ):
                success = False

        # Descargar logo
        if "logo_gobernacion" in st.secrets["google_drive"]:
            logo_path = IMAGES_DIR / "logo_gobernacion.png"
            if not download_file_with_timeout(
                drive_service, st.secrets["google_drive"]["logo_gobernacion"], logo_path
            ):
                success = False

        # Descargar imagen del mosquito
        if "mosquito_png" in st.secrets["google_drive"]:
            mosquito_path = IMAGES_DIR / "mosquito.png"
            if not download_file_with_timeout(
                drive_service, st.secrets["google_drive"]["mosquito_png"], mosquito_path
            ):
                success = False

        return success

    except Exception as e:
        st.error(f"Error al cargar desde Google Drive: {str(e)}")
        traceback.print_exc()  # Imprimir stack trace completo
        return False


# Modificar la función de carga para usar timeout
@st.cache_data(ttl=3600)
def load_datasets():
    """
    Carga los datasets necesarios para la aplicación.
    """
    # Ocultar mensajes de progreso con un spinner silencioso
    with st.spinner("Cargando datos..."):
        # Verificar archivos
        poblacion_file = DATA_DIR / "POBLACION.xlsx"
        vacunacion_file = DATA_DIR / "vacunacion_fa.csv"

        # Verificar que los archivos existan
        if not poblacion_file.exists() or not vacunacion_file.exists():
            # Solo mostrar error si los archivos no existen
            missing_files = []
            if not poblacion_file.exists():
                missing_files.append(f"POBLACION.xlsx")
            if not vacunacion_file.exists():
                missing_files.append(f"vacunacion_fa.csv")

            st.error(
                f"Error: No se encontraron los archivos: {', '.join(missing_files)}"
            )
            raise FileNotFoundError(
                f"Archivos no encontrados: {', '.join(missing_files)}"
            )

        # Cargar datos de población
        municipios_df = pd.read_excel(poblacion_file, sheet_name="Poblacion")

        # Cargar datos de vacunación con múltiples encodings
        try:
            # Intento 1: UTF-8 (estándar)
            vacunacion_df = pd.read_csv(
                vacunacion_file, low_memory=False, encoding="utf-8"
            )
        except UnicodeDecodeError:
            try:
                # Intento 2: Latin-1 (común en español)
                vacunacion_df = pd.read_csv(
                    vacunacion_file, low_memory=False, encoding="latin-1"
                )
            except UnicodeDecodeError:
                try:
                    # Intento 3: Windows CP1252 (muy común en Excel de Windows)
                    vacunacion_df = pd.read_csv(
                        vacunacion_file, low_memory=False, encoding="cp1252"
                    )
                except UnicodeDecodeError:
                    # Intento 4: ISO-8859-1 (otra codificación común)
                    vacunacion_df = pd.read_csv(
                        vacunacion_file, low_memory=False, encoding="iso-8859-1"
                    )

        # Normalizar DataFrame
        vacunacion_df = normalize_dataframe(vacunacion_df)

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
    # Importar la función de normalización
    from src.data.normalize import normalize_municipality_names

    # Crear copia para no modificar el original
    metricas_df = municipios_df.copy()

    # Verificar que exista la columna NombreMunicipioResidencia
    if "NombreMunicipioResidencia" not in vacunacion_df.columns:
        # Crear columna de vacunados con ceros
        metricas_df["Vacunados"] = 0
    else:
        # Normalizar nombres de municipios en datos de vacunación
        vacunacion_df_clean = normalize_municipality_names(
            vacunacion_df, "NombreMunicipioResidencia"
        )

        # Normalizar nombre de municipios en datos de población
        metricas_df = normalize_municipality_names(metricas_df, "DPMP")

        # Contar vacunados por municipio (con nombres normalizados)
        vacunados_por_municipio = (
            vacunacion_df_clean.groupby("NombreMunicipioResidencia_norm")
            .size()
            .reset_index()
        )
        vacunados_por_municipio.columns = ["Municipio", "Vacunados"]

        # Fusionar con municipios normalizados
        metricas_df = pd.merge(
            metricas_df,
            vacunados_por_municipio,
            left_on="DPMP_norm",
            right_on="Municipio",
            how="left",
        )

        # Eliminar columna auxiliar
        metricas_df = metricas_df.drop(
            ["DPMP_norm", "Municipio"], axis=1, errors="ignore"
        )

        # Verificar si la fusión funcionó
        if "Vacunados" not in metricas_df.columns:
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

    return metricas_df


def normalize_dataframe(df):
    """
    Normaliza los nombres de las columnas y añade columnas faltantes.
    """
    # Limpiar nombres de columnas (quitar espacios y caracteres invisibles)
    df.columns = [col.strip() for col in df.columns]

    # Imprimir columnas para diagnóstico
    print("Columnas después de limpiar espacios:", df.columns.tolist())

    # Buscar columnas similares a las que necesitamos
    column_map = {}
    required_columns = [
        "Grupo_Edad",
        "Sexo",
        "GrupoEtnico",
        "RegimenAfiliacion",
        "NombreAseguradora",
        "FA UNICA",
        "NombreMunicipioResidencia",
    ]

    for req_col in required_columns:
        # Buscar coincidencia exacta
        if req_col in df.columns:
            continue

        # Buscar coincidencia sin distinguir mayúsculas/minúsculas
        for col in df.columns:
            if col.lower() == req_col.lower():
                column_map[col] = req_col
                break

            # Buscar coincidencia aproximada
            if req_col.lower().replace("_", "") == col.lower().replace("_", "").replace(
                " ", ""
            ):
                column_map[col] = req_col
                break

    # Renombrar columnas encontradas
    if column_map:
        print(f"Renombrando columnas: {column_map}")
        df = df.rename(columns=column_map)

    # Crear columnas faltantes con valores predeterminados
    for req_col in required_columns:
        if req_col not in df.columns:
            print(f"Creando columna faltante: {req_col}")
            df[req_col] = "Sin especificar"

            # Caso especial para Grupo_Edad si tenemos Edad_Vacunacion
            if req_col == "Grupo_Edad" and "Edad_Vacunacion" in df.columns:
                df[req_col] = df["Edad_Vacunacion"].apply(
                    lambda x: (
                        "0-4"
                        if pd.notna(x) and x < 5
                        else (
                            "5-14"
                            if pd.notna(x) and x < 15
                            else (
                                "15-19"
                                if pd.notna(x) and x < 20
                                else (
                                    "20-29"
                                    if pd.notna(x) and x < 30
                                    else (
                                        "30-39"
                                        if pd.notna(x) and x < 40
                                        else (
                                            "40-49"
                                            if pd.notna(x) and x < 50
                                            else (
                                                "50-59"
                                                if pd.notna(x) and x < 60
                                                else (
                                                    "60-69"
                                                    if pd.notna(x) and x < 70
                                                    else (
                                                        "70-79"
                                                        if pd.notna(x) and x < 80
                                                        else (
                                                            "80+"
                                                            if pd.notna(x) and x >= 80
                                                            else "Sin especificar"
                                                        )
                                                    )
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )

    return df
