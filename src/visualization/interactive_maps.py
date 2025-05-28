"""
src/visualization/interactive_maps.py
Manejador de mapas interactivos para visualizar cobertura por veredas y municipios
"""

import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import st_folium
import numpy as np
from typing import Dict, Optional, Tuple, List
import branca.colormap as cm
from .geo_loader import get_geo_loader


class TolimaInteractiveMapManager:
    """
    Manejador de mapas interactivos para el Tolima con soporte de click events
    """

    def __init__(self):
        self.tolima_center = [4.43889, -75.2322]
        self.geo_loader = get_geo_loader()
        self.geodata = {}
        self._coverage_data = {}

        # Colores para diferentes niveles de cobertura
        self.coverage_colors = {
            "muy_alta": "#0d7b1b",  # Verde oscuro
            "alta": "#28a745",  # Verde
            "media": "#ffc107",  # Amarillo
            "baja": "#fd7e14",  # Naranja
            "muy_baja": "#dc3545",  # Rojo
            "sin_datos": "#6c757d",  # Gris
        }

    def load_geodata(self) -> bool:
        """
        Carga los datos geográficos necesarios
        """
        try:
            self.geodata = self.geo_loader.load_tolima_geodata()
            return len(self.geodata) > 0
        except Exception as e:
            st.error(f"❌ Error cargando geodatos: {str(e)}")
            return False

    def calculate_coverage_by_vereda(
        self,
        vacunacion_data: pd.DataFrame,
        poblacion_data: pd.DataFrame,
        fuente_poblacion: str = "DANE",
    ) -> pd.DataFrame:
        """
        Calcula la cobertura de vacunación por vereda
        """
        try:
            # Verificar si tenemos datos de vereda en vacunación
            if (
                "vereda" not in vacunacion_data.columns
                and "NombreVereda" not in vacunacion_data.columns
            ):
                # Si no tenemos datos de vereda, trabajar solo con municipios
                return self.calculate_coverage_by_municipio(
                    vacunacion_data, poblacion_data, fuente_poblacion
                )

            # Determinar columna de vereda
            vereda_col = (
                "vereda" if "vereda" in vacunacion_data.columns else "NombreVereda"
            )
            municipio_col = "NombreMunicipioResidencia"

            # Agrupar vacunados por vereda y municipio
            vacunados_vereda = (
                vacunacion_data.groupby([vereda_col, municipio_col])
                .size()
                .reset_index()
            )
            vacunados_vereda.columns = ["vereda", "municipio", "vacunados"]

            # Aquí necesitarías datos de población por vereda
            # Por ahora, estimamos basándonos en distribución proporcional
            # En un caso real, tendrías una tabla de población por vereda

            # Calcular cobertura estimada (esto sería más preciso con datos reales de población por vereda)
            municipio_totals = (
                poblacion_data.groupby("DPMP")[fuente_poblacion].sum().reset_index()
            )
            municipio_totals.columns = ["municipio", "poblacion_municipio"]

            # Fusionar datos
            coverage_vereda = pd.merge(
                vacunados_vereda, municipio_totals, on="municipio", how="left"
            )

            # Estimar población por vereda (distribución proporcional basada en vacunados)
            municipio_vacunados = (
                vacunados_vereda.groupby("municipio")["vacunados"].sum().reset_index()
            )
            municipio_vacunados.columns = ["municipio", "total_vacunados_municipio"]

            coverage_vereda = pd.merge(
                coverage_vereda, municipio_vacunados, on="municipio", how="left"
            )

            # Estimar población de vereda proporcionalmente
            coverage_vereda["poblacion_estimada_vereda"] = (
                coverage_vereda["vacunados"]
                / coverage_vereda["total_vacunados_municipio"]
                * coverage_vereda["poblacion_municipio"]
            ).fillna(
                100
            )  # Mínimo 100 personas por vereda

            # Calcular cobertura
            coverage_vereda["cobertura"] = (
                coverage_vereda["vacunados"]
                / coverage_vereda["poblacion_estimada_vereda"]
                * 100
            ).round(2)

            return coverage_vereda[
                [
                    "vereda",
                    "municipio",
                    "vacunados",
                    "poblacion_estimada_vereda",
                    "cobertura",
                ]
            ]

        except Exception as e:
            st.warning(f"⚠️ Error calculando cobertura por vereda: {str(e)}")
            return pd.DataFrame()

    def calculate_coverage_by_municipio(
        self,
        vacunacion_data: pd.DataFrame,
        poblacion_data: pd.DataFrame,
        fuente_poblacion: str = "DANE",
    ) -> pd.DataFrame:
        """
        Calcula la cobertura de vacunación por municipio
        """
        try:
            municipio_col = "NombreMunicipioResidencia"

            # Agrupar vacunados por municipio
            vacunados_municipio = (
                vacunacion_data.groupby(municipio_col).size().reset_index()
            )
            vacunados_municipio.columns = ["municipio", "vacunados"]

            # Normalizar nombres de municipios para el merge
            from src.data.normalize import normalize_municipality_names

            vacunados_norm = normalize_municipality_names(
                vacunados_municipio, "municipio"
            )
            poblacion_norm = normalize_municipality_names(poblacion_data, "DPMP")

            # Fusionar datos
            coverage_municipio = pd.merge(
                vacunados_norm,
                poblacion_norm[["DPMP", "DPMP_norm", fuente_poblacion]],
                left_on="municipio_norm",
                right_on="DPMP_norm",
                how="left",
            )

            # Calcular cobertura
            coverage_municipio["cobertura"] = (
                coverage_municipio["vacunados"]
                / coverage_municipio[fuente_poblacion]
                * 100
            ).round(2)

            # Limpiar datos
            result = coverage_municipio[
                ["municipio", "vacunados", fuente_poblacion, "cobertura"]
            ].copy()
            result.columns = ["municipio", "vacunados", "poblacion", "cobertura"]

            return result

        except Exception as e:
            st.error(f"❌ Error calculando cobertura por municipio: {str(e)}")
            return pd.DataFrame()

    def categorize_coverage(self, cobertura: float) -> str:
        """
        Categoriza el nivel de cobertura
        """
        if pd.isna(cobertura):
            return "sin_datos"
        elif cobertura >= 90:
            return "muy_alta"
        elif cobertura >= 70:
            return "alta"
        elif cobertura >= 50:
            return "media"
        elif cobertura >= 30:
            return "baja"
        else:
            return "muy_baja"

    def create_interactive_coverage_map(
        self,
        coverage_data: pd.DataFrame,
        nivel: str = "municipio",
        title: str = "Cobertura de Vacunación",
    ) -> folium.Map:
        """
        Crea un mapa interactivo de cobertura
        """
        # Crear mapa base
        m = folium.Map(
            location=self.tolima_center, zoom_start=8, tiles="CartoDB positron"
        )

        # Verificar si tenemos geodatos
        if nivel not in self.geodata:
            st.warning(f"⚠️ No hay geodatos disponibles para {nivel}")
            return m

        gdf = self.geodata[nivel].copy()

        # Determinar columna de nombre en geodatos
        name_col = "municipio" if nivel == "municipios" else "vereda"

        if name_col not in gdf.columns:
            # Buscar columna alternativa
            for col in ["nombre", "nom_mpio", "nom_vereda"]:
                if col in gdf.columns:
                    gdf[name_col] = gdf[col]
                    break

        # Fusionar geodatos con datos de cobertura
        if not coverage_data.empty:
            # Normalizar nombres para mejor matching
            gdf[f"{name_col}_norm"] = gdf[name_col].astype(str).str.lower().str.strip()
            coverage_data[f"{name_col}_norm"] = (
                coverage_data[name_col].astype(str).str.lower().str.strip()
            )

            # Merge de datos
            gdf_with_coverage = pd.merge(
                gdf,
                coverage_data,
                on=f"{name_col}_norm",
                how="left",
                suffixes=("_geo", "_cov"),
            )

            # Llenar valores faltantes
            gdf_with_coverage["cobertura"] = gdf_with_coverage["cobertura"].fillna(0)
            gdf_with_coverage["vacunados"] = gdf_with_coverage["vacunados"].fillna(0)
        else:
            gdf_with_coverage = gdf.copy()
            gdf_with_coverage["cobertura"] = 0
            gdf_with_coverage["vacunados"] = 0

        # Crear colormap
        cobertura_min = gdf_with_coverage["cobertura"].min()
        cobertura_max = gdf_with_coverage["cobertura"].max()

        if cobertura_max > cobertura_min:
            colormap = cm.linear.RdYlGn_11.scale(cobertura_min, cobertura_max)
        else:
            colormap = cm.linear.RdYlGn_11.scale(0, 100)

        # Añadir features al mapa
        for idx, row in gdf_with_coverage.iterrows():
            # Determinar color
            cobertura = row["cobertura"]
            color = colormap(cobertura) if not pd.isna(cobertura) else "#808080"

            # Crear popup con información detallada
            nombre = row.get(f"{name_col}_cov", row.get(name_col, "Sin nombre"))

            popup_content = f"""
            <div style="width:200px">
                <h4>{nombre}</h4>
                <hr>
                <b>Cobertura:</b> {cobertura:.1f}%<br>
                <b>Vacunados:</b> {int(row['vacunados'])}<br>
            """

            if "poblacion" in row:
                popup_content += f"<b>Población:</b> {int(row['poblacion'])}<br>"

            if nivel == "veredas" and "municipio_cov" in row:
                popup_content += f"<b>Municipio:</b> {row['municipio_cov']}<br>"

            popup_content += "</div>"

            # Crear feature
            feature = folium.GeoJson(
                row["geometry"].__geo_interface__,
                style_function=lambda x, color=color: {
                    "fillColor": color,
                    "color": "black",
                    "weight": 1,
                    "fillOpacity": 0.7,
                },
                popup=folium.Popup(popup_content, max_width=250),
                tooltip=f"{nombre}: {cobertura:.1f}%",
            )

            feature.add_to(m)

        # Añadir colormap al mapa
        colormap.caption = "Cobertura de Vacunación (%)"
        colormap.add_to(m)

        # Añadir título
        title_html = f"""
            <h3 align="center" style="font-size:20px"><b>{title}</b></h3>
        """
        m.get_root().html.add_child(folium.Element(title_html))

        return m

    def create_dual_level_map(
        self, municipio_coverage: pd.DataFrame, vereda_coverage: pd.DataFrame
    ) -> folium.Map:
        """
        Crea un mapa con dos niveles: municipios y veredas
        """
        m = folium.Map(
            location=self.tolima_center, zoom_start=8, tiles="CartoDB positron"
        )

        # Capa de municipios
        if "municipios" in self.geodata and not municipio_coverage.empty:
            municipios_layer = self.create_municipios_layer(municipio_coverage)
            municipios_layer.add_to(m)

        # Capa de veredas
        if "veredas" in self.geodata and not vereda_coverage.empty:
            veredas_layer = self.create_veredas_layer(vereda_coverage)
            veredas_layer.add_to(m)

        # Control de capas
        folium.LayerControl().add_to(m)

        return m

    def create_municipios_layer(
        self, coverage_data: pd.DataFrame
    ) -> folium.FeatureGroup:
        """
        Crea una capa de municipios
        """
        layer = folium.FeatureGroup(name="Municipios")

        gdf = self.geodata["municipios"].copy()

        # Merge con datos de cobertura
        gdf_merged = self.merge_coverage_data(gdf, coverage_data, "municipio")

        for idx, row in gdf_merged.iterrows():
            cobertura = row.get("cobertura", 0)
            color = self.get_coverage_color(cobertura)

            popup_content = f"""
            <div style="width:200px">
                <h4>{row.get('municipio', 'Sin nombre')}</h4>
                <hr>
                <b>Cobertura:</b> {cobertura:.1f}%<br>
                <b>Vacunados:</b> {int(row.get('vacunados', 0))}<br>
                <b>Población:</b> {int(row.get('poblacion', 0))}<br>
            </div>
            """

            folium.GeoJson(
                row["geometry"].__geo_interface__,
                style_function=lambda x, color=color: {
                    "fillColor": color,
                    "color": "black",
                    "weight": 2,
                    "fillOpacity": 0.6,
                },
                popup=folium.Popup(popup_content, max_width=250),
                tooltip=f"{row.get('municipio', 'Sin nombre')}: {cobertura:.1f}%",
            ).add_to(layer)

        return layer

    def create_veredas_layer(self, coverage_data: pd.DataFrame) -> folium.FeatureGroup:
        """
        Crea una capa de veredas
        """
        layer = folium.FeatureGroup(name="Veredas")

        gdf = self.geodata["veredas"].copy()

        # Merge con datos de cobertura
        gdf_merged = self.merge_coverage_data(gdf, coverage_data, "vereda")

        for idx, row in gdf_merged.iterrows():
            cobertura = row.get("cobertura", 0)
            color = self.get_coverage_color(cobertura)

            popup_content = f"""
            <div style="width:200px">
                <h4>{row.get('vereda', 'Sin nombre')}</h4>
                <hr>
                <b>Municipio:</b> {row.get('municipio', 'N/A')}<br>
                <b>Cobertura:</b> {cobertura:.1f}%<br>
                <b>Vacunados:</b> {int(row.get('vacunados', 0))}<br>
            </div>
            """

            folium.GeoJson(
                row["geometry"].__geo_interface__,
                style_function=lambda x, color=color: {
                    "fillColor": color,
                    "color": "darkblue",
                    "weight": 1,
                    "fillOpacity": 0.8,
                },
                popup=folium.Popup(popup_content, max_width=250),
                tooltip=f"{row.get('vereda', 'Sin nombre')}: {cobertura:.1f}%",
            ).add_to(layer)

        return layer

    def merge_coverage_data(
        self, gdf: gpd.GeoDataFrame, coverage_data: pd.DataFrame, level: str
    ) -> gpd.GeoDataFrame:
        """
        Fusiona geodatos con datos de cobertura
        """
        # Determinar columna de nombre
        name_col = level

        if name_col not in gdf.columns:
            # Buscar columna alternativa
            alt_cols = {
                "municipio": ["nombre", "nom_mpio", "mpio"],
                "vereda": ["nombre", "nom_vereda", "ver"],
            }

            for alt_col in alt_cols.get(level, []):
                if alt_col in gdf.columns:
                    gdf[name_col] = gdf[alt_col]
                    break

        # Normalizar nombres
        gdf[f"{name_col}_norm"] = gdf[name_col].astype(str).str.lower().str.strip()
        coverage_data[f"{name_col}_norm"] = (
            coverage_data[name_col].astype(str).str.lower().str.strip()
        )

        # Merge
        merged = pd.merge(
            gdf,
            coverage_data,
            on=f"{name_col}_norm",
            how="left",
            suffixes=("_geo", "_cov"),
        )

        # Llenar valores faltantes
        merged["cobertura"] = merged["cobertura"].fillna(0)
        merged["vacunados"] = merged["vacunados"].fillna(0)

        return merged

    def get_coverage_color(self, cobertura: float) -> str:
        """
        Obtiene el color basado en el nivel de cobertura
        """
        category = self.categorize_coverage(cobertura)
        return self.coverage_colors[category]

    def show_coverage_statistics(self, coverage_data: pd.DataFrame, nivel: str):
        """
        Muestra estadísticas de cobertura
        """
        if coverage_data.empty:
            st.warning(f"⚠️ No hay datos de cobertura para {nivel}")
            return

        # Calcular estadísticas
        stats = {
            "total_unidades": len(coverage_data),
            "cobertura_promedio": coverage_data["cobertura"].mean(),
            "cobertura_mediana": coverage_data["cobertura"].median(),
            "cobertura_max": coverage_data["cobertura"].max(),
            "cobertura_min": coverage_data["cobertura"].min(),
            "total_vacunados": coverage_data["vacunados"].sum(),
        }

        # Mostrar métricas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(f"Total {nivel}s", stats["total_unidades"])

        with col2:
            st.metric("Cobertura Promedio", f"{stats['cobertura_promedio']:.1f}%")

        with col3:
            st.metric(
                "Rango de Cobertura",
                f"{stats['cobertura_min']:.1f}% - {stats['cobertura_max']:.1f}%",
            )

        with col4:
            st.metric(
                "Total Vacunados", f"{stats['total_vacunados']:,}".replace(",", ".")
            )

        # Distribución por categorías
        coverage_data["categoria"] = coverage_data["cobertura"].apply(
            self.categorize_coverage
        )
        categoria_counts = coverage_data["categoria"].value_counts()

        # Crear gráfico de distribución
        categoria_labels = {
            "muy_alta": "Muy Alta (≥90%)",
            "alta": "Alta (70-89%)",
            "media": "Media (50-69%)",
            "baja": "Baja (30-49%)",
            "muy_baja": "Muy Baja (<30%)",
            "sin_datos": "Sin Datos",
        }

        dist_data = pd.DataFrame(
            {
                "Categoria": [
                    categoria_labels.get(cat, cat) for cat in categoria_counts.index
                ],
                "Cantidad": categoria_counts.values,
            }
        )

        fig = px.pie(
            dist_data,
            names="Categoria",
            values="Cantidad",
            title=f"Distribución de Cobertura por {nivel.title()}",
            color_discrete_map={
                "Muy Alta (≥90%)": self.coverage_colors["muy_alta"],
                "Alta (70-89%)": self.coverage_colors["alta"],
                "Media (50-69%)": self.coverage_colors["media"],
                "Baja (30-49%)": self.coverage_colors["baja"],
                "Muy Baja (<30%)": self.coverage_colors["muy_baja"],
                "Sin Datos": self.coverage_colors["sin_datos"],
            },
        )

        st.plotly_chart(fig, use_container_width=True)


def get_map_manager() -> TolimaInteractiveMapManager:
    """
    Factory function para obtener el manejador de mapas
    """
    return TolimaInteractiveMapManager()
