import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from src.visualization.charts import create_bar_chart, create_pie_chart


def normalize_demographic_data(df):
    """
    Normaliza los datos demográficos reemplazando valores NaN con "Sin dato"
    y aplicando normalización de géneros
    """
    df_clean = df.copy()
    
    # Normalizar género
    def normalize_gender(value):
        if pd.isna(value) or str(value).lower().strip() in ['nan', '', 'none', 'null', 'na']:
            return "Sin dato"
        
        value_str = str(value).lower().strip()
        
        if value_str in ['masculino', 'm', 'masc', 'hombre', 'h', 'male', '1']:
            return "Masculino"
        elif value_str in ['femenino', 'f', 'fem', 'mujer', 'female', '2']:
            return "Femenino"
        else:
            # Todas las demás clasificaciones van a "No Binario"
            return "No Binario"
    
    # Aplicar normalización de género si existe la columna
    gender_columns = ['Sexo', 'Genero']
    for col in gender_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].apply(normalize_gender)
    
    # Normalizar otras columnas demográficas
    demographic_columns = ['GrupoEtnico', 'Desplazado', 'Discapacitado', 'Grupo_Edad']
    
    for col in demographic_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna("Sin dato")
            df_clean[col] = df_clean[col].replace(["", "nan", "NaN", "null", "NULL"], "Sin dato")
    
    # Normalizar valores booleanos
    boolean_columns = ['Desplazado', 'Discapacitado']
    for col in boolean_columns:
        if col in df_clean.columns:
            def normalize_boolean(value):
                if pd.isna(value) or str(value).lower().strip() in ['nan', '', 'none', 'null', 'na', 'sin dato']:
                    return "Sin dato"
                
                value_str = str(value).lower().strip()
                if value_str in ['true', '1', 'si', 'sí', 'yes', 'y']:
                    return "Sí"
                elif value_str in ['false', '0', 'no', 'n']:
                    return "No"
                else:
                    return "Sin dato"
            
            df_clean[col] = df_clean[col].apply(normalize_boolean)
    
    return df_clean


def calculate_demographic_stats(data, column, title):
    """
    Calcula estadísticas demográficas para una columna específica
    """
    if column not in data.columns:
        return None
    
    # Contar valores
    counts = data[column].value_counts().reset_index()
    counts.columns = [column, 'Cantidad']
    
    # Calcular porcentajes
    total = counts['Cantidad'].sum()
    counts['Porcentaje'] = (counts['Cantidad'] / total * 100).round(1)
    
    # Calcular diversidad (índice de Shannon)
    proportions = counts['Cantidad'] / total
    shannon_diversity = -sum(p * np.log(p) for p in proportions if p > 0)
    
    return {
        'data': counts,
        'total': total,
        'categories': len(counts),
        'diversity': shannon_diversity,
        'most_common': counts.iloc[0][column] if len(counts) > 0 else "Sin dato",
        'most_common_pct': counts.iloc[0]['Porcentaje'] if len(counts) > 0 else 0
    }


def create_demographic_comparison_chart(data, x_col, y_col, comparison_col, title, colors):
    """
    Crea un gráfico de comparación demográfica avanzado
    """
    # Crear tabla cruzada
    cross_tab = pd.crosstab(data[x_col], data[comparison_col], normalize='index') * 100
    cross_tab = cross_tab.round(1)
    
    # Convertir a formato largo para plotly
    cross_tab_reset = cross_tab.reset_index()
    melted = pd.melt(cross_tab_reset, id_vars=[x_col], 
                     var_name=comparison_col, value_name='Porcentaje')
    
    # Crear gráfico de barras apiladas
    fig = px.bar(
        melted,
        x=x_col,
        y='Porcentaje',
        color=comparison_col,
        title=title,
        labels={'Porcentaje': 'Porcentaje (%)'},
        height=400,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis_tickangle=45,
        barmode='stack',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def show(data, filters, colors, fuente_poblacion="DANE"):
    """
    Muestra la página de perfil demográfico del dashboard.
    VERSIÓN MEJORADA: Enfocada en análisis estadísticos profundos de la población seleccionada,
    con normalización comprehensiva de datos demográficos.

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

    # Normalizar datos demográficos
    filtered_data["vacunacion"] = normalize_demographic_data(filtered_data["vacunacion"])

    # Determinar qué columna de cobertura usar según la fuente
    cobertura_col = f"Cobertura_{fuente_poblacion}"

    # =====================================================================
    # SECCIÓN 1: RESUMEN DEMOGRÁFICO GENERAL
    # =====================================================================
    st.subheader(f"Resumen Demográfico General (Población {fuente_poblacion})")

    # Calcular estadísticas demográficas principales
    total_vacunados = len(filtered_data["vacunacion"])
    
    # Estadísticas por categorías
    edad_stats = calculate_demographic_stats(filtered_data["vacunacion"], "Grupo_Edad", "Edad")
    genero_stats = calculate_demographic_stats(filtered_data["vacunacion"], "Sexo", "Género")
    etnia_stats = calculate_demographic_stats(filtered_data["vacunacion"], "GrupoEtnico", "Etnia")

    # Mostrar métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Vacunados",
            f"{total_vacunados:,}".replace(",", "."),
            delta=f"Población {fuente_poblacion}"
        )
    
    with col2:
        if genero_stats:
            st.metric(
                "Género Predominante",
                genero_stats['most_common'],
                delta=f"{genero_stats['most_common_pct']:.1f}%"
            )
        else:
            st.metric("Género Predominante", "No disponible")
    
    with col3:
        if edad_stats:
            st.metric(
                "Grupo Etario Principal",
                edad_stats['most_common'],
                delta=f"{edad_stats['most_common_pct']:.1f}%"
            )
        else:
            st.metric("Grupo Etario Principal", "No disponible")
    
    with col4:
        if etnia_stats:
            diversidad_etnica = f"{etnia_stats['diversity']:.2f}"
            st.metric(
                "Diversidad Étnica",
                diversidad_etnica,
                delta=f"{etnia_stats['categories']} categorías"
            )
        else:
            st.metric("Diversidad Étnica", "No disponible")

    # =====================================================================
    # SECCIÓN 2: ANÁLISIS DETALLADO POR GRUPOS DE EDAD
    # =====================================================================
    st.subheader("📊 Análisis Detallado por Grupos de Edad")

    col_left, col_right = st.columns(2)

    with col_left:
        # Gráfico de distribución por grupos de edad
        if edad_stats and edad_stats['data'] is not None:
            try:
                # Ordenar grupos de edad de manera lógica
                orden_grupos = ["0-4", "5-14", "15-19", "20-29", "30-39", 
                               "40-49", "50-59", "60-69", "70-79", "80+", "Sin dato"]
                
                edad_data = edad_stats['data'].copy()
                
                # Aplicar orden si es posible
                try:
                    edad_data['Grupo_Edad'] = pd.Categorical(
                        edad_data['Grupo_Edad'],
                        categories=[g for g in orden_grupos if g in edad_data['Grupo_Edad'].values] + 
                                  [g for g in edad_data['Grupo_Edad'].values if g not in orden_grupos],
                        ordered=True
                    )
                    edad_data = edad_data.sort_values('Grupo_Edad')
                except:
                    # Si falla el ordenamiento, usar orden alfabético
                    edad_data = edad_data.sort_values('Grupo_Edad')

                # Crear gráfico
                fig_edad = create_bar_chart(
                    data=edad_data,
                    x="Grupo_Edad",
                    y="Cantidad",
                    title="Distribución por grupos de edad",
                    color=colors["primary"],
                    height=400,
                )

                st.plotly_chart(fig_edad, use_container_width=True)

                # Análisis estadístico de edad
                st.markdown("**Análisis Estadístico:**")
                
                # Identificar grupos más y menos representados
                grupo_mayor = edad_data.iloc[0]['Grupo_Edad']
                cantidad_mayor = edad_data.iloc[0]['Cantidad']
                grupo_menor = edad_data.iloc[-1]['Grupo_Edad']
                cantidad_menor = edad_data.iloc[-1]['Cantidad']
                
                st.info(f"""
                - **Grupo más vacunado:** {grupo_mayor} ({cantidad_mayor:,} personas)
                - **Grupo menos vacunado:** {grupo_menor} ({cantidad_menor:,} personas)
                - **Razón mayor/menor:** {cantidad_mayor/cantidad_menor:.1f}x
                - **Diversidad etaria:** {edad_stats['diversity']:.2f} (Shannon)
                """.replace(",", "."))

            except Exception as e:
                st.error(f"Error al crear gráfico de distribución por grupos de edad: {str(e)}")
        else:
            st.error("No hay datos de grupos de edad disponibles")

    with col_right:
        # Análisis de cobertura por grupo de edad
        if edad_stats and "Grupo_Edad" in filtered_data["vacunacion"].columns:
            try:
                # Calcular cobertura teórica por grupo de edad
                # (esto es una aproximación basada en distribuciones típicas)
                
                # Crear gráfico de pirámide poblacional simplificada
                edad_counts = filtered_data["vacunacion"]["Grupo_Edad"].value_counts()
                
                # Separar por género si está disponible
                if "Sexo" in filtered_data["vacunacion"].columns:
                    pyramid_data = []
                    
                    for grupo in edad_counts.index:
                        if grupo != "Sin dato":
                            grupo_data = filtered_data["vacunacion"][
                                filtered_data["vacunacion"]["Grupo_Edad"] == grupo
                            ]
                            
                            masculino = len(grupo_data[grupo_data["Sexo"] == "Masculino"])
                            femenino = len(grupo_data[grupo_data["Sexo"] == "Femenino"])
                            no_binario = len(grupo_data[grupo_data["Sexo"] == "No Binario"])
                            
                            pyramid_data.extend([
                                {"Grupo_Edad": grupo, "Genero": "Masculino", "Cantidad": masculino},
                                {"Grupo_Edad": grupo, "Genero": "Femenino", "Cantidad": femenino},
                                {"Grupo_Edad": grupo, "Genero": "No Binario", "Cantidad": no_binario}
                            ])
                    
                    pyramid_df = pd.DataFrame(pyramid_data)
                    
                    # Crear gráfico de pirámide horizontal
                    fig_pyramid = px.bar(
                        pyramid_df,
                        x="Cantidad",
                        y="Grupo_Edad",
                        color="Genero",
                        orientation='h',
                        title="Distribución por Edad y Género",
                        height=400,
                        color_discrete_map={
                            "Masculino": colors["primary"],
                            "Femenino": colors["secondary"],
                            "No Binario": colors["accent"]
                        }
                    )
                    
                    fig_pyramid.update_layout(
                        plot_bgcolor="white",
                        paper_bgcolor="white",
                        barmode='group'
                    )
                    
                    st.plotly_chart(fig_pyramid, use_container_width=True)
                else:
                    # Si no hay datos de género, mostrar solo por edad
                    st.info("Datos de género no disponibles para análisis cruzado")

            except Exception as e:
                st.error(f"Error al crear análisis cruzado edad-género: {str(e)}")

    # =====================================================================
    # SECCIÓN 3: ANÁLISIS DE GÉNERO (NORMALIZADO)
    # =====================================================================
    st.subheader("👥 Análisis de Género (Normalizado)")

    col1, col2 = st.columns(2)

    with col1:
        # Gráfico de distribución por género
        if genero_stats and genero_stats['data'] is not None:
            try:
                # Crear gráfico de pastel
                fig_genero = create_pie_chart(
                    data=genero_stats['data'],
                    names="Sexo",
                    values="Cantidad",
                    title="Distribución por género",
                    color_map={},
                    height=400,
                    filters=None,
                )

                st.plotly_chart(fig_genero, use_container_width=True)

                # Estadísticas de género
                masculino_pct = genero_stats['data'][genero_stats['data']['Sexo'] == 'Masculino']['Porcentaje'].sum()
                femenino_pct = genero_stats['data'][genero_stats['data']['Sexo'] == 'Femenino']['Porcentaje'].sum()
                no_binario_pct = genero_stats['data'][genero_stats['data']['Sexo'] == 'No Binario']['Porcentaje'].sum()
                sin_dato_pct = genero_stats['data'][genero_stats['data']['Sexo'] == 'Sin dato']['Porcentaje'].sum()

                st.markdown("**Estadísticas de Género:**")
                st.info(f"""
                - **Masculino:** {masculino_pct:.1f}%
                - **Femenino:** {femenino_pct:.1f}%
                - **No Binario:** {no_binario_pct:.1f}%
                - **Sin dato:** {sin_dato_pct:.1f}%
                """)

            except Exception as e:
                st.error(f"Error al crear gráfico de distribución por género: {str(e)}")

    with col2:
        # Análisis cruzado género-edad
        if ("Sexo" in filtered_data["vacunacion"].columns and 
            "Grupo_Edad" in filtered_data["vacunacion"].columns):
            try:
                fig_genero_edad = create_demographic_comparison_chart(
                    filtered_data["vacunacion"],
                    "Grupo_Edad",
                    "Cantidad",
                    "Sexo",
                    "Distribución de Género por Grupo de Edad",
                    colors
                )
                
                st.plotly_chart(fig_genero_edad, use_container_width=True)
                
            except Exception as e:
                st.error(f"Error al crear análisis cruzado género-edad: {str(e)}")

    # =====================================================================
    # SECCIÓN 4: ANÁLISIS ÉTNICO Y DE VULNERABILIDAD
    # =====================================================================
    st.subheader("🌍 Análisis Étnico y Factores de Vulnerabilidad")

    # Distribución étnica
    col1, col2 = st.columns(2)

    with col1:
        if etnia_stats and etnia_stats['data'] is not None:
            try:
                # Tomar solo los grupos étnicos más representativos para mejor visualización
                etnia_data = etnia_stats['data'].head(8)  # Top 8 grupos étnicos
                
                fig_etnia = create_bar_chart(
                    data=etnia_data,
                    x="GrupoEtnico",
                    y="Cantidad",
                    title="Distribución por grupo étnico",
                    color=colors["accent"],
                    height=400,
                )

                st.plotly_chart(fig_etnia, use_container_width=True)

            except Exception as e:
                st.error(f"Error al crear gráfico de distribución por grupo étnico: {str(e)}")

    # Análisis de vulnerabilidad
    with col2:
        # Crear análisis combinado de desplazamiento y discapacidad
        try:
            vulnerabilidad_data = []
            
            # Calcular estadísticas de desplazamiento
            if "Desplazado" in filtered_data["vacunacion"].columns:
                desplazado_counts = filtered_data["vacunacion"]["Desplazado"].value_counts()
                desplazados_si = desplazado_counts.get("Sí", 0)
                desplazados_no = desplazado_counts.get("No", 0)
                desplazados_sin_dato = desplazado_counts.get("Sin dato", 0)
                
                vulnerabilidad_data.extend([
                    {"Categoria": "Desplazado - Sí", "Cantidad": desplazados_si},
                    {"Categoria": "Desplazado - No", "Cantidad": desplazados_no},
                    {"Categoria": "Desplazado - Sin dato", "Cantidad": desplazados_sin_dato}
                ])
            
            # Calcular estadísticas de discapacidad
            if "Discapacitado" in filtered_data["vacunacion"].columns:
                discapacidad_counts = filtered_data["vacunacion"]["Discapacitado"].value_counts()
                discapacidad_si = discapacidad_counts.get("Sí", 0)
                discapacidad_no = discapacidad_counts.get("No", 0)
                discapacidad_sin_dato = discapacidad_counts.get("Sin dato", 0)
                
                vulnerabilidad_data.extend([
                    {"Categoria": "Discapacidad - Sí", "Cantidad": discapacidad_si},
                    {"Categoria": "Discapacidad - No", "Cantidad": discapacidad_no},
                    {"Categoria": "Discapacidad - Sin dato", "Cantidad": discapacidad_sin_dato}
                ])
            
            if vulnerabilidad_data:
                vuln_df = pd.DataFrame(vulnerabilidad_data)
                
                fig_vulnerabilidad = create_bar_chart(
                    data=vuln_df,
                    x="Categoria",
                    y="Cantidad",
                    title="Factores de Vulnerabilidad",
                    color=colors["warning"],
                    height=400,
                    horizontal=False
                )
                
                st.plotly_chart(fig_vulnerabilidad, use_container_width=True)
                
                # Calcular porcentajes de vulnerabilidad
                total_registros = len(filtered_data["vacunacion"])
                pct_desplazados = (desplazados_si / total_registros * 100) if 'desplazados_si' in locals() else 0
                pct_discapacidad = (discapacidad_si / total_registros * 100) if 'discapacidad_si' in locals() else 0
                
                st.info(f"""
                **Indicadores de Vulnerabilidad:**
                - Población desplazada: {pct_desplazados:.1f}%
                - Población con discapacidad: {pct_discapacidad:.1f}%
                """)

        except Exception as e:
            st.error(f"Error al crear análisis de vulnerabilidad: {str(e)}")

    # =====================================================================
    # SECCIÓN 5: ANÁLISIS CRUZADO AVANZADO
    # =====================================================================
    st.subheader("🔄 Análisis Cruzado Avanzado")

    # Selector para diferentes tipos de análisis cruzado
    analisis_opciones = [
        "Género vs Grupo Étnico",
        "Edad vs Grupo Étnico",
        "Vulnerabilidad vs Edad",
        "Vulnerabilidad vs Género"
    ]
    
    analisis_seleccionado = st.selectbox(
        "Seleccione el tipo de análisis cruzado:",
        analisis_opciones
    )

    try:
        if analisis_seleccionado == "Género vs Grupo Étnico":
            if ("Sexo" in filtered_data["vacunacion"].columns and 
                "GrupoEtnico" in filtered_data["vacunacion"].columns):
                
                fig_cross = create_demographic_comparison_chart(
                    filtered_data["vacunacion"],
                    "GrupoEtnico",
                    "Cantidad",
                    "Sexo",
                    "Distribución de Género por Grupo Étnico",
                    colors
                )
                st.plotly_chart(fig_cross, use_container_width=True)
            else:
                st.warning("Datos insuficientes para este análisis")

        elif analisis_seleccionado == "Edad vs Grupo Étnico":
            if ("Grupo_Edad" in filtered_data["vacunacion"].columns and 
                "GrupoEtnico" in filtered_data["vacunacion"].columns):
                
                fig_cross = create_demographic_comparison_chart(
                    filtered_data["vacunacion"],
                    "Grupo_Edad",
                    "Cantidad",
                    "GrupoEtnico",
                    "Distribución Étnica por Grupo de Edad",
                    colors
                )
                st.plotly_chart(fig_cross, use_container_width=True)
            else:
                st.warning("Datos insuficientes para este análisis")

        elif analisis_seleccionado == "Vulnerabilidad vs Edad":
            if ("Grupo_Edad" in filtered_data["vacunacion"].columns and 
                "Desplazado" in filtered_data["vacunacion"].columns):
                
                fig_cross = create_demographic_comparison_chart(
                    filtered_data["vacunacion"],
                    "Grupo_Edad",
                    "Cantidad",
                    "Desplazado",
                    "Condición de Desplazamiento por Grupo de Edad",
                    colors
                )
                st.plotly_chart(fig_cross, use_container_width=True)
            else:
                st.warning("Datos insuficientes para este análisis")

        elif analisis_seleccionado == "Vulnerabilidad vs Género":
            if ("Sexo" in filtered_data["vacunacion"].columns and 
                "Desplazado" in filtered_data["vacunacion"].columns):
                
                fig_cross = create_demographic_comparison_chart(
                    filtered_data["vacunacion"],
                    "Sexo",
                    "Cantidad",
                    "Desplazado",
                    "Condición de Desplazamiento por Género",
                    colors
                )
                st.plotly_chart(fig_cross, use_container_width=True)
            else:
                st.warning("Datos insuficientes para este análisis")

    except Exception as e:
        st.error(f"Error al crear análisis cruzado: {str(e)}")

    # =====================================================================
    # SECCIÓN 6: TABLA CRUZADA DETALLADA Y INSIGHTS
    # =====================================================================
    st.subheader("📋 Tabla Cruzada Detallada")

    if st.checkbox("Mostrar tabla cruzada por grupo de edad y género"):
        try:
            if ("Grupo_Edad" in filtered_data["vacunacion"].columns and 
                "Sexo" in filtered_data["vacunacion"].columns):
                
                # Crear tabla cruzada
                tabla_cruzada = pd.crosstab(
                    filtered_data["vacunacion"]["Grupo_Edad"],
                    filtered_data["vacunacion"]["Sexo"],
                    margins=True,
                    margins_name="Total",
                )

                # Ordenar por grupos de edad si es posible
                try:
                    orden_grupos = ["0-4", "5-14", "15-19", "20-29", "30-39", 
                                   "40-49", "50-59", "60-69", "70-79", "80+", "Sin dato"]
                    existing_groups = [g for g in orden_grupos if g in tabla_cruzada.index]
                    if existing_groups:
                        tabla_cruzada = tabla_cruzada.reindex(existing_groups + ["Total"])
                except:
                    pass

                st.dataframe(tabla_cruzada, use_container_width=True)

                # Calcular y mostrar insights
                st.markdown("### 📊 Insights Demográficos:")
                
                total_sin_total = tabla_cruzada.drop("Total", axis=0).drop("Total", axis=1)
                
                # Insights automáticos
                insights = []
                
                # Insight sobre diversidad de género
                generos_con_datos = [col for col in total_sin_total.columns if col != "Sin dato"]
                if len(generos_con_datos) >= 2:
                    masculino_total = total_sin_total.get("Masculino", pd.Series()).sum()
                    femenino_total = total_sin_total.get("Femenino", pd.Series()).sum()
                    
                    if masculino_total > femenino_total:
                        diferencia = ((masculino_total - femenino_total) / femenino_total * 100)
                        insights.append(f"👨 **Predominio masculino** del {diferencia:.1f}% en la vacunación")
                    elif femenino_total > masculino_total:
                        diferencia = ((femenino_total - masculino_total) / masculino_total * 100)
                        insights.append(f"👩 **Predominio femenino** del {diferencia:.1f}% en la vacunación")
                    else:
                        insights.append("⚖️ **Distribución balanceada** entre géneros")
                
                # Insight sobre grupo etario más activo
                if len(total_sin_total) > 0:
                    grupo_mas_activo = total_sin_total.sum(axis=1).idxmax()
                    cantidad_mas_activo = total_sin_total.sum(axis=1).max()
                    pct_mas_activo = (cantidad_mas_activo / total_sin_total.sum().sum() * 100)
                    insights.append(f"🎯 **Grupo más activo:** {grupo_mas_activo} ({pct_mas_activo:.1f}% del total)")
                
                # Mostrar insights
                for insight in insights:
                    st.markdown(f"- {insight}")

        except Exception as e:
            st.error(f"Error al crear tabla cruzada: {str(e)}")

    # =====================================================================
    # INSIGHTS FINALES Y RECOMENDACIONES
    # =====================================================================
    st.markdown("---")
    st.subheader("💡 Resumen de Insights Demográficos")

    # Crear resumen automático de insights
    try:
        insights_finales = []
        
        # Insight sobre completitud de datos
        total_registros = len(filtered_data["vacunacion"])
        registros_sin_dato_genero = len(filtered_data["vacunacion"][filtered_data["vacunacion"]["Sexo"] == "Sin dato"])
        registros_sin_dato_edad = len(filtered_data["vacunacion"][filtered_data["vacunacion"]["Grupo_Edad"] == "Sin dato"])
        
        pct_sin_genero = (registros_sin_dato_genero / total_registros * 100)
        pct_sin_edad = (registros_sin_dato_edad / total_registros * 100)
        
        if pct_sin_genero > 10:
            insights_finales.append(f"⚠️ **{pct_sin_genero:.1f}% de registros sin datos de género** - revisar calidad de datos")
        
        if pct_sin_edad > 10:
            insights_finales.append(f"⚠️ **{pct_sin_edad:.1f}% de registros sin datos de edad** - revisar calidad de datos")
        
        # Insight sobre diversidad
        if etnia_stats and etnia_stats['diversity'] > 1.5:
            insights_finales.append(f"🌍 **Alta diversidad étnica** (Shannon: {etnia_stats['diversity']:.2f}) - población heterogénea")
        elif etnia_stats and etnia_stats['diversity'] < 0.5:
            insights_finales.append(f"🏛️ **Baja diversidad étnica** (Shannon: {etnia_stats['diversity']:.2f}) - población homogénea")
        
        # Mostrar insights finales
        if insights_finales:
            for insight in insights_finales:
                st.markdown(f"- {insight}")
        else:
            st.info("📊 Los datos demográficos muestran una distribución balanceada sin patrones de alerta.")

    except Exception as e:
        st.warning(f"No se pudieron calcular todos los insights finales: {str(e)}")