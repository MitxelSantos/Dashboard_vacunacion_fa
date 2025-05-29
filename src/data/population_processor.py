"""
src/data/population_processor.py
Procesador especializado para datos de población por EAPB
Maneja el archivo Poblacion_aseguramiento.xlsx con la nueva estructura
"""

import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path
from datetime import datetime
import re
import unicodedata


class PopulationEAPBProcessor:
    """
    Procesador especializado para datos de población por EAPB
    """

    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.population_data = None
        self.processing_info = {
            "file_date": None,
            "total_records": 0,
            "total_eapb": 0,
            "total_municipalities": 0,
            "reference_month": None,
            "reference_year": None,
            "processing_date": datetime.now(),
        }

    def load_population_data(self, filename="Poblacion_aseguramiento.xlsx"):
        """
        Carga y procesa el archivo de población por EAPB
        """
        file_path = self.data_dir / filename

        if not file_path.exists():
            st.error(f"❌ Archivo {filename} no encontrado en {self.data_dir}")
            return None

        try:
            st.info(f"📊 Cargando población por EAPB desde {filename}")

            # Intentar leer el archivo Excel
            with pd.ExcelFile(file_path) as excel_file:
                sheet_names = excel_file.sheet_names
                st.write(f"📄 Hojas disponibles: {', '.join(sheet_names)}")

                # Usar la primera hoja disponible
                if len(sheet_names) > 0:
                    sheet_name = sheet_names[0]
                    df = pd.read_excel(file_path, sheet_name=sheet_name)

                    st.success(
                        f"✅ Datos cargados: {len(df)} registros desde hoja '{sheet_name}'"
                    )

                    # Procesar los datos
                    processed_data = self._process_population_structure(df)

                    if processed_data is not None:
                        self.population_data = processed_data
                        self._extract_metadata(processed_data)
                        st.success(
                            f"✅ Procesamiento completado: {len(processed_data)} registros válidos"
                        )
                        return processed_data
                    else:
                        st.error("❌ Error en el procesamiento de datos")
                        return None
                else:
                    st.error("❌ No se encontraron hojas en el archivo Excel")
                    return None

        except Exception as e:
            st.error(f"❌ Error cargando archivo {filename}: {str(e)}")
            return None

    def _process_population_structure(self, df):
        """
        Procesa la estructura específica del archivo de población por EAPB
        Estructura esperada: Municipio (código-nombre), EAPB, tipos de aseguramiento, total, mes, año
        """
        try:
            # Mostrar estructura del archivo para análisis
            st.write("🔍 **Estructura del archivo:**")
            st.write(f"📊 Columnas: {list(df.columns)}")
            st.write(f"📋 Primeras filas:")
            st.dataframe(df.head(3), use_container_width=True)

            # Identificar columnas automáticamente
            columns_mapping = self._identify_columns(df)

            if not columns_mapping:
                st.error("❌ No se pudo identificar la estructura del archivo")
                return None

            # Renombrar columnas para estandarización
            df_processed = df.copy()
            df_processed = df_processed.rename(columns=columns_mapping)

            # Validar que tenemos las columnas esenciales
            required_columns = ["municipio", "eapb", "total"]
            missing_columns = [
                col for col in required_columns if col not in df_processed.columns
            ]

            if missing_columns:
                st.error(f"❌ Faltan columnas requeridas: {missing_columns}")
                return None

            # Procesar datos
            df_processed = self._clean_and_standardize(df_processed)
            df_processed = self._extract_municipality_info(df_processed)
            df_processed = self._validate_and_filter(df_processed)

            return df_processed

        except Exception as e:
            st.error(f"❌ Error procesando estructura: {str(e)}")
            return None

    def _identify_columns(self, df):
        """
        Identifica automáticamente las columnas basándose en patrones comunes
        """
        columns_mapping = {}

        for col in df.columns:
            col_lower = str(col).lower().strip()

            # Identificar columna de municipio
            if any(keyword in col_lower for keyword in ["municipio", "mpio", "muni"]):
                columns_mapping[col] = "municipio"

            # Identificar columna de EAPB
            elif any(
                keyword in col_lower
                for keyword in ["eapb", "aseguradora", "eps", "entidad"]
            ):
                columns_mapping[col] = "eapb"

            # Identificar columna de total
            elif col_lower in [
                "total",
                "total general",
                "total_general",
                "suma",
                "sumatoria",
            ]:
                columns_mapping[col] = "total"

            # Identificar columnas de tipos de aseguramiento
            elif "contributivo" in col_lower:
                columns_mapping[col] = "contributivo"
            elif "subsidiado" in col_lower:
                columns_mapping[col] = "subsidiado"
            elif "especial" in col_lower or "regimen especial" in col_lower:
                columns_mapping[col] = "especial"
            elif "excepcion" in col_lower or "excepción" in col_lower:
                columns_mapping[col] = "excepcion"

            # Identificar mes y año
            elif col_lower in ["mes", "month"]:
                columns_mapping[col] = "mes"
            elif col_lower in ["año", "ano", "year", "anio"]:
                columns_mapping[col] = "año"

        st.write(f"🔍 **Mapeo de columnas identificado:**")
        for original, mapped in columns_mapping.items():
            st.write(f"  • '{original}' → '{mapped}'")

        return columns_mapping

    def _clean_and_standardize(self, df):
        """
        Limpia y estandariza los datos
        """
        df_clean = df.copy()

        # Limpiar valores nulos y vacíos
        df_clean = df_clean.fillna("")

        # Limpiar columna de municipio
        if "municipio" in df_clean.columns:
            df_clean["municipio"] = df_clean["municipio"].astype(str).str.strip()
            df_clean = df_clean[df_clean["municipio"] != ""]
            df_clean = df_clean[
                ~df_clean["municipio"].str.lower().isin(["nan", "null", ""])
            ]

        # Limpiar columna de EAPB
        if "eapb" in df_clean.columns:
            df_clean["eapb"] = df_clean["eapb"].astype(str).str.strip().str.title()
            df_clean = df_clean[df_clean["eapb"] != ""]
            df_clean = df_clean[~df_clean["eapb"].str.lower().isin(["nan", "null", ""])]

        # Convertir columnas numéricas
        numeric_columns = [
            "total",
            "contributivo",
            "subsidiado",
            "especial",
            "excepcion",
        ]
        for col in numeric_columns:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce").fillna(0)

        return df_clean

    def _extract_municipality_info(self, df):
        """
        Extrae información del municipio (código y nombre) si están combinados
        """
        df_processed = df.copy()

        if "municipio" in df_processed.columns:
            # Buscar patrón de código - nombre
            municipality_pattern = r"^(\d+)\s*-\s*(.+)$"

            def extract_municipality_info(municipality_str):
                match = re.match(municipality_pattern, str(municipality_str).strip())
                if match:
                    code = match.group(1).strip()
                    name = match.group(2).strip()
                    return pd.Series([code, name, name.upper()])
                else:
                    # Si no hay patrón, usar todo como nombre
                    clean_name = str(municipality_str).strip()
                    return pd.Series(["", clean_name, clean_name.upper()])

            # Aplicar extracción
            municipality_info = df_processed["municipio"].apply(
                extract_municipality_info
            )
            df_processed[
                ["codigo_municipio", "nombre_municipio", "nombre_municipio_upper"]
            ] = municipality_info

            # Normalizar nombres de municipios
            df_processed["nombre_municipio_norm"] = df_processed[
                "nombre_municipio"
            ].apply(self._normalize_municipality_name)

        return df_processed

    def _normalize_municipality_name(self, name):
        """
        Normaliza nombres de municipios para mejor matching
        """
        if pd.isna(name) or str(name).strip() == "":
            return "sin_nombre"

        # Convertir a string y limpiar
        name_clean = str(name).strip().lower()

        # Remover acentos
        name_clean = unicodedata.normalize("NFKD", name_clean)
        name_clean = "".join(c for c in name_clean if not unicodedata.combining(c))

        # Mapeos específicos para municipios del Tolima
        municipality_mappings = {
            "san sebastian de mariquita": "mariquita",
            "san sebastián de mariquita": "mariquita",
            "armero guayabal": "armero",
            "armero - guayabal": "armero",
            "valle de san juan": "valle_san_juan",
            "santa isabel": "santa_isabel",
            "san antonio": "san_antonio",
            "san luis": "san_luis",
        }

        return municipality_mappings.get(name_clean, name_clean)

    def _validate_and_filter(self, df):
        """
        Valida y filtra registros inválidos
        """
        df_valid = df.copy()

        # Filtrar registros sin municipio o EAPB
        initial_count = len(df_valid)

        df_valid = df_valid[
            (df_valid["municipio"] != "")
            & (df_valid["eapb"] != "")
            & (df_valid["total"] > 0)
        ]

        final_count = len(df_valid)
        removed_count = initial_count - final_count

        if removed_count > 0:
            st.warning(f"⚠️ Se removieron {removed_count} registros inválidos")

        # Validar que tenemos datos del Tolima
        tolima_keywords = ["tolima", "ibague", "espinal", "honda", "melgar", "girardot"]
        has_tolima_data = (
            df_valid["nombre_municipio_norm"]
            .apply(
                lambda x: any(keyword in str(x).lower() for keyword in tolima_keywords)
            )
            .any()
        )

        if not has_tolima_data:
            st.warning("⚠️ No se detectaron municipios del Tolima en los datos")

        return df_valid

    def _extract_metadata(self, df):
        """
        Extrae metadatos del procesamiento
        """
        if df is not None and len(df) > 0:
            self.processing_info.update(
                {
                    "total_records": len(df),
                    "total_eapb": df["eapb"].nunique() if "eapb" in df.columns else 0,
                    "total_municipalities": (
                        df["nombre_municipio"].nunique()
                        if "nombre_municipio" in df.columns
                        else 0
                    ),
                }
            )

            # Extraer mes y año si están disponibles
            if "mes" in df.columns:
                unique_months = df["mes"].dropna().unique()
                if len(unique_months) > 0:
                    self.processing_info["reference_month"] = unique_months[0]

            if "año" in df.columns:
                unique_years = df["año"].dropna().unique()
                if len(unique_years) > 0:
                    self.processing_info["reference_year"] = int(unique_years[0])

    def get_population_summary(self):
        """
        Retorna resumen de la población por EAPB
        """
        if self.population_data is None:
            return None

        summary = {
            "total_afiliados": self.population_data["total"].sum(),
            "total_eapb": self.population_data["eapb"].nunique(),
            "total_municipios": self.population_data["nombre_municipio"].nunique(),
            "top_eapb": self.population_data.groupby("eapb")["total"]
            .sum()
            .sort_values(ascending=False)
            .head(5),
            "top_municipios": self.population_data.groupby("nombre_municipio")["total"]
            .sum()
            .sort_values(ascending=False)
            .head(10),
        }

        return summary

    def get_population_by_municipality(self):
        """
        Retorna población agrupada por municipio
        """
        if self.population_data is None:
            return None

        municipality_summary = (
            self.population_data.groupby(["nombre_municipio", "nombre_municipio_norm"])
            .agg(
                {
                    "total": "sum",
                    "contributivo": "sum",
                    "subsidiado": "sum",
                    "especial": "sum",
                    "excepcion": "sum",
                    "eapb": "nunique",
                }
            )
            .reset_index()
        )

        municipality_summary.columns = [
            "municipio",
            "municipio_norm",
            "total_poblacion",
            "contributivo",
            "subsidiado",
            "especial",
            "excepcion",
            "num_eapb",
        ]

        return municipality_summary

    def get_population_by_eapb(self):
        """
        Retorna población agrupada por EAPB
        """
        if self.population_data is None:
            return None

        eapb_summary = (
            self.population_data.groupby("eapb")
            .agg(
                {
                    "total": "sum",
                    "contributivo": "sum",
                    "subsidiado": "sum",
                    "especial": "sum",
                    "excepcion": "sum",
                    "nombre_municipio": "nunique",
                }
            )
            .reset_index()
        )

        eapb_summary.columns = [
            "eapb",
            "total_afiliados",
            "contributivo",
            "subsidiado",
            "especial",
            "excepcion",
            "num_municipios",
        ]

        return eapb_summary.sort_values("total_afiliados", ascending=False)

    def get_processing_info(self):
        """
        Retorna información del procesamiento
        """
        return self.processing_info.copy()

    def show_processing_summary(self):
        """
        Muestra resumen del procesamiento
        """
        st.subheader("📊 Resumen del Procesamiento de Población por EAPB")

        info = self.processing_info

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Registros", f"{info['total_records']:,}".replace(",", "."))

        with col2:
            st.metric("Total EAPB", info["total_eapb"])

        with col3:
            st.metric("Total Municipios", info["total_municipalities"])

        with col4:
            ref_date = "No disponible"
            if info["reference_month"] and info["reference_year"]:
                ref_date = f"{info['reference_month']}/{info['reference_year']}"
            st.metric("Fecha Referencia", ref_date)

        # Mostrar resumen si hay datos
        if self.population_data is not None:
            summary = self.get_population_summary()

            if summary:
                st.markdown("### 🏥 Top 5 EAPB por Afiliados")
                top_eapb_df = summary["top_eapb"].reset_index()
                top_eapb_df.columns = ["EAPB", "Total Afiliados"]
                top_eapb_df["Total Afiliados"] = top_eapb_df["Total Afiliados"].apply(
                    lambda x: f"{x:,}".replace(",", ".")
                )
                st.dataframe(top_eapb_df, use_container_width=True)

                st.markdown("### 🏘️ Top 10 Municipios por Población")
                top_mun_df = summary["top_municipios"].reset_index()
                top_mun_df.columns = ["Municipio", "Total Población"]
                top_mun_df["Total Población"] = top_mun_df["Total Población"].apply(
                    lambda x: f"{x:,}".replace(",", ".")
                )
                st.dataframe(top_mun_df, use_container_width=True)


def process_population_eapb(data_dir="data", filename="Poblacion_aseguramiento.xlsx"):
    """
    Función de conveniencia para procesar población por EAPB
    """
    processor = PopulationEAPBProcessor(data_dir)
    population_data = processor.load_population_data(filename)

    if population_data is not None:
        processor.show_processing_summary()
        return {
            "data": population_data,
            "processor": processor,
            "summary": processor.get_population_summary(),
            "by_municipality": processor.get_population_by_municipality(),
            "by_eapb": processor.get_population_by_eapb(),
            "metadata": processor.get_processing_info(),
        }
    else:
        return None


def test_population_processor():
    """
    Función de prueba del procesador de población
    """
    st.title("🧪 Prueba del Procesador de Población por EAPB")

    result = process_population_eapb()

    if result:
        st.success("✅ Procesamiento exitoso")

        # Mostrar datos procesados
        st.subheader("📊 Datos Procesados")
        st.dataframe(result["data"].head(10), use_container_width=True)

        # Mostrar resúmenes
        if result["by_municipality"] is not None:
            st.subheader("🏘️ Resumen por Municipio")
            st.dataframe(result["by_municipality"], use_container_width=True)

        if result["by_eapb"] is not None:
            st.subheader("🏥 Resumen por EAPB")
            st.dataframe(result["by_eapb"], use_container_width=True)
    else:
        st.error("❌ Error en el procesamiento")


if __name__ == "__main__":
    test_population_processor()
