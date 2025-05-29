import streamlit as st
import pandas as pd
import plotly.express as px
from src.visualization.charts import create_bar_chart, create_pie_chart


def create_metrics(filtered_data, fuente_poblacion):
    """Create main metrics with simplified calculations"""
    total_vacunados = len(filtered_data["vacunacion"])
    total_poblacion = filtered_data["metricas"][fuente_poblacion].sum()
    cobertura = (total_vacunados / total_poblacion * 100) if total_poblacion > 0 else 0
    susceptibles = max(0, total_poblacion - total_vacunados)

    return {
        "total_vacunados": total_vacunados,
        "total_poblacion": total_poblacion,
        "cobertura": cobertura,
        "susceptibles": susceptibles,
    }


def show(data, filters, colors, fuente_poblacion="DANE"):
    """Simplified overview page"""
    st.title("Visión General")

    if not isinstance(data, dict) or "vacunacion" not in data:
        st.error("Invalid data format")
        return

    # Display metrics
    metrics = create_metrics(data, fuente_poblacion)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Población Total", f"{metrics['total_poblacion']:,.0f}")
    with col2:
        st.metric("Vacunados", f"{metrics['total_vacunados']:,.0f}")
    with col3:
        st.metric("Cobertura", f"{metrics['cobertura']:.1f}%")
    with col4:
        st.metric("Susceptibles", f"{metrics['susceptibles']:,.0f}")

    # Main charts
    col1, col2 = st.columns(2)

    with col1:
        # Municipality coverage
        fig = create_bar_chart(
            data=data["metricas"],
            x="DPMP",
            y=f"Cobertura_{fuente_poblacion}",
            title="Cobertura por Municipio",
            color=colors["primary"],
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Age distribution
        if "Grupo_Edad" in data["vacunacion"].columns:
            edad_counts = data["vacunacion"]["Grupo_Edad"].value_counts()
            fig = create_pie_chart(
                data=edad_counts.reset_index(),
                names="index",
                values="Grupo_Edad",
                title="Distribución por Edad",
                color_map={},
            )
            st.plotly_chart(fig, use_container_width=True)


def mostrar_overview(data):
    """
    Display overview statistics and visualizations for the vaccination dashboard

    Args:
        data (pd.DataFrame): DataFrame containing vaccination data
    """
    st.header("Overview del Dashboard de Vacunación")

    # Basic statistics
    if not data.empty:
        total_vacunados = len(data)
        st.metric("Total de Vacunados", f"{total_vacunados:,}")

        # Add more overview statistics and visualizations as needed
        # You can customize this function based on your specific requirements
    else:
        st.warning("No hay datos disponibles para mostrar")
