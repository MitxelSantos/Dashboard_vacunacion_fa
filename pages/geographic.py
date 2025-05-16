import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from src.visualization.charts import create_bar_chart, create_scatter_plot

def show(data, filters, colors, fuente_poblacion="DANE"):
    """
    Muestra la página de distribución geográfica del dashboard.
    
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
    
    # Gráfico de cobertura por municipio
    st.subheader(f"Cobertura por municipio (Población {fuente_poblacion})")
    
    # Ordenar municipios por cobertura
    municipios_ordenados = filtered_data["metricas"].sort_values(by=cobertura_col, ascending=False)
    
    # Crear gráfico
    fig_cobertura = create_bar_chart(
        data=municipios_ordenados,
        x="DPMP",
        y=cobertura_col,
        title=f"Cobertura por municipio (Población {fuente_poblacion})",
        color=colors["primary"],
        height=500,
        formatter="%{y:.1f}%"
    )
    
    st.plotly_chart(fig_cobertura, use_container_width=True)
    
    # Dividir en dos columnas
    col1, col2 = st.columns(2)
    
    # Gráfico de población vs vacunados
    with col1:
        # Crear gráfico de dispersión
        fig_pob_vac = create_scatter_plot(
            data=filtered_data["metricas"],
            x=fuente_poblacion,
            y="Vacunados",
            title=f"Relación entre población {fuente_poblacion} y vacunados",
            color=colors["secondary"],
            hover_data=["DPMP", cobertura_col],
            height=400
        )
        
        st.plotly_chart(fig_pob_vac, use_container_width=True)
    
    # Gráfico de relación DANE vs SISBEN
    with col2:
        # Calcular diferencia porcentual
        filtered_data["metricas"]["Diferencia_Porcentual"] = ((filtered_data["metricas"]["SISBEN"] - filtered_data["metricas"]["DANE"]) / filtered_data["metricas"]["DANE"] * 100).round(2)
        
        # Crear gráfico de barras para la diferencia
        fig_diferencia = create_bar_chart(
            data=filtered_data["metricas"].sort_values(by="Diferencia_Porcentual"),
            x="DPMP",
            y="Diferencia_Porcentual",
            title="Diferencia porcentual entre población SISBEN y DANE",
            color=colors["accent"],
            height=400,
            formatter="%{y:.1f}%"
        )
        
        st.plotly_chart(fig_diferencia, use_container_width=True)
        
        st.markdown("""
        **Interpretación:** Valores positivos indican que la población SISBEN es mayor que la reportada 
        por el DANE. Valores negativos indican lo contrario.
        """)
    
    # Tabla de datos completa
    st.subheader("Datos detallados por municipio")
    
    # Preparar tabla
    tabla_datos = filtered_data["metricas"][["DPMP", "DANE", "SISBEN", "Vacunados", 
                                            "Cobertura_DANE", "Cobertura_SISBEN", 
                                            "Pendientes_DANE", "Pendientes_SISBEN"]].copy()
    
    # Calcular diferencias
    tabla_datos["Diferencia_Poblacion"] = tabla_datos["SISBEN"] - tabla_datos["DANE"]
    tabla_datos["Diferencia_Porcentual"] = ((tabla_datos["SISBEN"] - tabla_datos["DANE"]) / tabla_datos["DANE"] * 100).round(2)
    
    # Mostrar tabla
    st.dataframe(
        tabla_datos.style.format({
            "DANE": "{:,.0f}".replace(",", "."),
            "SISBEN": "{:,.0f}".replace(",", "."),
            "Vacunados": "{:,.0f}".replace(",", "."),
            "Cobertura_DANE": "{:.2f}%",
            "Cobertura_SISBEN": "{:.2f}%",
            "Pendientes_DANE": "{:,.0f}".replace(",", "."),
            "Pendientes_SISBEN": "{:,.0f}".replace(",", "."),
            "Diferencia_Poblacion": "{:+,.0f}".replace(",", "."),
            "Diferencia_Porcentual": "{:+.2f}%"
        }),
        use_container_width=True
    )