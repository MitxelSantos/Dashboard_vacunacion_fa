import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from src.visualization.charts import create_bar_chart, create_pie_chart

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
    
    # Normalizar valores en los datos
    if "NombreAseguradora" in filtered_data["vacunacion"].columns:
        filtered_data["vacunacion"]["NombreAseguradora"] = filtered_data["vacunacion"]["NombreAseguradora"].fillna("Sin especificar")
    
    if "RegimenAfiliacion" in filtered_data["vacunacion"].columns:
        filtered_data["vacunacion"]["RegimenAfiliacion"] = filtered_data["vacunacion"]["RegimenAfiliacion"].fillna("Sin especificar")
    
    if "NombreMunicipioResidencia" in filtered_data["vacunacion"].columns:
        filtered_data["vacunacion"]["NombreMunicipioResidencia"] = filtered_data["vacunacion"]["NombreMunicipioResidencia"].fillna("Sin especificar")
    
    # Dividir en dos columnas
    col1, col2 = st.columns(2)
    
    # Gráfico de distribución por régimen
    with col1:
        if "RegimenAfiliacion" in filtered_data["vacunacion"].columns:
            try:
                # Agrupar por régimen
                regimen_counts = filtered_data["vacunacion"]["RegimenAfiliacion"].value_counts().reset_index()
                regimen_counts.columns = ["RegimenAfiliacion", "Vacunados"]
                
                # Crear gráfico
                fig_regimen = create_bar_chart(
                    data=regimen_counts,
                    x="RegimenAfiliacion",
                    y="Vacunados",
                    title="Distribución por régimen de afiliación",
                    color=colors["primary"],
                    height=400
                )
                
                st.plotly_chart(fig_regimen, use_container_width=True)
            except Exception as e:
                st.error(f"Error al crear gráfico de distribución por régimen: {str(e)}")
        else:
            st.error("Columna 'RegimenAfiliacion' no encontrada en los datos.")
    
    # Gráfico de distribución por aseguradora
    with col2:
        if "NombreAseguradora" in filtered_data["vacunacion"].columns:
            try:
                # Agrupar por aseguradora
                aseguradora_counts = filtered_data["vacunacion"]["NombreAseguradora"].value_counts().reset_index()
                aseguradora_counts.columns = ["NombreAseguradora", "Vacunados"]
                
                # Tomar las 10 principales aseguradoras para mejor visualización
                top_aseguradoras = aseguradora_counts.head(10)
                
                # Crear gráfico
                fig_aseguradora = create_bar_chart(
                    data=top_aseguradoras,
                    x="Vacunados",
                    y="NombreAseguradora",
                    title="Top 10 aseguradoras",
                    color=colors["secondary"],
                    height=400,
                    horizontal=True
                )
                
                st.plotly_chart(fig_aseguradora, use_container_width=True)
            except Exception as e:
                st.error(f"Error al crear gráfico de distribución por aseguradora: {str(e)}")
        else:
            st.error("Columna 'NombreAseguradora' no encontrada en los datos.")
    
    # Análisis cruzado entre régimen y municipio
    st.subheader("Análisis por régimen y municipio")
    
    if ("RegimenAfiliacion" in filtered_data["vacunacion"].columns and 
        "NombreMunicipioResidencia" in filtered_data["vacunacion"].columns):
        try:
            # Normalizar los datos para la tabla cruzada
            datos_tabla = filtered_data["vacunacion"].copy()
            datos_tabla["RegimenAfiliacion"] = datos_tabla["RegimenAfiliacion"].fillna("Sin especificar")
            datos_tabla["NombreMunicipioResidencia"] = datos_tabla["NombreMunicipioResidencia"].fillna("Sin especificar")
            
            # Crear tabla cruzada
            regimen_municipio = pd.crosstab(
                datos_tabla["NombreMunicipioResidencia"],
                datos_tabla["RegimenAfiliacion"],
                margins=True,
                margins_name="Total"
            )
            
            # Mostrar tabla
            st.dataframe(regimen_municipio, use_container_width=True)
            
            # Opción para mostrar gráfico de los 5 municipios principales
            if st.checkbox("Mostrar gráfico de los 5 municipios principales por régimen"):
                # Obtener los 5 municipios con más vacunados
                top_municipios = regimen_municipio.sort_values(by="Total", ascending=False).head(6).index[:-1]  # Excluir Total
                
                # Filtrar datos para esos municipios
                top_data = datos_tabla[datos_tabla["NombreMunicipioResidencia"].isin(top_municipios)]
                
                # Contar por municipio y régimen
                top_counts = top_data.groupby(["NombreMunicipioResidencia", "RegimenAfiliacion"]).size().reset_index()
                top_counts.columns = ["Municipio", "Regimen", "Vacunados"]
                
                # Crear gráfico
                fig = px.bar(
                    top_counts,
                    x="Municipio",
                    y="Vacunados",
                    color="Regimen",
                    title="Distribución por régimen en los 5 municipios principales",
                    height=500,
                    barmode="group"
                )
                
                # Personalizar el diseño
                fig.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    margin=dict(l=10, r=10, t=40, b=10),
                    title={
                        'y':0.98,
                        'x':0.5,
                        'xanchor': 'center',
                        'yanchor': 'top'
                    },
                    title_font=dict(size=16),
                    legend_title="Régimen"
                )
                
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error al crear análisis cruzado régimen-municipio: {str(e)}")
    else:
        st.info("No hay suficientes datos para mostrar el análisis cruzado")
    
    # Análisis por aseguradora
    st.subheader("Análisis detallado por aseguradora")
    
    # Seleccionar aseguradora para análisis detallado
    if "NombreAseguradora" in filtered_data["vacunacion"].columns:
        try:
            # Obtener lista de aseguradoras
            aseguradoras_lista = list(filtered_data["vacunacion"]["NombreAseguradora"].dropna().unique())
            aseguradoras = ["Todas"] + sorted(aseguradoras_lista)
            
            aseguradora_seleccionada = st.selectbox(
                "Seleccione una aseguradora para análisis detallado:", 
                options=aseguradoras
            )
            
            if aseguradora_seleccionada != "Todas":
                # Filtrar datos para la aseguradora seleccionada
                datos_aseguradora = filtered_data["vacunacion"][filtered_data["vacunacion"]["NombreAseguradora"] == aseguradora_seleccionada]
                
                # Mostrar información
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    total_vacunados = len(datos_aseguradora)
                    porcentaje = (total_vacunados / len(filtered_data["vacunacion"]) * 100) if len(filtered_data["vacunacion"]) > 0 else 0
                    st.metric("Total vacunados", f"{total_vacunados:,}".replace(",", "."), f"{porcentaje:.2f}% del total")
                
                with col2:
                    # Distribución por sexo
                    if "Sexo" in datos_aseguradora.columns:
                        dist_sexo = datos_aseguradora["Sexo"].fillna("Sin especificar").value_counts().to_dict()
                        texto_sexo = ", ".join([f"{k}: {v:,}".replace(",", ".") for k, v in dist_sexo.items()])
                        st.metric("Distribución por sexo", texto_sexo)
                    else:
                        st.metric("Distribución por sexo", "No disponible")
                
                with col3:
                    # Distribución por régimen
                    if "RegimenAfiliacion" in datos_aseguradora.columns:
                        dist_regimen = datos_aseguradora["RegimenAfiliacion"].fillna("Sin especificar").value_counts().to_dict()
                        texto_regimen = ", ".join([f"{k}: {v:,}".replace(",", ".") for k, v in dist_regimen.items()])
                        st.metric("Distribución por régimen", texto_regimen)
                    else:
                        st.metric("Distribución por régimen", "No disponible")
                
                # Gráfico de distribución por municipio
                if "NombreMunicipioResidencia" in datos_aseguradora.columns:
                    municipio_counts = datos_aseguradora["NombreMunicipioResidencia"].fillna("Sin especificar").value_counts().reset_index()
                    municipio_counts.columns = ["Municipio", "Vacunados"]
                    
                    # Tomar los 10 principales municipios
                    top_municipios = municipio_counts.head(10)
                    
                    # Crear gráfico
                    fig = create_bar_chart(
                        data=top_municipios,
                        x="Vacunados",
                        y="Municipio",
                        title=f"Top 10 municipios con vacunados de {aseguradora_seleccionada}",
                        color=colors["accent"],
                        height=400,
                        horizontal=True
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error en el análisis detallado por aseguradora: {str(e)}")