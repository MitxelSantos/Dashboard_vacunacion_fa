import pandas as pd
import numpy as np
import streamlit as st


def normalize_gender_values(value):
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


def create_safe_data_structure(original_data=None):
    """
    Crea una estructura de datos segura para evitar errores críticos
    """
    base_structure = {
        "municipios": pd.DataFrame(columns=["DPMP", "DANE", "SISBEN"]),
        "vacunacion": pd.DataFrame(
            columns=[
                "IdPaciente",
                "Sexo",
                "Grupo_Edad",
                "GrupoEtnico",
                "RegimenAfiliacion",
                "NombreMunicipioResidencia",
            ]
        ),
        "metricas": pd.DataFrame(
            columns=[
                "DPMP",
                "DANE",
                "SISBEN",
                "Vacunados",
                "Cobertura_DANE",
                "Cobertura_SISBEN",
            ]
        ),
    }

    # Si hay datos originales, intentar preservar su estructura
    if original_data and isinstance(original_data, dict):
        for key in ["municipios", "vacunacion", "metricas"]:
            if key in original_data and isinstance(original_data[key], pd.DataFrame):
                base_structure[key] = original_data[key].copy()

    return base_structure


def safe_apply_filters_wrapper(apply_filters_func):
    """
    Wrapper seguro para apply_filters que garantiza que nunca devuelva None
    """

    def wrapper(*args, **kwargs):
        try:
            result = apply_filters_func(*args, **kwargs)

            # Validar que el resultado no sea None
            if result is None:
                st.error("❌ Error crítico: apply_filters devolvió None")
                return create_safe_data_structure()

            # Validar que sea un diccionario
            if not isinstance(result, dict):
                st.error("❌ Error crítico: apply_filters no devolvió un diccionario")
                return create_safe_data_structure()

            # Validar que tenga las claves necesarias
            required_keys = ["municipios", "vacunacion", "metricas"]
            for key in required_keys:
                if key not in result:
                    st.error(
                        f"❌ Error crítico: Falta la clave '{key}' en el resultado"
                    )
                    return create_safe_data_structure(args[0] if args else None)

                if result[key] is None:
                    st.warning(
                        f"⚠️ La clave '{key}' es None, reemplazando con DataFrame vacío"
                    )
                    result[key] = pd.DataFrame()
                elif not isinstance(result[key], pd.DataFrame):
                    st.warning(
                        f"⚠️ La clave '{key}' no es un DataFrame, creando uno vacío"
                    )
                    result[key] = pd.DataFrame()

            return result

        except Exception as e:
            st.error(f"❌ Error en apply_filters: {str(e)}")
            return create_safe_data_structure(args[0] if args else None)

    return wrapper


def normalize_categorical_values(df, columns_to_normalize=None):
    """
    Normaliza valores categóricos reemplazando NaN y valores vacíos con "Sin dato"
    VERSIÓN MEJORADA: Con manejo de errores robusto
    """
    try:
        if df is None or not isinstance(df, pd.DataFrame):
            return pd.DataFrame()

        df_clean = df.copy()

        if columns_to_normalize is None:
            # Definir columnas categóricas por defecto
            columns_to_normalize = [
                "GrupoEtnico",
                "RegimenAfiliacion",
                "NombreAseguradora",
                "NombreMunicipioResidencia",
                "NombreDptoResidencia",
                "Desplazado",
                "Discapacitado",
                "TipoIdentificacion",
                "Grupo_Edad",
            ]

        # Filtrar solo las columnas que existen en el DataFrame
        existing_columns = [
            col for col in columns_to_normalize if col in df_clean.columns
        ]

        for col in existing_columns:
            try:
                # Convertir a string si es categórica
                if pd.api.types.is_categorical_dtype(df_clean[col]):
                    df_clean[col] = df_clean[col].astype(str)

                # Reemplazar diversos tipos de valores vacíos/nulos
                df_clean[col] = df_clean[col].fillna("Sin dato")
                df_clean[col] = df_clean[col].replace(
                    [
                        "",
                        "nan",
                        "NaN",
                        "null",
                        "NULL",
                        "None",
                        "NONE",
                        "na",
                        "NA",
                        "#N/A",
                        "N/A",
                    ],
                    "Sin dato",
                )

                # Limpiar espacios en blanco que podrían considerarse como vacíos
                df_clean[col] = df_clean[col].apply(
                    lambda x: "Sin dato" if str(x).strip() == "" else str(x).strip()
                )
            except Exception as e:
                st.warning(f"⚠️ Error normalizando columna {col}: {str(e)}")
                continue

        return df_clean
    except Exception as e:
        st.error(f"❌ Error en normalize_categorical_values: {str(e)}")
        return df if df is not None else pd.DataFrame()


def normalize_boolean_values(df, boolean_columns=None):
    """
    Normaliza valores booleanos a formato estándar Sí/No/Sin dato
    VERSIÓN MEJORADA: Con manejo de errores robusto
    """
    try:
        if df is None or not isinstance(df, pd.DataFrame):
            return pd.DataFrame()

        df_clean = df.copy()

        if boolean_columns is None:
            boolean_columns = ["Desplazado", "Discapacitado"]

        # Filtrar solo las columnas que existen
        existing_boolean_columns = [
            col for col in boolean_columns if col in df_clean.columns
        ]

        def normalize_boolean(value):
            try:
                if pd.isna(value) or str(value).lower().strip() in [
                    "nan",
                    "",
                    "none",
                    "null",
                    "na",
                    "sin dato",
                ]:
                    return "Sin dato"

                value_str = str(value).lower().strip()
                if value_str in ["true", "1", "si", "sí", "yes", "y"]:
                    return "Sí"
                elif value_str in ["false", "0", "no", "n"]:
                    return "No"
                else:
                    return "Sin dato"
            except:
                return "Sin dato"

        for col in existing_boolean_columns:
            try:
                df_clean[col] = df_clean[col].apply(normalize_boolean)
            except Exception as e:
                st.warning(f"⚠️ Error normalizando columna booleana {col}: {str(e)}")
                continue

        return df_clean
    except Exception as e:
        st.error(f"❌ Error en normalize_boolean_values: {str(e)}")
        return df if df is not None else pd.DataFrame()


@safe_apply_filters_wrapper
def apply_filters(data, filters, fuente_poblacion="DANE"):
    """
    Aplica los filtros seleccionados a los datos.
    VERSIÓN CORREGIDA: Manejo robusto de errores y validación de datos.
    NUNCA DEVUELVE None - siempre devuelve una estructura válida.

    Args:
        data (dict): Diccionario con los dataframes
        filters (dict): Filtros seleccionados
        fuente_poblacion (str): Fuente de datos de población ("DANE" o "SISBEN")

    Returns:
        dict: Diccionario con los dataframes filtrados y normalizados
    """
    try:
        # =====================================================================
        # VALIDACIÓN INICIAL ROBUSTA
        # =====================================================================

        # Validación inicial de datos
        if not isinstance(data, dict):
            st.error("❌ Error: Los datos no son un diccionario válido")
            return create_safe_data_structure()

        # Verificar que existan las claves necesarias
        required_keys = ["municipios", "vacunacion", "metricas"]
        for key in required_keys:
            if key not in data:
                st.error(f"❌ Error: Falta la clave '{key}' en los datos")
                return create_safe_data_structure()
            if data[key] is None:
                st.error(f"❌ Error: La clave '{key}' es None en los datos")
                return create_safe_data_structure()
            if not isinstance(data[key], pd.DataFrame):
                st.error(f"❌ Error: La clave '{key}' no es un DataFrame")
                return create_safe_data_structure()

        # Aplicar normalización de EAPB si está disponible
        try:
            data = apply_eapb_normalization_to_filtered_data(data)
        except Exception as e:
            st.warning(f"⚠️ Error en normalización EAPB durante filtros: {e}")

        # Crear copias para no modificar los originales
        filtered_data = {
            "municipios": data["municipios"].copy(),
            "vacunacion": data["vacunacion"].copy(),
            "metricas": data["metricas"].copy(),
        }

        # Validar que los DataFrames no estén vacíos
        if len(filtered_data["vacunacion"]) == 0:
            st.warning("⚠️ No hay datos de vacunación para filtrar")
            return filtered_data

        # =====================================================================
        # PASO 1: NORMALIZACIÓN COMPREHENSIVA DE DATOS
        # =====================================================================

        # Normalizar datos de vacunación antes del filtrado
        vacunacion_df = filtered_data["vacunacion"]

        # Convertir columnas categóricas a strings para evitar errores
        for col in vacunacion_df.columns:
            if pd.api.types.is_categorical_dtype(vacunacion_df[col]):
                vacunacion_df[col] = vacunacion_df[col].astype(str)

        # Aplicar normalización de valores categóricos
        vacunacion_df = normalize_categorical_values(vacunacion_df)

        # Aplicar normalización de valores booleanos
        vacunacion_df = normalize_boolean_values(vacunacion_df)

        # Normalizar géneros específicamente
        gender_columns = ["Sexo", "Genero"]
        for col in gender_columns:
            if col in vacunacion_df.columns:
                vacunacion_df[col] = vacunacion_df[col].apply(normalize_gender_values)

        # =====================================================================
        # PASO 2: APLICACIÓN DE FILTROS CON MANEJO DE ERRORES
        # =====================================================================

        # Aplicar cada filtro en secuencia con manejo de errores
        try:
            # Primero manejar el filtro de municipio (caso especial)
            if (
                filters.get("municipio", "Todos") != "Todos"
                and "NombreMunicipioResidencia" in vacunacion_df.columns
            ):
                # Mapeo de nombres alternativos para filtrado
                municipality_map = {
                    "Mariquita": [
                        "San Sebastian De Mariquita",
                        "San Sebastián De Mariquita",
                        "San Sebastian de Mariquita",
                        "San Sebastián de Mariquita",
                    ],
                    "Armero": ["Armero Guayabal", "ARMERO GUAYABAL"],
                }

                municipio_filtro = filters["municipio"]

                # Verificar si el municipio seleccionado tiene nombres alternativos
                alt_names = municipality_map.get(municipio_filtro, [])

                if alt_names:
                    # Crear máscara para incluir tanto el nombre normal como los alternativos
                    mask = (
                        vacunacion_df["NombreMunicipioResidencia"].str.lower()
                        == municipio_filtro.lower()
                    )
                    for alt in alt_names:
                        mask = mask | (
                            vacunacion_df["NombreMunicipioResidencia"].str.lower()
                            == alt.lower()
                        )

                    # Aplicar filtro con la máscara expandida
                    vacunacion_df = vacunacion_df[mask]
                else:
                    # Filtro normal para otros municipios
                    vacunacion_df = vacunacion_df[
                        vacunacion_df["NombreMunicipioResidencia"].str.lower()
                        == municipio_filtro.lower()
                    ]

        except Exception as e:
            st.warning(f"⚠️ Error aplicando filtro de municipio: {str(e)}")

        # Mapeo mejorado de filtros con manejo de géneros normalizados
        column_mapping = {
            "grupo_edad": "Grupo_Edad",
            "sexo": "Genero" if "Genero" in vacunacion_df.columns else "Sexo",
            "grupo_etnico": "GrupoEtnico",
            "regimen": "RegimenAfiliacion",
            "aseguradora": "NombreAseguradora",
        }

        # Aplicar cada filtro solo si la columna existe
        for filter_key, column_name in column_mapping.items():
            try:
                if (
                    column_name in vacunacion_df.columns
                    and filters.get(filter_key, "Todos") != "Todos"
                ):

                    # Caso especial para género: normalizar el valor del filtro también
                    if filter_key == "sexo":
                        filter_value_normalized = normalize_gender_values(
                            filters[filter_key]
                        )
                        # Filtrar usando el valor normalizado
                        vacunacion_df = vacunacion_df[
                            vacunacion_df[column_name] == filter_value_normalized
                        ]
                    else:
                        # Para otros filtros, usar comparación insensible a mayúsculas/minúsculas
                        # pero considerando que ya hemos normalizado los datos

                        # Crear versión temporal para comparación
                        vacunacion_df.loc[:, f"{column_name}_lower"] = (
                            vacunacion_df[column_name].astype(str).str.lower()
                        )
                        filter_value_lower = filters[filter_key].lower()

                        # Filtrar usando la versión normalizada
                        vacunacion_df = vacunacion_df[
                            vacunacion_df[f"{column_name}_lower"] == filter_value_lower
                        ]

                        # Eliminar columna temporal
                        vacunacion_df = vacunacion_df.drop(
                            f"{column_name}_lower", axis=1
                        )

            except Exception as e:
                st.warning(f"⚠️ Error aplicando filtro {filter_key}: {str(e)}")
                continue

        # Actualizar el dataframe de vacunación filtrado
        filtered_data["vacunacion"] = vacunacion_df

        # =====================================================================
        # PASO 3: RECÁLCULO DE MÉTRICAS CON MANEJO DE ERRORES
        # =====================================================================

        try:
            # Recalcular métricas para datos filtrados
            if (
                "NombreMunicipioResidencia" in vacunacion_df.columns
                and len(vacunacion_df) > 0
            ):

                # Usar nombres normalizados
                from src.data.normalize import normalize_municipality_names

                vacunacion_df_clean = normalize_municipality_names(
                    vacunacion_df, "NombreMunicipioResidencia"
                )

                # Normalizar nombres en metricas
                metricas_df = normalize_municipality_names(
                    filtered_data["metricas"], "DPMP"
                )

                # Contar vacunados por municipio (versión normalizada)
                vacunados_por_municipio = (
                    vacunacion_df_clean.groupby("NombreMunicipioResidencia_norm")
                    .size()
                    .reset_index()
                )
                vacunados_por_municipio.columns = ["Municipio_norm", "Vacunados"]

                # Fusionar por nombre normalizado
                metricas_df = pd.merge(
                    metricas_df,
                    vacunados_por_municipio,
                    left_on="DPMP_norm",
                    right_on="Municipio_norm",
                    how="left",
                )

                # Eliminar columnas auxiliares
                cols_to_drop = ["DPMP_norm", "Municipio_norm"]
                for col in cols_to_drop:
                    if col in metricas_df.columns:
                        metricas_df = metricas_df.drop(col, axis=1)

                # Manejar columnas duplicadas de Vacunados
                if "Vacunados_y" in metricas_df.columns:
                    metricas_df["Vacunados"] = metricas_df["Vacunados_y"]
                    metricas_df = metricas_df.drop("Vacunados_y", axis=1)

                if "Vacunados_x" in metricas_df.columns:
                    if "Vacunados" not in metricas_df.columns:
                        metricas_df["Vacunados"] = metricas_df["Vacunados_x"]
                    metricas_df = metricas_df.drop("Vacunados_x", axis=1)

                # Si la fusión falló y no hay vacunados, preservar los valores originales o crear con ceros
                if "Vacunados" not in metricas_df.columns:
                    if "Vacunados" in filtered_data["metricas"].columns:
                        metricas_df["Vacunados"] = filtered_data["metricas"][
                            "Vacunados"
                        ]
                    else:
                        metricas_df["Vacunados"] = 0

                # Rellenar valores NaN
                metricas_df["Vacunados"] = metricas_df["Vacunados"].fillna(0)

                # Recalcular métricas con protección contra división por cero
                # Para DANE
                if "DANE" in metricas_df.columns:
                    metricas_df["Cobertura_DANE"] = np.where(
                        metricas_df["DANE"] > 0,
                        (metricas_df["Vacunados"] / metricas_df["DANE"] * 100).round(2),
                        0,
                    )
                    metricas_df["Pendientes_DANE"] = np.maximum(
                        metricas_df["DANE"] - metricas_df["Vacunados"], 0
                    )

                # Para SISBEN
                if "SISBEN" in metricas_df.columns:
                    metricas_df["Cobertura_SISBEN"] = np.where(
                        metricas_df["SISBEN"] > 0,
                        (metricas_df["Vacunados"] / metricas_df["SISBEN"] * 100).round(
                            2
                        ),
                        0,
                    )
                    metricas_df["Pendientes_SISBEN"] = np.maximum(
                        metricas_df["SISBEN"] - metricas_df["Vacunados"], 0
                    )

                # Actualizar el dataframe de métricas
                filtered_data["metricas"] = metricas_df

        except Exception as e:
            st.warning(f"⚠️ Error recalculando métricas: {str(e)}")
            # En caso de error, mantener métricas originales

        # =====================================================================
        # PASO 4: VALIDACIÓN FINAL Y LIMPIEZA
        # =====================================================================

        try:
            # Validar que los DataFrames resultantes tengan sentido
            if len(filtered_data["vacunacion"]) == 0:
                # Si no hay datos después del filtrado, informar al usuario
                # pero mantener la estructura para evitar errores
                st.warning(
                    "⚠️ Los filtros aplicados no devolvieron ningún resultado. Mostrando estructura vacía."
                )

            # Asegurar que las columnas de métricas existan
            required_metric_columns = [
                "Vacunados",
                "Cobertura_DANE",
                "Pendientes_DANE",
                "Cobertura_SISBEN",
                "Pendientes_SISBEN",
            ]

            for col in required_metric_columns:
                if col not in filtered_data["metricas"].columns:
                    if "Vacunados" in col:
                        filtered_data["metricas"][col] = 0
                    elif "Cobertura" in col:
                        filtered_data["metricas"][col] = 0.0
                    elif "Pendientes" in col:
                        # Calcular pendientes basándose en la fuente correspondiente
                        if (
                            "DANE" in col
                            and "DANE" in filtered_data["metricas"].columns
                        ):
                            filtered_data["metricas"][col] = filtered_data["metricas"][
                                "DANE"
                            ]
                        elif (
                            "SISBEN" in col
                            and "SISBEN" in filtered_data["metricas"].columns
                        ):
                            filtered_data["metricas"][col] = filtered_data["metricas"][
                                "SISBEN"
                            ]
                        else:
                            filtered_data["metricas"][col] = 0

        except Exception as e:
            st.warning(f"⚠️ Error en validación final: {str(e)}")

        # Garantizar que nunca devolvamos None
        if filtered_data is None:
            return create_safe_data_structure(data)

        return filtered_data

    except Exception as e:
        st.error(f"❌ Error crítico en apply_filters: {str(e)}")
        # Devolver estructura segura en caso de error crítico
        return create_safe_data_structure(data)


def apply_eapb_normalization_to_filtered_data(filtered_data):
    """
    Aplica normalización de EAPB a datos ya filtrados si no se aplicó previamente
    VERSIÓN MEJORADA: Con manejo de errores robusto

    Args:
        filtered_data: Diccionario con dataframes filtrados

    Returns:
        Diccionario con datos normalizados
    """
    try:
        if not isinstance(filtered_data, dict) or "vacunacion" not in filtered_data:
            return filtered_data

        # Verificar si ya se aplicó la normalización
        if (
            "NombreAseguradora" in filtered_data["vacunacion"].columns
            and "NombreAseguradora_original" not in filtered_data["vacunacion"].columns
        ):

            # Solo aplicar si no se había aplicado antes
            try:
                from .eapb_normalizer import normalize_eapb_names
                from .eapb_mappings import ALL_EAPB_MAPPINGS

                st.info("🔧 Aplicando normalización de EAPB...")

                filtered_data["vacunacion"] = normalize_eapb_names(
                    filtered_data["vacunacion"],
                    "NombreAseguradora",
                    ALL_EAPB_MAPPINGS,
                    create_backup=True,  # Crear respaldo para auditoría
                )

            except ImportError:
                st.warning(
                    "⚠️ Módulo de normalización EAPB no disponible - continuando sin normalización"
                )
            except Exception as e:
                st.warning(
                    f"⚠️ Error en normalización EAPB: {e} - continuando sin normalización"
                )

    except Exception as e:
        st.warning(f"⚠️ Error aplicando normalización EAPB en preprocessor: {e}")

    return filtered_data


# Resto de funciones auxiliares...


def get_filter_values_normalized(data):
    """
    Obtiene los valores únicos normalizados para cada filtro.
    VERSIÓN MEJORADA: Con manejo de errores robusto
    """
    try:
        if not isinstance(data, dict) or "vacunacion" not in data:
            return {}

        vacunacion_df = data["vacunacion"].copy()

        # Normalizar datos antes de extraer valores únicos
        vacunacion_df = normalize_categorical_values(vacunacion_df)
        vacunacion_df = normalize_boolean_values(vacunacion_df)

        # Normalizar géneros
        gender_columns = ["Sexo", "Genero"]
        for col in gender_columns:
            if col in vacunacion_df.columns:
                vacunacion_df[col] = vacunacion_df[col].apply(normalize_gender_values)

        # Extraer valores únicos normalizados
        filter_values = {}

        # Municipios
        if "NombreMunicipioResidencia" in vacunacion_df.columns:
            municipios = sorted(
                vacunacion_df["NombreMunicipioResidencia"].dropna().unique()
            )
            filter_values["municipios"] = [m for m in municipios if m != "Sin dato"]

        # Resto de la función... (implementar según necesidad)

        return filter_values

    except Exception as e:
        st.error(f"❌ Error en get_filter_values_normalized: {str(e)}")
        return {}


def validate_data_quality(data):
    """
    Valida la calidad de los datos y reporta estadísticas de completitud.
    VERSIÓN MEJORADA: Con manejo de errores robusto
    """
    try:
        if not isinstance(data, dict) or "vacunacion" not in data:
            return {
                "total_records": 0,
                "completeness": {},
                "data_quality_score": 0,
                "issues": ["No hay datos de vacunación disponibles"],
            }

        vacunacion_df = data["vacunacion"]
        total_records = len(vacunacion_df)

        quality_report = {
            "total_records": total_records,
            "completeness": {},
            "data_quality_score": 100,  # Valor por defecto optimista
            "issues": [],
        }

        if total_records == 0:
            quality_report["data_quality_score"] = 0
            quality_report["issues"].append("No hay registros de vacunación")
            return quality_report

        # Columnas críticas para evaluar
        critical_columns = [
            "NombreMunicipioResidencia",
            "Sexo",
            "Grupo_Edad",
            "GrupoEtnico",
            "RegimenAfiliacion",
            "FA UNICA",
        ]

        completeness_scores = []

        for col in critical_columns:
            if col in vacunacion_df.columns:
                # Contar registros completos (no NaN, no vacíos, no "Sin dato")
                complete_records = vacunacion_df[
                    (~vacunacion_df[col].isna())
                    & (vacunacion_df[col] != "Sin dato")
                    & (vacunacion_df[col].astype(str).str.strip() != "")
                    & (
                        ~vacunacion_df[col]
                        .astype(str)
                        .str.lower()
                        .isin(["nan", "null", "none"])
                    )
                ]

                completeness_pct = (
                    (len(complete_records) / total_records * 100)
                    if total_records > 0
                    else 0
                )
                quality_report["completeness"][col] = completeness_pct
                completeness_scores.append(completeness_pct)

                # Identificar problemas
                if completeness_pct < 80:
                    quality_report["issues"].append(
                        f"Baja completitud en {col}: {completeness_pct:.1f}%"
                    )
                elif completeness_pct < 95:
                    quality_report["issues"].append(
                        f"Completitud moderada en {col}: {completeness_pct:.1f}%"
                    )

        # Calcular score general de calidad
        if completeness_scores:
            quality_report["data_quality_score"] = np.mean(completeness_scores)

        return quality_report

    except Exception as e:
        return {
            "total_records": 0,
            "completeness": {},
            "data_quality_score": 0,
            "issues": [f"Error validando calidad de datos: {str(e)}"],
        }
