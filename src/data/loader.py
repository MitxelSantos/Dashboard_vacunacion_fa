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
    st.write("Inicio de carga de datos...")

    # Verificar archivos
    poblacion_file = DATA_DIR / "POBLACION.xlsx"
    vacunacion_file = DATA_DIR / "vacunacion_fa.csv"

    st.write(
        f"Verificando archivo {poblacion_file}... Existe: {poblacion_file.exists()}"
    )
    st.write(
        f"Verificando archivo {vacunacion_file}... Existe: {vacunacion_file.exists()}"
    )

    # Ahora intenta cargar
    st.write("Intentando cargar población...")
    municipios_df = pd.read_excel(poblacion_file, sheet_name="Poblacion")
    st.write(f"Población cargada: {len(municipios_df)} municipios")

    # Modificar esta parte para usar diferentes codificaciones
    st.write("Intentando cargar vacunación...")
    try:
        # Intento 1: UTF-8 (estándar)
        vacunacion_df = pd.read_csv(vacunacion_file, low_memory=False, encoding="utf-8")
    except UnicodeDecodeError:
        try:
            # Intento 2: Latin-1 (común en español)
            st.write("UTF-8 falló, intentando con Latin-1...")
            vacunacion_df = pd.read_csv(
                vacunacion_file, low_memory=False, encoding="latin-1"
            )
        except UnicodeDecodeError:
            try:
                # Intento 3: Windows CP1252 (muy común en Excel de Windows)
                st.write("Latin-1 falló, intentando con Windows CP1252...")
                vacunacion_df = pd.read_csv(
                    vacunacion_file, low_memory=False, encoding="cp1252"
                )
            except UnicodeDecodeError:
                # Intento 4: ISO-8859-1 (otra codificación común)
                st.write("CP1252 falló, intentando con ISO-8859-1...")
                vacunacion_df = pd.read_csv(
                    vacunacion_file, low_memory=False, encoding="iso-8859-1"
                )

    st.write(f"Vacunación cargada: {len(vacunacion_df)} registros")

    # Después de cargar vacunacion_df, añade:
    print("Columnas originales:", vacunacion_df.columns.tolist())

    # Normalizar DataFrame
    vacunacion_df = normalize_dataframe(vacunacion_df)

    print("Columnas normalizadas:", vacunacion_df.columns.tolist())

    st.write("Calculando métricas...")
    metricas_df = calculate_metrics(municipios_df, vacunacion_df)
    st.write("Carga completada exitosamente")

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

        # Normalizar quitando acentos y convirtiendo a minúsculas
        def normalize_text(text):
            import unicodedata

            # Normaliza quitando acentos
            text = (
                unicodedata.normalize("NFKD", text)
                .encode("ASCII", "ignore")
                .decode("ASCII")
            )
            # Convierte a minúsculas y quita espacios extra
            return text.lower().strip()

        # Aplicar normalización a los nombres de municipios
        vacunacion_df_clean["NombreMunicipioResidencia_norm"] = vacunacion_df_clean[
            "NombreMunicipioResidencia"
        ].apply(normalize_text)

        # Normalizar nombre de municipios en datos de población
        metricas_df["DPMP_norm"] = metricas_df["DPMP"].apply(normalize_text)

        # Imprimir nombres normalizados para diagnóstico
        print("Nombres de municipios normalizados en POBLACION.xlsx (primeros 10):")
        print(metricas_df["DPMP_norm"].head(10).tolist())

        print(
            "Nombres de municipios normalizados en vacunacion_fa.csv (muestra única):"
        )
        print(
            vacunacion_df_clean["NombreMunicipioResidencia_norm"].unique()[:10].tolist()
        )

        # CORREGIR NOMBRES ESPECÍFICOS DIRECTAMENTE
        # Mapeo de nombres alternativos
        name_mapping = {
            "san sebastian de mariquita": "mariquita",
            "armero guayabal": "armero",
        }

        # Aplicar mapeo a los nombres normalizados
        for alt_name, std_name in name_mapping.items():
            mask = vacunacion_df_clean["NombreMunicipioResidencia_norm"] == alt_name
            if mask.any():
                print(f"Encontrado '{alt_name}', reemplazando por '{std_name}'")
                vacunacion_df_clean.loc[mask, "NombreMunicipioResidencia_norm"] = (
                    std_name
                )

        # VERIFICACIÓN ADICIONAL - Buscar por coincidencia parcial
        print("BUSCAR POR COINCIDENCIA PARCIAL:")
        for name in vacunacion_df_clean["NombreMunicipioResidencia_norm"].unique():
            if "sebastian" in name or "mariquita" in name:
                print(f"En vacunación: '{name}'")

        for name in metricas_df["DPMP_norm"].unique():
            if "mariquita" in name:
                print(f"En población: '{name}'")

        # Contar vacunados por municipio (con nombres normalizados)
        vacunados_por_municipio = (
            vacunacion_df_clean.groupby("NombreMunicipioResidencia_norm")
            .size()
            .reset_index()
        )
        vacunados_por_municipio.columns = ["Municipio", "Vacunados"]

        # Diagnóstico de la fusión
        municipios_vacunacion = set(vacunados_por_municipio["Municipio"])
        municipios_poblacion = set(metricas_df["DPMP_norm"])
        comunes = municipios_vacunacion.intersection(municipios_poblacion)

        print(f"Municipios en vacunación: {len(municipios_vacunacion)}")
        print(f"Municipios en población: {len(municipios_poblacion)}")
        print(f"Municipios coincidentes: {len(comunes)}")

        # Imprimir municipios sin coincidencias
        municipios_solo_vacunacion = municipios_vacunacion - municipios_poblacion
        municipios_solo_poblacion = municipios_poblacion - municipios_vacunacion

        print(
            "Municipios solo en vacunación:", sorted(list(municipios_solo_vacunacion))
        )
        print("Municipios solo en población:", sorted(list(municipios_solo_poblacion)))

        # Fusionar con municipios normalizados
        metricas_df = pd.merge(
            metricas_df,
            vacunados_por_municipio,
            left_on="DPMP_norm",
            right_on="Municipio",
            how="left",
        )

        # Imprimir municipios sin coincidencias para diagnóstico
        print("Municipios sin coincidencias:")
        sin_coincidencias = metricas_df[metricas_df["Municipio"].isna()][
            "DPMP"
        ].tolist()
        print(sin_coincidencias)

        # Eliminar columna auxiliar
        metricas_df = metricas_df.drop(
            ["DPMP_norm", "Municipio"], axis=1, errors="ignore"
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
