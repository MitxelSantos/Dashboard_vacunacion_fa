import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from src.visualization.charts import (
    create_bar_chart,
    create_scatter_plot,
    create_line_chart,
)
from src.data import load_and_combine_data
import folium
from streamlit_folium import folium_static
import geopandas as gpd


def show(data, filters, colors, fuente_poblacion="DANE"):
    """
    Muestra la página de distribución geográfica del dashboard.
    VERSIÓN MEJORADA: Enfocada en análisis estadísticos de la población seleccionada,
    eliminando comparaciones excesivas DANE vs SISBEN.

    Args:
        data (dict): Diccionario con los dataframes
        filters (dict): Filtros seleccionados
        colors (dict): Colores institucionales
        fuente_poblacion (str): Fuente de datos de población ("DANE" o "SISBEN")
    """
    st.title("Distribución Geográfica")

    # Aplicar filtros a los datos
    from src.data.preprocessor import apply_filters

    filtered_data = apply_filters(data, filters, fuente_poblacion)

    # Determinar qué columna de cobertura usar según la fuente
    cobertura_col = f"Cobertura_{fuente_poblacion}"
    pendientes_col = f"Pendientes_{fuente_poblacion}"

    # =====================================================================
    # SECCIÓN 1: ANÁLISIS DE COBERTURA POR MUNICIPIO
    # =====================================================================
    st.subheader(f"Análisis de Cobertura por Municipio (Población {fuente_poblacion})")

    # Ordenar municipios por cobertura para análisis
    municipios_ordenados = filtered_data["metricas"].sort_values(
        by=cobertura_col, ascending=False
    )

    # Estadísticas descriptivas de cobertura
    cobertura_stats = {
        "Promedio": municipios_ordenados[cobertura_col].mean(),
        "Mediana": municipios_ordenados[cobertura_col].median(),
        "Mínimo": municipios_ordenados[cobertura_col].min(),
        "Máximo": municipios_ordenados[cobertura_col].max(),
        "Desviación Estándar": municipios_ordenados[cobertura_col].std(),
        "Q1 (25%)": municipios_ordenados[cobertura_col].quantile(0.25),
        "Q3 (75%)": municipios_ordenados[cobertura_col].quantile(0.75),
    }

    # Mostrar estadísticas en métricas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Cobertura Promedio",
            f"{cobertura_stats['Promedio']:.1f}%",
            delta=f"σ: {cobertura_stats['Desviación Estándar']:.1f}%",
        )

    with col2:
        st.metric(
            "Cobertura Mediana",
            f"{cobertura_stats['Mediana']:.1f}%",
            delta=f"Rango: {cobertura_stats['Máximo'] - cobertura_stats['Mínimo']:.1f}%",
        )

    with col3:
        st.metric(
            "Mejor Municipio",
            municipios_ordenados.iloc[0]["DPMP"],
            delta=f"{cobertura_stats['Máximo']:.1f}%",
        )

    with col4:
        st.metric(
            "Municipio con Menor Cobertura",
            municipios_ordenados.iloc[-1]["DPMP"],
            delta=f"{cobertura_stats['Mínimo']:.1f}%",
        )

    # Gráfico principal de cobertura por municipio
    fig_cobertura = create_bar_chart(
        data=municipios_ordenados,
        x="DPMP",
        y=cobertura_col,
        title=f"Cobertura por municipio (Población {fuente_poblacion})",
        color=colors["primary"],
        height=500,
        formatter="%{y:.1f}%",
    )

    # Añadir líneas de referencia estadísticas
    fig_cobertura.add_hline(
        y=cobertura_stats["Promedio"],
        line_dash="dash",
        line_color="red",
        annotation_text=f"Promedio: {cobertura_stats['Promedio']:.1f}%",
    )
    fig_cobertura.add_hline(
        y=cobertura_stats["Mediana"],
        line_dash="dot",
        line_color="blue",
        annotation_text=f"Mediana: {cobertura_stats['Mediana']:.1f}%",
    )

    st.plotly_chart(fig_cobertura, use_container_width=True)

    # =====================================================================
    # SECCIÓN 2: ANÁLISIS DE DISTRIBUCIÓN Y CONCENTRACIÓN
    # =====================================================================
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Distribución de Población y Vacunados")

        # Análisis de concentración de población vs vacunados
        total_poblacion = filtered_data["metricas"][fuente_poblacion].sum()
        total_vacunados = filtered_data["metricas"]["Vacunados"].sum()

        # Calcular porcentajes acumulados para curva de Lorenz simplificada
        municipios_sorted = filtered_data["metricas"].sort_values(
            fuente_poblacion, ascending=False
        )
        municipios_sorted["pct_poblacion"] = (
            municipios_sorted[fuente_poblacion] / total_poblacion * 100
        ).cumsum()
        municipios_sorted["pct_vacunados"] = (
            municipios_sorted["Vacunados"] / total_vacunados * 100
        ).cumsum()

        # Crear gráfico de concentración
        fig_concentracion = go.Figure()

        fig_concentracion.add_trace(
            go.Scatter(
                x=list(range(1, len(municipios_sorted) + 1)),
                y=municipios_sorted["pct_poblacion"],
                mode="lines+markers",
                name=f"% Acum. Población {fuente_poblacion}",
                line=dict(color=colors["primary"], width=3),
                hovertemplate="Municipio #%{x}<br>% Acum. Población: %{y:.1f}%<extra></extra>",
            )
        )

        fig_concentracion.add_trace(
            go.Scatter(
                x=list(range(1, len(municipios_sorted) + 1)),
                y=municipios_sorted["pct_vacunados"],
                mode="lines+markers",
                name="% Acum. Vacunados",
                line=dict(color=colors["secondary"], width=3),
                hovertemplate="Municipio #%{x}<br>% Acum. Vacunados: %{y:.1f}%<extra></extra>",
            )
        )

        fig_concentracion.update_layout(
            title="Concentración de Población vs Vacunados",
            xaxis_title="Municipios (ordenados por población)",
            yaxis_title="Porcentaje Acumulado",
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=400,
        )

        st.plotly_chart(fig_concentracion, use_container_width=True)

    with col_right:
        st.subheader("Relación Población vs Vacunados")

        # Gráfico de dispersión con línea de regresión
        fig_scatter = create_scatter_plot(
            data=filtered_data["metricas"],
            x=fuente_poblacion,
            y="Vacunados",
            title=f"Relación Población {fuente_poblacion} vs Vacunados",
            color=colors["accent"],
            hover_data=["DPMP", cobertura_col],
            height=400,
        )

        # Calcular correlación
        correlation = filtered_data["metricas"][fuente_poblacion].corr(
            filtered_data["metricas"]["Vacunados"]
        )

        # Añadir línea de regresión
        x_vals = filtered_data["metricas"][fuente_poblacion]
        y_vals = filtered_data["metricas"]["Vacunados"]

        if len(x_vals) > 1:
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                x_vals, y_vals
            )
            line_x = np.array([x_vals.min(), x_vals.max()])
            line_y = slope * line_x + intercept

            fig_scatter.add_trace(
                go.Scatter(
                    x=line_x,
                    y=line_y,
                    mode="lines",
                    name=f"Regresión (r={correlation:.3f})",
                    line=dict(color="red", dash="dash", width=2),
                    hoverinfo="skip",
                )
            )

        st.plotly_chart(fig_scatter, use_container_width=True)

        # Mostrar estadísticas de correlación
        st.info(
            f"""
        **Análisis de Correlación:**
        - Correlación: {correlation:.3f}
        - Interpretación: {'Fuerte' if abs(correlation) > 0.7 else 'Moderada' if abs(correlation) > 0.4 else 'Débil'} 
          correlación {'positiva' if correlation > 0 else 'negativa'}
        """
        )

    # =====================================================================
    # SECCIÓN 3: ANÁLISIS DE BRECHAS Y MUNICIPIOS PRIORITARIOS
    # =====================================================================
    st.subheader("Análisis de Brechas y Priorización")

    # Identificar municipios por categorías de cobertura
    municipios_alta = municipios_ordenados[municipios_ordenados[cobertura_col] >= 80]
    municipios_media = municipios_ordenados[
        (municipios_ordenados[cobertura_col] >= 50)
        & (municipios_ordenados[cobertura_col] < 80)
    ]
    municipios_baja = municipios_ordenados[municipios_ordenados[cobertura_col] < 50]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🟢 Cobertura Alta (≥80%)")
        st.metric("Cantidad de municipios", len(municipios_alta))
        if len(municipios_alta) > 0:
            st.write("**Municipios:**")
            for _, municipio in municipios_alta.head(5).iterrows():
                st.write(f"• {municipio['DPMP']}: {municipio[cobertura_col]:.1f}%")
            if len(municipios_alta) > 5:
                st.write(f"... y {len(municipios_alta) - 5} más")

    with col2:
        st.markdown("### 🟡 Cobertura Media (50-79%)")
        st.metric("Cantidad de municipios", len(municipios_media))
        if len(municipios_media) > 0:
            st.write("**Municipios:**")
            for _, municipio in municipios_media.head(5).iterrows():
                st.write(f"• {municipio['DPMP']}: {municipio[cobertura_col]:.1f}%")
            if len(municipios_media) > 5:
                st.write(f"... y {len(municipios_media) - 5} más")

    with col3:
        st.markdown("### 🔴 Cobertura Baja (<50%)")
        st.metric("Cantidad de municipios", len(municipios_baja))
        if len(municipios_baja) > 0:
            st.write("**Municipios PRIORITARIOS:**")
            for _, municipio in municipios_baja.iterrows():
                st.write(f"• {municipio['DPMP']}: {municipio[cobertura_col]:.1f}%")

    # =====================================================================
    # SECCIÓN 4: ANÁLISIS DE EFICIENCIA RELATIVA
    # =====================================================================
    st.subheader("Análisis de Eficiencia en Vacunación")

    # Calcular eficiencia relativa (vacunados por cada 1000 habitantes)
    filtered_data["metricas"]["Eficiencia"] = (
        filtered_data["metricas"]["Vacunados"]
        / filtered_data["metricas"][fuente_poblacion]
        * 1000
    ).round(2)

    # Categorizar municipios por tamaño de población para análisis comparativo
    q33 = filtered_data["metricas"][fuente_poblacion].quantile(0.33)
    q66 = filtered_data["metricas"][fuente_poblacion].quantile(0.66)

    def categorize_by_size(pop):
        if pop <= q33:
            return "Pequeño"
        elif pop <= q66:
            return "Mediano"
        else:
            return "Grande"

    filtered_data["metricas"]["Categoria_Tamaño"] = filtered_data["metricas"][
        fuente_poblacion
    ].apply(categorize_by_size)

    # Análisis por categoría de tamaño
    eficiencia_por_categoria = (
        filtered_data["metricas"]
        .groupby("Categoria_Tamaño")
        .agg(
            {
                "Eficiencia": ["mean", "median", "std", "count"],
                cobertura_col: ["mean", "median"],
            }
        )
        .round(2)
    )

    col_left, col_right = st.columns(2)

    with col_left:
        # Gráfico de eficiencia por categoría
        categoria_stats = (
            filtered_data["metricas"]
            .groupby("Categoria_Tamaño")[["Eficiencia", cobertura_col]]
            .mean()
            .reset_index()
        )
        categoria_stats.columns = [
            "Categoria",
            "Eficiencia_Promedio",
            "Cobertura_Promedio",
        ]

        fig_eficiencia = go.Figure()

        fig_eficiencia.add_trace(
            go.Bar(
                x=categoria_stats["Categoria"],
                y=categoria_stats["Eficiencia_Promedio"],
                name="Eficiencia (Vac/1000 hab)",
                marker_color=colors["primary"],
                yaxis="y1",
            )
        )

        fig_eficiencia.add_trace(
            go.Scatter(
                x=categoria_stats["Categoria"],
                y=categoria_stats["Cobertura_Promedio"],
                mode="lines+markers",
                name="Cobertura Promedio (%)",
                line=dict(color=colors["warning"], width=3),
                yaxis="y2",
            )
        )

        fig_eficiencia.update_layout(
            title="Eficiencia por Tamaño de Municipio",
            xaxis_title="Categoría de Municipio",
            yaxis=dict(title="Vacunados por 1000 hab", side="left"),
            yaxis2=dict(title="Cobertura (%)", side="right", overlaying="y"),
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=400,
        )

        st.plotly_chart(fig_eficiencia, use_container_width=True)

    with col_right:
        # Top 10 municipios más eficientes
        top_eficientes = filtered_data["metricas"].nlargest(10, "Eficiencia")

        fig_top_eficientes = create_bar_chart(
            data=top_eficientes,
            x="DPMP",
            y="Eficiencia",
            title="Top 10 Municipios Más Eficientes",
            color=colors["secondary"],
            height=400,
            formatter="%{y:.1f} vac/1000hab",
        )

        st.plotly_chart(fig_top_eficientes, use_container_width=True)

    # =====================================================================
    # SECCIÓN 5: RESUMEN ESTADÍSTICO Y TABLA DETALLADA
    # =====================================================================
    st.subheader("Resumen Estadístico Detallado")

    # Crear tabla resumen por categoría de tamaño
    resumen_estadistico = pd.DataFrame(
        {
            "Categoría": ["Pequeño", "Mediano", "Grande", "GENERAL"],
            "N° Municipios": [
                len(
                    filtered_data["metricas"][
                        filtered_data["metricas"]["Categoria_Tamaño"] == "Pequeño"
                    ]
                ),
                len(
                    filtered_data["metricas"][
                        filtered_data["metricas"]["Categoria_Tamaño"] == "Mediano"
                    ]
                ),
                len(
                    filtered_data["metricas"][
                        filtered_data["metricas"]["Categoria_Tamaño"] == "Grande"
                    ]
                ),
                len(filtered_data["metricas"]),
            ],
            "Población Promedio": [
                filtered_data["metricas"][
                    filtered_data["metricas"]["Categoria_Tamaño"] == "Pequeño"
                ][fuente_poblacion].mean(),
                filtered_data["metricas"][
                    filtered_data["metricas"]["Categoria_Tamaño"] == "Mediano"
                ][fuente_poblacion].mean(),
                filtered_data["metricas"][
                    filtered_data["metricas"]["Categoria_Tamaño"] == "Grande"
                ][fuente_poblacion].mean(),
                filtered_data["metricas"][fuente_poblacion].mean(),
            ],
            "Cobertura Promedio (%)": [
                filtered_data["metricas"][
                    filtered_data["metricas"]["Categoria_Tamaño"] == "Pequeño"
                ][cobertura_col].mean(),
                filtered_data["metricas"][
                    filtered_data["metricas"]["Categoria_Tamaño"] == "Mediano"
                ][cobertura_col].mean(),
                filtered_data["metricas"][
                    filtered_data["metricas"]["Categoria_Tamaño"] == "Grande"
                ][cobertura_col].mean(),
                filtered_data["metricas"][cobertura_col].mean(),
            ],
            "Eficiencia Promedio": [
                filtered_data["metricas"][
                    filtered_data["metricas"]["Categoria_Tamaño"] == "Pequeño"
                ]["Eficiencia"].mean(),
                filtered_data["metricas"][
                    filtered_data["metricas"]["Categoria_Tamaño"] == "Mediano"
                ]["Eficiencia"].mean(),
                filtered_data["metricas"][
                    filtered_data["metricas"]["Categoria_Tamaño"] == "Grande"
                ]["Eficiencia"].mean(),
                filtered_data["metricas"]["Eficiencia"].mean(),
            ],
        }
    )

    # Formatear la tabla
    resumen_estadistico["Población Promedio"] = resumen_estadistico[
        "Población Promedio"
    ].apply(lambda x: f"{x:,.0f}".replace(",", "."))
    resumen_estadistico["Cobertura Promedio (%)"] = resumen_estadistico[
        "Cobertura Promedio (%)"
    ].apply(lambda x: f"{x:.1f}%")
    resumen_estadistico["Eficiencia Promedio"] = resumen_estadistico[
        "Eficiencia Promedio"
    ].apply(lambda x: f"{x:.1f}")

    st.dataframe(resumen_estadistico, use_container_width=True)

    # Tabla de datos completa con categorización
    st.subheader("Datos Detallados por Municipio")

    # Preparar tabla final con todas las métricas
    tabla_final = filtered_data["metricas"][
        [
            "DPMP",
            fuente_poblacion,
            "Vacunados",
            cobertura_col,
            pendientes_col,
            "Eficiencia",
            "Categoria_Tamaño",
        ]
    ].copy()

    # Renombrar columnas para mejor presentación
    tabla_final.columns = [
        "Municipio",
        f"Población {fuente_poblacion}",
        "Vacunados",
        "Cobertura (%)",
        "Pendientes",
        "Eficiencia (Vac/1000hab)",
        "Categoría por Tamaño",
    ]

    # Función helper para formato con punto como separador de miles
    def format_with_dots(x):
        return f"{x:,.0f}".replace(",", ".")

    # Mostrar tabla con formato mejorado
    st.dataframe(
        tabla_final.style.format(
            {
                f"Población {fuente_poblacion}": lambda x: format_with_dots(x),
                "Vacunados": lambda x: format_with_dots(x),
                "Cobertura (%)": "{:.2f}%",
                "Pendientes": lambda x: format_with_dots(x),
                "Eficiencia (Vac/1000hab)": "{:.2f}",
            }
        ),
        use_container_width=True,
    )

    # Insights finales
    st.markdown("---")
    st.markdown("### 📊 Insights Clave:")

    insights = []

    # Insight sobre dispersión
    cv_cobertura = (
        cobertura_stats["Desviación Estándar"] / cobertura_stats["Promedio"]
    ) * 100
    if cv_cobertura > 30:
        insights.append(
            f"🔍 **Alta variabilidad** en cobertura entre municipios (CV: {cv_cobertura:.1f}%)"
        )
    else:
        insights.append(
            f"📈 **Cobertura relativamente homogénea** entre municipios (CV: {cv_cobertura:.1f}%)"
        )

    # Insight sobre correlación
    if abs(correlation) > 0.7:
        insights.append(
            f"📊 **Fuerte correlación** entre población y vacunados (r={correlation:.3f})"
        )
    elif abs(correlation) < 0.3:
        insights.append(
            f"⚠️ **Débil correlación** entre población y vacunados - revisar estrategias por municipio"
        )

    # Insight sobre municipios prioritarios
    if len(municipios_baja) > 0:
        insights.append(
            f"🎯 **{len(municipios_baja)} municipios requieren atención prioritaria** (cobertura <50%)"
        )

    # Mostrar insights
    for insight in insights:
        st.markdown(f"- {insight}")

    # =====================================================================
    # SECCIÓN 6: VISUALIZACIÓN GEOGRÁFICA
    # =====================================================================
    st.subheader("Visualización Geográfica de la Cobertura")

    # Load data
    df_combined, df_aseguramiento, fecha_corte = load_and_combine_data(
        "data/Resumen.xlsx",
        "data/vacunacion_fa.csv",
        "data/Poblacion_aseguramiento.xlsx",
    )

    # Load geographic data
    gdf = gpd.read_file("data/geo/municipios.shp")

    # Calculate metrics by municipality
    municipios_stats = (
        df_combined.groupby("Municipio")
        .agg({"Fecha_Aplicacion": "count"})
        .reset_index()
    )
    municipios_stats.columns = ["Municipio", "Total_Vacunados"]

    # Merge with population data
    municipios_stats = municipios_stats.merge(
        df_aseguramiento.groupby("Nombre_Municipio")["Total"].sum().reset_index(),
        left_on="Municipio",
        right_on="Nombre_Municipio",
        how="left",
    )

    # Calculate coverage
    municipios_stats["Cobertura"] = (
        municipios_stats["Total_Vacunados"] / municipios_stats["Total"] * 100
    ).round(2)

    # Create map
    m = folium.Map(location=[7.8890, -72.4966], zoom_start=8)

    # Add choropleth layer
    gdf = gdf.merge(
        municipios_stats, left_on="MPIO_CNMBR", right_on="Municipio", how="left"
    )

    folium.Choropleth(
        geo_data=gdf.__geo_interface__,
        name="Cobertura",
        data=municipios_stats,
        columns=["Municipio", "Cobertura"],
        key_on="feature.properties.MPIO_CNMBR",
        fill_color="YlOrRd",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name="Cobertura (%)",
    ).add_to(m)

    folium_static(m)

    # Additional charts
    fig = px.bar(
        municipios_stats.sort_values("Cobertura", ascending=False),
        x="Municipio",
        y="Cobertura",
        title="Cobertura por Municipio",
    )
    st.plotly_chart(fig)

    # =====================================================================
    # SECCIÓN 7: VISTA GEOGRÁFICA SIMPLIFICADA
    # =====================================================================
    st.subheader("Distribución Geográfica - Vista Simplificada")

    def mostrar_geographic(df_combined, df_aseguramiento):
        """Muestra la vista geográfica del dashboard"""

        st.header("Distribución Geográfica")

        # Agrupar datos por municipio
        municipios_data = (
            df_combined.groupby("Municipio")
            .agg({"Fecha_Aplicacion": "count"})
            .reset_index()
        )
        municipios_data.columns = ["Municipio", "Total_Vacunados"]

        # Crear mapa de calor
        fig = px.choropleth(
            municipios_data,
            locations="Municipio",
            color="Total_Vacunados",
            title="Distribución de Vacunación por Municipio",
            color_continuous_scale="Viridis",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Tabla de datos
        st.subheader("Detalle por Municipio")
        st.dataframe(municipios_data)

    mostrar_geographic(df_combined, df_aseguramiento)
