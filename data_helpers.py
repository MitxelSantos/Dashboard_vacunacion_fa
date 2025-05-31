"""
data_helpers.py - Utilidades específicas para manejo de datos de vacunación
Versión actualizada con rangos de edad correctos y cálculo de edad desde fecha de nacimiento
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Definición de rangos de edad correctos
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
        ],
    },
    "1-5": {
        "label": "1-5 años",
        "aliases": ["1-5", "1 A 5", "1A5", "1_5", "PREESCOLAR", "1 A 5 AÑOS"],
    },
    "6-10": {
        "label": "6-10 años",
        "aliases": ["6-10", "6 A 10", "6A10", "6_10", "ESCOLAR_MENOR", "6 A 10 AÑOS"],
    },
    "11-20": {
        "label": "11-20 años",
        "aliases": [
            "11-20",
            "11 A 20",
            "11A20",
            "11_20",
            "ADOLESCENTE",
            "11 A 20 AÑOS",
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
            "21 A 30 AÑOS",
        ],
    },
    "31-40": {
        "label": "31-40 años",
        "aliases": ["31-40", "31 A 40", "31A40", "31_40", "ADULTO", "31 A 40 AÑOS"],
    },
    "41-50": {
        "label": "41-50 años",
        "aliases": [
            "41-50",
            "41 A 50",
            "41A50",
            "41_50",
            "ADULTO_MEDIO",
            "41 A 50 AÑOS",
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
            "51 A 59 AÑOS",
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
}

# Patrones adicionales para consolidar en 60+
PATRONES_CONSOLIDAR_60 = [
    "60-69",
    "60 A 69",
    "60A69",
    "60_69",
    "70+",
    "70 +",
    "70 Y MAS",
    "70 Y MÁS",
    "70MAS",
    "70_MAS",
    "MAYOR 70",
    ">70",
    "MAYOR_70",
]


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


def detect_age_columns(df: pd.DataFrame) -> Dict[str, str]:
    """
    Detecta automáticamente las columnas de rangos de edad en el DataFrame
    Maneja 4 etapas de barridos: encontrada, previa, no_vacunada, vacunada_barrido

    Args:
        df: DataFrame con columnas de vacunación por edad

    Returns:
        Dict mapeando rango estándar -> nombre de columna encontrada (etapa 1 por defecto)
    """
    edad_columns = {}

    for col in df.columns:
        col_upper = str(col).upper().strip().replace(" ", "")

        for rango, config in RANGOS_EDAD_DEFINIDOS.items():
            for alias in config["aliases"]:
                alias_clean = alias.replace(" ", "").upper()
                # Solo tomar etapa 1 (sin sufijos) para compatibilidad
                if alias_clean == col_upper or (
                    alias_clean in col_upper
                    and not any(suf in col_upper for suf in ["2", "3", "4"])
                ):
                    edad_columns[rango] = col
                    break
            if rango in edad_columns:
                break

    return edad_columns


def detect_age_columns_by_stage(df: pd.DataFrame) -> Dict[str, Dict[str, str]]:
    """
    Detecta columnas de rangos de edad separadas por las 4 etapas de barridos

    Args:
        df: DataFrame con columnas de barridos

    Returns:
        Dict con estructura: {etapa: {rango: columna}}
    """
    age_columns_by_stage = {
        "etapa_1_encontrada": {},  # Población encontrada
        "etapa_2_previa": {},  # Vacunada previamente
        "etapa_3_no_vacunada": {},  # No vacunada encontrada
        "etapa_4_vacunada_barrido": {},  # Vacunada en barrido
    }

    # Patrones base para cada rango
    base_patterns = {
        "<1": ["<1", "< 1", "MENOR 1", "< 1 AÑO"],
        "1-5": ["1-5", "1 A 5", "1-5 AÑOS"],
        "6-10": ["6-10", "6 A 10", "6-10 AÑOS"],
        "11-20": ["11-20", "11 A 20", "11-20 AÑOS"],
        "21-30": ["21-30", "21 A 30", "21-30 AÑOS"],
        "31-40": ["31-40", "31 A 40", "31-40 AÑOS"],
        "41-50": ["41-50", "41 A 50", "41-50 AÑOS"],
        "51-59": ["51-59", "51 A 59", "51-59 AÑOS"],
        "60+": ["60+", "60 Y MAS", "60 Y MÁS"],
    }

    for col in df.columns:
        col_clean = str(col).upper().strip()

        # Determinar rango de edad
        rango_detectado = None
        for rango, patterns in base_patterns.items():
            for pattern in patterns:
                if pattern in col_clean:
                    rango_detectado = rango
                    break
            if rango_detectado:
                break

        if rango_detectado:
            # Determinar etapa basado en sufijos
            if col_clean.endswith(("2", "AÑOS2")):
                age_columns_by_stage["etapa_2_previa"][rango_detectado] = col
            elif col_clean.endswith(
                (
                    "3",
                    "AÑOS11",
                    "AÑOS12",
                    "AÑOS13",
                    "AÑOS14",
                    "AÑOS15",
                    "AÑOS16",
                    "AÑOS17",
                )
            ):
                age_columns_by_stage["etapa_3_no_vacunada"][rango_detectado] = col
            elif col_clean.endswith(
                ("4", "AÑOS21", "AÑOS22", "AÑOS23", "AÑOS24", "AÑOS25", "AÑOS26")
            ):
                age_columns_by_stage["etapa_4_vacunada_barrido"][rango_detectado] = col
            else:
                # Sin sufijo = etapa 1 (población encontrada)
                age_columns_by_stage["etapa_1_encontrada"][rango_detectado] = col

    return age_columns_by_stage


def detect_consolidation_columns(df: pd.DataFrame) -> List[str]:
    """
    Detecta columnas que deben consolidarse en el rango 60+

    Args:
        df: DataFrame con columnas de vacunación

    Returns:
        List de nombres de columnas para consolidar
    """
    columns_to_consolidate = []

    for col in df.columns:
        col_upper = str(col).upper().strip().replace(" ", "")

        for pattern in PATRONES_CONSOLIDAR_60:
            pattern_clean = pattern.replace(" ", "").upper()
            if pattern_clean in col_upper:
                columns_to_consolidate.append(col)
                break

    return columns_to_consolidate


def process_individual_data_by_age(
    df: pd.DataFrame,
    fecha_referencia_col: str = "FA UNICA",
    fecha_nacimiento_col: str = "FechaNacimiento",
) -> Dict[str, any]:
    """
    Procesa datos individuales calculando edades y clasificando por rangos

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

    # Contar por rango
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


def validate_barridos_structure(df: pd.DataFrame) -> Dict[str, any]:
    """
    Valida la estructura de datos de barridos territoriales

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
            "edad_columns": {},
            "consolidation_columns": [],
        },
        "stats": {
            "total_rows": len(df),
            "date_coverage": None,
            "municipios_count": 0,
            "veredas_count": 0,
            "total_vacunados": 0,
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

    # Detectar columnas de edad
    edad_cols = detect_age_columns(df)
    validation["columns_found"]["edad_columns"] = edad_cols

    if not edad_cols:
        validation["errors"].append("No se encontraron columnas de rangos de edad")
        validation["valid"] = False
    else:
        # Calcular total de vacunados
        total_vacunados = 0
        for rango, col_name in edad_cols.items():
            if col_name in df.columns:
                total_vacunados += df[col_name].fillna(0).sum()
        validation["stats"]["total_vacunados"] = total_vacunados

    # Detectar columnas para consolidación
    consolidation_cols = detect_consolidation_columns(df)
    validation["columns_found"]["consolidation_columns"] = consolidation_cols

    if consolidation_cols:
        validation["warnings"].append(
            f"Se encontraron {len(consolidation_cols)} columnas para consolidar en 60+"
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


def process_barridos_by_age(df: pd.DataFrame) -> Dict[str, any]:
    """
    Procesa totales de vacunación por rangos de edad desde barridos

    Args:
        df: DataFrame de barridos

    Returns:
        Dict con totales procesados
    """
    result = {
        "total_general": 0,
        "por_edad": {},
        "por_municipio": {},
        "por_vereda": {},
        "consolidacion": {
            "columnas_principales": {},
            "columnas_consolidadas": [],
            "total_consolidado": 0,
        },
        "resumen": {},
    }

    if df.empty:
        return result

    # Detectar columnas de edad y consolidación
    edad_columns = detect_age_columns(df)
    consolidation_columns = detect_consolidation_columns(df)

    result["consolidacion"]["columnas_principales"] = edad_columns
    result["consolidacion"]["columnas_consolidadas"] = consolidation_columns

    # Procesar columnas principales por rango de edad
    for rango, col_name in edad_columns.items():
        if col_name in df.columns:
            # Convertir a numérico de forma segura
            valores_numericos = pd.to_numeric(df[col_name], errors="coerce").fillna(0)
            total_rango = valores_numericos.sum()
            result["por_edad"][rango] = {
                "total": total_rango,
                "label": RANGOS_EDAD_DEFINIDOS[rango]["label"],
                "column": col_name,
            }
            result["total_general"] += total_rango

    # Consolidar columnas adicionales en 60+
    total_consolidado = 0
    for col in consolidation_columns:
        if col in df.columns:
            # Convertir a numérico de forma segura
            valores_numericos = pd.to_numeric(df[col], errors="coerce").fillna(0)
            total_consolidado += valores_numericos.sum()

    if total_consolidado > 0:
        result["consolidacion"]["total_consolidado"] = total_consolidado

        # Agregar al rango 60+
        if "60+" in result["por_edad"]:
            result["por_edad"]["60+"]["total"] += total_consolidado
        else:
            result["por_edad"]["60+"] = {
                "total": total_consolidado,
                "label": RANGOS_EDAD_DEFINIDOS["60+"]["label"],
                "column": "consolidado",
            }

        result["total_general"] += total_consolidado

    # Agrupar por municipio si existe la columna
    municipio_col = None
    for col in df.columns:
        if "MUNICIPIO" in str(col).upper():
            municipio_col = col
            break

    if municipio_col:
        for municipio in df[municipio_col].unique():
            if pd.notna(municipio):
                mask = df[municipio_col] == municipio
                df_mun = df[mask]

                total_municipio = 0
                por_edad_mun = {}

                # Procesar columnas principales
                for rango, col_name in edad_columns.items():
                    if col_name in df_mun.columns:
                        # Convertir a numérico de forma segura
                        valores_numericos = pd.to_numeric(
                            df_mun[col_name], errors="coerce"
                        ).fillna(0)
                        total_edad = valores_numericos.sum()
                        por_edad_mun[rango] = total_edad
                        total_municipio += total_edad

                # Agregar consolidación
                total_consolidado_mun = 0
                for col in consolidation_columns:
                    if col in df_mun.columns:
                        # Convertir a numérico de forma segura
                        valores_numericos = pd.to_numeric(
                            df_mun[col], errors="coerce"
                        ).fillna(0)
                        total_consolidado_mun += valores_numericos.sum()

                if total_consolidado_mun > 0:
                    por_edad_mun["60+"] = (
                        por_edad_mun.get("60+", 0) + total_consolidado_mun
                    )
                    total_municipio += total_consolidado_mun

                result["por_municipio"][municipio] = {
                    "total": total_municipio,
                    "por_edad": por_edad_mun,
                }

    # Estadísticas de resumen
    result["resumen"] = {
        "municipios_cubiertos": len(result["por_municipio"]),
        "rangos_con_datos": len(
            [r for r in result["por_edad"] if result["por_edad"][r]["total"] > 0]
        ),
        "rango_mas_vacunado": None,
        "municipio_mas_activo": None,
    }

    if result["por_edad"]:
        rango_max = max(result["por_edad"].items(), key=lambda x: x[1]["total"])
        result["resumen"]["rango_mas_vacunado"] = {
            "rango": rango_max[0],
            "total": rango_max[1]["total"],
            "label": rango_max[1]["label"],
        }

    if result["por_municipio"]:
        municipio_max = max(
            result["por_municipio"].items(), key=lambda x: x[1]["total"]
        )
        result["resumen"]["municipio_mas_activo"] = {
            "municipio": municipio_max[0],
            "total": municipio_max[1]["total"],
        }

    return result


def validate_population_structure(df: pd.DataFrame) -> Dict[str, any]:
    """
    Valida estructura de datos de población por EAPB

    Args:
        df: DataFrame de población

    Returns:
        Dict con información de validación
    """
    validation = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "structure": {
            "multiple_eapb_per_municipio": False,
            "total_registros": len(df),
            "municipios_unicos": 0,
            "eapb_unicas": 0,
            "poblacion_total": 0,
        },
    }

    if df.empty:
        validation["valid"] = False
        validation["errors"].append("DataFrame de población está vacío")
        return validation

    # Buscar columnas clave
    municipio_col = None
    eapb_col = None
    poblacion_col = None

    for col in df.columns:
        col_upper = str(col).upper()
        if "MUNICIPIO" in col_upper or "MPÍO" in col_upper:
            municipio_col = col
        elif "EAPB" in col_upper or "ASEGURADORA" in col_upper:
            eapb_col = col
        elif (
            "TOTAL" in col_upper or "POBLACION" in col_upper or "POBLACIÓN" in col_upper
        ):
            poblacion_col = col

    if not municipio_col:
        validation["errors"].append("No se encontró columna de municipio")
        validation["valid"] = False

    if not eapb_col:
        validation["errors"].append("No se encontró columna de EAPB")
        validation["valid"] = False

    if not poblacion_col:
        validation["warnings"].append("No se encontró columna de población total")

    # Analizar estructura
    if municipio_col and eapb_col:
        validation["structure"]["municipios_unicos"] = df[municipio_col].nunique()
        validation["structure"]["eapb_unicas"] = df[eapb_col].nunique()

        # Verificar si hay múltiples EAPB por municipio
        eapb_por_municipio = df.groupby(municipio_col)[eapb_col].nunique()
        if eapb_por_municipio.max() > 1:
            validation["structure"]["multiple_eapb_per_municipio"] = True
            validation["structure"][
                "promedio_eapb_por_municipio"
            ] = eapb_por_municipio.mean()
            validation["structure"]["max_eapb_por_municipio"] = eapb_por_municipio.max()
            validation["structure"]["municipios_con_multiples_eapb"] = (
                eapb_por_municipio > 1
            ).sum()

    # Calcular población total
    if poblacion_col:
        try:
            validation["structure"]["poblacion_total"] = df[poblacion_col].sum()
        except:
            validation["warnings"].append("Error calculando población total")

    return validation


def calculate_coverage_metrics(
    vacunados: int, poblacion_total: int, poblacion_objetivo: Optional[int] = None
) -> Dict[str, float]:
    """
    Calcula métricas de cobertura de vacunación

    Args:
        vacunados: Número total de vacunados
        poblacion_total: Población total
        poblacion_objetivo: Población objetivo (opcional, se calcula como % de total)

    Returns:
        Dict con métricas de cobertura
    """
    metrics = {
        "vacunados": vacunados,
        "poblacion_total": poblacion_total,
        "poblacion_objetivo": poblacion_objetivo,
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

    return metrics


def generate_age_distribution_report(
    historical_data: Dict, barridos_data: Dict
) -> Dict[str, any]:
    """
    Genera reporte comparativo de distribución por edades

    Args:
        historical_data: Datos procesados de vacunación individual
        barridos_data: Datos procesados de barridos

    Returns:
        Dict con reporte comparativo
    """
    report = {
        "timestamp": datetime.now(),
        "resumen": {
            "total_individual": historical_data.get("registros_validos", 0),
            "total_barridos": barridos_data.get("total_general", 0),
            "total_general": 0,
        },
        "por_edad": {},
        "comparativo": {},
        "estadisticas": {},
    }

    report["resumen"]["total_general"] = (
        report["resumen"]["total_individual"] + report["resumen"]["total_barridos"]
    )

    # Combinar datos por edad
    for rango, config in RANGOS_EDAD_DEFINIDOS.items():
        individual = 0
        barridos = 0

        if historical_data.get("por_edad", {}).get(rango):
            individual = historical_data["por_edad"][rango]["total"]

        if barridos_data.get("por_edad", {}).get(rango):
            barridos = barridos_data["por_edad"][rango]["total"]

        total_rango = individual + barridos

        report["por_edad"][rango] = {
            "label": config["label"],
            "individual": individual,
            "barridos": barridos,
            "total": total_rango,
            "porcentaje_total": (
                (total_rango / report["resumen"]["total_general"] * 100)
                if report["resumen"]["total_general"] > 0
                else 0
            ),
        }

    # Análisis comparativo
    if report["resumen"]["total_general"] > 0:
        rangos_con_datos = [
            r for r in report["por_edad"] if report["por_edad"][r]["total"] > 0
        ]

        if rangos_con_datos:
            # Rango más vacunado
            rango_max = max(
                rangos_con_datos, key=lambda r: report["por_edad"][r]["total"]
            )
            report["comparativo"]["rango_mas_vacunado"] = {
                "rango": rango_max,
                "label": report["por_edad"][rango_max]["label"],
                "total": report["por_edad"][rango_max]["total"],
                "porcentaje": report["por_edad"][rango_max]["porcentaje_total"],
            }

            # Rango menos vacunado (con datos)
            rango_min = min(
                rangos_con_datos, key=lambda r: report["por_edad"][r]["total"]
            )
            report["comparativo"]["rango_menos_vacunado"] = {
                "rango": rango_min,
                "label": report["por_edad"][rango_min]["label"],
                "total": report["por_edad"][rango_min]["total"],
                "porcentaje": report["por_edad"][rango_min]["porcentaje_total"],
            }

        # Dominancia de modalidad por rango
        dominancia = {}
        for rango in rangos_con_datos:
            data = report["por_edad"][rango]
            if data["total"] > 0:
                pct_individual = (data["individual"] / data["total"]) * 100
                pct_barridos = (data["barridos"] / data["total"]) * 100

                if pct_individual > pct_barridos:
                    dominancia[rango] = "individual"
                elif pct_barridos > pct_individual:
                    dominancia[rango] = "barridos"
                else:
                    dominancia[rango] = "equilibrado"

        report["comparativo"]["dominancia_por_rango"] = dominancia

    return report
