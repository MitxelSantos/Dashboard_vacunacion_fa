import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from src.visualization.charts import create_bar_chart, create_pie_chart


def clean_list(lista):
    """Limpia una lista, eliminando valores NaN y convirtiendo el resto a strings."""
    return [str(item) for item in lista if not pd.isna(item)]


def show(data, filters, colors, fuente_poblacion="DANE"):
    """
    Muestra la página de aseguramiento del dashboard.

    Args:
        data (dict): Diccionario con los dataframes
        filters (dict): Filtros seleccionados
        colors (dict): Colores institucionales
        fuente_poblacion (str): Fuente de datos de población ("DANE" o "SISBEN")
    """
    st.title("Aseguramiento")

    # Aplicar filtros a los datos
    from src.data.preprocessor import apply_filters

    filtered_data = apply_filters(data, filters, fuente_poblacion)

    # Asegúrate de que todos los valores son del tipo correcto
    # Esto soluciona problemas con valores NaN y comparaciones de tipos
    if "NombreAseguradora" in filtered_data["vacunacion"].columns:
        filtered_data["vacunacion"]["NombreAseguradora"] = filtered_data["vacunacion"][
            "NombreAseguradora"
        ].fillna("Sin especificar")

    if "RegimenAfiliacion" in filtered_data["vacunacion"].columns:
        filtered_data["vacunacion"]["RegimenAfiliacion"] = filtered_data["vacunacion"][
            "RegimenAfiliacion"
        ].fillna("Sin especificar")

    if "NombreMunicipioResidencia" in filtered_data["vacunacion"].columns:
        filtered_data["vacunacion"]["NombreMunicipioResidencia"] = filtered_data[
            "vacunacion"
        ]["NombreMunicipioResidencia"].fillna("Sin especificar")

    if "Sexo" in filtered_data["vacunacion"].columns:
        filtered_data["vacunacion"]["Sexo"] = filtered_data["vacunacion"][
            "Sexo"
        ].fillna("Sin especificar")

    # Dividir en dos columnas
    col1, col2 = st.columns(2)

    # Gráfico de distribución por régimen
    with col1:
        # Versión simplificada para evitar errores
        st.subheader("Distribución por régimen de afiliación")
        try:
            # Agrupar por régimen de manera segura
            regimen_counts = (
                filtered_data["vacunacion"]["RegimenAfiliacion"]
                .value_counts()
                .reset_index()
            )
            regimen_counts.columns = ["RegimenAfiliacion", "Vacunados"]

            # Mostrar la tabla en lugar del gráfico para depuración
            st.dataframe(regimen_counts)
        except Exception as e:
            st.error(f"Error al procesar datos de régimen: {str(e)}")

    # Gráfico de distribución por aseguradora
    with col2:
        # Versión simplificada para evitar errores
        st.subheader("Top aseguradoras")
        try:
            # Agrupar por aseguradora de manera segura
            aseguradora_counts = (
                filtered_data["vacunacion"]["NombreAseguradora"]
                .value_counts()
                .reset_index()
            )
            aseguradora_counts.columns = ["NombreAseguradora", "Vacunados"]

            # Mostrar la tabla en lugar del gráfico para depuración
            st.dataframe(aseguradora_counts.head(10))
        except Exception as e:
            st.error(f"Error al procesar datos de aseguradora: {str(e)}")

    # Análisis cruzado entre régimen y municipio - versión simplificada
    st.subheader("Análisis por régimen y municipio")

    try:
        # Hacer una versión simplificada de la tabla cruzada
        st.text(
            "Esta sección está temporalmente deshabilitada para solucionar errores."
        )
    except Exception as e:
        st.error(f"Error en tabla cruzada: {str(e)}")

    # Análisis por aseguradora - versión simplificada
    st.subheader("Análisis detallado por aseguradora")

    # Seleccionar aseguradora para análisis detallado - versión simplificada
    if "NombreAseguradora" in filtered_data["vacunacion"].columns:
        try:
            # Obtener aseguradoras únicas de manera segura
            aseguradoras_lista = [
                str(item)
                for item in filtered_data["vacunacion"]["NombreAseguradora"].unique()
                if not pd.isna(item)
            ]
            aseguradoras = ["Todas"] + sorted(aseguradoras_lista)

            aseguradora_seleccionada = st.selectbox(
                "Seleccione una aseguradora para análisis detallado:",
                options=aseguradoras,
            )

            if aseguradora_seleccionada != "Todas":
                st.success(f"Aseguradora seleccionada: {aseguradora_seleccionada}")
                st.text(
                    "Detalles temporalmente deshabilitados para solucionar errores."
                )
        except Exception as e:
            st.error(f"Error en la selección de aseguradora: {str(e)}")
