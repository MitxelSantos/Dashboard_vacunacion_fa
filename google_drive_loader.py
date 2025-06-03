"""
google_drive_loader.py - Cargador silencioso y optimizado para Google Drive
Versión limpia sin mensajes de diagnóstico
"""

import streamlit as st
import pandas as pd
import requests
import io
from google.oauth2.service_account import Credentials
import chardet


def get_google_credentials():
    """Obtiene credenciales de Google desde secrets"""
    try:
        credentials_info = dict(st.secrets["gcp_service_account"])
        scopes = [
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/spreadsheets.readonly",
        ]
        credentials = Credentials.from_service_account_info(
            credentials_info, scopes=scopes
        )
        return credentials
    except Exception:
        return None


def detect_csv_params(content_bytes):
    """Detecta parámetros óptimos para leer CSV"""
    try:
        detected = chardet.detect(content_bytes)
        encoding = detected.get("encoding", "utf-8")
        content_str = content_bytes.decode(encoding, errors="ignore")

        if "doctype html" in content_str.lower() or "<html" in content_str.lower():
            raise Exception("HTML content detected")

        lines = content_str.split("\n")[:10]
        separators = [",", ";", "\t", "|"]
        separator_scores = {}

        for sep in separators:
            counts = [line.count(sep) for line in lines[:5] if line.strip()]
            if counts:
                avg_count = sum(counts) / len(counts)
                consistency = 1.0 - (max(counts) - min(counts)) / (max(counts) + 1)
                separator_scores[sep] = avg_count * consistency
            else:
                separator_scores[sep] = 0

        best_separator = max(separator_scores, key=separator_scores.get)
        if separator_scores[best_separator] < 5:
            best_separator = ","

        return {
            "encoding": encoding,
            "separator": best_separator,
            "content": content_str,
        }

    except Exception:
        return {
            "encoding": "utf-8",
            "separator": ",",
            "content": content_bytes.decode("utf-8", errors="ignore"),
        }


def load_csv_robust(content_bytes, file_id):
    """Carga CSV con múltiples estrategias - SILENCIOSO"""
    csv_params = detect_csv_params(content_bytes)
    content_str = csv_params["content"]
    encoding = csv_params["encoding"]
    separator = csv_params["separator"]

    # Estrategias optimizadas (menos intentos)
    strategies = [
        # Estrategia 1: Coma estándar (más probable)
        {
            "params": {
                "sep": ",",
                "encoding": encoding,
                "on_bad_lines": "skip",
                "low_memory": False,
                "engine": "c",
            }
        },
        # Estrategia 2: Motor Python tolerante
        {
            "params": {
                "sep": ",",
                "encoding": encoding,
                "engine": "python",
                "on_bad_lines": "skip",
                "low_memory": False,
            }
        },
    ]

    for strategy in strategies:
        try:
            df = pd.read_csv(io.StringIO(content_str), **strategy["params"])

            if not df.empty and len(df.columns) > 5:
                return df

        except Exception:
            continue

    return pd.DataFrame()


def load_file_public_fallback(file_id, file_type="csv"):
    """Método público silencioso"""
    try:
        public_url = f"https://drive.google.com/uc?id={file_id}&export=download"
        response = requests.get(public_url, timeout=120)
        response.raise_for_status()

        content_preview = response.text[:200].lower()
        if "doctype html" in content_preview or "<html" in content_preview:
            return pd.DataFrame()

        if file_type == "csv":
            return load_csv_robust(response.content, file_id)
        elif file_type == "xlsx":
            return pd.read_excel(io.BytesIO(response.content))

    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=1800, show_spinner=False)
def load_file_from_drive_robust(file_id, file_type="csv"):
    """Carga archivo desde Google Drive - SILENCIOSO"""
    try:
        credentials = get_google_credentials()
        if not credentials:
            return pd.DataFrame()

        if credentials.expired:
            credentials.refresh(requests.Request())

        headers = {"Authorization": f"Bearer {credentials.token}"}
        download_url = f"https://drive.google.com/uc?id={file_id}&export=download"

        response = requests.get(download_url, headers=headers, timeout=120)
        response.raise_for_status()

        content_preview = response.text[:200].lower()
        if "doctype html" in content_preview or "<html" in content_preview:
            return load_file_public_fallback(file_id, file_type)

        if file_type == "csv":
            return load_csv_robust(response.content, file_id)
        elif file_type == "xlsx":
            return pd.read_excel(io.BytesIO(response.content), engine="openpyxl")
        else:
            return pd.DataFrame()

    except Exception:
        return load_file_public_fallback(file_id, file_type)


# ============================================================================
# FUNCIONES PRINCIPALES - SILENCIOSAS
# ============================================================================


def load_vaccination_data():
    """Carga datos de vacunación histórica - SILENCIOSO"""
    try:
        file_id = st.secrets["google_drive"]["vacunacion_csv"]
        df = load_file_from_drive_robust(file_id, "csv")

        if not df.empty:
            # Procesar fechas silenciosamente
            if "FA UNICA" in df.columns:
                df["FA UNICA"] = pd.to_datetime(df["FA UNICA"], errors="coerce")
            if "FechaNacimiento" in df.columns:
                df["FechaNacimiento"] = pd.to_datetime(
                    df["FechaNacimiento"], errors="coerce"
                )

        return df
    except Exception:
        return pd.DataFrame()


def load_population_data():
    """Carga datos de población - SILENCIOSO"""
    try:
        file_id = st.secrets["google_drive"]["poblacion_xlsx"]
        df = load_file_from_drive_robust(file_id, "xlsx")
        return df
    except Exception:
        return pd.DataFrame()


def load_barridos_data():
    """Carga datos de barridos - SILENCIOSO"""
    try:
        file_id = st.secrets["google_drive"].get("resumen_barridos_xlsx")
        if not file_id:
            return pd.DataFrame()

        df = load_file_from_drive_robust(file_id, "xlsx")

        if not df.empty and "FECHA" in df.columns:
            df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")

        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def load_logo():
    """Carga logo desde Google Drive - SILENCIOSO"""
    try:
        file_id = st.secrets["google_drive"]["logo_gobernacion"]
        credentials = get_google_credentials()

        if not credentials:
            return None

        if credentials.expired:
            credentials.refresh(requests.Request())

        headers = {"Authorization": f"Bearer {credentials.token}"}
        download_url = f"https://drive.google.com/uc?id={file_id}&export=download"

        response = requests.get(download_url, headers=headers, timeout=15)
        response.raise_for_status()

        if response.headers.get("content-type", "").startswith("text/html"):
            return None

        return io.BytesIO(response.content)

    except Exception:
        return None
