"""
vistas/maps.py
Vista de mapas interactivos para visualización geográfica de cobertura
"""

import streamlit as st
import pandas as pd
import numpy as np
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path


def show_maps_view(data, filters, colors, fuente_poblacion="DANE"):
    """
    Vista principal de mapas interactivos
    """
    st.title("🗺️ Mapas Interactivos de Cobertura")

    # Verificar dependencias
    try:
        from src.visualization.interactive_maps import get_map_manager
        from src.visualization.geo_loader import get_geo_loader
    except ImportError as e:
        st.error(f"❌ Error importando módulos de mapas: {str(e)}")
        st.info(
            "💡 Asegúrate de instalar: pip install geopandas folium streamlit-folium"
        )
        return

    # Aplicar filtros a los datos
    from src.data.preprocessor import apply_filters

    filtered_data = apply_filters(data, filters, fuente_poblacion)

    if len(filtered_data["vacunacion"]) == 0:
        st.warning("⚠️ No hay datos de vacunación disponibles con los filtros aplicados")
        return

    # Inicializar manejador de mapas
    map_manager = get_map_manager()

    # Sidebar para configuración de mapas
    st.sidebar.subheader("🗺️ Configuración de Mapas")

    # Selector de nivel de detalle
    nivel_detalle = st.sidebar.selectbox(
        "Nivel de detalle:",
        ["Municipios", "Veredas", "Ambos"],
        help="Selecciona el nivel geográfico a visualizar",
    )

    # Selector de tipo de mapa
    tipo_mapa = st.sidebar.selectbox(
        "Tipo de visualización:",
        ["Cobertura", "Densidad de Vacunados", "Comparativo"],
        help="Tipo de información a mostrar en el mapa",
    )

    # Opciones adicionales
    mostrar_estadisticas = st.sidebar.checkbox("Mostrar estadísticas", value=True)
    mostrar_leyenda = st.sidebar.checkbox("Mostrar leyenda", value=True)

    # =====================================================================
    # SECCIÓN 1: VERIFICACIÓN Y CARGA DE GEODATOS
    # =====================================================================

    st.subheader("📂 Estado de Archivos Geográficos")

    # Verificar disponibilidad de shapefiles
    geo_loader = get_geo_loader()
    available_shapefiles = geo_loader.list_available_shapefiles()

    # Mostrar estado de archivos
    col1, col2, col3 = st.columns(3)

    with col1:
        dept_status = "✅" if available_shapefiles["departamento"] else "❌"
        st.write(
            f"{dept_status} **Departamento:** {len(available_shapefiles['departamento'])} archivo(s)"
        )
        if available_shapefiles["departamento"]:
            for file in available_shapefiles["departamento"]:
                st.write(f"  • {file}")

    with col2:
        mun_status = "✅" if available_shapefiles["municipios"] else "❌"
        st.write(
            f"{mun_status} **Municipios:** {len(available_shapefiles['municipios'])} archivo(s)"
        )
        if available_shapefiles["municipios"]:
            for file in available_shapefiles["municipios"]:
                st.write(f"  • {file}")

    with col3:
        ver_status = "✅" if available_shapefiles["veredas"] else "❌"
        st.write(
            f"{ver_status} **Veredas:** {len(available_shapefiles['veredas'])} archivo(s)"
        )
        if available_shapefiles["veredas"]:
            for file in available_shapefiles["veredas"]:
                st.write(f"  • {file}")

    # Botón para cargar geodatos
    if st.button("🔄 Cargar Archivos Geográficos"):
        with st.spinner("Cargando shapefiles..."):
            success = map_manager.load_geodata()

            if success:
                st.success("✅ Geodatos cargados correctamente")

                # Mostrar información de validación
                validation = geo_loader.validate_geodata_structure(map_manager.geodata)

                if validation["errors"]:
                    st.error("❌ Errores encontrados:")
                    for error in validation["errors"]:
                        st.write(f"  - {error}")

                if validation["warnings"]:
                    st.warning("⚠️ Advertencias:")
                    for warning in validation["warnings"]:
                        st.write(f"  - {warning}")

                with st.expander("ℹ️ Información detallada de geodatos"):
                    for info in validation["info"]:
                        st.write(f"  - {info}")
            else:
                st.error("❌ No se pudieron cargar los geodatos")
                st.info(
                    """
                **Para usar mapas interactivos, necesitas:**
                1. Colocar tus archivos shapefile en la carpeta `data/geo/`
                2. Asegurarte de que cada shapefile tenga todos sus archivos (.shp, .shx, .dbf, .prj)
                3. Nombrar los archivos siguiendo los patrones: `tolima_municipios.shp`, `tolima_veredas.shp`
                """
                )
                return

    # Verificar si los geodatos están cargados
    if not hasattr(map_manager, "geodata") or not map_manager.geodata:
        st.info("💡 Haz clic en 'Cargar Archivos Geográficos' para comenzar")
        return

    # =====================================================================
    # SECCIÓN 2: CÁLCULO DE COBERTURA
    # =====================================================================

    st.subheader("📊 Cálculo de Cobertura por Área Geográfica")

    with st.spinner("Calculando cobertura..."):
        # Calcular cobertura por municipio
        municipio_coverage = map_manager.calculate_coverage_by_municipio(
            filtered_data["vacunacion"], filtered_data["metricas"], fuente_poblacion
        )

        # Calcular cobertura por vereda (si es posible)
        vereda_coverage = pd.DataFrame()
        if nivel_detalle in ["Veredas", "Ambos"]:
            vereda_coverage = map_manager.calculate_coverage_by_vereda(
                filtered_data["vacunacion"], filtered_data["metricas"], fuente_poblacion
            )

    # =====================================================================
    # SECCIÓN 3: MOSTRAR ESTADÍSTICAS
    # =====================================================================

    if mostrar_estadisticas:
        if nivel_detalle == "Municipios":
            map_manager.show_coverage_statistics(municipio_coverage, "municipio")
        elif nivel_detalle == "Veredas" and not vereda_coverage.empty:
            map_manager.show_coverage_statistics(vereda_coverage, "vereda")
        elif nivel_detalle == "Ambos":
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### Estadísticas por Municipio")
                map_manager.show_coverage_statistics(municipio_coverage, "municipio")
            with col2:
                st.markdown("#### Estadísticas por Vereda")
                if not vereda_coverage.empty:
                    map_manager.show_coverage_statistics(vereda_coverage, "vereda")
                else:
                    st.info("No hay datos de vereda disponibles")

    # =====================================================================
    # SECCIÓN 4: CREAR Y MOSTRAR MAPAS
    # =====================================================================

    st.subheader("🗺️ Mapa Interactivo de Cobertura")

    try:
        if nivel_detalle == "Municipios":
            # Mapa solo de municipios
            mapa = map_manager.create_interactive_coverage_map(
                municipio_coverage,
                nivel="municipios",
                title=f"Cobertura por Municipio - {fuente_poblacion}",
            )

        elif nivel_detalle == "Veredas":
            # Mapa solo de veredas
            if not vereda_coverage.empty:
                mapa = map_manager.create_interactive_coverage_map(
                    vereda_coverage,
                    nivel="veredas",
                    title=f"Cobertura por Vereda - {fuente_poblacion}",
                )
            else:
                st.warning("⚠️ No hay datos de vereda disponibles")
                return

        else:  # "Ambos"
            # Mapa con ambos niveles
            mapa = map_manager.create_dual_level_map(
                municipio_coverage, vereda_coverage
            )

        # Mostrar el mapa
        map_data = st_folium(
            mapa, width=1200, height=600, returned_objects=["last_object_clicked"]
        )

        # =====================================================================
        # SECCIÓN 5: MANEJO DE CLICKS EN EL MAPA
        # =====================================================================

        # Procesar clicks en el mapa
        if map_data["last_object_clicked"]:
            clicked_data = map_data["last_object_clicked"]

            st.subheader("📍 Información del Área Seleccionada")

            # Aquí podrías extraer más información basada en el click
            # Por ahora mostramos la información básica disponible

            if "popup" in clicked_data:
                st.info(
                    "ℹ️ Haz clic en cualquier área del mapa para ver información detallada"
                )

            # Mostrar gráficos adicionales para el área seleccionada
            if st.checkbox("Mostrar análisis detallado del área seleccionada"):
                show_detailed_area_analysis(filtered_data, clicked_data, colors)

        # =====================================================================
        # SECCIÓN 6: ANÁLISIS COMPLEMENTARIOS
        # =====================================================================

        st.subheader("📈 Análisis Complementarios")

        # Selector de análisis complementario
        analisis_complementario = st.selectbox(
            "Selecciona análisis adicional:",
            [
                "Ranking de Cobertura",
                "Análisis de Brechas",
                "Comparativo Temporal",
                "Distribución Demográfica",
            ],
        )

        if analisis_complementario == "Ranking de Cobertura":
            show_coverage_ranking(municipio_coverage, vereda_coverage, nivel_detalle)

        elif analisis_complementario == "Análisis de Brechas":
            show_coverage_gaps_analysis(
                municipio_coverage, vereda_coverage, fuente_poblacion
            )

        elif analisis_complementario == "Comparativo Temporal":
            show_temporal_coverage_comparison(filtered_data, colors)

        elif analisis_complementario == "Distribución Demográfica":
            show_demographic_distribution_map(filtered_data, map_manager, colors)

    except Exception as e:
        st.error(f"❌ Error creando mapa: {str(e)}")

        # Mostrar información de debug
        with st.expander("🔍 Información de debug"):
            st.write("**Error detallado:**", str(e))
            st.write("**Geodatos disponibles:**", list(map_manager.geodata.keys()))
            st.write("**Datos de cobertura:**")
            if not municipio_coverage.empty:
                st.write("  - Municipios:", len(municipio_coverage))
            if not vereda_coverage.empty:
                st.write("  - Veredas:", len(vereda_coverage))


def show_detailed_area_analysis(filtered_data, clicked_data, colors):
    """
    Muestra análisis detallado para un área específica seleccionada
    """
    st.markdown("### 🔍 Análisis Detallado del Área")

    # Aquí podrías filtrar los datos específicamente para el área clickeada
    # Por ejemplo, si tienes información sobre qué municipio/vereda fue clickeada

    # Por ahora, mostramos un análisis general
    col1, col2 = st.columns(2)

    with col1:
        # Distribución por género en el área
        if "Sexo" in filtered_data["vacunacion"].columns:
            genero_dist = filtered_data["vacunacion"]["Sexo"].value_counts()
            fig = px.pie(
                values=genero_dist.values,
                names=genero_dist.index,
                title="Distribución por Género",
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Distribución por grupo de edad
        if "Grupo_Edad" in filtered_data["vacunacion"].columns:
            edad_dist = filtered_data["vacunacion"]["Grupo_Edad"].value_counts().head(8)
            fig = px.bar(
                x=edad_dist.index, y=edad_dist.values, title="Distribución por Edad"
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)


def show_coverage_ranking(municipio_coverage, vereda_coverage, nivel_detalle):
    """
    Muestra ranking de cobertura
    """
    st.markdown("### 🏆 Ranking de Cobertura")

    if nivel_detalle in ["Municipios", "Ambos"] and not municipio_coverage.empty:
        st.markdown("#### Top 10 Municipios")

        top_municipios = municipio_coverage.nlargest(10, "cobertura")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**🥇 Mejor Cobertura**")
            st.dataframe(
                top_municipios[["municipio", "cobertura", "vacunados"]].head(5),
                use_container_width=True,
            )

        with col2:
            st.markdown("**🔻 Menor Cobertura**")
            bottom_municipios = municipio_coverage.nsmallest(5, "cobertura")
            st.dataframe(
                bottom_municipios[["municipio", "cobertura", "vacunados"]],
                use_container_width=True,
            )

    if nivel_detalle in ["Veredas", "Ambos"] and not vereda_coverage.empty:
        st.markdown("#### Top 10 Veredas")

        top_veredas = vereda_coverage.nlargest(10, "cobertura")
        st.dataframe(
            top_veredas[["vereda", "municipio", "cobertura", "vacunados"]],
            use_container_width=True,
        )


def show_coverage_gaps_analysis(municipio_coverage, vereda_coverage, fuente_poblacion):
    """
    Análisis de brechas de cobertura
    """
    st.markdown("### 📊 Análisis de Brechas de Cobertura")

    if not municipio_coverage.empty:
        # Identificar municipios con baja cobertura
        low_coverage = municipio_coverage[municipio_coverage["cobertura"] < 50]

        if not low_coverage.empty:
            st.warning(
                f"⚠️ {len(low_coverage)} municipios tienen cobertura menor al 50%"
            )

            # Calcular población en riesgo
            poblacion_riesgo = (
                low_coverage["poblacion"].sum() - low_coverage["vacunados"].sum()
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Municipios en Riesgo", len(low_coverage))

            with col2:
                st.metric(
                    "Población en Riesgo", f"{poblacion_riesgo:,}".replace(",", ".")
                )

            with col3:
                cobertura_promedio_riesgo = low_coverage["cobertura"].mean()
                st.metric("Cobertura Promedio", f"{cobertura_promedio_riesgo:.1f}%")

            # Mostrar lista de municipios prioritarios
            st.markdown("#### 🎯 Municipios Prioritarios")
            priority_municipios = low_coverage.sort_values("cobertura")[
                ["municipio", "cobertura", "poblacion", "vacunados"]
            ]
            st.dataframe(priority_municipios, use_container_width=True)

        else:
            st.success("✅ Todos los municipios tienen cobertura superior al 50%")


def show_temporal_coverage_comparison(filtered_data, colors):
    """
    Comparativo temporal de cobertura (si hay datos de fecha)
    """
    st.markdown("### 📅 Evolución Temporal por Área")

    if "FA UNICA" in filtered_data["vacunacion"].columns:
        # Convertir fechas
        filtered_data["vacunacion"]["FechaVacunacion"] = pd.to_datetime(
            filtered_data["vacunacion"]["FA UNICA"], errors="coerce"
        )

        # Agrupar por fecha y municipio
        if "NombreMunicipioResidencia" in filtered_data["vacunacion"].columns:
            temporal_data = (
                filtered_data["vacunacion"]
                .groupby(
                    [
                        filtered_data["vacunacion"]["FechaVacunacion"].dt.date,
                        "NombreMunicipioResidencia",
                    ]
                )
                .size()
                .reset_index()
            )

            temporal_data.columns = ["Fecha", "Municipio", "Vacunados"]

            # Mostrar solo los 5 municipios principales
            top_municipios = (
                filtered_data["vacunacion"]["NombreMunicipioResidencia"]
                .value_counts()
                .head(5)
                .index
            )
            temporal_filtered = temporal_data[
                temporal_data["Municipio"].isin(top_municipios)
            ]

            if not temporal_filtered.empty:
                fig = px.line(
                    temporal_filtered,
                    x="Fecha",
                    y="Vacunados",
                    color="Municipio",
                    title="Evolución de Vacunación por Municipio",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay suficientes datos temporales para mostrar")
    else:
        st.info("No hay datos de fecha disponibles para análisis temporal")


def show_demographic_distribution_map(filtered_data, map_manager, colors):
    """
    Distribución demográfica en el mapa
    """
    st.markdown("### 👥 Distribución Demográfica")

    # Análisis por género y municipio
    if (
        "Sexo" in filtered_data["vacunacion"].columns
        and "NombreMunicipioResidencia" in filtered_data["vacunacion"].columns
    ):
        demo_data = (
            filtered_data["vacunacion"]
            .groupby(["NombreMunicipioResidencia", "Sexo"])
            .size()
            .reset_index()
        )
        demo_data.columns = ["Municipio", "Genero", "Cantidad"]

        # Crear gráfico de distribución
        fig = px.bar(
            demo_data,
            x="Municipio",
            y="Cantidad",
            color="Genero",
            title="Distribución de Género por Municipio",
            color_discrete_map={
                "Masculino": colors.get("primary", "#1f77b4"),
                "Femenino": colors.get("secondary", "#ff7f0e"),
                "No Binario": colors.get("accent", "#2ca02c"),
            },
        )
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)


def show(data, filters, colors, fuente_poblacion="DANE"):
    """
    Función principal para mostrar la vista de mapas
    (Compatible con la estructura existente del dashboard)
    """
    show_maps_view(data, filters, colors, fuente_poblacion)
