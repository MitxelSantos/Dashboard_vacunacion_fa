"""
src/visualization/geo_loader.py
Cargador avanzado de shapefiles para el Tolima con soporte para veredas
"""

import streamlit as st
import geopandas as gpd
import pandas as pd
from pathlib import Path
import os
from typing import Dict, Optional, Tuple
import unicodedata
import re


class TolimaGeoLoader:
    """
    Cargador especializado para shapefiles del Tolima
    """

    def __init__(self, geo_dir: str = "data/geo"):
        self.geo_dir = Path(geo_dir)
        self.geo_dir.mkdir(exist_ok=True, parents=True)

        # Cache para evitar recargar archivos
        self._cache = {}

        # Patrones de archivos esperados
        self.shapefile_patterns = {
            "departamento": [
                "tolima_departamento",
                "tolima_depto",
                "departamento_tolima",
            ],
            "municipios": ["tolima_municipios", "municipios_tolima", "municipios"],
            "veredas": ["tolima_veredas", "veredas_tolima", "veredas"],
        }

    def list_available_shapefiles(self) -> Dict[str, list]:
        """
        Lista todos los shapefiles disponibles en el directorio
        """
        available = {"departamento": [], "municipios": [], "veredas": [], "otros": []}

        if not self.geo_dir.exists():
            return available

        # Buscar archivos .shp
        shp_files = list(self.geo_dir.glob("*.shp"))

        for shp_file in shp_files:
            filename = shp_file.stem.lower()

            # Clasificar por tipo
            classified = False
            for geo_type, patterns in self.shapefile_patterns.items():
                if any(pattern in filename for pattern in patterns):
                    available[geo_type].append(shp_file.name)
                    classified = True
                    break

            if not classified:
                available["otros"].append(shp_file.name)

        return available

    def load_shapefile(
        self, filename: str, use_cache: bool = True
    ) -> Optional[gpd.GeoDataFrame]:
        """
        Carga un shapefile específico con validación y limpieza
        """
        cache_key = f"shapefile_{filename}"

        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        shp_path = self.geo_dir / filename

        if not shp_path.exists():
            st.warning(f"⚠️ Shapefile no encontrado: {filename}")
            return None

        try:
            # Cargar el shapefile
            gdf = gpd.read_file(str(shp_path))

            # Validar que tenga geometrías
            if gdf.empty:
                st.warning(f"⚠️ Shapefile vacío: {filename}")
                return None

            # Asegurar que esté en un CRS apropiado (WGS84)
            if gdf.crs is None:
                st.warning(f"⚠️ CRS no definido para {filename}, asumiendo WGS84")
                gdf.set_crs(epsg=4326, inplace=True)
            elif gdf.crs.to_epsg() != 4326:
                gdf = gdf.to_crs(epsg=4326)

            # Limpiar y normalizar nombres de columnas
            gdf.columns = [self._normalize_column_name(col) for col in gdf.columns]

            # Normalizar campos de texto importantes
            for col in gdf.columns:
                if col in ["nombre", "municipio", "vereda", "depto", "departamento"]:
                    if gdf[col].dtype == "object":
                        gdf[col] = gdf[col].astype(str).str.strip().str.title()

            # Cache el resultado
            if use_cache:
                self._cache[cache_key] = gdf

            st.success(f"✅ Shapefile cargado: {filename} ({len(gdf)} características)")
            return gdf

        except Exception as e:
            st.error(f"❌ Error cargando shapefile {filename}: {str(e)}")
            return None

    def _normalize_column_name(self, col_name: str) -> str:
        """
        Normaliza nombres de columnas para mayor consistencia
        """
        # Convertir a string y limpiar
        col_str = str(col_name).strip().lower()

        # Remover acentos
        col_str = unicodedata.normalize("NFKD", col_str)
        col_str = "".join(c for c in col_str if not unicodedata.combining(c))

        # Reemplazar espacios y caracteres especiales
        col_str = re.sub(r"[^\w]", "_", col_str)

        # Mapeos comunes
        common_mappings = {
            "nom_mpio": "municipio",
            "nom_vereda": "vereda",
            "nombre_municipio": "municipio",
            "nombre_vereda": "vereda",
            "mpio_cnmbr": "municipio",
            "ver_cnmbr": "vereda",
            "dpmp": "municipio",
            "codigo_municipio": "cod_municipio",
            "codigo_vereda": "cod_vereda",
        }

        return common_mappings.get(col_str, col_str)

    def load_tolima_geodata(self) -> Dict[str, gpd.GeoDataFrame]:
        """
        Carga todos los shapefiles disponibles del Tolima
        """
        available = self.list_available_shapefiles()
        geodata = {}

        st.info("📂 Cargando shapefiles del Tolima...")

        # Cargar cada tipo de shapefile
        for geo_type, files in available.items():
            if files and geo_type != "otros":
                # Usar el primer archivo encontrado de cada tipo
                filename = files[0]
                gdf = self.load_shapefile(filename)

                if gdf is not None:
                    geodata[geo_type] = gdf
                    st.write(f"  • {geo_type.title()}: {len(gdf)} características")

        if not geodata:
            st.warning("⚠️ No se encontraron shapefiles válidos del Tolima")

        return geodata

    def validate_geodata_structure(
        self, geodata: Dict[str, gpd.GeoDataFrame]
    ) -> Dict[str, list]:
        """
        Valida la estructura de los datos geográficos cargados
        """
        validation_report = {"errors": [], "warnings": [], "info": []}

        required_columns = {
            "departamento": ["geometry"],
            "municipios": ["geometry", "municipio"],
            "veredas": ["geometry", "vereda", "municipio"],
        }

        for geo_type, gdf in geodata.items():
            required_cols = required_columns.get(geo_type, ["geometry"])

            # Verificar columnas requeridas
            missing_cols = [col for col in required_cols if col not in gdf.columns]
            if missing_cols:
                validation_report["errors"].append(
                    f"{geo_type}: Faltan columnas requeridas: {missing_cols}"
                )

            # Verificar geometrías válidas
            invalid_geoms = gdf.geometry.isna().sum()
            if invalid_geoms > 0:
                validation_report["warnings"].append(
                    f"{geo_type}: {invalid_geoms} geometrías inválidas"
                )

            # Información general
            validation_report["info"].append(
                f"{geo_type}: {len(gdf)} características, {len(gdf.columns)} columnas"
            )

        return validation_report

    def create_unified_geodataframe(
        self, geodata: Dict[str, gpd.GeoDataFrame]
    ) -> gpd.GeoDataFrame:
        """
        Crea un GeoDataFrame unificado con información jerárquica
        """
        unified_features = []

        # Procesar departamento
        if "departamento" in geodata:
            dept_gdf = geodata["departamento"].copy()
            dept_gdf["nivel"] = "departamento"
            dept_gdf["nombre"] = "Tolima"
            dept_gdf["padre"] = None
            unified_features.append(dept_gdf[["geometry", "nivel", "nombre", "padre"]])

        # Procesar municipios
        if "municipios" in geodata:
            mun_gdf = geodata["municipios"].copy()
            mun_gdf["nivel"] = "municipio"

            # Usar la columna de municipio encontrada
            municipio_col = None
            for col in ["municipio", "nombre", "nom_mpio"]:
                if col in mun_gdf.columns:
                    municipio_col = col
                    break

            if municipio_col:
                mun_gdf["nombre"] = mun_gdf[municipio_col]
            else:
                mun_gdf["nombre"] = "Municipio Sin Nombre"

            mun_gdf["padre"] = "Tolima"
            unified_features.append(mun_gdf[["geometry", "nivel", "nombre", "padre"]])

        # Procesar veredas
        if "veredas" in geodata:
            ver_gdf = geodata["veredas"].copy()
            ver_gdf["nivel"] = "vereda"

            # Usar las columnas encontradas
            vereda_col = None
            municipio_col = None

            for col in ["vereda", "nombre", "nom_vereda"]:
                if col in ver_gdf.columns:
                    vereda_col = col
                    break

            for col in ["municipio", "nom_mpio", "mpio"]:
                if col in ver_gdf.columns:
                    municipio_col = col
                    break

            if vereda_col:
                ver_gdf["nombre"] = ver_gdf[vereda_col]
            else:
                ver_gdf["nombre"] = "Vereda Sin Nombre"

            if municipio_col:
                ver_gdf["padre"] = ver_gdf[municipio_col]
            else:
                ver_gdf["padre"] = "Municipio Desconocido"

            unified_features.append(ver_gdf[["geometry", "nivel", "nombre", "padre"]])

        # Combinar todos los features
        if unified_features:
            unified_gdf = pd.concat(unified_features, ignore_index=True)
            return gpd.GeoDataFrame(unified_gdf)

        return gpd.GeoDataFrame()


def get_geo_loader() -> TolimaGeoLoader:
    """
    Factory function para obtener el loader de geodatos
    """
    return TolimaGeoLoader()


def test_geo_loader():
    """
    Función de prueba para el cargador de geodatos
    """
    st.markdown("### 🧪 Prueba del Cargador de Geodatos")

    loader = get_geo_loader()

    # Listar archivos disponibles
    available = loader.list_available_shapefiles()

    st.write("**Archivos shapefile disponibles:**")
    for geo_type, files in available.items():
        if files:
            st.write(f"  • {geo_type.title()}: {', '.join(files)}")
        else:
            st.write(f"  • {geo_type.title()}: No encontrado")

    # Intentar cargar geodatos
    if st.button("🔄 Cargar Geodatos"):
        geodata = loader.load_tolima_geodata()

        if geodata:
            # Mostrar validación
            validation = loader.validate_geodata_structure(geodata)

            if validation["errors"]:
                st.error("❌ Errores encontrados:")
                for error in validation["errors"]:
                    st.write(f"  - {error}")

            if validation["warnings"]:
                st.warning("⚠️ Advertencias:")
                for warning in validation["warnings"]:
                    st.write(f"  - {warning}")

            st.success("✅ Información de geodatos:")
            for info in validation["info"]:
                st.write(f"  - {info}")

            # Crear vista unificada
            unified = loader.create_unified_geodataframe(geodata)
            if not unified.empty:
                st.write(f"**GeoDataFrame unificado:** {len(unified)} características")

                # Mostrar muestra de datos
                sample_data = unified.head().drop("geometry", axis=1)
                st.dataframe(sample_data, use_container_width=True)

        else:
            st.error("❌ No se pudieron cargar geodatos")


if __name__ == "__main__":
    test_geo_loader()
