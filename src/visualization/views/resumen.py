import streamlit as st
import plotly.express as px
from src.utils.helpers import get_image_as_base64


def mostrar_resumen(df, fecha_actualizacion, fecha_corte):
    # Header y logos
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        logo_base64 = get_image_as_base64("static/logo.png")
        st.markdown(
            f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_base64}" width="200"></div>',
            unsafe_allow_html=True,
        )

    # Métricas principales
    total_vacunados = len(df)
    total_municipios = df["Municipio"].nunique()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Vacunados", f"{total_vacunados:,}")
    with col2:
        st.metric("Municipios", total_municipios)

    # Gráfica de distribución por municipio
    fig_municipios = px.bar(
        df["Municipio"].value_counts().reset_index(),
        x="Municipio",
        y="count",
        title="Vacunación por Municipio",
    )
    st.plotly_chart(fig_municipios, use_container_width=True)

    # Tabla detallada
    st.subheader("Detalle de Vacunación")
    st.dataframe(df)
