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


def download_file_with_timeout(
    drive_service, file_id, destination_path, timeout=300
):  # Aumentar timeout
    """
    Descarga un archivo de Google Drive con tiempo de espera máximo.
    """
    try:
        start_time = time.time()

        # Obtener información del archivo
        file_info = (
            drive_service.files().get(fileId=file_id, fields="size,name").execute()
        )
        file_size = int(file_info.get("size", 0))
        file_name = file_info.get("name", "Desconocido")

        st.write(f"Descargando {file_name} ({file_size/1024/1024:.2f} MB)...")

        # Para archivos muy grandes, descargar en chunks
        if file_size > 100 * 1024 * 1024:  # Más de 100MB
            st.warning(
                f"⚠️ El archivo {file_name} es muy grande ({file_size/1024/1024:.2f} MB)"
            )

        request = drive_service.files().get_media(fileId=file_id)

        # Asegurar que el directorio existe
        destination_path.parent.mkdir(exist_ok=True, parents=True)

        with open(destination_path, "wb") as f:
            downloader = MediaIoBaseDownload(
                f, request, chunksize=10 * 1024 * 1024
            )  # 10MB chunks
            done = False
            while not done:
                # Verificar tiempo de espera
                if time.time() - start_time > timeout:
                    st.error(f"⏱️ Tiempo de espera excedido al descargar {file_name}")
                    return False

                status, done = downloader.next_chunk()
                st.write(f"Progreso: {int(status.progress() * 100)}%")

        # Verificar que el archivo se descargó completo
        if destination_path.exists():
            downloaded_size = destination_path.stat().st_size
            st.success(f"✅ Archivo descargado: {downloaded_size/1024/1024:.2f} MB")

            # Verificar integridad
            if (
                downloaded_size < file_size * 0.9
            ):  # Si es menos del 90% del tamaño esperado
                st.warning(
                    f"⚠️ El archivo descargado parece incompleto: {downloaded_size} bytes vs {file_size} bytes esperados"
                )

        return destination_path.exists()
    except Exception as e:
        st.error(f"❌ Error al descargar {file_id}: {str(e)}")
        import traceback

        st.text(traceback.format_exc())
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

    # Verificar si tenemos secretos configurados
    if "google_drive" not in st.secrets:
        st.error("❌ No se encontró la configuración de Google Drive en los secretos")
        return False

    if "gcp_service_account" not in st.secrets:
        st.error(
            "❌ No se encontró la configuración de GCP Service Account en los secretos"
        )
        return False

    try:
        st.info("📥 Iniciando descarga de archivos desde Google Drive...")

        # Verificar que los IDs de archivos estén configurados
        required_files = ["poblacion_xlsx", "vacunacion_csv", "logo_gobernacion"]
        missing_files = [
            f for f in required_files if f not in st.secrets["google_drive"]
        ]

        if missing_files:
            st.error(
                f"❌ Faltan IDs de archivos en la configuración: {', '.join(missing_files)}"
            )
            return False

        # Crear credenciales
        try:
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/drive.readonly"],
            )
            st.success("✅ Credenciales de servicio creadas correctamente")
        except Exception as e:
            st.error(f"❌ Error al crear credenciales de servicio: {str(e)}")
            st.write(
                "Detalles:",
                st.secrets["gcp_service_account"].get("client_email", "N/A"),
            )
            return False

        # Construir servicio de Drive
        try:
            drive_service = build("drive", "v3", credentials=credentials)

            # Verificar conexión - intentar listar archivos
            response = drive_service.files().list(pageSize=1).execute()
            if "files" in response:
                st.success("✅ Conexión exitosa con Google Drive API")
            else:
                st.error("❌ Error al conectar con Google Drive: Respuesta inválida")
                return False

        except Exception as e:
            st.error(f"❌ Error al construir servicio de Drive: {str(e)}")
            return False

        # Descargar archivo de población
        if "poblacion_xlsx" in st.secrets["google_drive"]:
            poblacion_path = DATA_DIR / "POBLACION.xlsx"
            file_id = st.secrets["google_drive"]["poblacion_xlsx"]

            st.write(f"📄 Descargando archivo de población... (ID: {file_id})")
            try:
                request = (
                    drive_service.files()
                    .get(fileId=file_id, fields="name,size,mimeType")
                    .execute()
                )
                st.write(
                    f"Información del archivo: {request.get('name')} ({request.get('mimeType')})"
                )

                result = download_file_with_timeout(
                    drive_service,
                    file_id,
                    poblacion_path,
                )

                if result and poblacion_path.exists():
                    st.success(
                        f"✅ Archivo de población descargado correctamente ({poblacion_path.stat().st_size} bytes)"
                    )
                else:
                    st.error(f"❌ No se pudo descargar el archivo de población")
            except Exception as e:
                st.error(f"❌ Error al descargar archivo de población: {str(e)}")

        # Descargar archivo de vacunación
        if "vacunacion_csv" in st.secrets["google_drive"]:
            vacunacion_path = DATA_DIR / "vacunacion_fa.csv"
            file_id = st.secrets["google_drive"]["vacunacion_csv"]

            st.write(f"📄 Descargando archivo de vacunación... (ID: {file_id})")
            try:
                request = (
                    drive_service.files()
                    .get(fileId=file_id, fields="name,size,mimeType")
                    .execute()
                )
                st.write(
                    f"Información del archivo: {request.get('name')} ({request.get('mimeType')})"
                )

                result = download_file_with_timeout(
                    drive_service,
                    file_id,
                    vacunacion_path,
                )

                if result and vacunacion_path.exists():
                    st.success(
                        f"✅ Archivo de vacunación descargado correctamente ({vacunacion_path.stat().st_size} bytes)"
                    )
                else:
                    st.error(f"❌ No se pudo descargar el archivo de vacunación")
            except Exception as e:
                st.error(f"❌ Error al descargar archivo de vacunación: {str(e)}")

        # Descargar logo
        if "logo_gobernacion" in st.secrets["google_drive"]:
            logo_path = IMAGES_DIR / "logo_gobernacion.png"
            file_id = st.secrets["google_drive"]["logo_gobernacion"]

            st.write(f"🖼️ Descargando logo... (ID: {file_id})")
            try:
                request = (
                    drive_service.files()
                    .get(fileId=file_id, fields="name,size,mimeType")
                    .execute()
                )
                st.write(
                    f"Información del archivo: {request.get('name')} ({request.get('mimeType')})"
                )

                result = download_file_with_timeout(
                    drive_service,
                    file_id,
                    logo_path,
                )

                if result and logo_path.exists():
                    st.success(
                        f"✅ Logo descargado correctamente ({logo_path.stat().st_size} bytes)"
                    )
                else:
                    st.error(f"❌ No se pudo descargar el logo")
            except Exception as e:
                st.error(f"❌ Error al descargar logo: {str(e)}")

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
            st.error(
                f"❌ Faltan archivos después de la descarga: {', '.join(missing_files)}"
            )
            return False

        st.success("✅ Todos los archivos fueron descargados exitosamente")
        return True

    except Exception as e:
        import traceback

        st.error(f"❌ Error general al cargar desde Google Drive: {str(e)}")
        st.error(traceback.format_exc())
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
