"""
src/data/vaccination_combiner.py
Combinador inteligente de las dos bases de vacunación:
- vacunacion_fa.csv (histórica pre-emergencia)
- Resumen.xlsx (brigadas emergencia)
Usa la fecha más antigua de Resumen como punto de corte
"""

import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path
from datetime import datetime, date
import warnings


class VaccinationCombiner:
    """
    Combinador inteligente de bases de vacunación con división temporal automática
    """

    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.historical_data = None
        self.brigades_data = None
        self.combined_data = None
        self.cutoff_date = None
        self.processing_info = {
            "cutoff_date": None,
            "historical_records": 0,
            "brigades_records": 0,
            "combined_records": 0,
            "historical_date_range": None,
            "brigades_date_range": None,
            "processing_date": datetime.now(),
            "data_integrity_check": {},
        }

    def load_and_combine_data(
        self, historical_file="vacunacion_fa.csv", brigades_file="Resumen.xlsx"
    ):
        """
        Carga y combina ambas bases de datos usando fecha de corte automática
        """
        st.info("🔄 Iniciando combinación de bases de vacunación...")

        # PASO 1: Cargar brigadas para determinar fecha de corte
        st.info("📅 **PASO 1:** Determinando fecha de corte desde brigadas...")
        brigades_data = self._load_brigades_data(brigades_file)

        if brigades_data is None:
            st.error("❌ No se pudo cargar datos de brigadas")
            return None

        # PASO 2: Determinar fecha de corte
        cutoff_date = self._determine_cutoff_date(brigades_data)

        if cutoff_date is None:
            st.error("❌ No se pudo determinar fecha de corte")
            return None

        self.cutoff_date = cutoff_date
        st.success(
            f"✅ **Fecha de corte determinada:** {cutoff_date.strftime('%d/%m/%Y')}"
        )

        # PASO 3: Cargar datos históricos con filtro de fecha
        st.info("📚 **PASO 2:** Cargando datos históricos...")
        historical_data = self._load_historical_data(historical_file, cutoff_date)

        if historical_data is None:
            st.warning("⚠️ No se pudieron cargar datos históricos")
            historical_data = pd.DataFrame()

        # PASO 4: Filtrar brigadas desde fecha de corte
        st.info("🚨 **PASO 3:** Filtrando brigadas desde fecha de corte...")
        brigades_filtered = self._filter_brigades_from_cutoff(
            brigades_data, cutoff_date
        )

        # PASO 5: Combinar y estandarizar
        st.info("🔗 **PASO 4:** Combinando y estandarizando datos...")
        combined_data = self._combine_and_standardize(
            historical_data, brigades_filtered
        )

        if combined_data is not None:
            self.historical_data = historical_data
            self.brigades_data = brigades_filtered
            self.combined_data = combined_data
            self._calculate_processing_info()

            st.success(
                f"✅ **Combinación exitosa:** {len(combined_data)} registros totales"
            )
            self._show_combination_summary()

            return combined_data
        else:
            st.error("❌ Error en la combinación de datos")
            return None

    def _load_brigades_data(self, filename):
        """
        Carga datos de brigadas desde Resumen.xlsx
        """
        file_path = self.data_dir / filename

        if not file_path.exists():
            st.error(f"❌ Archivo {filename} no encontrado")
            return None

        try:
            # Leer archivo Excel
            with pd.ExcelFile(file_path) as excel_file:
                sheet_names = excel_file.sheet_names
                st.write(f"📄 Hojas en {filename}: {', '.join(sheet_names)}")

                # Buscar hoja de vacunación
                sheet_name = None
                for name in sheet_names:
                    if "vacunacion" in name.lower():
                        sheet_name = name
                        break

                if sheet_name is None:
                    sheet_name = sheet_names[0]
                    st.info(f"📄 Usando hoja: {sheet_name}")

                df = pd.read_excel(file_path, sheet_name=sheet_name)

                st.success(
                    f"✅ Brigadas cargadas: {len(df)} registros desde '{sheet_name}'"
                )

                # Mostrar estructura
                st.write(f"📊 Columnas: {list(df.columns)}")

                return df

        except Exception as e:
            st.error(f"❌ Error cargando brigadas: {str(e)}")
            return None

    def _determine_cutoff_date(self, brigades_df):
        """
        Determina la fecha de corte como la fecha MÁS ANTIGUA en los datos de brigadas
        """
        # Buscar columnas de fecha
        date_columns = []
        for col in brigades_df.columns:
            col_lower = str(col).lower().strip()
            if any(keyword in col_lower for keyword in ["fecha", "date", "dia"]):
                date_columns.append(col)

        if not date_columns:
            st.error("❌ No se encontraron columnas de fecha en brigadas")
            return None

        st.write(f"📅 Columnas de fecha encontradas: {date_columns}")

        # Probar cada columna de fecha
        valid_dates = []

        for col in date_columns:
            try:
                # Convertir a datetime
                dates_series = pd.to_datetime(brigades_df[col], errors="coerce")

                # Filtrar fechas válidas
                valid_dates_in_col = dates_series.dropna()

                if len(valid_dates_in_col) > 0:
                    st.write(
                        f"✅ Columna '{col}': {len(valid_dates_in_col)} fechas válidas"
                    )
                    st.write(
                        f"  Rango: {valid_dates_in_col.min().strftime('%d/%m/%Y')} - {valid_dates_in_col.max().strftime('%d/%m/%Y')}"
                    )
                    valid_dates.extend(valid_dates_in_col.tolist())
                else:
                    st.write(f"⚠️ Columna '{col}': No hay fechas válidas")

            except Exception as e:
                st.write(f"❌ Error procesando columna '{col}': {str(e)}")

        if not valid_dates:
            st.error("❌ No se encontraron fechas válidas en ninguna columna")
            return None

        # Encontrar la fecha MÁS ANTIGUA
        cutoff_date = min(valid_dates)

        st.success(
            f"🎯 **Fecha de corte (más antigua):** {cutoff_date.strftime('%d/%m/%Y')}"
        )
        st.info(f"📋 **Lógica aplicada:**")
        st.info(
            f"  • Todo ANTES del {cutoff_date.strftime('%d/%m/%Y')} → Base histórica"
        )
        st.info(f"  • Todo DESDE el {cutoff_date.strftime('%d/%m/%Y')} → Base brigadas")

        return cutoff_date

    def _load_historical_data(self, filename, cutoff_date):
        """
        Carga datos históricos ANTES de la fecha de corte
        """
        file_path = self.data_dir / filename

        if not file_path.exists():
            st.warning(f"⚠️ Archivo histórico {filename} no encontrado")
            return pd.DataFrame()

        try:
            # Leer CSV
            df = pd.read_csv(file_path, low_memory=False)

            st.write(f"📚 Datos históricos cargados: {len(df)} registros")
            st.write(f"📊 Columnas: {list(df.columns)}")

            # Buscar columna de fecha de vacunación
            date_col = None
            for col in df.columns:
                if "FA UNICA" in str(col) or "fecha" in str(col).lower():
                    date_col = col
                    break

            if date_col is None:
                st.error("❌ No se encontró columna de fecha en datos históricos")
                return pd.DataFrame()

            # Convertir fechas
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

            # Filtrar ANTES de la fecha de corte
            df_filtered = df[df[date_col] < cutoff_date].copy()

            st.success(
                f"✅ Datos históricos filtrados: {len(df_filtered)} registros antes del {cutoff_date.strftime('%d/%m/%Y')}"
            )

            if len(df_filtered) > 0:
                date_range = f"{df_filtered[date_col].min().strftime('%d/%m/%Y')} - {df_filtered[date_col].max().strftime('%d/%m/%Y')}"
                st.info(f"📅 Rango histórico: {date_range}")

            return df_filtered

        except Exception as e:
            st.error(f"❌ Error cargando datos históricos: {str(e)}")
            return pd.DataFrame()

    def _filter_brigades_from_cutoff(self, brigades_df, cutoff_date):
        """
        Filtra brigadas DESDE la fecha de corte (inclusive)
        """
        try:
            # Buscar la columna de fecha principal
            date_col = None
            for col in brigades_df.columns:
                col_lower = str(col).lower().strip()
                if "fecha" in col_lower:
                    date_col = col
                    break

            if date_col is None:
                st.warning(
                    "⚠️ No se encontró columna de fecha en brigadas, usando todos los datos"
                )
                return brigades_df.copy()

            # Convertir fechas
            brigades_df[date_col] = pd.to_datetime(
                brigades_df[date_col], errors="coerce"
            )

            # Filtrar DESDE la fecha de corte (inclusive)
            df_filtered = brigades_df[brigades_df[date_col] >= cutoff_date].copy()

            st.success(
                f"✅ Brigadas filtradas: {len(df_filtered)} registros desde el {cutoff_date.strftime('%d/%m/%Y')}"
            )

            if len(df_filtered) > 0:
                date_range = f"{df_filtered[date_col].min().strftime('%d/%m/%Y')} - {df_filtered[date_col].max().strftime('%d/%m/%Y')}"
                st.info(f"📅 Rango brigadas: {date_range}")

            return df_filtered

        except Exception as e:
            st.error(f"❌ Error filtrando brigadas: {str(e)}")
            return brigades_df.copy()

    def _combine_and_standardize(self, historical_df, brigades_df):
        """
        Combina y estandariza ambas bases de datos
        """
        try:
            combined_records = []

            # PARTE 1: Procesar datos históricos
            if len(historical_df) > 0:
                st.info("🔄 Procesando datos históricos...")
                historical_standardized = self._standardize_historical_data(
                    historical_df
                )
                combined_records.append(historical_standardized)
                st.success(
                    f"✅ Históricos estandarizados: {len(historical_standardized)} registros"
                )

            # PARTE 2: Procesar datos de brigadas
            if len(brigades_df) > 0:
                st.info("🔄 Procesando datos de brigadas...")
                brigades_standardized = self._standardize_brigades_data(brigades_df)
                combined_records.append(brigades_standardized)
                st.success(
                    f"✅ Brigadas estandarizadas: {len(brigades_standardized)} registros"
                )

            # PARTE 3: Combinar todo
            if combined_records:
                combined_df = pd.concat(combined_records, ignore_index=True, sort=False)

                # Limpiar y validar datos combinados
                combined_df = self._clean_combined_data(combined_df)

                st.success(f"✅ Datos combinados: {len(combined_df)} registros totales")

                return combined_df
            else:
                st.error("❌ No hay datos para combinar")
                return None

        except Exception as e:
            st.error(f"❌ Error combinando datos: {str(e)}")
            return None

    def _standardize_historical_data(self, df):
        """
        Estandariza datos históricos con cálculo de edad actual
        """
        standardized = pd.DataFrame()

        # Mapear columnas estándar
        column_mapping = {
            "IdPaciente": "id_paciente",
            "Documento": "documento",
            "PrimerNombre": "primer_nombre",
            "PrimerApellido": "primer_apellido",
            "Sexo": "sexo",
            "FechaNacimiento": "fecha_nacimiento",
            "NombreMunicipioResidencia": "municipio_residencia",
            "GrupoEtnico": "grupo_etnico",
            "Desplazado": "desplazado",
            "Discapacitado": "discapacitado",
            "RegimenAfiliacion": "regimen_afiliacion",
            "NombreAseguradora": "nombre_aseguradora",
            "FA UNICA": "fecha_vacunacion",
        }

        # Copiar columnas disponibles
        for original, standard in column_mapping.items():
            if original in df.columns:
                standardized[standard] = df[original].copy()

        # Calcular edad ACTUAL (no al momento de vacunación)
        if "fecha_nacimiento" in standardized.columns:
            standardized["fecha_nacimiento"] = pd.to_datetime(
                standardized["fecha_nacimiento"], errors="coerce"
            )
            standardized["edad_actual"] = standardized["fecha_nacimiento"].apply(
                lambda x: self._calculate_current_age(x) if pd.notna(x) else None
            )
            standardized["grupo_edad"] = standardized["edad_actual"].apply(
                self._categorize_age
            )

        # Convertir fecha de vacunación
        if "fecha_vacunacion" in standardized.columns:
            standardized["fecha_vacunacion"] = pd.to_datetime(
                standardized["fecha_vacunacion"], errors="coerce"
            )

        # Marcar como datos históricos
        standardized["tipo_registro"] = "historico"
        standardized["periodo"] = "pre_emergencia"

        return standardized

    def _standardize_brigades_data(self, df):
        """
        Estandariza datos de brigadas de emergencia
        """
        standardized = pd.DataFrame()

        # Buscar y mapear columnas disponibles
        for col in df.columns:
            col_lower = str(col).lower().strip()

            if "fecha" in col_lower:
                standardized["fecha_vacunacion"] = pd.to_datetime(
                    df[col], errors="coerce"
                )
            elif "municipio" in col_lower:
                standardized["municipio_residencia"] = (
                    df[col].astype(str).str.strip().str.title()
                )
            elif "vereda" in col_lower:
                standardized["vereda"] = df[col].astype(str).str.strip().str.title()
            elif "efectiva" in col_lower and "no" not in col_lower:
                standardized["visitas_efectivas"] = pd.to_numeric(
                    df[col], errors="coerce"
                ).fillna(0)
            elif "tpvb" in col_lower:
                standardized["poblacion_vacunada_brigada"] = pd.to_numeric(
                    df[col], errors="coerce"
                ).fillna(0)

        # Marcar como datos de brigadas
        standardized["tipo_registro"] = "brigada"
        standardized["periodo"] = "emergencia"

        # Para brigadas, no tenemos datos individuales sino agregados
        # Crear registros sintéticos basados en poblacion_vacunada_brigada
        if "poblacion_vacunada_brigada" in standardized.columns:
            # Expandir registros según población vacunada
            expanded_records = []

            for idx, row in standardized.iterrows():
                vacunados = int(row.get("poblacion_vacunada_brigada", 0))

                if vacunados > 0:
                    for i in range(vacunados):
                        new_record = row.copy()
                        new_record["id_paciente"] = f"BRIGADA_{idx}_{i}"
                        new_record["sexo"] = "Sin dato"  # No disponible en brigadas
                        new_record["edad_actual"] = None
                        new_record["grupo_edad"] = "Sin dato"
                        expanded_records.append(new_record)

            if expanded_records:
                expanded_df = pd.DataFrame(expanded_records)
                return expanded_df

        return standardized

    def _calculate_current_age(self, birth_date):
        """
        Calcula edad actual basada en fecha de nacimiento
        """
        if pd.isna(birth_date):
            return None

        try:
            today = date.today()
            age = (
                today.year
                - birth_date.year
                - ((today.month, today.day) < (birth_date.month, birth_date.day))
            )
            return max(0, age)  # Evitar edades negativas
        except:
            return None

    def _categorize_age(self, age):
        """
        Categoriza edad en grupos estándar
        """
        if pd.isna(age) or age is None:
            return "Sin dato"

        age = int(age)

        if age < 1:
            return "Menor de 1 año"
        elif age <= 4:
            return "1 a 4 años"
        elif age <= 9:
            return "5 a 9 años"
        elif age <= 19:
            return "10 a 19 años"
        elif age <= 29:
            return "20 a 29 años"
        elif age <= 39:
            return "30 a 39 años"
        elif age <= 49:
            return "40 a 49 años"
        elif age <= 59:
            return "50 a 59 años"
        elif age <= 69:
            return "60 a 69 años"
        else:
            return "70 años o más"

    def _clean_combined_data(self, df):
        """
        Limpia y valida datos combinados
        """
        df_clean = df.copy()

        # Limpiar valores nulos en columnas críticas
        string_columns = [
            "sexo",
            "municipio_residencia",
            "grupo_etnico",
            "regimen_afiliacion",
            "nombre_aseguradora",
        ]
        for col in string_columns:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].fillna("Sin dato")
                df_clean[col] = df_clean[col].replace(
                    ["", "nan", "NaN", "null"], "Sin dato"
                )

        # Validar fechas
        if "fecha_vacunacion" in df_clean.columns:
            df_clean = df_clean[df_clean["fecha_vacunacion"].notna()]

        # Remover duplicados basado en id_paciente si existe
        if "id_paciente" in df_clean.columns:
            initial_count = len(df_clean)
            df_clean = df_clean.drop_duplicates(subset=["id_paciente"], keep="first")
            final_count = len(df_clean)

            if initial_count != final_count:
                st.info(f"🔄 Duplicados removidos: {initial_count - final_count}")

        return df_clean

    def _calculate_processing_info(self):
        """
        Calcula información del procesamiento
        """
        self.processing_info.update(
            {
                "cutoff_date": self.cutoff_date,
                "historical_records": (
                    len(self.historical_data) if self.historical_data is not None else 0
                ),
                "brigades_records": (
                    len(self.brigades_data) if self.brigades_data is not None else 0
                ),
                "combined_records": (
                    len(self.combined_data) if self.combined_data is not None else 0
                ),
            }
        )

        # Rangos de fechas
        if self.historical_data is not None and len(self.historical_data) > 0:
            if "fecha_vacunacion" in self.combined_data.columns:
                hist_dates = self.combined_data[
                    self.combined_data["periodo"] == "pre_emergencia"
                ]["fecha_vacunacion"]
                if len(hist_dates) > 0:
                    self.processing_info["historical_date_range"] = (
                        hist_dates.min(),
                        hist_dates.max(),
                    )

        if self.brigades_data is not None and len(self.brigades_data) > 0:
            if "fecha_vacunacion" in self.combined_data.columns:
                brig_dates = self.combined_data[
                    self.combined_data["periodo"] == "emergencia"
                ]["fecha_vacunacion"]
                if len(brig_dates) > 0:
                    self.processing_info["brigades_date_range"] = (
                        brig_dates.min(),
                        brig_dates.max(),
                    )

    def _show_combination_summary(self):
        """
        Muestra resumen de la combinación
        """
        st.subheader("📊 Resumen de Combinación de Datos")

        info = self.processing_info

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Fecha de Corte",
                (
                    info["cutoff_date"].strftime("%d/%m/%Y")
                    if info["cutoff_date"]
                    else "N/A"
                ),
            )

        with col2:
            st.metric(
                "Datos Históricos", f"{info['historical_records']:,}".replace(",", ".")
            )

        with col3:
            st.metric(
                "Datos Brigadas", f"{info['brigades_records']:,}".replace(",", ".")
            )

        with col4:
            st.metric(
                "Total Combinado", f"{info['combined_records']:,}".replace(",", ".")
            )

        # Información de rangos de fechas
        if info["historical_date_range"]:
            start, end = info["historical_date_range"]
            st.info(
                f"📅 **Período Histórico:** {start.strftime('%d/%m/%Y')} - {end.strftime('%d/%m/%Y')}"
            )

        if info["brigades_date_range"]:
            start, end = info["brigades_date_range"]
            st.info(
                f"🚨 **Período Emergencia:** {start.strftime('%d/%m/%Y')} - {end.strftime('%d/%m/%Y')}"
            )

    def get_combined_data(self):
        """
        Retorna datos combinados
        """
        return self.combined_data

    def get_historical_data(self):
        """
        Retorna solo datos históricos
        """
        if self.combined_data is not None:
            return self.combined_data[self.combined_data["periodo"] == "pre_emergencia"]
        return None

    def get_brigades_data(self):
        """
        Retorna solo datos de brigadas
        """
        if self.combined_data is not None:
            return self.combined_data[self.combined_data["periodo"] == "emergencia"]
        return None

    def get_processing_info(self):
        """
        Retorna información del procesamiento
        """
        return self.processing_info.copy()


def combine_vaccination_data(
    data_dir="data", historical_file="vacunacion_fa.csv", brigades_file="Resumen.xlsx"
):
    """
    Función de conveniencia para combinar datos de vacunación
    """
    combiner = VaccinationCombiner(data_dir)
    combined_data = combiner.load_and_combine_data(historical_file, brigades_file)

    if combined_data is not None:
        return {
            "combined": combined_data,
            "historical": combiner.get_historical_data(),
            "brigades": combiner.get_brigades_data(),
            "metadata": combiner.get_processing_info(),
            "combiner": combiner,
        }
    else:
        return None


def test_vaccination_combiner():
    """
    Función de prueba del combinador
    """
    st.title("🧪 Prueba del Combinador de Vacunación")

    result = combine_vaccination_data()

    if result:
        st.success("✅ Combinación exitosa")

        # Mostrar datos combinados
        st.subheader("📊 Datos Combinados")
        st.dataframe(result["combined"].head(10), use_container_width=True)

        # Mostrar distribución por período
        if "periodo" in result["combined"].columns:
            period_counts = result["combined"]["periodo"].value_counts()
            st.subheader("📈 Distribución por Período")

            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Pre-emergencia",
                    f"{period_counts.get('pre_emergencia', 0):,}".replace(",", "."),
                )
            with col2:
                st.metric(
                    "Emergencia",
                    f"{period_counts.get('emergencia', 0):,}".replace(",", "."),
                )
    else:
        st.error("❌ Error en la combinación")


if __name__ == "__main__":
    test_vaccination_combiner()
