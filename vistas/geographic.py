import streamlit as st
import pandas as pd
import plotly.express as px


def mostrar_geographic(data):
    st.header("Distribución Geográfica de Vacunación")

    if not data.empty:
        if "region" in data.columns:
            region_stats = data.groupby("region").size().reset_index(name="count")
            fig = px.bar(
                region_stats,
                x="region",
                y="count",
                title="Vacunaciones por Región",
            )
            st.plotly_chart(fig)
    else:
        st.warning("No hay datos geográficos disponibles para mostrar")
