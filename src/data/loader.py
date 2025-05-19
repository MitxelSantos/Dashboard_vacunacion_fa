import pandas as pd
import numpy as np
from pathlib import Path
import streamlit as st
import os
import time
import io
import traceback

# Google APIs
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

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


def download_file_with_timeout(drive_service, file_id, destination_path, timeout=1800):
    """
    Descarga un archivo de Google Drive con manejo avanzado para archivos muy grandes.
    """
    try:
        start_time = time.time()

        # Obtener información del archivo
        file_info = (
            drive_service.files()
            .get(fileId=file_id, fields="size,name,mimeType")
            .execute()
        )
        file_size = int(file_info.get("size", 0))

        # Asegurar que el directorio existe
        destination_path.parent.mkdir(exist_ok=True, parents=True)

        # Para archivos extremadamente grandes, usar un enfoque por bloques
        if file_size > 200 * 1024 * 1024:  # > 200MB
            # Usar bloques más grandes para acelerar la descarga
            chunk_size = 50 * 1024 * 1024  # 50MB por chunk

            # Crear request para descargar en chunks para usar menos memoria
            request = drive_service.files().get_media(fileId=file_id)

            with open(destination_path, "wb") as f:
                downloader = MediaIoBaseDownload(f, request, chunksize=chunk_size)
                done = False

                while not done:
                    # Verificar tiempo de espera máximo
                    if time.time() - start_time > timeout:
                        # Si hay un archivo parcial, eliminarlo para no confundir
                        if destination_path.exists():
                            destination_path.unlink()
                        return False

                    # Descargar siguiente chunk
                    try:
                        status, done = downloader.next_chunk()
                    except Exception:
                        # Intentar continuar con el siguiente chunk en lugar de abortar
                        continue
        else:
            # Para archivos medianos, usar el método estándar con chunks más grandes
            request = drive_service.files().get_media(fileId=file_id)

            with open(destination_path, "wb") as f:
                downloader = MediaIoBaseDownload(
                    f, request, chunksize=20 * 1024 * 1024
                )  # 20MB chunks
                done = False

                while not done:
                    if time.time() - start_time > timeout:
                        return False

                    status, done = downloader.next_chunk()

        # Verificar resultado
        if destination_path.exists():
            downloaded_size = destination_path.stat().st_size

            # Verificar integridad
            if downloaded_size >= file_size * 0.99:  # Permitir 1% de diferencia
                return True
            else:
                size_difference = abs(file_size - downloaded_size)
                percent_difference = (size_difference / file_size) * 100

                # Si la diferencia es pequeña, aceptar el archivo
                if percent_difference < 5:  # Menos del 5% de diferencia
                    return True
                else:
                    return False
        else:
            return False

    except Exception:
        return False


def load_from_drive():
    """
    Descarga archivos de Google Drive usando la cuenta de servicio.
    Proporciona información detallada sobre el proceso de descarga para facilitar depuración.
    """
    # Asegurar que las carpetas existan
    DATA_DIR.mkdir(exist_ok=True, parents=True)
    ASSETS_DIR.mkdir(exist_ok=True, parents=True)
    IMAGES_DIR.mkdir(exist_ok=True, parents=True)

    print("Iniciando descarga desde Google Drive...")

    # Verificar si tenemos secretos configurados
    if "google_drive" not in st.secrets:
        return False

    if "gcp_service_account" not in st.secrets:
        return False

    try:
        # Verificar que los IDs de archivos estén configurados
        required_files = ["poblacion_xlsx", "vacunacion_csv", "logo_gobernacion"]
        missing_files = [
            f for f in required_files if f not in st.secrets["google_drive"]
        ]

        if missing_files:
            return False

        # Crear credenciales
        try:
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/drive.readonly"],
            )
        except Exception:
            return False

        # Construir servicio de Drive
        try:
            drive_service = build("drive", "v3", credentials=credentials)

            # Verificar conexión - intentar listar archivos
            response = drive_service.files().list(pageSize=1).execute()
            if "files" not in response:
                return False

        except Exception:
            return False

        # Descargar archivo de población
        if "poblacion_xlsx" in st.secrets["google_drive"]:
            poblacion_path = DATA_DIR / "POBLACION.xlsx"
            file_id = st.secrets["google_drive"]["poblacion_xlsx"]

            try:
                drive_service.files().get(
                    fileId=file_id, fields="name,size,mimeType"
                ).execute()

                download_file_with_timeout(
                    drive_service,
                    file_id,
                    poblacion_path,
                )
            except Exception:
                pass

        # Descargar archivo de vacunación
        if "vacunacion_csv" in st.secrets["google_drive"]:
            vacunacion_path = DATA_DIR / "vacunacion_fa.csv"
            file_id = st.secrets["google_drive"]["vacunacion_csv"]

            try:
                drive_service.files().get(
                    fileId=file_id, fields="name,size,mimeType"
                ).execute()

                download_file_with_timeout(
                    drive_service,
                    file_id,
                    vacunacion_path,
                )
            except Exception:
                pass

        # Descargar logo
        if "logo_gobernacion" in st.secrets["google_drive"]:
            logo_path = IMAGES_DIR / "logo_gobernacion.png"
            file_id = st.secrets["google_drive"]["logo_gobernacion"]

            try:
                drive_service.files().get(
                    fileId=file_id, fields="name,size,mimeType"
                ).execute()

                download_file_with_timeout(
                    drive_service,
                    file_id,
                    logo_path,
                )
            except Exception:
                pass

        # Verificación final
        required_files_paths = [
            DATA_DIR / "POBLACION.xlsx",
            DATA_DIR / "vacunacion_fa.csv",
            IMAGES_DIR / "logo_gobernacion.png",
        ]

        missing_files = [
            str(path) for path in required_files_paths if not path.exists()
        ]

        if missing_files:
            return False

        return True

    except Exception:
        return False


def download_file(drive_service, file_id, destination_path):
    """
    Descarga un archivo de Google Drive a una ubicación local.

    Args:
        drive_service: Servicio de Google Drive
        file_id (str): ID del archivo en Google Drive
        destination_path (Path): Ruta local donde guardar el archivo
    """
    request = drive_service.files().get_media(fileId=file_id)

    with open(destination_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()


# Modificar la función de carga para usar timeout
# @st.cache_data(ttl=3600)
def load_datasets():
    """
    Carga los datasets necesarios para la aplicación.
    """
    with st.spinner("Cargando datos..."):
        # Verificar archivos
        poblacion_file = DATA_DIR / "POBLACION.xlsx"
        vacunacion_file = DATA_DIR / "vacunacion_fa.csv"

        # Si ya tenemos ambos archivos, no es necesario descargar de Drive
        if not (poblacion_file.exists() and vacunacion_file.exists()):
            # Intentar cargar desde Google Drive
            from src.data.drive_loader import load_from_drive

            load_from_drive()

        # Verificar si existen los archivos después de intentar cargarlos
        missing_files = []
        if not poblacion_file.exists():
            missing_files.append("POBLACION.xlsx")
        if not vacunacion_file.exists():
            missing_files.append("vacunacion_fa.csv")

        if missing_files:
            raise FileNotFoundError(
                f"Archivos no encontrados: {', '.join(missing_files)}"
            )

        # Cargar archivo de población
        municipios_df = pd.read_excel(poblacion_file, sheet_name="Poblacion")

        # Para archivos CSV grandes, usar estas optimizaciones
        try:
            # Para CSV extremadamente grandes, primero determinar las columnas que realmente necesitamos
            required_columns = [
                "IdPaciente",
                "TipoIdentificacion",
                "Documento",
                "Sexo",
                "FechaNacimiento",
                "NombreMunicipioResidencia",
                "GrupoEtnico",
                "RegimenAfiliacion",
                "NombreAseguradora",
                "FA UNICA",
                "Edad_Vacunacion",
            ]

            # Primero leer solo las columnas necesarias y usar dtype optimization
            # Elimino mensaje de diagnóstico: st.write("🔄 Leyendo CSV grande con optimizaciones...")

            # Determinar qué columnas existen en el archivo
            # Leer solo unas pocas líneas para ver la estructura
            temp_df = pd.read_csv(vacunacion_file, nrows=5)
            available_columns = temp_df.columns.tolist()

            # Crear lista de columnas que efectivamente existen
            use_columns = [col for col in required_columns if col in available_columns]

            # Preparar diccionario de dtypes optimizados
            dtypes = {
                "IdPaciente": "str",
                "TipoIdentificacion": "category",
                "Documento": "str",
                "Sexo": "category",
                "GrupoEtnico": "category",
                "RegimenAfiliacion": "category",
                "NombreAseguradora": "category",
                "NombreMunicipioResidencia": "category",
            }

            # Usar dtypes solo para columnas que realmente existen
            use_dtypes = {k: v for k, v in dtypes.items() if k in use_columns}

            # Leer el CSV con optimizaciones
            vacunacion_df = pd.read_csv(
                vacunacion_file,
                usecols=use_columns,
                dtype=use_dtypes,
                low_memory=False,
                encoding="utf-8",
                on_bad_lines="skip",  # Ignorar líneas problemáticas
            )

            # Elimino mensaje de diagnóstico: st.success(f"✅ CSV cargado exitosamente: {len(vacunacion_df)} registros")

        except UnicodeDecodeError:
            # Intentar con otras codificaciones
            for encoding in ["latin-1", "cp1252", "iso-8859-1"]:
                try:
                    vacunacion_df = pd.read_csv(
                        vacunacion_file, low_memory=False, encoding=encoding
                    )
                    break
                except UnicodeDecodeError:
                    continue
            else:
                st.error("❌ No se pudo determinar la codificación del archivo CSV")
                raise

        # Normalizar DataFrame
        vacunacion_df = normalize_dataframe(vacunacion_df)

        # Calcular métricas
        metricas_df = calculate_metrics(municipios_df, vacunacion_df)

        try:
            import time
            from datetime import datetime

            file_stats = vacunacion_file.stat()
            file_size = file_stats.st_size / (1024 * 1024)  # Tamaño en MB
            modified_time = datetime.fromtimestamp(file_stats.st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            num_rows = len(vacunacion_df)
            st.sidebar.info(
                f"""
            **Diagnóstico archivo CSV:**
            - Tamaño: {file_size:.2f} MB
            - Modificado: {modified_time}
            - Filas: {num_rows:,}
            """
            )
        except Exception as e:
            pass  # Ignorar errores en el diagnóstico

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

    # Si existe Sexo pero no Genero, crear columna Genero
    if "Sexo" in df.columns and "Genero" not in df.columns:
        # Crear columna Genero basada en Sexo
        df["Genero"] = df["Sexo"].copy()

        # Normalizar categorías a MASCULINO, FEMENINO, NO BINARIO
        # Primero asegurarse de que no es una columna categórica
        if pd.api.types.is_categorical_dtype(df["Genero"]):
            df["Genero"] = df["Genero"].astype(str)

        # Luego aplicar la normalización
        df["Genero"] = df["Genero"].str.strip()
        df["Genero"] = df["Genero"].apply(
            lambda x: (
                "MASCULINO"
                if str(x).lower() in ["masculino", "m", "masc", "hombre", "h", "male"]
                else (
                    "FEMENINO"
                    if str(x).lower() in ["femenino", "f", "fem", "mujer", "female"]
                    else (
                        "NO BINARIO"
                        if str(x).lower()
                        in ["no binario", "nb", "otro", "other", "non-binary"]
                        else (
                            "Sin especificar"
                            if pd.isna(x) or str(x).lower() in ["nan", "", "none"]
                            else x
                        )
                    )
                )
            )
        )

    # El resto del código original de la función...

    # Buscar columnas similares a las que necesitamos
    column_map = {}
    required_columns = [
        "Grupo_Edad",
        "Sexo",
        "Genero",  # Añadir Genero como columna requerida
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
        df = df.rename(columns=column_map)

    # Crear columnas faltantes con valores predeterminados
    for req_col in required_columns:
        if req_col not in df.columns:
            # Asegurarse de que todas las columnas estén como tipo objeto para evitar problemas con categorical
            for col in df.columns:
                if pd.api.types.is_categorical_dtype(df[col]):
                    df[col] = df[col].astype(str)

            # Crear la columna con valor predeterminado
            df[req_col] = "Sin especificar"

            # Caso especial para Grupo_Edad si tenemos Edad_Vacunacion
            if req_col == "Grupo_Edad" and "Edad_Vacunacion" in df.columns:
                # Primero asegurarse de que Edad_Vacunacion no sea categórica
                if pd.api.types.is_categorical_dtype(df["Edad_Vacunacion"]):
                    df["Edad_Vacunacion"] = df["Edad_Vacunacion"].astype(str)

                try:
                    # Convertir a valores numéricos, forzando NaN en caso de error
                    edad_numerica = pd.to_numeric(
                        df["Edad_Vacunacion"], errors="coerce"
                    )

                    # Crear grupos de edad basados en valores numéricos
                    df[req_col] = edad_numerica.apply(
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
                                                                if pd.notna(x)
                                                                and x >= 80
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
                except Exception as e:
                    # En caso de error, mantener el valor predeterminado
                    df[req_col] = "Sin especificar"

    return df
