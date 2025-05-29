"""
src/data/unified_loader.py
Cargador unificado para todas las fuentes de datos del dashboard.
Maneja población por EAPB, vacunación histórica y brigadas de emergencia.
VERSIÓN CORREGIDA - Eliminadas definiciones conflictivas
"""

import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path
from datetime import datetime, date
import warnings
import traceback
from .preprocessor import clean_dates, clean_age, normalize_municipality_names
from .data_cleaner import clean_data, calculate_current_age
from .vaccination_combiner import combine_vaccination_data
import os
from typing import Union, Optional

# Configuración de rutas
DATA_DIR = Path(__file__).parent.parent.parent / "data"

# Configuración de fechas críticas
FECHA_EMERGENCIA = pd.Timestamp("2024-09-01")  # Fecha de inicio de emergencia
FECHA_ACTUAL = pd.Timestamp.now()
FECHA_REFERENCIA_POBLACION = pd.Timestamp(
    "2025-04-01"
)  # Fecha de referencia población EAPB


class UnifiedDataLoader:
    """
    Cargador unificado que maneja todas las fuentes de datos del dashboard
    """

    def __init__(self):
        self.data = {}
        self.metadata = {
            "fecha_actualizacion": None,
            "fecha_emergencia": FECHA_EMERGENCIA,
            "fecha_poblacion_eapb": FECHA_REFERENCIA_POBLACION,
            "total_registros_historicos": 0,
            "total_registros_emergencia": 0,
            "fecha_mas_antigua": None,
            "fecha_mas_reciente": None,
        }
        self.errors = []
        self.warnings = []

    def load_all_data(self):
        """
        Carga todas las fuentes de datos de manera unificada
        """
        st.info("🔄 Iniciando carga unificada de datos...")

        try:
            # 1. Cargar población por EAPB (nueva base)
            self._load_population_eapb()

            # 2. Cargar vacunación histórica
            self._load_historical_vaccination()

            # 3. Cargar brigadas de emergencia
            self._load_emergency_brigades()

            # 4. Determinar fechas de corte y metadatos
            self._calculate_metadata()

            # 5. Validar integridad de datos
            self._validate_data_integrity()

            st.success(f"✅ Datos cargados exitosamente")
            self._show_loading_summary()

            return self.data, self.metadata

        except Exception as e:
            st.error(f"❌ Error crítico en carga de datos: {str(e)}")
            st.error("📋 Detalles del error:")
            st.code(traceback.format_exc())
            return None, None

    def _load_population_eapb(self):
        """
        Carga archivo Poblacion_aseguramiento.xlsx
        """
        st.info("📊 Cargando población por EAPB...")

        file_path = DATA_DIR / "Poblacion_aseguramiento.xlsx"

        if not file_path.exists():
            error_msg = f"Archivo {file_path} no encontrado"
            self.errors.append(error_msg)
            st.error(f"❌ {error_msg}")
            return

        try:
            # Leer todas las hojas para análisis
            with pd.ExcelFile(file_path) as excel_file:
                sheet_names = excel_file.sheet_names
                st.write(f"📄 Hojas encontradas: {', '.join(sheet_names)}")

                # Usar la primera hoja o buscar hoja específica
                if "Hoja1" in sheet_names:
                    sheet_name = "Hoja1"
                elif len(sheet_names) > 0:
                    sheet_name = sheet_names[0]
                else:
                    raise ValueError("No se encontraron hojas en el archivo")

                df = pd.read_excel(file_path, sheet_name=sheet_name)

                st.success(
                    f"✅ Población EAPB cargada: {len(df)} registros de {sheet_name}"
                )

                # Mostrar estructura para verificación
                st.write(f"📋 Columnas detectadas: {list(df.columns)}")
                st.write(f"📊 Muestra de datos:")
                st.dataframe(df.head(3), use_container_width=True)

                self.data["poblacion_eapb"] = df

        except Exception as e:
            error_msg = f"Error cargando población EAPB: {str(e)}"
            self.errors.append(error_msg)
            st.error(f"❌ {error_msg}")

    def _load_historical_vaccination(self):
        """
        Carga vacunacion_fa.csv (datos históricos pre-emergencia)
        """
        st.info("📈 Cargando vacunación histórica...")

        file_path = DATA_DIR / "vacunacion_fa.csv"

        if not file_path.exists():
            warning_msg = (
                f"Archivo {file_path} no encontrado - continuando sin datos históricos"
            )
            self.warnings.append(warning_msg)
            st.warning(f"⚠️ {warning_msg}")
            self.data["vacunacion_historica"] = pd.DataFrame()
            return

        try:
            # Leer CSV con configuraciones optimizadas
            df = pd.read_csv(
                file_path,
                low_memory=False,
                encoding="utf-8",
                parse_dates=["FA UNICA", "FechaNacimiento"],
                date_parser=pd.to_datetime,
                na_values=["", "nan", "NaN", "null", "NULL", "None"],
            )

            # Filtrar solo datos PRE-emergencia
            if "FA UNICA" in df.columns:
                df["FA UNICA"] = pd.to_datetime(df["FA UNICA"], errors="coerce")
                df_filtered = df[df["FA UNICA"] < FECHA_EMERGENCIA].copy()

                st.success(
                    f"✅ Vacunación histórica cargada: {len(df_filtered)} registros (pre-emergencia)"
                )
                st.info(
                    f"📅 Registros filtrados hasta: {FECHA_EMERGENCIA.strftime('%d/%m/%Y')}"
                )

                self.data["vacunacion_historica"] = df_filtered

            else:
                st.warning("⚠️ Columna 'FA UNICA' no encontrada en datos históricos")
                self.data["vacunacion_historica"] = df

        except Exception as e:
            error_msg = f"Error cargando vacunación histórica: {str(e)}"
            self.errors.append(error_msg)
            st.error(f"❌ {error_msg}")
            self.data["vacunacion_historica"] = pd.DataFrame()

    def _load_emergency_brigades(self):
        """
        Carga Resumen.xlsx (brigadas de emergencia post-septiembre)
        """
        st.info("🚨 Cargando brigadas de emergencia...")

        file_path = DATA_DIR / "Resumen.xlsx"

        if not file_path.exists():
            warning_msg = (
                f"Archivo {file_path} no encontrado - continuando sin datos de brigadas"
            )
            self.warnings.append(warning_msg)
            st.warning(f"⚠️ {warning_msg}")
            self.data["brigadas_emergencia"] = pd.DataFrame()
            return

        try:
            # Leer archivo de brigadas
            with pd.ExcelFile(file_path) as excel_file:
                sheet_names = excel_file.sheet_names
                st.write(f"📄 Hojas de brigadas: {', '.join(sheet_names)}")

                # Buscar hoja de Vacunacion
                if "Vacunacion" in sheet_names:
                    df = pd.read_excel(file_path, sheet_name="Vacunacion")
                elif len(sheet_names) > 0:
                    df = pd.read_excel(file_path, sheet_name=sheet_names[0])
                    st.info(f"📄 Usando hoja: {sheet_names[0]}")
                else:
                    raise ValueError("No se encontraron hojas válidas")

                # Convertir fechas si existe columna FECHA
                if "FECHA" in df.columns:
                    df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")

                    # Filtrar solo datos POST-emergencia
                    df_filtered = df[df["FECHA"] >= FECHA_EMERGENCIA].copy()

                    st.success(
                        f"✅ Brigadas emergencia cargadas: {len(df_filtered)} registros (post-emergencia)"
                    )

                    self.data["brigadas_emergencia"] = df_filtered
                else:
                    st.warning("⚠️ Columna FECHA no encontrada en brigadas")
                    self.data["brigadas_emergencia"] = df

        except Exception as e:
            error_msg = f"Error cargando brigadas emergencia: {str(e)}"
            self.errors.append(error_msg)
            st.error(f"❌ {error_msg}")
            self.data["brigadas_emergencia"] = pd.DataFrame()

    def _calculate_metadata(self):
        """
        Calcula metadatos del conjunto de datos completo
        """
        try:
            # Contar registros
            self.metadata["total_registros_historicos"] = len(
                self.data.get("vacunacion_historica", pd.DataFrame())
            )
            self.metadata["total_registros_emergencia"] = len(
                self.data.get("brigadas_emergencia", pd.DataFrame())
            )

            # Calcular fechas extremas
            fechas_historicas = []
            fechas_emergencia = []

            # Fechas históricas
            if not self.data.get("vacunacion_historica", pd.DataFrame()).empty:
                hist_df = self.data["vacunacion_historica"]
                if "FA UNICA" in hist_df.columns:
                    fechas_validas = hist_df["FA UNICA"].dropna()
                    if len(fechas_validas) > 0:
                        fechas_historicas.extend(fechas_validas.tolist())

            # Fechas emergencia
            if not self.data.get("brigadas_emergencia", pd.DataFrame()).empty:
                emerg_df = self.data["brigadas_emergencia"]
                if "FECHA" in emerg_df.columns:
                    fechas_validas = emerg_df["FECHA"].dropna()
                    if len(fechas_validas) > 0:
                        fechas_emergencia.extend(fechas_validas.tolist())

            # Combinar todas las fechas
            todas_fechas = fechas_historicas + fechas_emergencia

            if todas_fechas:
                self.metadata["fecha_mas_antigua"] = min(todas_fechas)
                self.metadata["fecha_mas_reciente"] = max(todas_fechas)
                self.metadata["fecha_actualizacion"] = self.metadata[
                    "fecha_mas_reciente"
                ]
            else:
                self.metadata["fecha_actualizacion"] = FECHA_ACTUAL

        except Exception as e:
            st.warning(f"⚠️ Error calculando metadatos: {str(e)}")
            self.metadata["fecha_actualizacion"] = FECHA_ACTUAL

    def _validate_data_integrity(self):
        """
        Valida la integridad de los datos cargados
        """
        st.info("🔍 Validando integridad de datos...")

        validation_results = []

        # Validar población EAPB
        if "poblacion_eapb" in self.data and not self.data["poblacion_eapb"].empty:
            df = self.data["poblacion_eapb"]
            validation_results.append(f"✅ Población EAPB: {len(df)} registros")

            # Verificar estructura esperada
            expected_patterns = ["municipio", "eapb", "total"]
            found_patterns = []
            for col in df.columns:
                col_lower = str(col).lower()
                for pattern in expected_patterns:
                    if pattern in col_lower:
                        found_patterns.append(pattern)
                        break

            if len(found_patterns) >= 2:
                validation_results.append(f"✅ Estructura válida: {found_patterns}")
            else:
                validation_results.append(f"⚠️ Estructura incierta: revisar columnas")

        # Validar datos de vacunación
        total_vacunacion = 0
        if not self.data.get("vacunacion_historica", pd.DataFrame()).empty:
            total_vacunacion += len(self.data["vacunacion_historica"])
            validation_results.append(
                f"✅ Vacunación histórica: {len(self.data['vacunacion_historica'])} registros"
            )

        if not self.data.get("brigadas_emergencia", pd.DataFrame()).empty:
            # Contar registros individuales de vacunación de brigadas si es posible
            brigadas_count = len(self.data["brigadas_emergencia"])
            validation_results.append(
                f"✅ Brigadas emergencia: {brigadas_count} operaciones"
            )

        # Mostrar resultados
        for result in validation_results:
            st.write(result)

        # Validar consistencia temporal
        if (
            self.metadata["fecha_mas_antigua"]
            and self.metadata["fecha_mas_reciente"]
            and self.metadata["fecha_mas_antigua"]
            <= self.metadata["fecha_mas_reciente"]
        ):
            st.success(f"✅ Consistencia temporal validada")
        else:
            st.warning("⚠️ Posible inconsistencia temporal en los datos")

    def _show_loading_summary(self):
        """
        Muestra resumen de la carga de datos
        """
        st.markdown("---")
        st.subheader("📋 Resumen de Carga de Datos")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### 📊 Población EAPB")
            if "poblacion_eapb" in self.data:
                st.metric("Registros", len(self.data["poblacion_eapb"]))
                st.caption(
                    f"Referencia: {FECHA_REFERENCIA_POBLACION.strftime('%m/%Y')}"
                )
            else:
                st.error("No cargado")

        with col2:
            st.markdown("### 📈 Vacunación Histórica")
            count = len(self.data.get("vacunacion_historica", pd.DataFrame()))
            st.metric("Registros", f"{count:,}".replace(",", "."))
            st.caption(f"Hasta: {FECHA_EMERGENCIA.strftime('%d/%m/%Y')}")

        with col3:
            st.markdown("### 🚨 Brigadas Emergencia")
            count = len(self.data.get("brigadas_emergencia", pd.DataFrame()))
            st.metric("Operaciones", count)
            st.caption(f"Desde: {FECHA_EMERGENCIA.strftime('%d/%m/%Y')}")

        # Información temporal
        if self.metadata["fecha_actualizacion"]:
            st.info(
                f"📅 **Última actualización:** {self.metadata['fecha_actualizacion'].strftime('%d/%m/%Y %H:%M')}"
            )

        # Mostrar errores y advertencias si existen
        if self.errors:
            st.error("❌ **Errores encontrados:**")
            for error in self.errors:
                st.write(f"  • {error}")

        if self.warnings:
            st.warning("⚠️ **Advertencias:**")
            for warning in self.warnings:
                st.write(f"  • {warning}")

    def get_combined_vaccination_data(self):
        """
        Retorna datos de vacunación combinados con marcadores de período
        """
        combined_data = []

        # Datos históricos
        if not self.data.get("vacunacion_historica", pd.DataFrame()).empty:
            hist_df = self.data["vacunacion_historica"].copy()
            hist_df["periodo"] = "historico"
            hist_df["tipo_registro"] = "individual"
            combined_data.append(hist_df)

        # Datos de brigadas (necesitará procesamiento adicional)
        if not self.data.get("brigadas_emergencia", pd.DataFrame()).empty:
            brigadas_df = self.data["brigadas_emergencia"].copy()
            brigadas_df["periodo"] = "emergencia"
            brigadas_df["tipo_registro"] = "brigada"
            combined_data.append(brigadas_df)

        if combined_data:
            return pd.concat(combined_data, ignore_index=True, sort=False)
        else:
            return pd.DataFrame()

    def get_population_reference(self):
        """
        Retorna datos de población de referencia por EAPB
        """
        return self.data.get("poblacion_eapb", pd.DataFrame())

    def get_metadata(self):
        """
        Retorna metadatos del sistema
        """
        return self.metadata.copy()


# Función de conveniencia para usar en el dashboard
@st.cache_data(ttl=3600)
def load_unified_data():
    """
    Función de conveniencia para cargar datos unificados con cache
    """
    loader = UnifiedDataLoader()
    return loader.load_all_data()


# Función para pruebas
def test_unified_loader():
    """
    Función de prueba del cargador unificado
    """
    st.title("🧪 Prueba del Cargador Unificado")

    loader = UnifiedDataLoader()
    data, metadata = loader.load_all_data()

    if data and metadata:
        st.success("✅ Prueba exitosa")

        st.subheader("📊 Datos Cargados")
        for key, df in data.items():
            if isinstance(df, pd.DataFrame):
                st.write(f"**{key}:** {len(df)} registros")

        st.subheader("📋 Metadatos")
        st.json(metadata)

    else:
        st.error("❌ Prueba fallida")


def load_vacunacion_resumen(path):
    df = pd.read_csv(path)
    df = clean_dates(df, ["Fecha_Aplicacion"])
    df = normalize_municipality_names(df, "Municipio")
    return df


def load_vacunacion_historica(path):
    df = pd.read_csv(path)
    df = clean_dates(df, ["Fecha_Aplicacion", "Fecha_Nacimiento"])
    df = normalize_municipality_names(df, "Municipio")
    df = clean_age(df, "Fecha_Nacimiento")
    return df


def get_fecha_corte(df_resumen):
    return df_resumen["Fecha_Aplicacion"].min()


def unify_vacunacion(resumen_path, historica_path):
    df_resumen = load_vacunacion_resumen(resumen_path)
    fecha_corte = get_fecha_corte(df_resumen)
    df_historica = load_vacunacion_historica(historica_path)
    df_historica = df_historica[df_historica["Fecha_Aplicacion"] < fecha_corte]
    df_unificada = pd.concat([df_historica, df_resumen], ignore_index=True)
    fecha_actualizacion = df_unificada["Fecha_Aplicacion"].max()
    return df_unificada, fecha_actualizacion, fecha_corte


@st.cache_data(ttl=3600, show_spinner=False)  # Cache por 1 hora
def load_and_combine_data(resumen_path, historico_path, aseguramiento_path):
    """
    Carga y combina los datos con validación mejorada
    FUNCIÓN PRINCIPAL - CORREGIDA para manejar 3 parámetros
    """
    try:
        progress_text = st.empty()
        progress_bar = st.progress(0)

        # 1. Verificar que las rutas son strings, no DataFrames
        if not isinstance(resumen_path, (str, Path)):
            st.error(
                f"❌ resumen_path debe ser una ruta de archivo, no {type(resumen_path)}"
            )
            return None, None, None

        if not isinstance(historico_path, (str, Path)):
            st.error(
                f"❌ historico_path debe ser una ruta de archivo, no {type(historico_path)}"
            )
            return None, None, None

        if not isinstance(aseguramiento_path, (str, Path)):
            st.error(
                f"❌ aseguramiento_path debe ser una ruta de archivo, no {type(aseguramiento_path)}"
            )
            return None, None, None

        # 1. Cargar datos de aseguramiento (archivo pequeño)
        progress_text.text("🔄 Cargando datos de aseguramiento...")

        # Verificar si el archivo existe
        if not os.path.exists(aseguramiento_path):
            st.error(f"❌ Archivo no encontrado: {aseguramiento_path}")
            return None, None, None

        df_aseguramiento = pd.read_excel(aseguramiento_path)
        progress_bar.progress(20)

        # 2. Cargar datos históricos (archivo grande) con optimizaciones
        progress_text.text("🔄 Cargando datos históricos...")

        if not os.path.exists(historico_path):
            st.warning(f"⚠️ Archivo histórico no encontrado: {historico_path}")
            df_historico = pd.DataFrame()
        else:
            try:
                df_historico = pd.read_csv(
                    historico_path,
                    usecols=[
                        "IdPaciente",
                        "TipoIdentificacion",
                        "Documento",
                        "FechaNacimiento",
                        "NombreMunicipioResidencia",
                        "RegimenAfiliacion",
                        "NombreAseguradora",
                        "FA UNICA",
                    ],
                    dtype={
                        "IdPaciente": "str",
                        "TipoIdentificacion": "category",
                        "Documento": "str",
                        "NombreMunicipioResidencia": "category",
                        "RegimenAfiliacion": "category",
                        "NombreAseguradora": "category",
                    },
                    parse_dates=["FechaNacimiento", "FA UNICA"],
                    date_parser=lambda x: pd.to_datetime(x, errors="coerce"),
                )
            except Exception as e:
                st.warning(f"⚠️ Error cargando datos históricos: {str(e)}")
                df_historico = pd.DataFrame()

        progress_bar.progress(50)

        # Validar y limpiar fechas si hay datos históricos
        if not df_historico.empty:
            invalid_dates = df_historico["FA UNICA"].isna().sum()
            total_records = len(df_historico)
            invalid_percent = (invalid_dates / total_records) * 100

            if invalid_percent > 5:  # More than 5% invalid dates
                st.warning(
                    f"⚠️ Alto porcentaje de fechas inválidas: {invalid_percent:.1f}%"
                )
                df_historico = df_historico.dropna(subset=["FA UNICA"])
                st.info(
                    f"ℹ️ Se removieron {invalid_dates} registros con fechas inválidas"
                )

            progress_text.text("🔄 Procesando datos históricos...")
            df_historico = clean_data(df_historico)

        progress_bar.progress(70)

        # 3. Cargar datos de brigadas
        progress_text.text("🔄 Cargando datos de brigadas...")

        if not os.path.exists(resumen_path):
            st.warning(f"⚠️ Archivo de brigadas no encontrado: {resumen_path}")
            df_brigadas = pd.DataFrame()
            fecha_corte = pd.Timestamp.now()
        else:
            try:
                df_brigadas = pd.read_excel(
                    resumen_path,
                    sheet_name="Vacunacion",
                    usecols=["FECHA", "MUNICIPIO", "TPE", "TPVP"],
                    parse_dates=["FECHA"],
                )

                # Limpiar datos de brigadas
                df_brigadas = clean_data(df_brigadas)

                # Determinar fecha de corte
                fecha_corte = (
                    df_brigadas["FECHA"].min()
                    if not df_brigadas.empty
                    else pd.Timestamp.now()
                )
            except Exception as e:
                st.warning(f"⚠️ Error cargando datos de brigadas: {str(e)}")
                df_brigadas = pd.DataFrame()
                fecha_corte = pd.Timestamp.now()

        progress_bar.progress(90)

        # 4. Combinar datos - combinación simple sin vaccination_combiner
        progress_text.text("🔄 Combinando datos...")

        if not df_historico.empty and not df_brigadas.empty:
            try:
                # Combinar datos de manera simple
                # Agregar marcador de período a cada DataFrame
                df_historico_marked = df_historico.copy()
                df_historico_marked["periodo"] = "historico"
                df_historico_marked["tipo_registro"] = "individual"

                # Para brigadas, crear registros sintéticos si es necesario
                # Por ahora, usar los datos tal como están
                df_brigadas_marked = df_brigadas.copy()
                df_brigadas_marked["periodo"] = "emergencia"
                df_brigadas_marked["tipo_registro"] = "brigada"

                # Combinar DataFrames
                df_combined = pd.concat(
                    [df_historico_marked, df_brigadas_marked],
                    ignore_index=True,
                    sort=False,
                )

            except Exception as e:
                st.warning(f"⚠️ Error combinando datos: {str(e)}")
                # Fallback: usar datos históricos solamente
                df_combined = df_historico
        elif not df_historico.empty:
            df_combined = df_historico
        elif not df_brigadas.empty:
            df_combined = df_brigadas
        else:
            st.error("❌ No se pudieron cargar datos de ninguna fuente")
            return None, None, None

        progress_bar.progress(100)
        progress_text.text("✅ Datos cargados y combinados exitosamente")

        return df_combined, df_aseguramiento, fecha_corte

    except Exception as e:
        st.error(f"Error cargando datos: {str(e)}")
        st.error(f"Traceback: {traceback.format_exc()}")
        return None, None, None
    finally:
        # Limpiar elementos de progreso
        try:
            progress_text.empty()
            progress_bar.empty()
        except:
            pass


# Función auxiliar para cargar un solo archivo CSV (mantenida para compatibilidad)
def load_single_csv_file(file_path: Union[str, Path]) -> Optional[pd.DataFrame]:
    """
    Load a single CSV file
    Función auxiliar para compatibilidad
    """
    try:
        if not isinstance(file_path, (str, os.PathLike)):
            raise TypeError("El archivo debe ser una ruta válida (string o PathLike)")

        # Convert to Path object for better path handling
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"No se encontró el archivo: {file_path}")

        # Read the CSV file
        df = pd.read_csv(file_path)
        return df

    except Exception as e:
        print(f"Error cargando datos: {str(e)}")
        return None
