import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from src.visualization.charts import (
    create_bar_chart,
    create_pie_chart,
    create_scatter_plot,
)


# Función auxiliar para formatear números grandes de manera responsiva
def format_responsive_number(number, is_small_screen=False):
    """Formatea números grandes de manera más compacta para pantallas pequeñas"""
    # Manejar valores nulos o no numéricos
    if pd.isna(number):
        return "N/A"
    
    try:
        # Convertir a float para manejar cualquier entrada numérica
        number = float(number)
        
        # Para valores muy grandes, siempre usar notación compacta
        if number >= 1_000_000:
            return f"{number/1_000_000:.1f}M"
        elif number >= 10_000 or is_small_screen:
            # Usar notación K para valores mayores a 10,000 o en pantallas pequeñas
            if number >= 1_000:
                return f"{number/1_000:.1f}K"
        
        # Para valores más pequeños o en pantallas grandes
        if is_small_screen:
            return f"{number:.0f}"
        else:
            # Formato normal con puntos como separador de miles
            return f"{number:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        # Devolver valor original si falla el formateo
        return str(number)


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

    # Resumen de métricas
    st.subheader(
        f"Resumen de Vacunación - Fiebre Amarilla (Población {fuente_poblacion})"
    )

    # Métricas para comparar ambas fuentes
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### Métricas basadas en población {fuente_poblacion}")

        # Calcular métricas para todos los tipos de filtros
        # Para todos los filtros, usar directamente el conteo de registros en los datos filtrados
        if any(filters[k] != "Todos" for k in filters):
            # Si hay algún filtro aplicado
            total_vacunados = len(filtered_data["vacunacion"])

            # Para la población total y pendientes, debemos hacer cálculos específicos
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

        # Calcular cobertura y pendientes
        cobertura = (
            (total_vacunados / total_poblacion * 100) if total_poblacion > 0 else 0
        )
        pendientes = total_poblacion - total_vacunados

        # Detectar tamaño de pantalla para formato responsivo
        is_small_screen = st.session_state.get("_is_small_screen", False)
        screen_width = st.session_state.get("_screen_width", 1200)
        is_very_small_screen = screen_width < 768

        # Crear CSS personalizado para las tarjetas de métricas
        st.markdown("""
        <style>
        .metric-card {
            background-color: white;
            border-radius: 8px;
            padding: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            text-align: center;
            border-left: 4px solid var(--primary-color);
            margin-bottom: 10px;
            height: 100%;
            /* Añadimos estas propiedades para evitar desbordamiento */
            overflow: hidden;
            position: relative;
        }
        .metric-card:hover {
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
            transform: translateY(-2px);
            transition: all 0.3s ease;
        }
        .metric-title {
            font-size: 0.85rem;
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }
        .metric-value {
            font-size: clamp(1rem, 2vw, 1.6rem);
            font-weight: 700;
            color: #7D0F2B;
            /* Estas propiedades aseguran que el texto se ajuste al tamaño de la tarjeta */
            width: 100%;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .metric-poblacion { border-color: #7D0F2B; }
        .metric-vacunados { border-color: #F2A900; }
        .metric-cobertura { border-color: #509E2F; }
        .metric-pendientes { border-color: #F7941D; }

        /* Estilos adicionales para columnas más equilibradas */
        div.row-widget.stHorizontal {
            gap: 10px;
        }
        div.row-widget.stHorizontal > div {
            flex: 1;
            min-width: 0;
        }
        </style>
        """, unsafe_allow_html=True)

        # Diseño adaptable según el tamaño de pantalla
        if is_very_small_screen:
            # Diseño 2x2 para pantallas muy pequeñas
            row1_col1, row1_col2 = st.columns(2)
            row2_col1, row2_col2 = st.columns(2)
            
            with row1_col1:
                # Usar notación compacta para población total en pantallas muy pequeñas
                poblacion_display = format_responsive_number(total_poblacion, True)
                st.markdown(f"""
                <div class="metric-card metric-poblacion">
                    <div class="metric-title">Población Total</div>
                    <div class="metric-value">{poblacion_display}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with row1_col2:
                # Usar notación compacta para vacunados en pantallas muy pequeñas
                vacunados_display = format_responsive_number(total_vacunados, True)
                st.markdown(f"""
                <div class="metric-card metric-vacunados">
                    <div class="metric-title">Vacunados</div>
                    <div class="metric-value">{vacunados_display}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with row2_col1:
                # Formatear antes
                cobertura_formatted = f"{cobertura:.1f}"
                st.markdown(f"""
                <div class="metric-card metric-cobertura">
                    <div class="metric-title">Cobertura</div>
                    <div class="metric-value">{cobertura_formatted}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with row2_col2:
                # Usar notación compacta para pendientes en pantallas muy pequeñas
                pendientes_display = format_responsive_number(pendientes, True)
                st.markdown(f"""
                <div class="metric-card metric-pendientes">
                    <div class="metric-title">Pendientes</div>
                    <div class="metric-value">{pendientes_display}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            # Diseño normal 1x4
            col1_1, col1_2, col1_3, col1_4 = st.columns(4)
            
            with col1_1:
                # Usar notación compacta para población total sin importar el tamaño de pantalla
                poblacion_display = format_responsive_number(total_poblacion, True) if total_poblacion >= 100000 else format_responsive_number(total_poblacion, is_small_screen)
                st.markdown(f"""
                <div class="metric-card metric-poblacion">
                    <div class="metric-title">Población Total</div>
                    <div class="metric-value">{poblacion_display}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col1_2:
                # Usar notación compacta para vacunados si es un número grande
                vacunados_display = format_responsive_number(total_vacunados, True) if total_vacunados >= 100000 else format_responsive_number(total_vacunados, is_small_screen)
                st.markdown(f"""
                <div class="metric-card metric-vacunados">
                    <div class="metric-title">Vacunados</div>
                    <div class="metric-value">{vacunados_display}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col1_3:
                # Formatear antes
                cobertura_formatted = f"{cobertura:.1f}" if is_small_screen else f"{cobertura:.2f}"
                st.markdown(f"""
                <div class="metric-card metric-cobertura">
                    <div class="metric-title">Cobertura</div>
                    <div class="metric-value">{cobertura_formatted}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col1_4:
                # Usar notación compacta para pendientes si es un número grande
                pendientes_display = format_responsive_number(pendientes, True) if pendientes >= 100000 else format_responsive_number(pendientes, is_small_screen)
                st.markdown(f"""
                <div class="metric-card metric-pendientes">
                    <div class="metric-title">Pendientes</div>
                    <div class="metric-value">{pendientes_display}</div>
                </div>
                """, unsafe_allow_html=True)

    with col2:
        # Mostrar comparativa entre DANE y SISBEN
        st.markdown("### Comparativa DANE vs SISBEN")

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

            # Detectar tamaño de pantalla
            is_small_screen = st.session_state.get("_is_small_screen", False)

            # Formatear valores antes de crear el DataFrame (OPCIÓN 3)
            if is_small_screen:
                # Formato para pantallas pequeñas
                dane_formatted = f"{dane_total/1000:.1f}K" if dane_total >= 1000 else f"{dane_total:.0f}"
                sisben_formatted = f"{sisben_total/1000:.1f}K" if sisben_total >= 1000 else f"{sisben_total:.0f}"
                dane_cob = f"{((vacunados_total / dane_total * 100) if dane_total > 0 else 0):.1f}%"
                sisben_cob = f"{((vacunados_total / sisben_total * 100) if sisben_total > 0 else 0):.1f}%"
            else:
                # Formato normal
                dane_formatted = f"{dane_total:,.0f}".replace(",", ".")
                sisben_formatted = f"{sisben_total:,.0f}".replace(",", ".")
                dane_cob = f"{((vacunados_total / dane_total * 100) if dane_total > 0 else 0):.2f}%"
                sisben_cob = f"{((vacunados_total / sisben_total * 100) if sisben_total > 0 else 0):.2f}%"

            # Crear DataFrame con valores ya formateados
            comparativa = {
                "Fuente": ["DANE", "SISBEN"],
                "Población Total": [dane_formatted, sisben_formatted],
                "Cobertura (%)": [dane_cob, sisben_cob],
            }

            comparativa_df = pd.DataFrame(comparativa)

            # Mostrar sin formateo adicional
            st.dataframe(comparativa_df, use_container_width=True)

            # Para el gráfico, necesitamos una versión con valores numéricos
            comparativa_num = {
                "Fuente": ["DANE", "SISBEN"],
                "Población Total": [dane_total, sisben_total],
                "Cobertura (%)": [
                    (vacunados_total / dane_total * 100) if dane_total > 0 else 0,
                    (vacunados_total / sisben_total * 100) if sisben_total > 0 else 0,
                ],
            }
            comparativa_df_num = pd.DataFrame(comparativa_num)

            # Crear gráfico de barras para comparar coberturas
            fig = create_bar_chart(
                data=comparativa_df_num,
                x="Fuente",
                y="Cobertura (%)",
                title="Cobertura según fuente de población",
                color=colors["primary"],
                height=250,
                filters=None,  # No pasar filtros a la gráfica para que no se muestren en el título
            )

            st.plotly_chart(fig, use_container_width=True)

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
                filters=None,  # No pasar filtros
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
                # Asegurarse de que los datos estén en formato string y sin espacios
                filtered_data["vacunacion"]["Grupo_Edad"] = filtered_data["vacunacion"][
                    "Grupo_Edad"
                ].astype(str)
                filtered_data["vacunacion"]["Grupo_Edad"] = filtered_data["vacunacion"][
                    "Grupo_Edad"
                ].str.strip()
                filtered_data["vacunacion"]["Grupo_Edad"] = filtered_data["vacunacion"][
                    "Grupo_Edad"
                ].replace("nan", "Sin especificar")

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
                        "0-4",
                        "5-14",
                        "15-19",
                        "20-29",
                        "30-39",
                        "40-49",
                        "50-59",
                        "60-69",
                        "70-79",
                        "80+",
                    ]
                    # Verificar si tenemos estos grupos en nuestros datos
                    grupos_presentes = set(edad_counts["Grupo_Edad"])
                    grupos_orden = [g for g in orden_grupos if g in grupos_presentes]

                    # Si hay grupos en el orden predefinido, usarlos
                    if grupos_orden:
                        edad_counts["Grupo_Edad"] = pd.Categorical(
                            edad_counts["Grupo_Edad"],
                            categories=grupos_orden
                            + [g for g in grupos_presentes if g not in grupos_orden],
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
                    filters=None,  # No pasar filtros
                )

                st.plotly_chart(fig_edad, use_container_width=True)
            except Exception as e:
                st.error(
                    f"Error al crear gráfico de distribución por grupos de edad: {str(e)}"
                )

    # Añadir gráfico de dispersión para comparar DANE vs SISBEN
    if (
        "DANE" in filtered_data["metricas"].columns
        and "SISBEN" in filtered_data["metricas"].columns
    ):
        st.subheader("Comparativa DANE vs SISBEN por municipio")

        # Crear gráfico de dispersión
        fig_scatter = create_scatter_plot(
            data=filtered_data["metricas"],
            x="DANE",
            y="SISBEN",
            title="Relación entre población DANE y SISBEN por municipio",
            color=colors["accent"],
            hover_data=["DPMP", "Vacunados", "Cobertura_DANE", "Cobertura_SISBEN"],
            height=500,
            filters=None,  # No pasar filtros
        )

        st.plotly_chart(fig_scatter, use_container_width=True)

        st.markdown(
            """
        **Interpretación:** Los puntos por encima de la línea diagonal indican municipios donde la población SISBEN 
        es mayor que la reportada por el DANE. Los puntos por debajo indican lo contrario.
        """
        )

    # División en 3 columnas para gráficos de pastel
    st.subheader("Distribución demográfica de vacunados")
    col1, col2, col3 = st.columns(3)

    # Gráfico de distribución por género (antes sexo)
    with col1:
        # Verificar si existe Genero o usar Sexo como fallback
        if "Genero" in filtered_data["vacunacion"].columns:
            genero_col = "Genero"
        elif "Sexo" in filtered_data["vacunacion"].columns:
            genero_col = "Sexo"
            # Normalizar los valores de sexo a las categorías de género
            filtered_data["vacunacion"]["Genero_Normalizado"] = filtered_data[
                "vacunacion"
            ][genero_col].apply(
                lambda x: (
                    "MASCULINO"
                    if str(x).lower()
                    in ["masculino", "m", "masc", "hombre", "h", "male"]
                    else (
                        "FEMENINO"
                        if str(x).lower() in ["femenino", "f", "fem", "mujer", "female"]
                        else (
                            "NO BINARIO"
                            if str(x).lower()
                            in ["no binario", "nb", "otro", "other", "non-binary"]
                            else "Sin especificar"
                        )
                    )
                )
            )
            genero_col = "Genero_Normalizado"
        else:
            st.error("No se encontró columna de Género o Sexo en los datos.")
            genero_col = None

        if genero_col:
            try:
                # Asegurarse de que no hay valores nulos
                filtered_data["vacunacion"][genero_col] = filtered_data["vacunacion"][
                    genero_col
                ].fillna("Sin especificar")

                # Agrupar por género
                genero_counts = (
                    filtered_data["vacunacion"][genero_col].value_counts().reset_index()
                )
                genero_counts.columns = ["Genero", "Vacunados"]

                # Crear gráfico
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
            # Agrupar por grupo étnico
            etnia_counts = (
                filtered_data["vacunacion"]["GrupoEtnico"].value_counts().reset_index()
            )
            etnia_counts.columns = ["GrupoEtnico", "Vacunados"]

            # Crear gráfico
            fig_etnia = create_pie_chart(
                data=etnia_counts,
                names="GrupoEtnico",
                values="Vacunados",
                title="Distribución por grupo étnico",
                color_map={},  # Colores automáticos
                height=350,
                filters=None,  # No pasar filtros
            )

            st.plotly_chart(fig_etnia, use_container_width=True)
        else:
            st.error("Columna 'GrupoEtnico' no encontrada en los datos.")

    # Gráfico de distribución por régimen
    with col3:
        if "RegimenAfiliacion" in filtered_data["vacunacion"].columns:
            # Agrupar por régimen
            regimen_counts = (
                filtered_data["vacunacion"]["RegimenAfiliacion"]
                .value_counts()
                .reset_index()
            )
            regimen_counts.columns = ["RegimenAfiliacion", "Vacunados"]

            # Crear gráfico
            fig_regimen = create_pie_chart(
                data=regimen_counts,
                names="RegimenAfiliacion",
                values="Vacunados",
                title="Distribución por régimen",
                color_map={},  # Colores automáticos
                height=350,
                filters=None,  # No pasar filtros
            )

            st.plotly_chart(fig_regimen, use_container_width=True)
        else:
            st.error("Columna 'RegimenAfiliacion' no encontrada en los datos.")