import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from src.visualization.charts import (
    create_bar_chart,
    create_pie_chart,
    create_scatter_plot,
)


# Función auxiliar para formatear números grandes de manera responsiva
def format_responsive_number(number, is_small_screen=False):
    """Formatea números con puntos como separador de miles - sin abreviaciones"""
    # Manejar valores nulos o no numéricos
    if pd.isna(number):
        return "N/A"
    
    try:
        # Convertir a float para manejar cualquier entrada numérica
        number = float(number)
        
        # Formato normal con puntos como separador de miles - SIN ABREVIACIONES
        return f"{number:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        # Devolver valor original si falla el formateo
        return str(number)


def normalize_gender(value):
    """Normaliza los valores de género a las tres categorías estándar"""
    if pd.isna(value) or str(value).lower() in ['nan', '', 'none', 'null']:
        return "Sin dato"
    
    value_str = str(value).lower().strip()
    
    if value_str in ['masculino', 'm', 'masc', 'hombre', 'h', 'male', '1']:
        return "Masculino"
    elif value_str in ['femenino', 'f', 'fem', 'mujer', 'female', '2']:
        return "Femenino"
    else:
        # Todas las demás clasificaciones van a "No Binario"
        return "No Binario"


def create_improved_bar_chart_with_hover(data, x_col, y_col, title, color, height=400):
    """
    Crea un gráfico de barras mejorado que siempre muestra porcentajes 
    y cantidad en hover
    """
    fig = go.Figure()
    
    # Calcular porcentajes
    total = data[y_col].sum()
    percentages = (data[y_col] / total * 100).round(1)
    
    fig.add_trace(go.Bar(
        x=data[x_col],
        y=percentages,
        text=[f"{p}%" for p in percentages],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>' +
                      'Porcentaje: %{y}%<br>' +
                      'Cantidad: %{customdata:,}<br>' +
                      '<extra></extra>',
        customdata=data[y_col],
        marker_color=color,
        name=''
    ))
    
    fig.update_layout(
        title=title,
        title_x=0.5,
        xaxis_title="",
        yaxis_title="Porcentaje (%)",
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        showlegend=False
    )
    
    return fig


def show(data, filters, colors, fuente_poblacion="DANE"):
    """
    Muestra la página de visión general del dashboard.

    Args:
        data (dict): Diccionario con los dataframes
        filters (dict): Filtros seleccionados
        colors (dict): Colores institucionales
        fuente_poblacion (str): Fuente de datos de población ("DANE" o "SISBEN")
    """
    st.title("Visión General")

    # Aplicar filtros a los datos
    from src.data.preprocessor import apply_filters

    filtered_data = apply_filters(data, filters, fuente_poblacion)

    # Verificar que las columnas existan en los dataframes
    if fuente_poblacion not in filtered_data["metricas"].columns:
        st.error(
            f"Columna '{fuente_poblacion}' no encontrada en los datos. Usando 'DANE' como alternativa."
        )
        fuente_poblacion = "DANE"

    if "Vacunados" not in filtered_data["metricas"].columns:
        st.error("Columna 'Vacunados' no encontrada en los datos.")
        # Crear columna de vacunados
        filtered_data["metricas"]["Vacunados"] = 0

    # =====================================================================
    # SECCIÓN 1: MÉTRICAS PRINCIPALES (OCUPAN TODO EL ANCHO HORIZONTAL)
    # =====================================================================
    st.subheader(f"Resumen de Vacunación - Fiebre Amarilla (Población {fuente_poblacion})")

    # Calcular métricas
    if any(filters[k] != "Todos" for k in filters):
        # Si hay algún filtro aplicado
        total_vacunados = len(filtered_data["vacunacion"])

        # Para la población total y susceptibles, debemos hacer cálculos específicos
        if filters["municipio"] != "Todos":
            # Si hay filtro de municipio, buscar la población de ese municipio
            municipio_data = filtered_data["metricas"][
                filtered_data["metricas"]["DPMP"].str.lower()
                == filters["municipio"].lower()
            ]

            # Caso especial para Mariquita y Armero
            if filters["municipio"] == "Mariquita" and len(municipio_data) == 0:
                municipio_data = filtered_data["metricas"][
                    filtered_data["metricas"]["DPMP"].str.lower()
                    == "san sebastian de mariquita"
                ]
            elif filters["municipio"] == "Armero" and len(municipio_data) == 0:
                municipio_data = filtered_data["metricas"][
                    filtered_data["metricas"]["DPMP"].str.lower()
                    == "armero guayabal"
                ]

            if len(municipio_data) > 0:
                total_poblacion = municipio_data[fuente_poblacion].sum()
            else:
                total_poblacion = filtered_data["metricas"][fuente_poblacion].sum()
        else:
            # Para otros filtros, usar la población total
            total_poblacion = filtered_data["metricas"][fuente_poblacion].sum()
    else:
        # Sin filtros, usar las métricas calculadas
        total_poblacion = filtered_data["metricas"][fuente_poblacion].sum()
        total_vacunados = filtered_data["metricas"]["Vacunados"].sum()

    # Calcular cobertura y susceptibles
    cobertura = (total_vacunados / total_poblacion * 100) if total_poblacion > 0 else 0
    susceptibles = total_poblacion - total_vacunados

    # Detectar tamaño de pantalla para formato responsivo
    is_small_screen = st.session_state.get("_is_small_screen", False)
    screen_width = st.session_state.get("_screen_width", 1200)
    is_very_small_screen = screen_width < 768

    # CSS mejorado para las métricas que ocupan todo el ancho horizontal
    st.markdown("""
    <style>
    .metrics-container {
        display: flex;
        justify-content: space-between;
        gap: 15px;
        margin-bottom: 30px;
        flex-wrap: wrap;
    }
    .metric-card-full {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        text-align: center;
        border-left: 5px solid var(--primary-color);
        flex: 1;
        min-width: 200px;
        transition: all 0.3s ease;
    }
    .metric-card-full:hover {
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
        transform: translateY(-3px);
    }
    .metric-title-full {
        font-size: 1rem;
        font-weight: 600;
        color: #333;
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value-full {
        font-size: 2.2rem;
        font-weight: 700;
        color: #7D0F2B;
        margin-bottom: 5px;
        line-height: 1.1;
    }
    .metric-poblacion { border-color: #7D0F2B; }
    .metric-vacunados { border-color: #F2A900; }
    .metric-cobertura { border-color: #509E2F; }
    .metric-susceptibles { border-color: #F7941D; }
    
    /* Responsivo para pantallas pequeñas */
    @media (max-width: 768px) {
        .metrics-container {
            flex-direction: column;
        }
        .metric-card-full {
            min-width: auto;
        }
        .metric-value-full {
            font-size: 1.8rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    # Crear métricas que ocupan todo el ancho horizontal
    poblacion_display = format_responsive_number(total_poblacion)
    vacunados_display = format_responsive_number(total_vacunados)
    cobertura_formatted = f"{cobertura:.1f}"
    susceptibles_display = format_responsive_number(susceptibles)

    st.markdown(f"""
    <div class="metrics-container">
        <div class="metric-card-full metric-poblacion">
            <div class="metric-title-full">Población Total</div>
            <div class="metric-value-full">{poblacion_display}</div>
        </div>
        <div class="metric-card-full metric-vacunados">
            <div class="metric-title-full">Vacunados</div>
            <div class="metric-value-full">{vacunados_display}</div>
        </div>
        <div class="metric-card-full metric-cobertura">
            <div class="metric-title-full">Cobertura</div>
            <div class="metric-value-full">{cobertura_formatted}%</div>
        </div>
        <div class="metric-card-full metric-susceptibles">
            <div class="metric-title-full">Susceptibles</div>
            <div class="metric-value-full">{susceptibles_display}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # =====================================================================
    # SECCIÓN 2: COMPARATIVA DANE vs SISBEN (SOLO GRÁFICO DE BARRAS)
    # =====================================================================
    st.subheader("Comparativa de Cobertura DANE vs SISBEN")

    # Verificar que ambas columnas existan
    if (
        "DANE" not in filtered_data["metricas"].columns
        or "SISBEN" not in filtered_data["metricas"].columns
    ):
        st.error("Faltan columnas necesarias para la comparativa DANE vs SISBEN")
    else:
        # Preparar datos para la comparativa, considerando los filtros
        if any(filters[k] != "Todos" for k in filters):
            if filters["municipio"] != "Todos":
                # Si hay filtro de municipio, buscar los datos específicos
                municipio_data = filtered_data["metricas"][
                    filtered_data["metricas"]["DPMP"].str.lower()
                    == filters["municipio"].lower()
                ]

                # Caso especial para Mariquita y Armero
                if filters["municipio"] == "Mariquita" and len(municipio_data) == 0:
                    municipio_data = filtered_data["metricas"][
                        filtered_data["metricas"]["DPMP"].str.lower()
                        == "san sebastian de mariquita"
                    ]
                elif filters["municipio"] == "Armero" and len(municipio_data) == 0:
                    municipio_data = filtered_data["metricas"][
                        filtered_data["metricas"]["DPMP"].str.lower()
                        == "armero guayabal"
                    ]

                if len(municipio_data) > 0:
                    dane_total = municipio_data["DANE"].sum()
                    sisben_total = municipio_data["SISBEN"].sum()
                else:
                    dane_total = filtered_data["metricas"]["DANE"].sum()
                    sisben_total = filtered_data["metricas"]["SISBEN"].sum()
            else:
                # Para otros filtros, usar todas las poblaciones
                dane_total = filtered_data["metricas"]["DANE"].sum()
                sisben_total = filtered_data["metricas"]["SISBEN"].sum()

            # Usar el conteo de registros para todos los filtros
            vacunados_total = len(filtered_data["vacunacion"])
        else:
            # Sin filtros, usar los totales
            dane_total = filtered_data["metricas"]["DANE"].sum()
            sisben_total = filtered_data["metricas"]["SISBEN"].sum()
            vacunados_total = filtered_data["metricas"]["Vacunados"].sum()

        # Crear DataFrame para el gráfico mejorado
        comparativa_data = pd.DataFrame({
            "Fuente": ["DANE", "SISBEN"],
            "Poblacion": [dane_total, sisben_total],
            "Cobertura": [
                (vacunados_total / dane_total * 100) if dane_total > 0 else 0,
                (vacunados_total / sisben_total * 100) if sisben_total > 0 else 0,
            ],
        })

        # Crear gráfico mejorado que muestra porcentaje y hover con cantidad
        fig_comparativa = create_improved_bar_chart_with_hover(
            data=comparativa_data,
            x_col="Fuente",
            y_col="Poblacion",
            title="Cobertura según fuente de población",
            color=colors["primary"],
            height=350
        )

        st.plotly_chart(fig_comparativa, use_container_width=True)

    # =====================================================================
    # SECCIÓN 3: GRÁFICOS PRINCIPALES
    # =====================================================================
    # Dividir en dos columnas para los gráficos principales
    col_left, col_right = st.columns(2)

    # Gráfico de cobertura por municipio (Top 10)
    with col_left:
        # Determinar qué columna de cobertura usar según la fuente
        cobertura_col = f"Cobertura_{fuente_poblacion}"

        # Verificar que la columna exista
        if cobertura_col not in filtered_data["metricas"].columns:
            st.error(
                f"Columna '{cobertura_col}' no encontrada en los datos. No se puede mostrar gráfico de cobertura por municipio."
            )
        else:
            # Ordenar municipios por cobertura
            top_municipios = (
                filtered_data["metricas"]
                .sort_values(by=cobertura_col, ascending=False)
                .head(10)
            )

            # Crear gráfico
            fig_mun = create_bar_chart(
                data=top_municipios,
                x="DPMP",
                y=cobertura_col,
                title=f"Cobertura por municipio (Top 10) - {fuente_poblacion}",
                color=colors["primary"],
                height=400,
                formatter="%{y:.1f}%",
                filters=None,
            )

            st.plotly_chart(fig_mun, use_container_width=True)

    # Gráfico de distribución por grupos de edad
    with col_right:
        # Verificar que Grupo_Edad exista
        if "Grupo_Edad" not in filtered_data["vacunacion"].columns:
            st.error(
                "Columna 'Grupo_Edad' no encontrada en los datos. No se puede mostrar distribución por grupo de edad."
            )
        else:
            try:
                # Normalizar datos de edad y reemplazar NaN con "Sin dato"
                filtered_data["vacunacion"]["Grupo_Edad"] = filtered_data["vacunacion"][
                    "Grupo_Edad"
                ].astype(str)
                filtered_data["vacunacion"]["Grupo_Edad"] = filtered_data["vacunacion"][
                    "Grupo_Edad"
                ].str.strip()
                filtered_data["vacunacion"]["Grupo_Edad"] = filtered_data["vacunacion"][
                    "Grupo_Edad"
                ].replace(["nan", "NaN", ""], "Sin dato")

                # Agrupar por grupo de edad
                edad_counts = (
                    filtered_data["vacunacion"]["Grupo_Edad"]
                    .value_counts()
                    .reset_index()
                )
                edad_counts.columns = ["Grupo_Edad", "Vacunados"]

                # Ordenar por grupos de edad
                try:
                    orden_grupos = [
                        "0-4", "5-14", "15-19", "20-29", "30-39", 
                        "40-49", "50-59", "60-69", "70-79", "80+", "Sin dato"
                    ]
                    # Verificar si tenemos estos grupos en nuestros datos
                    grupos_presentes = set(edad_counts["Grupo_Edad"])
                    grupos_orden = [g for g in orden_grupos if g in grupos_presentes]

                    # Añadir grupos no contemplados al final
                    grupos_orden.extend([g for g in grupos_presentes if g not in grupos_orden])

                    # Si hay grupos en el orden predefinido, usarlos
                    if grupos_orden:
                        edad_counts["Grupo_Edad"] = pd.Categorical(
                            edad_counts["Grupo_Edad"],
                            categories=grupos_orden,
                            ordered=True,
                        )
                        edad_counts = edad_counts.sort_values("Grupo_Edad")
                except:
                    # Si falla la categorización, usar orden alfabético
                    edad_counts = edad_counts.sort_values("Grupo_Edad")

                # Crear gráfico
                fig_edad = create_bar_chart(
                    data=edad_counts,
                    x="Grupo_Edad",
                    y="Vacunados",
                    title="Distribución por grupos de edad",
                    color=colors["secondary"],
                    height=400,
                    filters=None,
                )

                st.plotly_chart(fig_edad, use_container_width=True)
            except Exception as e:
                st.error(
                    f"Error al crear gráfico de distribución por grupos de edad: {str(e)}"
                )

    # =====================================================================
    # SECCIÓN 4: ANÁLISIS DE CORRELACIÓN (DANE vs SISBEN)
    # =====================================================================
    if (
        "DANE" in filtered_data["metricas"].columns
        and "SISBEN" in filtered_data["metricas"].columns
    ):
        st.subheader("Análisis de Correlación DANE vs SISBEN por municipio")

        # Crear gráfico de dispersión
        fig_scatter = create_scatter_plot(
            data=filtered_data["metricas"],
            x="DANE",
            y="SISBEN",
            title="Relación entre población DANE y SISBEN por municipio",
            color=colors["accent"],
            hover_data=["DPMP", "Vacunados", "Cobertura_DANE", "Cobertura_SISBEN"],
            height=500,
            filters=None,
        )

        st.plotly_chart(fig_scatter, use_container_width=True)

        st.markdown(
            """
        **Interpretación:** Los puntos por encima de la línea diagonal indican municipios donde la población SISBEN 
        es mayor que la reportada por el DANE. Los puntos por debajo indican lo contrario.
        """
        )

    # =====================================================================
    # SECCIÓN 5: DISTRIBUCIÓN DEMOGRÁFICA (GRÁFICOS DE PASTEL MEJORADOS)
    # =====================================================================
    st.subheader("Distribución demográfica de vacunados")
    col1, col2, col3 = st.columns(3)

    # Gráfico de distribución por género (normalizado)
    with col1:
        # Verificar si existe Genero o usar Sexo como fallback
        if "Genero" in filtered_data["vacunacion"].columns:
            genero_col = "Genero"
        elif "Sexo" in filtered_data["vacunacion"].columns:
            genero_col = "Sexo"
        else:
            st.error("No se encontró columna de Género o Sexo en los datos.")
            genero_col = None

        if genero_col:
            try:
                # Normalizar géneros usando la nueva función
                filtered_data["vacunacion"]["Genero_Normalizado"] = filtered_data["vacunacion"][genero_col].apply(normalize_gender)

                # Agrupar por género normalizado
                genero_counts = (
                    filtered_data["vacunacion"]["Genero_Normalizado"]
                    .value_counts()
                    .reset_index()
                )
                genero_counts.columns = ["Genero", "Vacunados"]

                # Crear gráfico de pastel
                fig_genero = create_pie_chart(
                    data=genero_counts,
                    names="Genero",
                    values="Vacunados",
                    title="Distribución por género",
                    color_map={},
                    height=350,
                    filters=None,
                )

                st.plotly_chart(fig_genero, use_container_width=True)
            except Exception as e:
                st.error(f"Error al crear gráfico de distribución por género: {str(e)}")

    # Gráfico de distribución por etnia
    with col2:
        if "GrupoEtnico" in filtered_data["vacunacion"].columns:
            # Normalizar valores NaN a "Sin dato"
            filtered_data["vacunacion"]["GrupoEtnico_clean"] = filtered_data["vacunacion"]["GrupoEtnico"].fillna("Sin dato")
            filtered_data["vacunacion"]["GrupoEtnico_clean"] = filtered_data["vacunacion"]["GrupoEtnico_clean"].replace(["", "nan", "NaN"], "Sin dato")
            
            # Agrupar por grupo étnico
            etnia_counts = (
                filtered_data["vacunacion"]["GrupoEtnico_clean"]
                .value_counts()
                .reset_index()
            )
            etnia_counts.columns = ["GrupoEtnico", "Vacunados"]

            fig_etnia = create_pie_chart(
                data=etnia_counts,
                names="GrupoEtnico",
                values="Vacunados",
                title="Distribución por grupo étnico",
                color_map={},
                height=350,
                filters=None,
            )

            st.plotly_chart(fig_etnia, use_container_width=True)
        else:
            st.error("Columna 'GrupoEtnico' no encontrada en los datos.")

    # Gráfico de distribución por régimen
    with col3:
        if "RegimenAfiliacion" in filtered_data["vacunacion"].columns:
            # Normalizar valores NaN a "Sin dato"
            filtered_data["vacunacion"]["RegimenAfiliacion_clean"] = filtered_data["vacunacion"]["RegimenAfiliacion"].fillna("Sin dato")
            filtered_data["vacunacion"]["RegimenAfiliacion_clean"] = filtered_data["vacunacion"]["RegimenAfiliacion_clean"].replace(["", "nan", "NaN"], "Sin dato")
            
            # Agrupar por régimen
            regimen_counts = (
                filtered_data["vacunacion"]["RegimenAfiliacion_clean"]
                .value_counts()
                .reset_index()
            )
            regimen_counts.columns = ["RegimenAfiliacion", "Vacunados"]

            fig_regimen = create_pie_chart(
                data=regimen_counts,
                names="RegimenAfiliacion",
                values="Vacunados",
                title="Distribución por régimen",
                color_map={},
                height=350,
                filters=None,
            )

            st.plotly_chart(fig_regimen, use_container_width=True)
        else:
            st.error("Columna 'RegimenAfiliacion' no encontrada en los datos.")