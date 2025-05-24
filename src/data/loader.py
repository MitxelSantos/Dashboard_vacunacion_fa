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


def normalize_gender_comprehensive(value):
    """
    Normaliza los valores de género de manera comprehensiva
    """
    if pd.isna(value) or str(value).lower().strip() in [
        "nan",
        "",
        "none",
        "null",
        "na",
    ]:
        return "Sin dato"

    value_str = str(value).lower().strip()

    if value_str in ["masculino", "m", "masc", "hombre", "h", "male", "1"]:
        return "Masculino"
    elif value_str in ["femenino", "f", "fem", "mujer", "female", "2"]:
        return "Femenino"
    else:
        # Todas las demás clasificaciones van a "No Binario"
        return "No Binario"


def comprehensive_nan_normalization(df):
    """
    Normaliza todos los valores NaN/vacíos a "Sin dato" de manera comprehensiva
    """
    df_clean = df.copy()

    # Lista de columnas categóricas comunes que deben ser normalizadas
    categorical_columns = [
        "GrupoEtnico",
        "RegimenAfiliacion",
        "NombreAseguradora",
        "NombreMunicipioResidencia",
        "NombreDptoResidencia",
        "Desplazado",
        "Discapacitado",
        "TipoIdentificacion",
        "PrimerNombre",
        "PrimerApellido",
        "NombreMunicipioNacimiento",
        "NombreDptoNacimiento",
    ]

    # Identificar columnas categóricas existentes
    existing_categorical = [
        col for col in categorical_columns if col in df_clean.columns
    ]

    # También incluir columnas de tipo object que no estén en la lista
    object_columns = df_clean.select_dtypes(
        include=["object", "string"]
    ).columns.tolist()
    all_columns_to_clean = list(set(existing_categorical + object_columns))

    # Excluir columnas numéricas importantes y fechas
    exclude_columns = ["Documento", "Edad_Vacunacion", "FA UNICA", "FechaNacimiento"]
    columns_to_clean = [
        col for col in all_columns_to_clean if col not in exclude_columns
    ]

    # Normalizar cada columna
    for col in columns_to_clean:
        if col in df_clean.columns:
            # Convertir a string si es categórica
            if pd.api.types.is_categorical_dtype(df_clean[col]):
                df_clean[col] = df_clean[col].astype(str)

            # Reemplazar diversos tipos de valores vacíos/nulos
            df_clean[col] = df_clean[col].fillna("Sin dato")
            df_clean[col] = df_clean[col].replace(
                ["", "nan", "NaN", "null", "NULL", "None", "NONE", "na", "NA", "#N/A"],
                "Sin dato",
            )

            # Limpiar espacios en blanco que podrían considerarse como vacíos
            df_clean[col] = df_clean[col].apply(
                lambda x: "Sin dato" if str(x).strip() == "" else str(x).strip()
            )

    return df_clean


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


# @st.cache_data(ttl=3600)
def load_datasets():
    """
    Carga los datasets necesarios para la aplicación.
    VERSIÓN MEJORADA: Incluye normalización comprehensiva de datos y normalización de EAPB.
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
                "PrimerNombre",
                "PrimerApellido",
                "Sexo",
                "FechaNacimiento",
                "NombreMunicipioResidencia",
                "NombreDptoResidencia",
                "GrupoEtnico",
                "Desplazado",
                "Discapacitado",
                "RegimenAfiliacion",
                "NombreAseguradora",
                "FA UNICA",
                "Edad_Vacunacion",
            ]

            # Primero leer solo unas pocas líneas para ver la estructura
            temp_df = pd.read_csv(vacunacion_file, nrows=5)
            available_columns = temp_df.columns.tolist()

            # Crear lista de columnas que efectivamente existen
            use_columns = [col for col in required_columns if col in available_columns]

            # Preparar diccionario de dtypes optimizados
            dtypes = {
                "IdPaciente": "str",
                "TipoIdentificacion": "category",
                "Documento": "str",
                "PrimerNombre": "str",
                "PrimerApellido": "str",
                "Sexo": "category",
                "GrupoEtnico": "category",
                "RegimenAfiliacion": "category",
                "NombreAseguradora": "category",
                "NombreMunicipioResidencia": "category",
                "NombreDptoResidencia": "category",
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

        # =====================================================================
        # NORMALIZACIÓN COMPREHENSIVA DE DATOS
        # =====================================================================

        # 1. Normalizar valores NaN/vacíos a "Sin dato"
        vacunacion_df = comprehensive_nan_normalization(vacunacion_df)

        # 2. Normalizar DataFrame con funciones mejoradas
        vacunacion_df = normalize_dataframe_improved(vacunacion_df)

        # =====================================================================
        # NUEVA SECCIÓN: NORMALIZACIÓN DE EAPB
        # =====================================================================
        try:
            print("🔧 Aplicando normalización de EAPB...")
            from .eapb_normalizer import normalize_eapb_names
            from .eapb_mappings import ALL_EAPB_MAPPINGS

            # Aplicar normalización de EAPB
            vacunacion_df = normalize_eapb_names(
                vacunacion_df,
                "NombreAseguradora",
                ALL_EAPB_MAPPINGS,
                create_backup=True,  # Crear respaldo para auditoría
            )

            print("✅ Normalización de EAPB completada exitosamente")

        except ImportError:
            print(
                "⚠️ Módulo de normalización EAPB no disponible - continuando sin normalización"
            )
        except Exception as e:
            print(
                f"⚠️ Error en normalización EAPB: {str(e)} - continuando sin normalización"
            )

        # =====================================================================
        # CALCULAR MÉTRICAS
        # =====================================================================
        # 3. Calcular métricas
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


def normalize_dataframe_improved(df):
    """
    Normaliza los nombres de las columnas y añade columnas faltantes.
    VERSIÓN MEJORADA: Implementa normalización comprehensiva de géneros y manejo de "Sin dato".
    """
    # Limpiar nombres de columnas (quitar espacios y caracteres invisibles)
    df.columns = [col.strip() for col in df.columns]

    # =====================================================================
    # NORMALIZACIÓN DE GÉNEROS
    # =====================================================================
    # Manejar columnas de género/sexo
    gender_columns = ["Sexo", "Genero"]
    gender_col_found = None

    for col in gender_columns:
        if col in df.columns:
            gender_col_found = col
            break

    if gender_col_found:
        # Aplicar normalización comprehensiva de géneros
        df[gender_col_found] = df[gender_col_found].apply(
            normalize_gender_comprehensive
        )

        # Si encontramos Sexo pero no Genero, crear Genero
        if gender_col_found == "Sexo" and "Genero" not in df.columns:
            df["Genero"] = df["Sexo"].copy()
    else:
        # Si no existe ninguna columna de género, crear una
        df["Sexo"] = "Sin dato"
        df["Genero"] = "Sin dato"

    # =====================================================================
    # BÚSQUEDA Y NORMALIZACIÓN DE COLUMNAS
    # =====================================================================
    # Buscar columnas similares a las que necesitamos
    column_map = {}
    required_columns = [
        "Grupo_Edad",
        "Sexo",
        "Genero",
        "GrupoEtnico",
        "RegimenAfiliacion",
        "NombreAseguradora",
        "FA UNICA",
        "NombreMunicipioResidencia",
        "Desplazado",
        "Discapacitado",
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

    # =====================================================================
    # CREACIÓN DE COLUMNAS FALTANTES
    # =====================================================================
    # Crear columnas faltantes con valores predeterminados
    for req_col in required_columns:
        if req_col not in df.columns:
            # Asegurarse de que todas las columnas estén como tipo objeto para evitar problemas con categorical
            for col in df.columns:
                if pd.api.types.is_categorical_dtype(df[col]):
                    df[col] = df[col].astype(str)

            # Crear la columna con valor predeterminado
            df[req_col] = "Sin dato"

            # =====================================================================
            # CASO ESPECIAL: GRUPO_EDAD
            # =====================================================================
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
                    def categorize_age(age):
                        """
                        Categoriza la edad en grupos estándar actualizados
                        Rangos: Menor de 1 año, 1 a 4 años, 5 a 9 años, 10 a 19 años,
                            20 a 29 años, 30 a 39 años, 40 a 49 años, 50 a 59 años,
                            60 a 69 años, 70 años o más
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

                    df[req_col] = edad_numerica.apply(categorize_age)

                except Exception as e:
                    # En caso de error, mantener el valor predeterminado
                    df[req_col] = "Sin dato"

    # =====================================================================
    # NORMALIZACIÓN FINAL DE VALORES BOOLEANOS
    # =====================================================================
    # Normalizar columnas booleanas especiales
    boolean_columns = ["Desplazado", "Discapacitado"]
    for col in boolean_columns:
        if col in df.columns:
            # Convertir valores booleanos y strings a formato estándar
            def normalize_boolean(value):
                if pd.isna(value) or str(value).lower().strip() in [
                    "nan",
                    "",
                    "none",
                    "null",
                    "na",
                ]:
                    return "Sin dato"

                value_str = str(value).lower().strip()
                if value_str in ["true", "1", "si", "sí", "yes", "y"]:
                    return "Sí"
                elif value_str in ["false", "0", "no", "n"]:
                    return "No"
                else:
                    return "Sin dato"

            df[col] = df[col].apply(normalize_boolean)

    return df
