"""
vistas/geographic.py - Análisis geográfico con lógica temporal
Enfocado en distribución por municipios sin duplicados
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def show_geographic_tab(combined_data, COLORS):
    """Muestra análisis geográfico por municipios"""
    st.header("🗺️ Distribución Geográfica")

    # Análisis de vacunación PRE-emergencia por municipios
    show_individual_by_municipality(combined_data, COLORS)

    # Análisis de barridos DURANTE emergencia por municipios
    show_barridos_by_municipality(combined_data, COLORS)

    # Comparación territorial combinada
    show_territorial_comparison(combined_data, COLORS)


def show_individual_by_municipality(combined_data, COLORS):
    """Muestra distribución de vacunación PRE-emergencia por municipios"""
    st.subheader("🏥 Vacunación PRE-Emergencia por Municipios")

    individual_municipios = combined_data["individual_pre"]["por_municipio"]

    if not individual_municipios:
        st.warning("⚠️ No hay datos de municipios para vacunación PRE-emergencia")
        return

    # Convertir a DataFrame y ordenar
    df_individual = pd.DataFrame(
        list(individual_municipios.items()), columns=["Municipio", "Vacunados"]
    )
    df_individual = df_individual.sort_values("Vacunados", ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        # Top 15 municipios
        top_15 = df_individual.head(15)

        fig = px.bar(
            top_15,
            x="Vacunados",
            y="Municipio",
            orientation="h",
            title="Top 15 Municipios - Vacunación PRE-Emergencia",
            color_discrete_sequence=[COLORS["primary"]],
            text="Vacunados",
        )

        fig.update_traces(texttemplate="%{text:,}", textposition="outside")

        fig.update_layout(
            plot_bgcolor=COLORS["white"],
            paper_bgcolor=COLORS["white"],
            height=500,
            yaxis={"categoryorder": "total ascending"},
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Concentración - Top 5 vs Resto
        total_individual = df_individual["Vacunados"].sum()
        top_5_total = df_individual.head(5)["Vacunados"].sum()
        resto_total = total_individual - top_5_total

        concentracion_data = {
            "Categoria": ["Top 5 Municipios", "Resto de Municipios"],
            "Vacunados": [top_5_total, resto_total],
            "Porcentaje": [
                (top_5_total / total_individual) * 100,
                (resto_total / total_individual) * 100,
            ],
        }

        fig_pie = px.pie(
            values=concentracion_data["Vacunados"],
            names=concentracion_data["Categoria"],
            title="Concentración Vacunación PRE-Emergencia",
            color_discrete_sequence=[COLORS["primary"], COLORS["accent"]],
        )

        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(height=500)

        st.plotly_chart(fig_pie, use_container_width=True)

    # Estadísticas
    municipios_count = len(df_individual)
    promedio_por_municipio = df_individual["Vacunados"].mean()
    municipio_lider = df_individual.iloc[0]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Municipios con Vacunación PRE", f"{municipios_count}")

    with col2:
        st.metric("Promedio por Municipio", f"{promedio_por_municipio:.0f}")

    with col3:
        st.metric(
            "Municipio Líder PRE",
            f"{municipio_lider['Vacunados']:,}",
            delta=municipio_lider["Municipio"],
        )


def show_barridos_by_municipality(combined_data, COLORS):
    """Muestra distribución de barridos DURANTE emergencia por municipios"""
    st.subheader("🚨 Barridos DURANTE Emergencia por Municipios")

    barridos_municipios = combined_data["barridos"]["vacunados_barrido"][
        "por_municipio"
    ]

    if not barridos_municipios:
        st.warning("⚠️ No hay datos de municipios para barridos DURANTE emergencia")
        return

    # Convertir a DataFrame y ordenar
    df_barridos = pd.DataFrame(
        list(barridos_municipios.items()), columns=["Municipio", "Vacunados"]
    )
    df_barridos = df_barridos.sort_values("Vacunados", ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        # Top 15 municipios
        top_15 = df_barridos.head(15)

        fig = px.bar(
            top_15,
            x="Vacunados",
            y="Municipio",
            orientation="h",
            title="Top 15 Municipios - Barridos DURANTE Emergencia",
            color_discrete_sequence=[COLORS["warning"]],
            text="Vacunados",
        )

        fig.update_traces(texttemplate="%{text:,}", textposition="outside")

        fig.update_layout(
            plot_bgcolor=COLORS["white"],
            paper_bgcolor=COLORS["white"],
            height=500,
            yaxis={"categoryorder": "total ascending"},
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Análisis de intensidad de barridos
        df_barridos["Categoria"] = df_barridos["Vacunados"].apply(
            lambda x: (
                "Alta Intensidad (>500)"
                if x > 500
                else (
                    "Media Intensidad (100-500)"
                    if x >= 100
                    else "Baja Intensidad (<100)"
                )
            )
        )

        categoria_counts = df_barridos["Categoria"].value_counts()

        fig_intensidad = px.pie(
            values=categoria_counts.values,
            names=categoria_counts.index,
            title="Intensidad de Barridos por Municipios",
            color_discrete_sequence=[
                COLORS["warning"],
                COLORS["secondary"],
                COLORS["accent"],
            ],
        )

        fig_intensidad.update_traces(textposition="inside", textinfo="percent+label")
        fig_intensidad.update_layout(height=500)

        st.plotly_chart(fig_intensidad, use_container_width=True)

    # Estadísticas
    municipios_barridos = len(df_barridos)
    promedio_barridos = df_barridos["Vacunados"].mean()
    municipio_lider_barridos = df_barridos.iloc[0]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Municipios con Barridos", f"{municipios_barridos}")

    with col2:
        st.metric("Promedio por Municipio", f"{promedio_barridos:.0f}")

    with col3:
        st.metric(
            "Municipio Líder DURANTE",
            f"{municipio_lider_barridos['Vacunados']:,}",
            delta=municipio_lider_barridos["Municipio"],
        )


def show_territorial_comparison(combined_data, COLORS):
    """Muestra comparación territorial entre modalidades"""
    st.subheader("⚖️ Comparación Territorial: PRE vs DURANTE Emergencia")

    individual_municipios = combined_data["individual_pre"]["por_municipio"]
    barridos_municipios = combined_data["barridos"]["vacunados_barrido"][
        "por_municipio"
    ]

    if not individual_municipios and not barridos_municipios:
        st.warning("⚠️ No hay datos municipales para comparar")
        return

    # Combinar datos de ambas modalidades
    all_municipios = set(individual_municipios.keys()) | set(barridos_municipios.keys())

    comparison_data = []
    for municipio in all_municipios:
        individual_count = individual_municipios.get(municipio, 0)
        barridos_count = barridos_municipios.get(municipio, 0)
        total_count = individual_count + barridos_count

        if total_count > 0:  # Solo incluir municipios con vacunación
            comparison_data.append(
                {
                    "Municipio": municipio,
                    "PRE-Emergencia": individual_count,
                    "DURANTE Emergencia": barridos_count,
                    "Total Real": total_count,
                    "Prop_PRE": (
                        (individual_count / total_count * 100) if total_count > 0 else 0
                    ),
                    "Prop_DURANTE": (
                        (barridos_count / total_count * 100) if total_count > 0 else 0
                    ),
                }
            )

    if not comparison_data:
        st.warning("⚠️ No hay datos para comparación territorial")
        return

    df_comparison = pd.DataFrame(comparison_data)
    df_comparison = df_comparison.sort_values("Total Real", ascending=False)

    # Gráfico de barras apiladas - Top 20
    top_20 = df_comparison.head(20)

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            name="PRE-Emergencia",
            x=top_20["Municipio"],
            y=top_20["PRE-Emergencia"],
            marker_color=COLORS["primary"],
        )
    )

    fig.add_trace(
        go.Bar(
            name="DURANTE Emergencia",
            x=top_20["Municipio"],
            y=top_20["DURANTE Emergencia"],
            marker_color=COLORS["warning"],
        )
    )

    fig.update_layout(
        title="Comparación Territorial: PRE vs DURANTE Emergencia (Top 20)",
        xaxis_title="Municipio",
        yaxis_title="Cantidad de Vacunados",
        barmode="stack",
        plot_bgcolor=COLORS["white"],
        paper_bgcolor=COLORS["white"],
        height=500,
        xaxis={"tickangle": 45},
    )

    st.plotly_chart(fig, use_container_width=True)

    # Análisis de estrategias territoriales
    st.markdown("**🎯 Análisis de Estrategias Temporales por Municipio:**")

    # Clasificar municipios por estrategia dominante
    df_comparison["Estrategia"] = df_comparison.apply(
        lambda row: (
            "Principalmente PRE-Emergencia"
            if row["Prop_PRE"] > 70
            else (
                "Principalmente DURANTE Emergencia"
                if row["Prop_DURANTE"] > 70
                else "Estrategia Temporal Mixta"
            )
        ),
        axis=1,
    )

    estrategia_counts = df_comparison["Estrategia"].value_counts()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Principalmente PRE",
            estrategia_counts.get("Principalmente PRE-Emergencia", 0),
        )

    with col2:
        st.metric(
            "Principalmente DURANTE",
            estrategia_counts.get("Principalmente DURANTE Emergencia", 0),
        )

    with col3:
        st.metric("Estrategia Mixta", estrategia_counts.get("Estrategia Temporal Mixta", 0))

    # Municipios destacados por estrategia
    if len(df_comparison) > 0:
        municipio_mas_pre = df_comparison.loc[df_comparison["Prop_PRE"].idxmax()]
        municipio_mas_durante = df_comparison.loc[df_comparison["Prop_DURANTE"].idxmax()]

        col1, col2 = st.columns(2)

        with col1:
            st.info(
                f"**🏥 Mayor dependencia PRE-emergencia:**\n{municipio_mas_pre['Municipio']}\n{municipio_mas_pre['Prop_PRE']:.1f}% PRE-emergencia"
            )

        with col2:
            st.info(
                f"**🚨 Mayor dependencia DURANTE emergencia:**\n{municipio_mas_durante['Municipio']}\n{municipio_mas_durante['Prop_DURANTE']:.1f}% DURANTE emergencia"
            )

    # Información sobre renuentes si disponible
    renuentes_municipios = combined_data["barridos"]["renuentes"]["por_municipio"]
    
    if renuentes_municipios:
        st.markdown("**🚫 Análisis de Renuentes por Municipio:**")
        
        df_renuentes = pd.DataFrame(
            list(renuentes_municipios.items()), columns=["Municipio", "Renuentes"]
        )
        df_renuentes = df_renuentes.sort_values("Renuentes", ascending=False).head(10)
        
        if not df_renuentes.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                fig_renuentes = px.bar(
                    df_renuentes,
                    x="Renuentes",
                    y="Municipio",
                    orientation="h",
                    title="Top 10 Municipios con Más Renuentes",
                    color_discrete_sequence=[COLORS["accent"]],
                    text="Renuentes",
                )
                
                fig_renuentes.update_traces(texttemplate="%{text:,}", textposition="outside")
                fig_renuentes.update_layout(
                    plot_bgcolor=COLORS["white"],
                    paper_bgcolor=COLORS["white"],
                    height=400,
                    yaxis={"categoryorder": "total ascending"},
                )
                
                st.plotly_chart(fig_renuentes, use_container_width=True)
            
            with col2:
                total_renuentes = df_renuentes["Renuentes"].sum()
                municipio_max_renuentes = df_renuentes.iloc[0]
                
                st.metric("Total Renuentes (Top 10)", f"{total_renuentes:,}")
                st.metric(
                    "Municipio con Más Renuentes",
                    f"{municipio_max_renuentes['Renuentes']:,}",
                    delta=municipio_max_renuentes["Municipio"],
                )