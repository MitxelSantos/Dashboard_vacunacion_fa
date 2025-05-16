import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from src.visualization.charts import create_bar_chart, create_pie_chart

def show(data, filters, colors, fuente_poblacion="DANE"):
    """
    Muestra la página de perfil demográfico del dashboard.
    
    Args:
        data (dict): Diccionario con los dataframes
        filters (dict): Filtros seleccionados
        colors (dict): Colores institucionales
        fuente_poblacion (str): Fuente de datos de población ("DANE" o "SISBEN")
    """
    st.title("Perfil Demográfico")
    
    # Aplicar filtros a los datos
    from src.data.preprocessor import apply_filters
    filtered_data = apply_filters(data, filters, fuente_poblacion)
    
    # Determinar qué columna de cobertura usar según la fuente
    cobertura_col = f"Cobertura_{fuente_poblacion}"
    
    # Dividir en dos columnas
    col1, col2 = st.columns(2)
    
    # Gráfico de cobertura por grupos de edad
    with col1:
        # Agrupar por grupo de edad
        edad_counts = filtered_data["vacunacion"]["Grupo_Edad"].value_counts().reset_index()
        edad_counts.columns = ["Grupo_Edad", "Vacunados"]
        
        # Ordenar por grupos de edad (para mantener el orden correcto)
        orden_grupos = ['0-4', '5-14', '15-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+']
        edad_counts['Grupo_Edad'] = pd.Categorical(edad_counts['Grupo_Edad'], categories=orden_grupos, ordered=True)
        edad_counts = edad_counts.sort_values('Grupo_Edad')
        
        # Crear gráfico
        fig_edad = create_bar_chart(
            data=edad_counts,
            x="Grupo_Edad",
            y="Vacunados",
            title="Distribución por grupos de edad",
            color=colors["primary"],
            height=400
        )
        
        st.plotly_chart(fig_edad, use_container_width=True)
    
    # Gráfico de distribución por sexo
    with col2:
        # Agrupar por sexo
        sexo_counts = filtered_data["vacunacion"]["Sexo"].value_counts().reset_index()
        sexo_counts.columns = ["Sexo", "Vacunados"]
        
        # Mapa de colores para sexo
        color_map_sexo = {
            "Masculino": colors["primary"],
            "Femenino": colors["secondary"]
        }
        
        # Crear gráfico
        fig_sexo = create_pie_chart(
            data=sexo_counts,
            names="Sexo",
            values="Vacunados",
            title="Distribución por sexo",
            color_map=color_map_sexo,
            height=400
        )
        
        st.plotly_chart(fig_sexo, use_container_width=True)
    
    # Gráfico de distribución por grupo étnico
    st.subheader("Distribución por grupo étnico")
    
    # Agrupar por grupo étnico
    etnia_counts = filtered_data["vacunacion"]["GrupoEtnico"].value_counts().reset_index()
    etnia_counts.columns = ["GrupoEtnico", "Vacunados"]
    
    # Crear gráfico
    fig_etnia = create_bar_chart(
        data=etnia_counts,
        x="GrupoEtnico",
        y="Vacunados",
        title="Distribución por grupo étnico",
        color=colors["accent"],
        height=400
    )
    
    st.plotly_chart(fig_etnia, use_container_width=True)
    
    # Análisis de factores de vulnerabilidad
    st.subheader("Factores de vulnerabilidad")
    
    col1, col2 = st.columns(2)
    
    # Gráfico de desplazados
    with col1:
        if "Desplazado" in filtered_data["vacunacion"].columns:
            desplazado_counts = filtered_data["vacunacion"]["Desplazado"].value_counts().reset_index()
            desplazado_counts.columns = ["Desplazado", "Vacunados"]
            
            # Crear gráfico
            fig_desplazado = create_pie_chart(
                data=desplazado_counts,
                names="Desplazado",
                values="Vacunados",
                title="Distribución por condición de desplazamiento",
                color_map={},
                height=350
            )
            
            st.plotly_chart(fig_desplazado, use_container_width=True)
        else:
            st.info("No se encontraron datos sobre condición de desplazamiento")
    
    # Gráfico de discapacitados
    with col2:
        if "Discapacitado" in filtered_data["vacunacion"].columns:
            discapacitado_counts = filtered_data["vacunacion"]["Discapacitado"].value_counts().reset_index()
            discapacitado_counts.columns = ["Discapacitado", "Vacunados"]
            
            # Crear gráfico
            fig_discapacitado = create_pie_chart(
                data=discapacitado_counts,
                names="Discapacitado",
                values="Vacunados",
                title="Distribución por condición de discapacidad",
                color_map={},
                height=350
            )
            
            st.plotly_chart(fig_discapacitado, use_container_width=True)
        else:
            st.info("No se encontraron datos sobre condición de discapacidad")
    
    # Tabla de datos demográficos
    st.subheader("Datos demográficos detallados")
    
    # Agrupar por grupo de edad y sexo
    if st.checkbox("Mostrar tabla cruzada por grupo de edad y sexo"):
        tabla_cruzada = pd.crosstab(
            filtered_data["vacunacion"]["Grupo_Edad"], 
            filtered_data["vacunacion"]["Sexo"],
            margins=True,
            margins_name="Total"
        )
        
        # Ordenar por grupos de edad
        if all(grupo in tabla_cruzada.index for grupo in orden_grupos):
            tabla_cruzada = tabla_cruzada.reindex(orden_grupos + ["Total"])
        
        st.dataframe(tabla_cruzada, use_container_width=True)