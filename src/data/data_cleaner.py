"""
src/data/data_cleaner.py
Limpieza unificada para todas las fuentes de datos.
Aplica las mismas reglas de limpieza a todas las bases para evitar inconsistencias.
"""

import pandas as pd
import numpy as np
import streamlit as st
import re
import unicodedata
from datetime import datetime, date


class UnifiedDataCleaner:
    """
    Limpiador unificado que aplica las mismas reglas a todas las fuentes de datos
    """

    def __init__(self):
        self.cleaning_stats = {
            "columns_normalized": 0,
            "values_normalized": 0,
            "dates_processed": 0,
            "gender_normalized": 0,
            "municipalities_normalized": 0,
            "eapb_normalized": 0,
        }

        # Mapeos de normalización
        self.gender_mapping = {
            "masculino": "Masculino",
            "m": "Masculino",
            "masc": "Masculino",
            "hombre": "Masculino",
            "h": "Masculino",
            "male": "Masculino",
            "1": "Masculino",
            "femenino": "Femenino",
            "f": "Femenino",
            "fem": "Femenino",
            "mujer": "Femenino",
            "female": "Femenino",
            "2": "Femenino",
        }

        self.municipality_mapping = {
            "san sebastian de mariquita": "mariquita",
            "san sebastián de mariquita": "mariquita",
            "armero guayabal": "armero",
            "armero - guayabal": "armero",
        }

        # Valores que se consideran como "Sin dato"
        self.null_values = [
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
            "Sin dato",
            "sin dato",
            "SIN DATO",
            np.nan,
            None,
        ]

    def clean_all_data(self, data_dict):
        """
        Aplica limpieza unificada a todos los DataFrames en el diccionario

        Args:
            data_dict: Diccionario con DataFrames {'key': DataFrame}

        Returns:
            Diccionario con DataFrames limpios
        """
        st.info("🧹 Iniciando limpieza unificada de datos...")

        cleaned_data = {}

        for key, df in data_dict.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                st.write(f"🔧 Limpiando: {key}")
                cleaned_data[key] = self._clean_dataframe(df, key)
            else:
                cleaned_data[key] = df

        self._show_cleaning_summary()
        return cleaned_data

    def _clean_dataframe(self, df, df_name):
        """
        Aplica limpieza completa a un DataFrame individual
        """
        df_clean = df.copy()

        # 1. Normalizar nombres de columnas
        df_clean = self._normalize_column_names(df_clean)

        # 2. Limpiar valores nulos y vacíos
        df_clean = self._normalize_null_values(df_clean)

        # 3. Limpiar datos específicos según el tipo de DataFrame
        if "poblacion" in df_name.lower():
            df_clean = self._clean_population_data(df_clean)
        elif "vacunacion" in df_name.lower() or "historica" in df_name.lower():
            df_clean = self._clean_vaccination_data(df_clean)
        elif "brigadas" in df_name.lower() or "emergencia" in df_name.lower():
            df_clean = self._clean_brigades_data(df_clean)

        # 4. Aplicar limpiezas comunes
        df_clean = self._apply_common_cleanings(df_clean)

        return df_clean

    def _normalize_column_names(self, df):
        """
        Normaliza nombres de columnas eliminando espacios y caracteres especiales
        """
        original_columns = df.columns.tolist()

        # Normalizar nombres de columnas
        new_columns = []
        for col in df.columns:
            # Eliminar espacios al principio y final
            normalized = str(col).strip()
            new_columns.append(normalized)

        df.columns = new_columns

        # Contar cambios
        changes = sum(
            1 for old, new in zip(original_columns, new_columns) if old != new
        )
        self.cleaning_stats["columns_normalized"] += changes

        return df

    def _normalize_null_values(self, df):
        """
        Normaliza valores nulos, vacíos y variantes a "Sin dato"
        """
        df_clean = df.copy()

        # Aplicar a columnas de tipo object/string
        for col in df_clean.select_dtypes(include=["object", "string"]).columns:
            # Reemplazar valores nulos
            mask = df_clean[col].isin(self.null_values) | df_clean[col].isna()

            # También verificar strings vacíos después de strip
            mask = mask | (df_clean[col].astype(str).str.strip() == "")

            values_changed = mask.sum()
            df_clean.loc[mask, col] = "Sin dato"

            self.cleaning_stats["values_normalized"] += values_changed

        return df_clean

    def _clean_population_data(self, df):
        """
        Limpieza específica para datos de población por EAPB
        """
        df_clean = df.copy()

        # Buscar columna de municipio (puede tener código-nombre)
        municipio_cols = [col for col in df_clean.columns if "municipio" in col.lower()]

        if municipio_cols:
            municipio_col = municipio_cols[0]

            # Si la columna tiene formato "código - nombre", extraer nombre
            if df_clean[municipio_col].astype(str).str.contains(" - ").any():
                df_clean[f"{municipio_col}_codigo"] = (
                    df_clean[municipio_col].astype(str).str.split(" - ").str[0]
                )
                df_clean[f"{municipio_col}_nombre"] = (
                    df_clean[municipio_col].astype(str).str.split(" - ").str[1]
                )

                # Normalizar nombres de municipios
                df_clean[f"{municipio_col}_nombre_norm"] = (
                    df_clean[f"{municipio_col}_nombre"].str.lower().str.strip()
                )

                # Aplicar mapeo de municipios
                for old_name, new_name in self.municipality_mapping.items():
                    mask = df_clean[f"{municipio_col}_nombre_norm"] == old_name
                    df_clean.loc[mask, f"{municipio_col}_nombre_norm"] = new_name

                self.cleaning_stats["municipalities_normalized"] += len(
                    self.municipality_mapping
                )

        # Buscar columna de EAPB
        eapb_cols = [
            col
            for col in df_clean.columns
            if "eapb" in col.lower() or "aseguradora" in col.lower()
        ]

        if eapb_cols:
            eapb_col = eapb_cols[0]
            # Normalizar nombres de EAPB
            df_clean[f"{eapb_col}_normalized"] = (
                df_clean[eapb_col].astype(str).str.strip().str.title()
            )
            self.cleaning_stats["eapb_normalized"] += len(df_clean)

        # Convertir columnas numéricas
        numeric_cols = []
        for col in df_clean.columns:
            if any(
                word in col.lower()
                for word in ["total", "contributivo", "subsidiado", "especial"]
            ):
                try:
                    df_clean[col] = pd.to_numeric(
                        df_clean[col], errors="coerce"
                    ).fillna(0)
                    numeric_cols.append(col)
                except:
                    pass

        return df_clean

    def _clean_vaccination_data(self, df):
        """
        Limpieza específica para datos de vacunación histórica
        """
        df_clean = df.copy()

        # Normalizar género
        gender_cols = [
            col
            for col in df_clean.columns
            if col.lower() in ["sexo", "genero", "género"]
        ]

        for gender_col in gender_cols:
            if gender_col in df_clean.columns:
                df_clean[f"{gender_col}_normalized"] = (
                    df_clean[gender_col].astype(str).str.lower().str.strip()
                )

                # Aplicar mapeo de género
                for old_val, new_val in self.gender_mapping.items():
                    mask = df_clean[f"{gender_col}_normalized"] == old_val
                    df_clean.loc[mask, f"{gender_col}_normalized"] = new_val

                # Valores no mapeados se convierten en "No Binario"
                mapped_values = list(self.gender_mapping.values()) + ["Sin dato"]
                mask_unmapped = ~df_clean[f"{gender_col}_normalized"].isin(
                    mapped_values
                )
                df_clean.loc[mask_unmapped, f"{gender_col}_normalized"] = "No Binario"

                self.cleaning_stats["gender_normalized"] += len(df_clean)

        # Normalizar nombres de municipios
        municipio_cols = [
            col
            for col in df_clean.columns
            if "municipio" in col.lower() and "residencia" in col.lower()
        ]

        for municipio_col in municipio_cols:
            if municipio_col in df_clean.columns:
                df_clean[f"{municipio_col}_normalized"] = (
                    df_clean[municipio_col].astype(str).str.lower().str.strip()
                )

                # Aplicar mapeo de municipios
                for old_name, new_name in self.municipality_mapping.items():
                    mask = df_clean[f"{municipio_col}_normalized"] == old_name
                    df_clean.loc[mask, f"{municipio_col}_normalized"] = new_name

        # Procesar fechas
        date_cols = [
            col
            for col in df_clean.columns
            if "fecha" in col.lower() or col in ["FA UNICA"]
        ]

        for date_col in date_cols:
            if date_col in df_clean.columns:
                df_clean[f"{date_col}_processed"] = pd.to_datetime(
                    df_clean[date_col], errors="coerce"
                )
                self.cleaning_stats["dates_processed"] += (
                    df_clean[f"{date_col}_processed"].notna().sum()
                )

        # Normalizar columnas categóricas comunes
        categorical_cols = [
            "RegimenAfiliacion",
            "GrupoEtnico",
            "NombreAseguradora",
            "Desplazado",
            "Discapacitado",
        ]

        for cat_col in categorical_cols:
            if cat_col in df_clean.columns:
                # Normalizar valores booleanos para Desplazado/Discapacitado
                if cat_col in ["Desplazado", "Discapacitado"]:
                    df_clean[cat_col] = (
                        df_clean[cat_col].astype(str).str.lower().str.strip()
                    )
                    boolean_mapping = {
                        "true": "Sí",
                        "1": "Sí",
                        "si": "Sí",
                        "sí": "Sí",
                        "yes": "Sí",
                        "y": "Sí",
                        "false": "No",
                        "0": "No",
                        "no": "No",
                        "n": "No",
                    }

                    for old_val, new_val in boolean_mapping.items():
                        mask = df_clean[cat_col] == old_val
                        df_clean.loc[mask, cat_col] = new_val

                    # Valores no mapeados se convierten en "Sin dato"
                    mapped_values = list(boolean_mapping.values()) + ["Sin dato"]
                    mask_unmapped = ~df_clean[cat_col].isin(mapped_values)
                    df_clean.loc[mask_unmapped, cat_col] = "Sin dato"

        return df_clean

    def _clean_brigades_data(self, df):
        """
        Limpieza específica para datos de brigadas de emergencia
        """
        df_clean = df.copy()

        # Normalizar nombres de columnas de brigadas (con espacios problemáticos)
        column_mapping = {
            "Efectivas (E)": ["efectivas", "efectiva"],
            "No Efectivas (NE)": ["no efectivas", "no efectiva"],
            "Fallidas (F)": ["fallidas", "fallida"],
            "Casa renuente": ["casa renuente", "renuente"],
            "TPE": ["tpe", "total poblacion encontrada"],
            "TPVP": ["tpvp", "total poblacion vacunada previa"],
            "TPNVP": ["tpnvp", "total poblacion no vacunada"],
            "TPVB": ["tpvb", "total poblacion vacunada brigada"],
        }

        # Crear alias para columnas con nombres problemáticos
        for standard_name, possible_names in column_mapping.items():
            for col in df_clean.columns:
                col_normalized = col.strip().lower()
                if any(name in col_normalized for name in possible_names):
                    if standard_name not in df_clean.columns:
                        df_clean[standard_name] = pd.to_numeric(
                            df_clean[col], errors="coerce"
                        ).fillna(0)
                    break

        # Normalizar municipios y veredas
        location_cols = ["MUNICIPIO", "VEREDAS"]
        for loc_col in location_cols:
            if loc_col in df_clean.columns:
                df_clean[f"{loc_col}_normalized"] = (
                    df_clean[loc_col].astype(str).str.strip().str.title()
                )

        # Normalizar fechas
        if "FECHA" in df_clean.columns:
            df_clean["FECHA_processed"] = pd.to_datetime(
                df_clean["FECHA"], errors="coerce"
            )
            self.cleaning_stats["dates_processed"] += (
                df_clean["FECHA_processed"].notna().sum()
            )

        # Convertir columnas numéricas de grupos de edad
        age_patterns = [
            "< 1 AÑO",
            "1-5 AÑOS",
            "6-10 AÑOS",
            "11-20 AÑOS",
            "21-30 AÑOS",
            "31-40 AÑOS",
            "41-50 AÑOS",
            "51-59 AÑOS",
            "60 Y MAS",
        ]

        for col in df_clean.columns:
            col_upper = col.upper().strip()
            if any(pattern in col_upper for pattern in age_patterns):
                df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce").fillna(0)

        return df_clean

    def _apply_common_cleanings(self, df):
        """
        Aplica limpiezas comunes a todos los DataFrames
        """
        df_clean = df.copy()

        # Eliminar filas completamente vacías
        df_clean = df_clean.dropna(how="all")

        # Eliminar columnas completamente vacías
        df_clean = df_clean.dropna(axis=1, how="all")

        # Normalizar strings: eliminar espacios extra
        for col in df_clean.select_dtypes(include=["object", "string"]).columns:
            try:
                df_clean[col] = df_clean[col].astype(str).str.strip()
                # Eliminar espacios múltiples
                df_clean[col] = df_clean[col].str.replace(r"\s+", " ", regex=True)
            except:
                pass

        return df_clean

    def _show_cleaning_summary(self):
        """
        Muestra resumen de la limpieza realizada
        """
        st.subheader("🧹 Resumen de Limpieza")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Columnas normalizadas", self.cleaning_stats["columns_normalized"]
            )
            st.metric("Valores normalizados", self.cleaning_stats["values_normalized"])

        with col2:
            st.metric("Fechas procesadas", self.cleaning_stats["dates_processed"])
            st.metric("Géneros normalizados", self.cleaning_stats["gender_normalized"])

        with col3:
            st.metric(
                "Municipios normalizados",
                self.cleaning_stats["municipalities_normalized"],
            )
            st.metric("EAPB normalizadas", self.cleaning_stats["eapb_normalized"])

        st.success("✅ Limpieza unificada completada")

    def get_cleaning_stats(self):
        """
        Retorna estadísticas de limpieza
        """
        return self.cleaning_stats.copy()


# Función de conveniencia
def clean_unified_data(data_dict):
    """
    Función de conveniencia para limpiar datos unificados

    Args:
        data_dict: Diccionario con DataFrames a limpiar

    Returns:
        Diccionario con DataFrames limpios
    """
    cleaner = UnifiedDataCleaner()
    return cleaner.clean_all_data(data_dict)


# Función de prueba
def test_data_cleaner():
    """
    Función de prueba del limpiador de datos
    """
    st.title("🧪 Prueba del Limpiador Unificado")

    # Crear datos de prueba
    test_data = {
        "test_vaccination": pd.DataFrame(
            {
                " Sexo ": ["masculino", "f", "M", "", np.nan],
                "NombreMunicipioResidencia": [
                    "IBAGUÉ",
                    "san Sebastian de mariquita",
                    "",
                    "HONDA",
                    "Armero Guayabal",
                ],
                " Edad_Vacunacion ": [25, 30, "", 45, 55],
                "FA UNICA": [
                    "2024-01-15",
                    "2024-02-20",
                    "",
                    "2024-03-10",
                    "2024-04-05",
                ],
            }
        ),
        "test_population": pd.DataFrame(
            {
                "Municipio": ["001 - IBAGUÉ", "002 - MARIQUITA", "003 - HONDA"],
                " EAPB ": ["Nueva EPS", "Salud Total", ""],
                "Total": [1000, 800, 1200],
            }
        ),
    }

    # Aplicar limpieza
    cleaner = UnifiedDataCleaner()
    cleaned_data = cleaner.clean_all_data(test_data)

    # Mostrar resultados
    st.subheader("📊 Datos Originales vs Limpios")

    for key in test_data.keys():
        st.write(f"**{key}:**")

        col1, col2 = st.columns(2)
        with col1:
            st.write("Original:")
            st.dataframe(test_data[key])
        with col2:
            st.write("Limpio:")
            st.dataframe(cleaned_data[key])


if __name__ == "__main__":
    test_data_cleaner()

import pandas as pd
from datetime import datetime


def clean_data(df):
    """
    Limpieza centralizada de datos
    """
    # Normalizar nombres de municipios
    if "Municipio" in df.columns:
        df["Municipio"] = df["Municipio"].str.upper().str.strip()

    # Convertir fechas
    date_columns = ["Fecha_Aplicacion", "Fecha_Nacimiento"]
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df


def calculate_current_age(df):
    """
    Calcula la edad actual basada en la fecha de nacimiento
    """
    if "Fecha_Nacimiento" in df.columns:
        today = datetime.now()
        df["Edad_Actual"] = ((today - df["Fecha_Nacimiento"]).dt.days / 365.25).astype(
            int
        )
    return df
