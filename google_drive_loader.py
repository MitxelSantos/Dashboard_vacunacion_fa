"""
google_drive_loader.py - Carga con timeout agresivo para evitar cuelgues
"""

import streamlit as st
import pandas as pd
import requests
import io
from google.oauth2.service_account import Credentials
import threading
import time
from typing import Optional


class TimeoutException(Exception):
    pass


def download_with_timeout(url: str, headers: dict = None, timeout: int = 60) -> bytes:
    """Descarga con timeout estricto usando threading"""
    result = {"content": None, "error": None, "completed": False}

    def download_worker():
        try:
            response = requests.get(url, headers=headers, timeout=timeout, stream=True)
            response.raise_for_status()

            # Leer por chunks con timeout
            chunks = []
            start_time = time.time()

            for chunk in response.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
                if chunk:
                    chunks.append(chunk)

                # Verificar timeout total
                if time.time() - start_time > timeout:
                    raise TimeoutException(f"Download exceeded {timeout}s")

            result["content"] = b"".join(chunks)
            result["completed"] = True

        except Exception as e:
            result["error"] = str(e)
            result["completed"] = True

    # Ejecutar en thread separado
    thread = threading.Thread(target=download_worker)
    thread.daemon = True
    thread.start()

    # Esperar con progreso
    progress_bar = st.progress(0)
    status_text = st.empty()

    elapsed = 0
    while elapsed < timeout and not result["completed"]:
        progress = min(elapsed / timeout, 0.95)
        progress_bar.progress(progress)
        status_text.text(f"⏱️ Descargando... {elapsed}s/{timeout}s")

        time.sleep(1)
        elapsed += 1

    # Limpiar UI
    progress_bar.empty()
    status_text.empty()

    if not result["completed"]:
        raise TimeoutException(f"Download timeout after {timeout}s")

    if result["error"]:
        raise Exception(result["error"])

    return result["content"]


@st.cache_resource
def get_google_credentials():
    """Obtiene credenciales (cached)"""
    try:
        credentials_info = dict(st.secrets["gcp_service_account"])
        scopes = ["https://www.googleapis.com/auth/drive.readonly"]
        return Credentials.from_service_account_info(credentials_info, scopes=scopes)
    except Exception:
        return None


def load_file_with_aggressive_timeout(
    file_id: str, file_type: str = "csv", timeout: int = 90
) -> pd.DataFrame:
    """Carga archivo con timeout muy agresivo"""

    st.info(f"🔄 Cargando {file_type.upper()} (máximo {timeout}s)...")

    try:
        # Método 1: Intento autenticado
        credentials = get_google_credentials()
        if credentials:
            if credentials.expired:
                credentials.refresh(requests.Request())

            headers = {"Authorization": f"Bearer {credentials.token}"}
            url = f"https://drive.google.com/uc?id={file_id}&export=download"

            try:
                content = download_with_timeout(url, headers, timeout=timeout // 2)

                # Verificar que no es HTML
                if b"doctype html" in content.lower()[:1000]:
                    raise Exception("Got HTML instead of file")

                return process_content(content, file_type)

            except Exception as e:
                st.warning(f"⚠️ Método autenticado falló: {str(e)}")

        # Método 2: Público (ya sabemos que funciona para barridos)
        st.info("🌐 Intentando método público...")
        public_url = f"https://drive.google.com/uc?id={file_id}&export=download"

        content = download_with_timeout(public_url, timeout=timeout // 2)

        # Verificar contenido
        if b"doctype html" in content.lower()[:1000]:
            raise Exception("File not public or permission denied")

        return process_content(content, file_type)

    except Exception as e:
        st.error(f"❌ Error cargando {file_id}: {str(e)}")
        return pd.DataFrame()


def process_content(content: bytes, file_type: str) -> pd.DataFrame:
    """Procesa contenido descargado"""
    try:
        if file_type == "csv":
            # CSV optimizado
            content_str = content.decode("utf-8", errors="ignore")
            df = pd.read_csv(
                io.StringIO(content_str),
                sep=",",
                engine="c",
                low_memory=False,
                on_bad_lines="skip",
            )
        elif file_type == "xlsx":
            # Excel optimizado
            df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
        else:
            raise Exception(f"Unsupported file type: {file_type}")

        return df

    except Exception as e:
        raise Exception(f"Error processing {file_type}: {str(e)}")


# ============================================================================
# FUNCIONES PRINCIPALES CON TIMEOUT AGRESIVO
# ============================================================================


def load_vaccination_data() -> pd.DataFrame:
    """Carga vacunación con timeout agresivo"""
    try:
        file_id = st.secrets["google_drive"]["vacunacion_csv"]
        df = load_file_with_aggressive_timeout(file_id, "csv", timeout=120)

        # Procesar fechas
        if not df.empty:
            if "FA UNICA" in df.columns:
                df["FA UNICA"] = pd.to_datetime(df["FA UNICA"], errors="coerce")
            if "FechaNacimiento" in df.columns:
                df["FechaNacimiento"] = pd.to_datetime(
                    df["FechaNacimiento"], errors="coerce"
                )

        return df

    except Exception as e:
        st.error(f"❌ Error crítico cargando vacunación: {str(e)}")
        return pd.DataFrame()


def load_population_data() -> pd.DataFrame:
    """Carga población con timeout agresivo"""
    try:
        file_id = st.secrets["google_drive"]["poblacion_xlsx"]
        return load_file_with_aggressive_timeout(file_id, "xlsx", timeout=60)

    except Exception as e:
        st.error(f"❌ Error crítico cargando población: {str(e)}")
        return pd.DataFrame()


def load_barridos_data() -> pd.DataFrame:
    """Carga barridos con timeout agresivo - NO SE PUEDE COLGAR"""
    try:
        file_id = st.secrets["google_drive"].get("resumen_barridos_xlsx")

        if not file_id:
            st.warning("⚠️ ID de barridos no configurado")
            return pd.DataFrame()

        df = load_file_with_aggressive_timeout(file_id, "xlsx", timeout=90)

        # Procesar fechas
        if not df.empty and "FECHA" in df.columns:
            df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")

        return df

    except Exception as e:
        st.error(f"❌ Error crítico cargando barridos: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=7200, show_spinner=False)
def load_logo() -> Optional[bytes]:
    """Carga logo con timeout"""
    try:
        file_id = st.secrets["google_drive"]["logo_gobernacion"]
        credentials = get_google_credentials()

        if not credentials:
            return None

        if credentials.expired:
            credentials.refresh(requests.Request())

        headers = {"Authorization": f"Bearer {credentials.token}"}
        url = f"https://drive.google.com/uc?id={file_id}&export=download"

        # Timeout muy corto para logo
        content = download_with_timeout(url, headers, timeout=15)

        return io.BytesIO(content)

    except Exception:
        return None
