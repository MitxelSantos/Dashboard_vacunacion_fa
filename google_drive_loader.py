"""
google_drive_loader.py - Carga de datos desde Google Drive
VERSIÓN CORREGIDA - Compatible con la configuración de secretos actual
"""

import streamlit as st
import pandas as pd
import os
import tempfile
import requests
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_secrets():
    """
    Valida que los secretos de Google Drive estén configurados correctamente
    """
    try:
        # IDs de archivos en Google Drive (nombres actualizados)
        file_ids = {
            "vacunacion_csv": st.secrets.get("google_drive", {}).get("vacunacion_csv"),
            "resumen_barridos_xlsx": st.secrets.get("google_drive", {}).get(
                "resumen_barridos_xlsx"
            ),
            "poblacion_xlsx": st.secrets.get("google_drive", {}).get(
                "poblacion_xlsx"
            ),  # OPCIONAL
            "logo_gobernacion": st.secrets.get("google_drive", {}).get(
                "logo_gobernacion"
            ),  # OPCIONAL
        }

        # Verificar que al menos los archivos críticos estén configurados
        critical_files = ["vacunacion_csv", "resumen_barridos_xlsx"]
        missing_critical = [key for key in critical_files if not file_ids.get(key)]

        if missing_critical:
            return False, f"Faltan IDs críticos: {missing_critical}"

        # Verificar opcional
        optional_files = ["poblacion_xlsx", "logo_gobernacion"]
        missing_optional = [key for key in optional_files if not file_ids.get(key)]

        if missing_optional:
            logger.info(f"Archivos opcionales no configurados: {missing_optional}")

        return True, "Configuración de Google Drive válida"

    except Exception as e:
        return False, f"Error validando secretos: {str(e)}"


def download_from_drive(file_id, file_name, target_dir="temp"):
    """
    Descarga un archivo específico desde Google Drive usando su ID
    """
    try:
        if not file_id:
            logger.warning(f"No se proporcionó ID para {file_name}")
            return None

        # URL de descarga directa de Google Drive
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"

        # Crear directorio temporal si no existe
        temp_dir = Path(target_dir)
        temp_dir.mkdir(exist_ok=True)

        # Ruta de destino
        target_path = temp_dir / file_name

        logger.info(f"Descargando {file_name} desde Google Drive...")

        # Realizar la descarga
        response = requests.get(download_url, timeout=30)
        response.raise_for_status()

        # Guardar archivo
        with open(target_path, "wb") as f:
            f.write(response.content)

        logger.info(f"Archivo descargado exitosamente: {target_path}")
        return str(target_path)

    except requests.RequestException as e:
        logger.error(f"Error de red descargando {file_name}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error descargando {file_name}: {str(e)}")
        return None


def load_vaccination_data():
    """
    Carga datos históricos de vacunación individual desde Google Drive
    """
    try:
        # Obtener ID del archivo (nombre actualizado)
        file_id = st.secrets.get("google_drive", {}).get("vacunacion_csv")

        if not file_id:
            logger.error("ID de archivo de vacunación no configurado")
            return pd.DataFrame()

        # Descargar archivo
        file_path = download_from_drive(file_id, "vacunacion_fa.csv")

        if not file_path or not Path(file_path).exists():
            logger.error("No se pudo descargar el archivo de vacunación")
            return pd.DataFrame()

        # Cargar CSV
        df = pd.read_csv(
            file_path, low_memory=False, encoding="utf-8", on_bad_lines="skip"
        )

        logger.info(f"Datos de vacunación cargados: {len(df):,} registros")

        # Validaciones básicas
        required_columns = ["FA UNICA", "NombreMunicipioResidencia"]
        missing_cols = [col for col in required_columns if col not in df.columns]

        if missing_cols:
            logger.warning(f"Columnas faltantes en vacunación: {missing_cols}")

        # Verificar columna crítica para cálculo de edad
        if "FechaNacimiento" not in df.columns:
            logger.warning(
                "Columna FechaNacimiento no encontrada - edad no se podrá calcular"
            )

        return df

    except Exception as e:
        logger.error(f"Error cargando datos de vacunación: {str(e)}")
        return pd.DataFrame()


def load_barridos_data():
    """
    Carga datos de barridos territoriales desde Google Drive
    """
    try:
        # Obtener ID del archivo (nombre actualizado)
        file_id = st.secrets.get("google_drive", {}).get("resumen_barridos_xlsx")

        if not file_id:
            logger.error("ID de archivo de barridos no configurado")
            return pd.DataFrame()

        # Descargar archivo
        file_path = download_from_drive(file_id, "Resumen.xlsx")

        if not file_path or not Path(file_path).exists():
            logger.error("No se pudo descargar el archivo de barridos")
            return pd.DataFrame()

        # Intentar cargar desde diferentes hojas
        sheet_names = ["Barridos", "Vacunacion", 0]
        df = None

        for sheet in sheet_names:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet)
                logger.info(
                    f"Datos de barridos cargados desde hoja '{sheet}': {len(df):,} registros"
                )
                break
            except Exception as e:
                logger.warning(f"No se pudo leer hoja '{sheet}': {str(e)}")
                continue

        if df is None:
            logger.error("No se pudo leer ninguna hoja del archivo de barridos")
            return pd.DataFrame()

        # Validaciones básicas para rangos de edad
        expected_age_patterns = [
            "<1",
            "1-5",
            "6-10",
            "11-20",
            "21-30",
            "31-40",
            "41-50",
            "51-59",
            "60",
        ]
        age_columns_found = []

        for col in df.columns:
            col_str = str(col).upper()
            for pattern in expected_age_patterns:
                if pattern in col_str:
                    age_columns_found.append(col)
                    break

        logger.info(
            f"Columnas de edad encontradas en barridos: {len(age_columns_found)}"
        )

        if len(age_columns_found) == 0:
            logger.warning("No se encontraron columnas de rangos de edad en barridos")

        return df

    except Exception as e:
        logger.error(f"Error cargando datos de barridos: {str(e)}")
        return pd.DataFrame()


def load_population_data():
    """
    Carga datos de población por municipios desde Google Drive (OPCIONAL)
    """
    try:
        # Obtener ID del archivo (nombre actualizado, opcional)
        file_id = st.secrets.get("google_drive", {}).get("poblacion_xlsx")

        if not file_id:
            logger.info("ID de archivo de población no configurado (opcional)")
            return pd.DataFrame()

        # Descargar archivo
        file_path = download_from_drive(file_id, "Poblacion_aseguramiento.xlsx")

        if not file_path or not Path(file_path).exists():
            logger.info("No se pudo descargar el archivo de población (opcional)")
            return pd.DataFrame()

        # Cargar Excel
        df = pd.read_excel(file_path)

        logger.info(f"Datos de población cargados: {len(df):,} registros")

        # Validaciones para identificar columnas clave
        municipio_col = None
        poblacion_col = None

        for col in df.columns:
            col_upper = str(col).upper()
            if "MUNICIPIO" in col_upper:
                municipio_col = col
            elif "TOTAL" in col_upper or "POBLACION" in col_upper:
                poblacion_col = col

        if municipio_col:
            municipios_unicos = df[municipio_col].nunique()
            logger.info(f"Municipios únicos en población: {municipios_unicos}")
        else:
            logger.warning("No se encontró columna de municipio en datos de población")

        if poblacion_col:
            total_poblacion = df[poblacion_col].sum()
            logger.info(f"Población total: {total_poblacion:,}")
        else:
            logger.warning("No se encontró columna de población total")

        return df

    except Exception as e:
        logger.info(f"Error cargando datos de población (opcional): {str(e)}")
        return pd.DataFrame()


def load_logo():
    """
    Descarga logo desde Google Drive (OPCIONAL)
    """
    try:
        # Obtener ID del archivo (nombre actualizado, opcional)
        file_id = st.secrets.get("google_drive", {}).get("logo_gobernacion")

        if not file_id:
            logger.info("ID de logo no configurado (opcional)")
            return None

        # Descargar archivo
        file_path = download_from_drive(
            file_id, "logo_gobernacion.png", "assets/images"
        )

        if file_path and Path(file_path).exists():
            logger.info("Logo descargado exitosamente")
            return file_path
        else:
            logger.info("No se pudo descargar el logo (opcional)")
            return None

    except Exception as e:
        logger.info(f"Error descargando logo (opcional): {str(e)}")
        return None


def load_from_drive(file_type="all"):
    """
    Función principal para cargar datos específicos o todos desde Google Drive

    Args:
        file_type (str): 'vacunacion', 'barridos', 'poblacion', 'logo', o 'all'

    Returns:
        dict: Diccionario con los DataFrames/rutas cargados
    """
    results = {
        "vacunacion": pd.DataFrame(),
        "barridos": pd.DataFrame(),
        "poblacion": pd.DataFrame(),
        "logo": None,
        "status": {
            "vacunacion": False,
            "barridos": False,
            "poblacion": False,  # Opcional
            "logo": False,  # Opcional
        },
    }

    try:
        # Validar configuración primero
        valid, message = validate_secrets()
        if not valid:
            logger.error(f"Configuración inválida: {message}")
            return results

        # Cargar datos según el tipo solicitado
        if file_type in ["vacunacion", "all"]:
            try:
                results["vacunacion"] = load_vaccination_data()
                results["status"]["vacunacion"] = not results["vacunacion"].empty
            except Exception as e:
                logger.error(f"Error cargando vacunación: {str(e)}")

        if file_type in ["barridos", "all"]:
            try:
                results["barridos"] = load_barridos_data()
                results["status"]["barridos"] = not results["barridos"].empty
            except Exception as e:
                logger.error(f"Error cargando barridos: {str(e)}")

        if file_type in ["poblacion", "all"]:
            try:
                results["poblacion"] = load_population_data()
                results["status"]["poblacion"] = not results["poblacion"].empty
                # Población es opcional, no es error si está vacía
            except Exception as e:
                logger.info(f"Población no disponible (opcional): {str(e)}")

        if file_type in ["logo", "all"]:
            try:
                results["logo"] = load_logo()
                results["status"]["logo"] = results["logo"] is not None
                # Logo es opcional, no es error si no está
            except Exception as e:
                logger.info(f"Logo no disponible (opcional): {str(e)}")

        # Log del resumen
        critical_loaded = (
            results["status"]["vacunacion"] and results["status"]["barridos"]
        )
        logger.info(
            f"Carga completada - Críticos: {critical_loaded}, Población: {results['status']['poblacion']}, Logo: {results['status']['logo']}"
        )

        return results

    except Exception as e:
        logger.error(f"Error general en carga desde Drive: {str(e)}")
        return results


def check_drive_availability():
    """
    Verifica si Google Drive está disponible y configurado correctamente
    """
    try:
        valid, message = validate_secrets()
        return valid, message
    except Exception as e:
        return False, f"Error verificando Google Drive: {str(e)}"


def get_drive_file_info():
    """
    Obtiene información de los archivos configurados en Google Drive
    """
    try:
        file_ids = {
            "vacunacion_csv": st.secrets.get("google_drive", {}).get("vacunacion_csv"),
            "resumen_barridos_xlsx": st.secrets.get("google_drive", {}).get(
                "resumen_barridos_xlsx"
            ),
            "poblacion_xlsx": st.secrets.get("google_drive", {}).get("poblacion_xlsx"),
            "logo_gobernacion": st.secrets.get("google_drive", {}).get(
                "logo_gobernacion"
            ),
        }

        info = {
            "configurados": sum(1 for file_id in file_ids.values() if file_id),
            "total": len(file_ids),
            "criticos_configurados": all(
                file_ids[key] for key in ["vacunacion_csv", "resumen_barridos_xlsx"]
            ),
            "opcionales_configurados": sum(
                1 for key in ["poblacion_xlsx", "logo_gobernacion"] if file_ids[key]
            ),
            "detalles": file_ids,
        }

        return info

    except Exception as e:
        logger.error(f"Error obteniendo información de Drive: {str(e)}")
        return {
            "configurados": 0,
            "total": 4,
            "criticos_configurados": False,
            "opcionales_configurados": 0,
            "detalles": {},
            "error": str(e),
        }


if __name__ == "__main__":
    # Script de prueba para validar configuración
    print("🔍 VALIDADOR DE CONFIGURACIÓN GOOGLE DRIVE")
    print("=" * 50)

    # Verificar disponibilidad
    available, message = check_drive_availability()
    print(f"Disponibilidad: {'✅' if available else '❌'} {message}")

    # Obtener información de archivos
    info = get_drive_file_info()
    print(f"\nArchivos configurados: {info['configurados']}/{info['total']}")
    print(f"Críticos configurados: {'✅' if info['criticos_configurados'] else '❌'}")
    print(f"Opcionales configurados: {info['opcionales_configurados']}/2")

    # Mostrar detalles
    print("\nDetalles de configuración:")
    for key, value in info["detalles"].items():
        status = "✅" if value else "❌"
        optional = (
            "(opcional)"
            if key in ["poblacion_xlsx", "logo_gobernacion"]
            else "(crítico)"
        )
        print(f"  {status} {key}: {optional}")
