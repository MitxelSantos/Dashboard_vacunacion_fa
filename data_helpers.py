"""
data_helpers.py - Utilidades específicas para manejo de datos de vacunación
Versión 2.2 - Actualizada con 11 rangos de edad y estructura completa
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Definición de rangos de edad correctos (11 rangos)
RANGOS_EDAD_DEFINIDOS = {
    "<1": {
        "label": "< 1 año",
        "aliases": [
            "<1",
            "< 1",
            "MENOR 1",
            "MENOR_1",
            "0-11M",
            "0-1",
            "LACTANTE",
            "0A11M",
            "< 1 AÑO",
        ],
    },
    "1-5": {
        "label": "1-5 años",
        "aliases": ["1-5", "1 A 5", "1A5", "1_5", "PREESCOLAR", "1-5 AÑOS"],
    },
    "6-10": {
        "label": "6-10 años",
        "aliases": ["6-10", "6 A 10", "6A10", "6_10", "ESCOLAR_MENOR", "6-10 AÑOS"],
    },
    "11-20": {
        "label": "11-20 años",
        "aliases": [
            "11-20",
            "11 A 20",
            "11A20",
            "11_20",
            "ADOLESCENTE",
            "11-20 AÑOS",
        ],
    },
    "21-30": {
        "label": "21-30 años",
        "aliases": [
            "21-30",
            "21 A 30",
            "21A30",
            "21_30",
            "ADULTO_JOVEN",
            "21-30 AÑOS",
        ],
    },
    "31-40": {
        "label": "31-40 años",
        "aliases": ["31-40", "31 A 40", "31A40", "31_40", "ADULTO", "31-40 AÑOS"],
    },
    "41-50": {
        "label": "41-50 años",
        "aliases": [
            "41-50",
            "41 A 50",
            "41A50",
            "41_50",
            "ADULTO_MEDIO",
            "41-50 AÑOS",
        ],
    },
    "51-59": {
        "label": "51-59 años",
        "aliases": [
            "51-59",
            "51 A 59",
            "51A59",
            "51_59",
            "ADULTO_MAYOR",
            "51-59 AÑOS",
        ],
    },
    "60+": {
        "label": "60 años y más",
        "aliases": [
            "60+",
            "60 +",
            "60 Y MAS",
            "60 Y MÁS",
            "60MAS",
            "60_MAS",
            "MAYOR 60",
            ">60",
            "MAYOR_60",
        ],
    },
    "60-69": {
        "label": "60-69 años",
        "aliases": [
            "60-69",
            "60 A 69",
            "60A69",
            "60_69",
            "60-69 AÑOS",
        ],
    },
    "70+": {
        "label": "70 años y más",
        "aliases": [
            "70+",
            "70 +",
            "70 Y MAS",
            "70 Y MÁS",
            "70MAS",
            "70_MAS",
            "MAYOR 70",
            ">70",
            "MAYOR_70",
            "70 AÑOS Y MAS",
        ],
    },
}

# Columnas de totales por etapa
TOTALES_POR_ETAPA = {
    "etapa_1": ["TPE"],
    "etapa_2": ["TPVP"],
    "etapa_3": ["TPNVP"],
    "etapa_4": ["TPVB"],
}


def calculate_age(fecha_nacimiento, fecha_referencia=None):
    """
    Calcula la edad en años a partir de la fecha de nacimiento

    Args:
        fecha_nacimiento: Fecha de nacimiento (datetime)
        fecha_referencia: Fecha de referencia para calcular edad (default: hoy)

    Returns:
        int: Edad en años
    """
    if pd.isna(fecha_nacimiento):
        return None

    if fecha_referencia is None:
        fecha_referencia = datetime.now()

    try:
        # Convertir a datetime si no lo es
        if isinstance(fecha_nacimiento, str):
            fecha_nacimiento = pd.to_datetime(fecha_nacimiento)
        if isinstance(fecha_referencia, str):
            fecha_referencia = pd.to_datetime(fecha_referencia)

        edad = fecha_referencia.year - fecha_nacimiento.year

        # Ajustar si no ha llegado el cumpleaños este año
        if (fecha_referencia.month, fecha_referencia.day) < (
            fecha_nacimiento.month,
            fecha_nacimiento.day,
        ):
            edad -= 1

        return max(0, edad)  # No permitir edades negativas
    except Exception as e:
        return None


def classify_age_group(edad):
    """
    Clasifica una edad en el rango correspondiente

    Args:
        edad: Edad en años (int)

    Returns:
        str: Código del rango de edad
    """
    if pd.isna(edad) or edad is None:
        return None

    try:
        edad = int(edad)
    except:
        return None

    if edad < 1:
        return "<1"
    elif 1 <= edad <= 5:
        return "1-5"
    elif 6 <= edad <= 10:
        return "6-10"
    elif 11 <= edad <= 20:
        return "11-20"
    elif 21 <= edad <= 30:
        return "21-30"
    elif 31 <= edad <= 40:
        return "31-40"
    elif 41 <= edad <= 50:
        return "41-50"
    elif 51 <= edad <= 59:
        return "51-59"
    else:  # 60 y más
        return "60+"


def validate_barridos_structure_v2(df: pd.DataFrame) -> Dict[str, any]:
    """
    Valida la estructura de datos de barridos territoriales (v2.2)
    Actualizada para 11 rangos + totales

    Args:
        df: DataFrame de barridos

    Returns:
        Dict con información de validación
    """
    validation = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "columns_found": {
            "fecha": None,
            "municipio": None,
            "vereda": None,
            "edad_columns_by_stage": {},
            "total_columns_by_stage": {},
        },
        "stats": {
            "total_rows": len(df),
            "date_coverage": None,
            "municipios_count": 0,
            "veredas_count": 0,
            "rangos_detectados": 0,
            "etapas_completas": 0,
        },
    }

    if df.empty:
        validation["valid"] = False
        validation["errors"].append("DataFrame está vacío")
        return validation

    # Verificar columnas esenciales
    essential_columns = {
        "fecha": ["FECHA", "DATE", "FECHA_BARRIDO"],
        "municipio": ["MUNICIPIO", "MUNICIPALITY", "MPÍO"],
        "vereda": ["VEREDA", "VEREDAS", "VILLAGE", "CORREGIMIENTO"],
    }

    for key, possible_names in essential_columns.items():
        found_col = None
        for col in df.columns:
            if any(name.upper() in str(col).upper() for name in possible_names):
                found_col = col
                break

        validation["columns_found"][key] = found_col
        if found_col is None:
            validation["warnings"].append(f"No se encontró columna de {key}")

    # Detectar columnas de edad por etapa (11 rangos)
    rangos_detectados = 0
    etapas_completas = 0

    for rango, config in RANGOS_EDAD_DEFINIDOS.items():
        columnas_encontradas = []

        for col in df.columns:
            col_upper = str(col).upper().strip()
            for alias in config["aliases"]:
                if alias.upper() in col_upper:
                    columnas_encontradas.append(col)
                    break

        if columnas_encontradas:
            rangos_detectados += 1
            # Asignar a etapas por posición
            for i, col in enumerate(columnas_encontradas[:4]):  # Máximo 4 etapas
                etapa_key = f"etapa_{i+1}"
                if (
                    etapa_key
                    not in validation["columns_found"]["edad_columns_by_stage"]
                ):
                    validation["columns_found"]["edad_columns_by_stage"][etapa_key] = {}
                validation["columns_found"]["edad_columns_by_stage"][etapa_key][
                    rango
                ] = col

    # Detectar columnas de totales
    for etapa, patterns in TOTALES_POR_ETAPA.items():
        for col in df.columns:
            col_str = str(col).upper().strip()
            if col_str in [p.upper() for p in patterns]:
                validation["columns_found"]["total_columns_by_stage"][etapa] = col
                break

    # Contar etapas completas (con 11 rangos + total)
    for etapa_key in ["etapa_1", "etapa_2", "etapa_3", "etapa_4"]:
        edad_count = len(
            validation["columns_found"]["edad_columns_by_stage"].get(etapa_key, {})
        )
        total_col = validation["columns_found"]["total_columns_by_stage"].get(etapa_key)

        if edad_count == 11 and total_col:
            etapas_completas += 1

    validation["stats"]["rangos_detectados"] = rangos_detectados
    validation["stats"]["etapas_completas"] = etapas_completas

    if rangos_detectados < 11:
        validation["warnings"].append(
            f"Solo se detectaron {rangos_detectados}/11 rangos de edad"
        )

    if etapas_completas < 4:
        validation["warnings"].append(
            f"Solo {etapas_completas}/4 etapas están completas"
        )

    # Estadísticas básicas
    if validation["columns_found"]["municipio"]:
        validation["stats"]["municipios_count"] = df[
            validation["columns_found"]["municipio"]
        ].nunique()

    if validation["columns_found"]["vereda"]:
        validation["stats"]["veredas_count"] = df[
            validation["columns_found"]["vereda"]
        ].nunique()

    if validation["columns_found"]["fecha"]:
        fecha_col = validation["columns_found"]["fecha"]
        try:
            fechas = pd.to_datetime(df[fecha_col], errors="coerce")
            fechas_validas = fechas.dropna()
            if len(fechas_validas) > 0:
                validation["stats"]["date_coverage"] = {
                    "inicio": fechas_validas.min(),
                    "fin": fechas_validas.max(),
                    "dias": (fechas_validas.max() - fechas_validas.min()).days + 1,
                    "fechas_validas": len(fechas_validas),
                    "fechas_invalidas": len(fechas) - len(fechas_validas),
                }
        except Exception as e:
            validation["warnings"].append(f"Error procesando fechas: {str(e)}")

    return validation


def calculate_coverage_metrics_v2(
    vacunados: int,
    poblacion_total: int,
    poblacion_objetivo: Optional[int] = None,
    renuentes: int = 0,
) -> Dict[str, float]:
    """
    Calcula métricas de cobertura de vacunación (v2.2)
    Incluye análisis de renuencia

    Args:
        vacunados: Número total de vacunados
        poblacion_total: Población total
        poblacion_objetivo: Población objetivo (opcional, se calcula como % de total)
        renuentes: Número de renuentes

    Returns:
        Dict con métricas de cobertura
    """
    metrics = {
        "vacunados": vacunados,
        "poblacion_total": poblacion_total,
        "poblacion_objetivo": poblacion_objetivo,
        "renuentes": renuentes,
    }

    if poblacion_total > 0:
        metrics["cobertura_general"] = (vacunados / poblacion_total) * 100

        # Si no se especifica población objetivo, usar 80% de la población total
        if poblacion_objetivo is None:
            poblacion_objetivo = poblacion_total * 0.8
            metrics["poblacion_objetivo"] = poblacion_objetivo

        if poblacion_objetivo > 0:
            metrics["avance_meta"] = (vacunados / poblacion_objetivo) * 100
            metrics["faltante_meta"] = max(0, poblacion_objetivo - vacunados)
            metrics["porcentaje_faltante"] = max(
                0, (poblacion_objetivo - vacunados) / poblacion_objetivo * 100
            )

            # Clasificación de avance
            if metrics["avance_meta"] >= 100:
                metrics["status_meta"] = "COMPLETADA"
            elif metrics["avance_meta"] >= 80:
                metrics["status_meta"] = "ALTA"
            elif metrics["avance_meta"] >= 50:
                metrics["status_meta"] = "MEDIA"
            else:
                metrics["status_meta"] = "BAJA"

        # Métricas de renuencia
        total_contactado = vacunados + renuentes
        if total_contactado > 0:
            metrics["tasa_aceptacion"] = (vacunados / total_contactado) * 100
            metrics["tasa_renuencia"] = (renuentes / total_contactado) * 100

        if poblacion_total > 0:
            metrics["cobertura_contacto"] = (total_contactado / poblacion_total) * 100
            metrics["poblacion_sin_contactar"] = max(
                0, poblacion_total - total_contactado
            )
            metrics["porcentaje_sin_contactar"] = (
                metrics["poblacion_sin_contactar"] / poblacion_total * 100
            )

    return metrics


def generate_comprehensive_report_v2(
    historical_data: Dict, barridos_data: Dict, population_data: Dict = None
) -> Dict[str, any]:
    """
    Genera reporte comprehensivo de vacunación (v2.2)
    Incluye análisis completo de 11 rangos, etapas y métricas

    Args:
        historical_data: Datos procesados de vacunación individual
        barridos_data: Datos procesados de barridos
        population_data: Datos de población (opcional)

    Returns:
        Dict con reporte comprehensivo
    """
    report = {
        "timestamp": datetime.now(),
        "version": "2.2",
        "resumen": {
            "total_individual": historical_data.get("total_individual", 0),
            "total_barridos": barridos_data.get("total_vacunados", 0),
            "total_renuentes": barridos_data.get("total_renuentes", 0),
            "total_general": 0,
        },
        "por_edad": {},
        "metricas": {},
        "estructura": {
            "rangos_procesados": 0,
            "etapas_detectadas": 0,
            "calidad_datos": "PENDIENTE",
        },
    }

    report["resumen"]["total_general"] = (
        report["resumen"]["total_individual"] + report["resumen"]["total_barridos"]
    )

    # Combinar datos por edad (11 rangos)
    rangos_procesados = 0
    for rango, config in RANGOS_EDAD_DEFINIDOS.items():
        individual = 0
        barridos = 0
        renuentes = 0

        if historical_data.get("por_edad", {}).get(rango):
            individual = historical_data["por_edad"][rango].get("total", 0)

        if barridos_data.get("por_edad", {}).get(rango):
            barridos = barridos_data["por_edad"][rango].get("total", 0)

        if barridos_data.get("renuentes_por_edad", {}).get(rango):
            renuentes = barridos_data["renuentes_por_edad"][rango].get("total", 0)

        total_rango = individual + barridos

        if total_rango > 0 or renuentes > 0:
            rangos_procesados += 1

            report["por_edad"][rango] = {
                "label": config["label"],
                "individual": individual,
                "barridos": barridos,
                "renuentes": renuentes,
                "total_vacunados": total_rango,
                "porcentaje_total": (
                    (total_rango / report["resumen"]["total_general"] * 100)
                    if report["resumen"]["total_general"] > 0
                    else 0
                ),
                "tasa_aceptacion": (
                    (total_rango / (total_rango + renuentes) * 100)
                    if (total_rango + renuentes) > 0
                    else 0
                ),
            }

    report["estructura"]["rangos_procesados"] = rangos_procesados

    # Calcular métricas de cobertura
    if population_data:
        poblacion_total = population_data.get("total", 0)
        if poblacion_total > 0:
            report["metricas"] = calculate_coverage_metrics_v2(
                vacunados=report["resumen"]["total_general"],
                poblacion_total=poblacion_total,
                renuentes=report["resumen"]["total_renuentes"],
            )

    # Evaluar calidad de datos
    if rangos_procesados >= 9:  # Al menos 9 de 11 rangos
        if rangos_procesados == 11:
            report["estructura"]["calidad_datos"] = "EXCELENTE"
        else:
            report["estructura"]["calidad_datos"] = "BUENA"
    elif rangos_procesados >= 6:
        report["estructura"]["calidad_datos"] = "REGULAR"
    else:
        report["estructura"]["calidad_datos"] = "DEFICIENTE"

    return report


# Funciones de compatibilidad (mantener versiones anteriores funcionando)
def process_individual_data_by_age(
    df: pd.DataFrame,
    fecha_referencia_col: str = "FA UNICA",
    fecha_nacimiento_col: str = "FechaNacimiento",
) -> Dict[str, any]:
    """
    Procesa datos individuales calculando edades y clasificando por rangos
    Versión actualizada para 11 rangos

    Args:
        df: DataFrame con datos individuales
        fecha_referencia_col: Nombre de columna con fecha de referencia
        fecha_nacimiento_col: Nombre de columna con fecha de nacimiento

    Returns:
        Dict con totales procesados por edad
    """
    result = {
        "total_registros": len(df),
        "registros_validos": 0,
        "por_edad": {},
        "estadisticas": {},
        "errores": [],
    }

    if df.empty:
        return result

    # Verificar que existan las columnas necesarias
    if fecha_nacimiento_col not in df.columns:
        result["errores"].append(f"Columna '{fecha_nacimiento_col}' no encontrada")
        return result

    if fecha_referencia_col not in df.columns:
        result["errores"].append(f"Columna '{fecha_referencia_col}' no encontrada")
        return result

    # Crear copia de trabajo
    df_work = df.copy()

    # Calcular edades
    df_work["edad_calculada"] = df_work.apply(
        lambda row: (
            calculate_age(row[fecha_nacimiento_col], row[fecha_referencia_col])
            if pd.notna(row[fecha_nacimiento_col])
            and pd.notna(row[fecha_referencia_col])
            else None
        ),
        axis=1,
    )

    # Clasificar en rangos
    df_work["rango_edad"] = df_work["edad_calculada"].apply(classify_age_group)

    # Contar registros válidos
    registros_validos = df_work["edad_calculada"].notna().sum()
    result["registros_validos"] = registros_validos

    # Contar por rango (11 rangos)
    if registros_validos > 0:
        age_counts = df_work["rango_edad"].value_counts()

        for rango, config in RANGOS_EDAD_DEFINIDOS.items():
            count = age_counts.get(rango, 0)
            result["por_edad"][rango] = {
                "total": count,
                "label": config["label"],
                "porcentaje": (
                    (count / registros_validos * 100) if registros_validos > 0 else 0
                ),
            }

        # Estadísticas de edad
        edades_validas = df_work["edad_calculada"].dropna()
        if len(edades_validas) > 0:
            result["estadisticas"] = {
                "edad_minima": int(edades_validas.min()),
                "edad_maxima": int(edades_validas.max()),
                "edad_promedio": float(edades_validas.mean()),
                "edad_mediana": float(edades_validas.median()),
                "desviacion_estandar": float(edades_validas.std()),
            }

    return result
