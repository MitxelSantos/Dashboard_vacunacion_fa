import pandas as pd
import numpy as np
from pathlib import Path
import streamlit as st
import os
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Directorio de datos
DATA_DIR = Path(__file__).parent.parent.parent / "data"
IMAGES_DIR = Path(__file__).parent.parent.parent / "assets" / "images"


def load_from_drive():
    """
    Descarga archivos de Google Drive usando la cuenta de servicio.
    """
    # Asegurar que las carpetas existan
    DATA_DIR.mkdir(exist_ok=True, parents=True)
    IMAGES_DIR.mkdir(exist_ok=True, parents=True)

    # Verificar si tenemos secretos configurados
    if "google_drive" in st.secrets and "gcp_service_account" in st.secrets:
        try:
            # Crear credenciales
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/drive.readonly"],
            )

            # Construir servicio de Drive
            drive_service = build("drive", "v3", credentials=credentials)

            # Descargar archivo de población
            if "poblacion_xlsx" in st.secrets["google_drive"]:
                poblacion_path = DATA_DIR / "POBLACION.xlsx"
                download_file(
                    drive_service,
                    st.secrets["google_drive"]["poblacion_xlsx"],
                    poblacion_path,
                )
                print(f"Descargado: {poblacion_path}")

            # Descargar archivo de vacunación
            if "vacunacion_csv" in st.secrets["google_drive"]:
                vacunacion_path = DATA_DIR / "vacunacion_fa.csv"
                download_file(
                    drive_service,
                    st.secrets["google_drive"]["vacunacion_csv"],
                    vacunacion_path,
                )
                print(f"Descargado: {vacunacion_path}")

            # Descargar logo
            if "logo_gobernacion" in st.secrets["google_drive"]:
                logo_path = IMAGES_DIR / "logo_gobernacion.png"
                download_file(
                    drive_service,
                    st.secrets["google_drive"]["logo_gobernacion"],
                    logo_path,
                )
                print(f"Descargado: {logo_path}")

            # Descargar imagen del mosquito
            if "mosquito_png" in st.secrets["google_drive"]:
                mosquito_path = IMAGES_DIR / "mosquito.png"
                download_file(
                    drive_service,
                    st.secrets["google_drive"]["mosquito_png"],
                    mosquito_path,
                )
                print(f"Descargado: {mosquito_path}")

            return True

        except Exception as e:
            st.warning(f"No se pudieron cargar archivos desde Google Drive: {str(e)}")
            print(f"Error cargando archivos de Drive: {str(e)}")
            return False
    else:
        print("No se encontraron secretos de Google Drive configurados")
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
            print(f"Descarga {int(status.progress() * 100)}%")
