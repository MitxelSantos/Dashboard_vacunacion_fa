import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime


def show(data, filters, colors):
    """
    Función principal para la vista geográfica
    Compatible con la estructura del app.py
    """
    st.header("🗺️ Distribución Geográfica de Vacunación")

    if data is None or len(data) == 0:
        st.warning("⚠️ No hay datos de vacunación disponibles para mostrar")
        return

    try:
        # Verificar si tenemos columna de municipio
        municipio_columns = [
            "NombreMunicipioResidencia",
            "Municipio",
            "MUNICIPIO",
            "municipio_residencia",
        ]

        municipio_col = None
        for col in municipio_columns:
            if col in data.columns:
                municipio_col = col
                break

        if municipio_col is None:
            st.error("❌ No se encontró información de municipios en los datos")
            return

        # Limpiar datos de municipio
        data_clean = data.copy()

        # Manejar columnas categóricas correctamente
        if data_clean[municipio_col].dtype.name == "category":
            # Si es categórica, convertir a string primero
            data_clean[municipio_col] = data_clean[municipio_col].astype(str)

        # Ahora podemos hacer las operaciones de limpieza
        data_clean[municipio_col] = data_clean[municipio_col].fillna("Sin dato")
        data_clean[municipio_col] = (
            data_clean[municipio_col].astype(str).str.strip().str.title()
        )

        mostrar_geographic_analysis(data_clean, municipio_col, colors)

    except Exception as e:
        st.error(f"❌ Error procesando datos geográficos: {str(e)}")

        # Mostrar información de debug
        with st.expander("🔧 Información de debug"):
            st.write("**Columnas disponibles:**")
            st.write(list(data.columns))
            st.write("**Forma de datos:**", data.shape)


def mostrar_geographic_analysis(data, municipio_col, colors):
    """
    Muestra el análisis geográfico completo
    """

    # ==========================================
    # SECCIÓN 1: MÉTRICAS GENERALES
    # ==========================================
    st.subheader("📊 Métricas Geográficas Generales")

    total_vacunados = len(data)
    total_municipios = data[municipio_col].nunique()

    # Calcular distribución
    municipios_stats = data[municipio_col].value_counts().reset_index()
    municipios_stats.columns = ["Municipio", "Vacunados"]

    # Estadísticas
    promedio_por_municipio = municipios_stats["Vacunados"].mean()
    municipio_lider = municipios_stats.iloc[0]["Municipio"]
    vacunados_lider = municipios_stats.iloc[0]["Vacunados"]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Municipios", total_municipios, delta=f"de 47 municipios")

    with col2:
        st.metric(
            "Total Vacunados",
            f"{total_vacunados:,}".replace(",", "."),
            delta=f"Promedio: {promedio_por_municipio:.0f}/municipio",
        )

    with col3:
        st.metric(
            "Municipio Líder",
            municipio_lider,
            delta=f"{vacunados_lider:,} vacunados".replace(",", "."),
        )

    with col4:
        # Calcular cobertura territorial
        cobertura_territorial = (total_municipios / 47) * 100
        st.metric(
            "Cobertura Territorial", f"{cobertura_territorial:.1f}%", delta="del Tolima"
        )

    # ==========================================
    # SECCIÓN 2: DISTRIBUCIÓN POR MUNICIPIOS
    # ==========================================
    st.subheader("🏘️ Distribución por Municipios")

    col1, col2 = st.columns(2)

    with col1:
        # Top 15 municipios
        top_municipios = municipios_stats.head(15)

        fig_top = px.bar(
            top_municipios,
            x="Vacunados",
            y="Municipio",
            orientation="h",
            title="Top 15 Municipios por Vacunación",
            color_discrete_sequence=[colors.get("primary", "#7D0F2B")],
            height=500,
        )

        fig_top.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            yaxis={"categoryorder": "total ascending"},
        )

        st.plotly_chart(fig_top, use_container_width=True)

    with col2:
        # Distribución por categorías
        # Crear categorías de municipios por tamaño
        def categorizar_municipio(vacunados):
            if vacunados >= 1000:
                return "Muy Alta (≥1000)"
            elif vacunados >= 500:
                return "Alta (500-999)"
            elif vacunados >= 100:
                return "Media (100-499)"
            elif vacunados >= 50:
                return "Baja (50-99)"
            else:
                return "Muy Baja (<50)"

        municipios_stats["Categoria"] = municipios_stats["Vacunados"].apply(
            categorizar_municipio
        )

        # Contar por categoría
        categoria_counts = municipios_stats["Categoria"].value_counts().reset_index()
        categoria_counts.columns = ["Categoria", "Municipios"]

        # Definir orden lógico
        orden_categorias = [
            "Muy Alta (≥1000)",
            "Alta (500-999)",
            "Media (100-499)",
            "Baja (50-99)",
            "Muy Baja (<50)",
        ]
        categoria_counts["Categoria"] = pd.Categorical(
            categoria_counts["Categoria"], categories=orden_categorias, ordered=True
        )
        categoria_counts = categoria_counts.sort_values("Categoria")

        fig_categoria = px.pie(
            categoria_counts,
            names="Categoria",
            values="Municipios",
            title="Distribución de Municipios por Nivel de Vacunación",
            color_discrete_sequence=px.colors.qualitative.Set3,
            height=500,
        )

        fig_categoria.update_traces(textposition="inside", textinfo="percent+label")
        fig_categoria.update_layout(plot_bgcolor="white", paper_bgcolor="white")

        st.plotly_chart(fig_categoria, use_container_width=True)

    # ==========================================
    # SECCIÓN 3: ANÁLISIS TEMPORAL GEOGRÁFICO
    # ==========================================
    if "FA UNICA" in data.columns or "FechaVacunacion" in data.columns:
        st.subheader("📅 Evolución Temporal por Municipios")

        # Determinar columna de fecha
        fecha_col = "FA UNICA" if "FA UNICA" in data.columns else "FechaVacunacion"

        try:
            # Convertir fechas
            data_temporal = data.copy()
            data_temporal[fecha_col] = pd.to_datetime(
                data_temporal[fecha_col], errors="coerce"
            )

            # Filtrar fechas válidas
            data_temporal = data_temporal[data_temporal[fecha_col].notna()]

            if len(data_temporal) > 0:
                # Crear serie temporal para top 8 municipios
                top_8_municipios = municipios_stats.head(8)["Municipio"].tolist()
                data_top_8 = data_temporal[
                    data_temporal[municipio_col].isin(top_8_municipios)
                ]

                # Agrupar por fecha y municipio
                temporal_data = (
                    data_top_8.groupby([data_top_8[fecha_col].dt.date, municipio_col])
                    .size()
                    .reset_index()
                )
                temporal_data.columns = ["Fecha", "Municipio", "Vacunados"]
                temporal_data["Fecha"] = pd.to_datetime(temporal_data["Fecha"])

                fig_temporal = px.line(
                    temporal_data,
                    x="Fecha",
                    y="Vacunados",
                    color="Municipio",
                    title="Evolución Temporal - Top 8 Municipios",
                    height=400,
                )

                fig_temporal.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white", hovermode="x unified"
                )

                st.plotly_chart(fig_temporal, use_container_width=True)
            else:
                st.warning("⚠️ No hay fechas válidas para análisis temporal")

        except Exception as e:
            st.warning(f"⚠️ Error en análisis temporal: {str(e)}")

    # ==========================================
    # SECCIÓN 4: TABLA DETALLADA
    # ==========================================
    st.subheader("📋 Detalle por Municipios")

    # Preparar tabla con estadísticas adicionales
    tabla_detallada = municipios_stats.copy()
    tabla_detallada["Porcentaje"] = (
        tabla_detallada["Vacunados"] / total_vacunados * 100
    ).round(2)
    tabla_detallada["Categoria"] = tabla_detallada["Vacunados"].apply(
        categorizar_municipio
    )

    # Agregar ranking
    tabla_detallada["Ranking"] = range(1, len(tabla_detallada) + 1)

    # Reordenar columnas
    tabla_detallada = tabla_detallada[
        ["Ranking", "Municipio", "Vacunados", "Porcentaje", "Categoria"]
    ]

    # Mostrar tabla con filtros
    col_filtro1, col_filtro2 = st.columns(2)

    with col_filtro1:
        categoria_filtro = st.selectbox(
            "Filtrar por categoría:", ["Todas"] + orden_categorias
        )

    with col_filtro2:
        min_vacunados = st.number_input(
            "Mínimo de vacunados:",
            min_value=0,
            max_value=int(tabla_detallada["Vacunados"].max()),
            value=0,
        )

    # Aplicar filtros
    tabla_filtrada = tabla_detallada.copy()

    if categoria_filtro != "Todas":
        tabla_filtrada = tabla_filtrada[tabla_filtrada["Categoria"] == categoria_filtro]

    if min_vacunados > 0:
        tabla_filtrada = tabla_filtrada[tabla_filtrada["Vacunados"] >= min_vacunados]

    # Mostrar tabla
    st.dataframe(tabla_filtrada, use_container_width=True, hide_index=True)

    # ==========================================
    # SECCIÓN 5: INSIGHTS GEOGRÁFICOS
    # ==========================================
    st.subheader("💡 Insights Geográficos")

    try:
        insights = []

        # Concentración geográfica
        top_5_porcentaje = (
            municipios_stats.head(5)["Vacunados"].sum() / total_vacunados * 100
        )
        if top_5_porcentaje > 60:
            insights.append(
                f"🎯 **Alta concentración**: Top 5 municipios representan {top_5_porcentaje:.1f}% de la vacunación"
            )
        elif top_5_porcentaje < 40:
            insights.append(
                f"🌐 **Distribución equilibrada**: Top 5 municipios solo representan {top_5_porcentaje:.1f}% de la vacunación"
            )

        # Análisis de cobertura
        municipios_sin_datos = 47 - total_municipios
        if municipios_sin_datos > 0:
            insights.append(
                f"⚠️ **{municipios_sin_datos} municipios sin datos** de vacunación registrados"
            )
        else:
            insights.append(
                "✅ **Cobertura completa**: Todos los 47 municipios tienen registro de vacunación"
            )

        # Análisis de variabilidad
        coef_variacion = (
            municipios_stats["Vacunados"].std() / municipios_stats["Vacunados"].mean()
        ) * 100
        if coef_variacion > 100:
            insights.append(
                f"📊 **Alta variabilidad**: Gran disparidad entre municipios (CV: {coef_variacion:.1f}%)"
            )
        elif coef_variacion < 50:
            insights.append(
                f"📊 **Distribución uniforme**: Poca disparidad entre municipios (CV: {coef_variacion:.1f}%)"
            )

        # Mostrar insights
        if insights:
            for insight in insights:
                st.markdown(f"- {insight}")
        else:
            st.info("📊 Distribución geográfica estándar sin patrones destacables")

    except Exception as e:
        st.warning(f"⚠️ Error calculando insights: {str(e)}")


def mostrar_geographic(data):
    """
    Función de compatibilidad hacia atrás
    """
    st.header("Distribución Geográfica de Vacunación")

    if data is None or data.empty:
        st.warning("No hay datos geográficos disponibles para mostrar")
        return

    # Buscar columna de región o municipio
    region_col = None
    possible_cols = [
        "region",
        "Region",
        "REGION",
        "Municipio",
        "MUNICIPIO",
        "NombreMunicipioResidencia",
    ]

    for col in possible_cols:
        if col in data.columns:
            region_col = col
            break

    if region_col is not None:
        region_stats = data.groupby(region_col).size().reset_index(name="count")
        fig = px.bar(
            region_stats,
            x=region_col,
            y="count",
            title=f"Vacunaciones por {region_col}",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No se encontró información regional en los datos")

        # Mostrar información disponible
        with st.expander("🔍 Información disponible"):
            st.write("**Columnas disponibles:**")
            st.write(list(data.columns))
