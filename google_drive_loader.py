"""
google_drive_loader.py - VERSIÓN CORREGIDA
Basada en la arquitectura exitosa del segundo repositorio
"""

import streamlit as st
import pandas as pd
import io
import time
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Directorios
DATA_DIR = Path(__file__).parent / "data"
ASSETS_DIR = Path(__file__).parent / "assets"
IMAGES_DIR = ASSETS_DIR / "images"

# Asegurar que las carpetas existan
DATA_DIR.mkdir(exist_ok=True, parents=True)
ASSETS_DIR.mkdir(exist_ok=True, parents=True)
IMAGES_DIR.mkdir(exist_ok=True, parents=True)


def download_file_with_robust_timeout(
    drive_service, file_id, destination_path, timeout=1800
):
    """
    Descarga un archivo de Google Drive con manejo robusto para archivos grandes.
    Basado en la versión exitosa del segundo repositorio.
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

        # Para archivos grandes, usar chunks grandes
        if file_size > 200 * 1024 * 1024:  # > 200MB
            chunk_size = 50 * 1024 * 1024  # 50MB por chunk
        else:
            chunk_size = 20 * 1024 * 1024  # 20MB chunks

        # Crear request para descargar
        request = drive_service.files().get_media(fileId=file_id)

        with open(destination_path, "wb") as f:
            downloader = MediaIoBaseDownload(f, request, chunksize=chunk_size)
            done = False

            while not done:
                # Verificar tiempo de espera máximo
                if time.time() - start_time > timeout:
                    if destination_path.exists():
                        destination_path.unlink()  # Eliminar archivo parcial
                    return False

                try:
                    status, done = downloader.next_chunk()
                except Exception:
                    # Intentar continuar con el siguiente chunk
                    continue

        # Verificar resultado
        if destination_path.exists():
            downloaded_size = destination_path.stat().st_size
            # Permitir hasta 5% de diferencia
            if downloaded_size >= file_size * 0.95:
                return True
            else:
                return False
        else:
            return False

    except Exception:
        return False


def validate_secrets():
    """
    Valida que todos los secretos necesarios estén configurados.
    """
    # Verificar secretos básicos
    if "google_drive" not in st.secrets:
        return False, "Falta configuración 'google_drive' en secrets"

    if "gcp_service_account" not in st.secrets:
        return False, "Falta configuración 'gcp_service_account' en secrets"

    # Verificar IDs de archivos
    required_files = ["poblacion_xlsx", "vacunacion_csv", "logo_gobernacion"]
    missing_files = [f for f in required_files if f not in st.secrets["google_drive"]]

    if missing_files:
        return False, f"Faltan IDs de archivos en Google Drive: {missing_files}"

    return True, "Configuración válida"


def create_drive_service():
    """
    Crea el servicio de Google Drive con manejo de errores robusto.
    """
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
            return None

        return drive_service

    except Exception as e:
        st.error(f"Error creando servicio de Google Drive: {str(e)}")
        return None


def load_from_drive():
    """
    Descarga archivos de Google Drive usando la arquitectura exitosa.
    """
    # Validar secretos primero
    valid, message = validate_secrets()
    if not valid:
        st.warning(f"⚠️ Configuración de Google Drive: {message}")
        return False

    # Crear servicio
    drive_service = create_drive_service()
    if drive_service is None:
        st.error("❌ No se pudo conectar a Google Drive")
        return False

    success_count = 0
    total_files = 3

    # Lista de archivos a descargar
    files_to_download = [
        {
            "key": "poblacion_xlsx",
            "path": DATA_DIR / "POBLACION.xlsx",
            "name": "Población",
        },
        {
            "key": "vacunacion_csv",
            "path": DATA_DIR / "vacunacion_fa.csv",
            "name": "Vacunación",
        },
        {
            "key": "logo_gobernacion",
            "path": IMAGES_DIR / "logo_gobernacion.png",
            "name": "Logo",
        },
    ]

    # Barra de progreso
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, file_info in enumerate(files_to_download):
        status_text.text(f"Descargando {file_info['name']}...")

        try:
            file_id = st.secrets["google_drive"][file_info["key"]]

            # Verificar que el archivo existe en Drive
            drive_service.files().get(
                fileId=file_id, fields="name,size,mimeType"
            ).execute()

            # Descargar archivo
            success = download_file_with_robust_timeout(
                drive_service,
                file_id,
                file_info["path"],
                timeout=1800,  # 30 minutos timeout
            )

            if success:
                success_count += 1
                st.success(f"✅ {file_info['name']} descargado exitosamente")
            else:
                st.error(f"❌ Error descargando {file_info['name']}")

        except Exception as e:
            st.error(f"❌ Error con {file_info['name']}: {str(e)}")

        # Actualizar progreso
        progress_bar.progress((i + 1) / total_files)

    # Limpiar UI
    progress_bar.empty()
    status_text.empty()

    # Verificar archivos críticos
    required_files_paths = [
        DATA_DIR / "POBLACION.xlsx",
        DATA_DIR / "vacunacion_fa.csv",
    ]

    missing_critical = [str(path) for path in required_files_paths if not path.exists()]

    if missing_critical:
        st.error(f"❌ Archivos críticos faltantes: {missing_critical}")
        return False

    st.success(f"✅ Descarga completada: {success_count}/{total_files} archivos")
    return success_count >= 2  # Al menos población y vacunación


# Funciones específicas para cada tipo de archivo
def load_vaccination_data() -> pd.DataFrame:
    """Carga datos de vacunación con fallback robusto"""
    try:
        file_path = DATA_DIR / "vacunacion_fa.csv"

        # Si no existe, intentar descargar
        if not file_path.exists():
            if load_from_drive():
                pass  # Archivo descargado
            else:
                return pd.DataFrame()

        # Cargar archivo con optimizaciones
        if file_path.exists():
            df = pd.read_csv(
                file_path, low_memory=False, encoding="utf-8", on_bad_lines="skip"
            )

            # Procesar fechas
            if "FA UNICA" in df.columns:
                df["FA UNICA"] = pd.to_datetime(df["FA UNICA"], errors="coerce")
            if "FechaNacimiento" in df.columns:
                df["FechaNacimiento"] = pd.to_datetime(
                    df["FechaNacimiento"], errors="coerce"
                )

            return df

        return pd.DataFrame()

    except Exception as e:
        st.error(f"❌ Error cargando datos de vacunación: {str(e)}")
        return pd.DataFrame()


def load_population_data() -> pd.DataFrame:
    """Carga datos de población con fallback robusto"""
    try:
        file_path = DATA_DIR / "POBLACION.xlsx"

        # Si no existe, intentar descargar
        if not file_path.exists():
            if load_from_drive():
                pass  # Archivo descargado
            else:
                return pd.DataFrame()

        # Cargar archivo
        if file_path.exists():
            # Intentar diferentes hojas
            try:
                df = pd.read_excel(file_path, sheet_name="Poblacion")
            except:
                df = pd.read_excel(file_path, sheet_name=0)

            return df

        return pd.DataFrame()

    except Exception as e:
        st.error(f"❌ Error cargando datos de población: {str(e)}")
        return pd.DataFrame()


def load_barridos_data() -> pd.DataFrame:
    """Carga datos de barridos con fallback robusto"""
    try:
        file_path = DATA_DIR / "Resumen.xlsx"

        # Si no existe, intentar descargar
        if not file_path.exists():
            if load_from_drive():
                pass  # Archivo descargado
            else:
                return pd.DataFrame()

        # Cargar archivo
        if file_path.exists():
            # Intentar diferentes hojas
            try:
                df = pd.read_excel(file_path, sheet_name="Vacunacion")
            except:
                try:
                    df = pd.read_excel(file_path, sheet_name="Barridos")
                except:
                    df = pd.read_excel(file_path, sheet_name=0)

            # Procesar fechas
            if "FECHA" in df.columns:
                df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")

            return df

        return pd.DataFrame()

    except Exception as e:
        st.error(f"❌ Error cargando datos de barridos: {str(e)}")
        return pd.DataFrame()


def load_logo():
    """Carga logo con manejo de errores"""
    try:
        logo_path = IMAGES_DIR / "logo_gobernacion.png"

        if not logo_path.exists():
            load_from_drive()

        if logo_path.exists():
            return str(logo_path)

        return None

    except Exception:
        return None
