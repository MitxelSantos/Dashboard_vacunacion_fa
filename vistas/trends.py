import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from src.visualization.charts import create_line_chart, create_bar_chart
from datetime import datetime, timedelta


def show(data, filters, colors, fuente_poblacion="DANE"):
    """
    Muestra la página de tendencias del dashboard.

    Args:
        data (dict): Diccionario con los dataframes
        filters (dict): Filtros seleccionados
        colors (dict): Colores institucionales
        fuente_poblacion (str): Fuente de datos de población ("DANE" o "SISBEN")
    """
    st.title("Tendencias Temporales")

    # Aplicar filtros a los datos
    from src.data.preprocessor import apply_filters

    filtered_data = apply_filters(data, filters, fuente_poblacion)

    # Usar directamente FA UNICA como fecha de vacunación
    if "FA UNICA" in filtered_data["vacunacion"].columns:
        try:

            # Convertir a datetime
            filtered_data["vacunacion"]["FechaVacunacion"] = pd.to_datetime(
                filtered_data["vacunacion"]["FA UNICA"], errors="coerce"
            )

            # Filtrar registros con fechas válidas
            fechas_validas = ~filtered_data["vacunacion"]["FechaVacunacion"].isna()
            if fechas_validas.sum() > 0:
                filtered_data["vacunacion"] = filtered_data["vacunacion"][
                    fechas_validas
                ]
                process_dates(filtered_data, colors, fuente_poblacion, filters)
            else:
                st.error(
                    "No se pudieron obtener fechas válidas de la columna 'FA UNICA'"
                )
        except Exception as e:
            st.error(f"Error al procesar fechas de 'FA UNICA': {str(e)}")
    else:
        st.error("La columna 'FA UNICA' no se encuentra en los datos")


def process_dates(filtered_data, colors, fuente_poblacion, filters):
    """
    Procesa los datos de fechas y muestra los gráficos de tendencias.

    Args:
        filtered_data (dict): Datos filtrados para visualización
        colors (dict): Colores institucionales
        fuente_poblacion (str): Fuente de datos de población
        filters (dict): Filtros aplicados a los datos
    """
    # Agrupar por fecha
    vacunacion_diaria = (
        filtered_data["vacunacion"]
        .groupby(filtered_data["vacunacion"]["FechaVacunacion"].dt.date)
        .size()
        .reset_index()
    )
    vacunacion_diaria.columns = ["Fecha", "Vacunados"]

    # Calcular vacunados acumulados
    vacunacion_diaria["Vacunados_Acumulados"] = vacunacion_diaria["Vacunados"].cumsum()

    # Calcular cobertura acumulada si hay datos de población
    total_poblacion = filtered_data["metricas"][fuente_poblacion].sum()
    if total_poblacion > 0:
        vacunacion_diaria["Cobertura_Acumulada"] = (
            vacunacion_diaria["Vacunados_Acumulados"] / total_poblacion * 100
        ).round(2)

    # Gráfico de vacunados por día
    st.subheader("Evolución diaria de vacunación")

    fig_diaria = create_bar_chart(
        data=vacunacion_diaria,
        x="Fecha",
        y="Vacunados",
        title="Vacunados por día",
        color=colors["primary"],
        height=400,
        filters=filters,  # Pasar los filtros a la función
    )

    st.plotly_chart(fig_diaria, use_container_width=True)

    # Gráfico de vacunados acumulados
    st.subheader("Evolución acumulada de vacunación")

    fig_acumulada = create_line_chart(
        data=vacunacion_diaria,
        x="Fecha",
        y="Vacunados_Acumulados",
        title="Vacunados acumulados",
        color=colors["secondary"],
        height=400,
        filters=filters,  # Pasar los filtros a la función
    )

    st.plotly_chart(fig_acumulada, use_container_width=True)

    # Gráfico de cobertura acumulada si existe
    if "Cobertura_Acumulada" in vacunacion_diaria.columns:
        st.subheader(f"Evolución de cobertura (Población {fuente_poblacion})")

        fig_cobertura = create_line_chart(
            data=vacunacion_diaria,
            x="Fecha",
            y="Cobertura_Acumulada",
            title=f"Cobertura acumulada (Población {fuente_poblacion})",
            color=colors["accent"],
            height=400,
            filters=filters,  # Pasar los filtros a la función
        )

        st.plotly_chart(fig_cobertura, use_container_width=True)

    # Análisis por meses
    st.subheader("Análisis por meses")

    # Extraer mes y año
    filtered_data["vacunacion"]["Mes_Año"] = filtered_data["vacunacion"][
        "FechaVacunacion"
    ].dt.strftime("%Y-%m")

    # Agrupar por mes
    vacunacion_mensual = (
        filtered_data["vacunacion"].groupby("Mes_Año").size().reset_index()
    )
    vacunacion_mensual.columns = ["Mes_Año", "Vacunados"]

    # Ordenar por fecha
    vacunacion_mensual = vacunacion_mensual.sort_values("Mes_Año")

    # Crear gráfico
    fig_mensual = create_bar_chart(
        data=vacunacion_mensual,
        x="Mes_Año",
        y="Vacunados",
        title="Vacunados por mes",
        color=colors["primary"],
        height=400,
        filters=filters,  # Pasar los filtros a la función
    )

    st.plotly_chart(fig_mensual, use_container_width=True)

    # Proyección simple (si se desea)
    if st.checkbox("Mostrar proyección simple de cobertura"):
        st.subheader("Proyección simple de cobertura")

        # Calcular promedio diario de vacunados en los últimos 30 días
        if len(vacunacion_diaria) > 30:
            ultimos_30_dias = vacunacion_diaria.tail(30)
            promedio_diario = ultimos_30_dias["Vacunados"].mean()
        else:
            promedio_diario = vacunacion_diaria["Vacunados"].mean()

        # Calcular días restantes para alcanzar 95% de cobertura
        if total_poblacion > 0:
            vacunados_actuales = vacunacion_diaria["Vacunados_Acumulados"].iloc[-1]
            objetivo_95 = total_poblacion * 0.95
            vacunados_restantes = objetivo_95 - vacunados_actuales

            if vacunados_restantes > 0 and promedio_diario > 0:
                dias_restantes = vacunados_restantes / promedio_diario

                col1, col2 = st.columns(2)

                with col1:
                    st.metric(
                        label="Promedio diario de vacunación (últimos 30 días)",
                        value=f"{promedio_diario:.1f} personas/día",
                    )

                with col2:
                    fecha_proyectada = datetime.now() + timedelta(days=dias_restantes)
                    st.metric(
                        label="Fecha proyectada para alcanzar 95% de cobertura",
                        value=fecha_proyectada.strftime("%d/%m/%Y"),
                    )

                # Información sobre la proyección
                st.info(
                    """
                **Nota sobre la proyección**: Esta es una proyección lineal simple basada en el promedio
                diario de vacunación. La proyección real puede variar debido a múltiples factores como
                campañas de vacunación, disponibilidad de vacunas, etc.
                """
                )
            else:
                st.success("¡Ya se ha alcanzado el 95% de cobertura!")
