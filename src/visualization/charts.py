import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from scipy import stats


def create_bar_chart(
    data,
    x,
    y,
    title,
    color,
    height=None,
    horizontal=False,
    formatter=None,
    filters=None,
):
    """
    Crea un gráfico de barras estándar usando Plotly.
    """
    # Determinar altura adaptativa basada en la pantalla
    if height is None:
        height = 300 if st.session_state.get("_is_small_screen", False) else 400

    # Usar solo el título original sin añadir los filtros
    full_title = title

    if horizontal:
        fig = px.bar(
            data,
            y=x,
            x=y,
            title=full_title,
            color_discrete_sequence=[color],
            height=height,
            orientation="h",
        )
    else:
        fig = px.bar(
            data,
            x=x,
            y=y,
            title=full_title,
            color_discrete_sequence=[color],
            height=height,
        )
        # Mejorar la rotación de etiquetas para barras verticales
        fig.update_layout(
            xaxis=dict(
                tickangle=-45,
                automargin=True,  # Importante para adaptabilidad
                title=None if st.session_state.get("_is_small_screen", False) else x,
            )
        )

    # Forzar colores en cada barra individualmente
    fig.update_traces(marker_color=color)

    # Personalizar el diseño con ajustes responsivos
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(
            l=10,
            r=10,
            t=40,
            b=10 if st.session_state.get("_is_small_screen", False) else 20,
        ),
        title={"y": 0.98, "x": 0.5, "xanchor": "center", "yanchor": "top"},
        title_font=dict(
            size=14 if st.session_state.get("_is_small_screen", False) else 16
        ),
        autosize=True,  # Importante para responsividad
    )

    # Aplicar formateador si se proporciona
    if formatter:
        position = (
            "inside" if st.session_state.get("_is_small_screen", False) else "outside"
        )
        fig.update_traces(texttemplate=formatter, textposition=position)

    # Para pantallas pequeñas, simplificar etiquetas
    if st.session_state.get("_is_small_screen", False):
        # Reducir el número de barras visibles si hay muchas
        if not horizontal and len(data) > 8:
            # Mostrar solo cada segunda o tercera etiqueta
            step = 2 if len(data) < 15 else 3
            tickvals = list(range(0, len(data), step))
            ticktext = [data[x].iloc[i] if i < len(data) else "" for i in tickvals]
            fig.update_layout(
                xaxis=dict(tickmode="array", tickvals=tickvals, ticktext=ticktext)
            )

        # Simplificar etiquetas en eje Y para mejor visualización
        fig.update_layout(
            yaxis=dict(
                tickformat=".1s", automargin=True  # Formato científico simplificado
            )
        )

        # Reducir el tamaño de las barras para que quepan más
        fig.update_traces(width=0.6)

    return fig


def create_pie_chart(data, names, values, title, color_map, height=400, filters=None):
    """
    Crea un gráfico circular usando Plotly.

    Args:
        data (pd.DataFrame): Datos para el gráfico
        names (str): Columna para las categorías
        values (str): Columna para los valores
        title (str): Título del gráfico
        color_map (dict): Mapa de colores para las categorías
        height (int): Altura del gráfico
        filters (dict): Filtros aplicados para mostrar en el título

    Returns:
        fig: Figura de Plotly
    """
    # Ajustar altura para dispositivos móviles
    if st.session_state.get("_is_small_screen", False):
        height = max(300, height - 50)

    # Añadir información de filtros al título si existe
    full_title = title
    if filters:
        filter_info = []
        for key, value in filters.items():
            if value != "Todos":
                filter_info.append(f"{key}: {value}")

        if filter_info:
            full_title = f"{title} - {' | '.join(filter_info)}"

    # Verificar si hay un mapa de colores para todas las categorías
    categories = data[names].unique()

    # Crear una copia de la paleta de colores institucional
    institutional_colors = [
        "#7D0F2B",  # Vinotinto institucional
        "#F2A900",  # Amarillo dorado
        "#5A4214",  # Marrón dorado oscuro
        "#A83C50",  # Vinotinto claro
        "#FFB82E",  # Amarillo dorado claro
        "#8C5A30",  # Marrón medio
        "#640D22",  # Vinotinto oscuro
        "#D99000",  # Ocre
        "#3F2D0F",  # Marrón oscuro
        "#B5485E",  # Rosa vinotinto
        "#FFCD65",  # Amarillo pálido
        "#BF8040",  # Bronce
    ]

    # Mapas de colores por categoría para mantener consistencia
    category_color_maps = {
        # Genero/Sexo
        "masculino": "#7D0F2B",  # Vinotinto para masculino
        "femenino": "#F2A900",  # Amarillo para femenino
        "no binario": "#5A4214",  # Marrón para no binario
        # Las mismas reglas para mayúsculas
        "MASCULINO": "#7D0F2B",
        "FEMENINO": "#F2A900",
        "NO BINARIO": "#5A4214",
        # Abreviaturas
        "M": "#7D0F2B",
        "F": "#F2A900",
        "NB": "#5A4214",
        # Otros valores comunes
        "si": "#7D0F2B",
        "no": "#F2A900",
        "sí": "#7D0F2B",
        "Sin especificar": "#A83C50",  # Color coherente para valores no especificados
    }

    # Determinar colores para las categorías presentes
    colors = []

    # Primero revisar si es un gráfico de género/sexo
    is_gender_chart = "genero" in title.lower() or "sexo" in title.lower()

    for cat in categories:
        cat_str = str(cat).lower()
        assigned_color = None

        # Buscar en nuestro mapa de categorías
        for key, color in category_color_maps.items():
            if cat_str == key.lower() or key.lower() in cat_str:
                assigned_color = color
                break

        # Si no se encontró un color específico
        if assigned_color is None:
            # Usar un color del mapa suministrado (si existe)
            if color_map and cat in color_map:
                assigned_color = color_map[cat]
            # Si es un gráfico de género, usar colores por defecto bien definidos
            elif is_gender_chart:
                if "masc" in cat_str or cat_str == "m":
                    assigned_color = "#7D0F2B"  # Vinotinto
                elif "fem" in cat_str or cat_str == "f":
                    assigned_color = "#F2A900"  # Amarillo
                elif "bin" in cat_str or "nb" in cat_str:
                    assigned_color = "#5A4214"  # Marrón
                else:
                    # Color por índice para otros casos
                    idx = len(colors) % len(institutional_colors)
                    assigned_color = institutional_colors[idx]
            else:
                # Color por índice para categorías no reconocidas
                idx = len(colors) % len(institutional_colors)
                assigned_color = institutional_colors[idx]

        colors.append(assigned_color)

    # Crear el gráfico
    fig = px.pie(
        data,
        names=names,
        values=values,
        title=full_title,
        color_discrete_sequence=colors,
        height=height,
    )

    # Personalizar el diseño
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=40, b=10),
        title={"y": 0.98, "x": 0.5, "xanchor": "center", "yanchor": "top"},
        title_font=dict(
            size=16 if not st.session_state.get("_is_small_screen", False) else 14
        ),
        autosize=True,  # Importante para responsividad
    )

    # Configuración responsiva para dispositivos móviles
    if st.session_state.get("_is_small_screen", False):
        # Etiquetas más simplificadas para pantallas pequeñas
        fig.update_traces(textposition="inside", textinfo="percent")
        # Leyenda más compacta
        fig.update_layout(
            legend=dict(
                font=dict(size=10), yanchor="top", y=0.99, xanchor="left", x=0.01
            )
        )
    else:
        fig.update_traces(textposition="inside", textinfo="percent+label")

    return fig


def create_scatter_plot(
    data,
    x,
    y,
    title,
    color,
    size=None,
    hover_data=None,
    height=400,
    log_x=False,
    log_y=False,
    filters=None,
):
    """
    Crea un gráfico de dispersión usando Plotly.

    Args:
        data (pd.DataFrame): Datos para el gráfico
        x (str): Columna para el eje X
        y (str): Columna para el eje Y
        title (str): Título del gráfico
        color (str): Color principal de los puntos
        size (str): Columna para determinar el tamaño de los puntos
        hover_data (list): Lista de columnas para mostrar en el hover
        height (int): Altura del gráfico
        log_x (bool): Si es True, utiliza escala logarítmica en X
        log_y (bool): Si es True, utiliza escala logarítmica en Y
        filters (dict): Filtros aplicados para mostrar en el título

    Returns:
        fig: Figura de Plotly
    """
    # Añadir información de filtros al título si existe
    full_title = title
    if filters:
        filter_info = []
        for key, value in filters.items():
            if value != "Todos":
                filter_info.append(f"{key}: {value}")

        if filter_info:
            full_title = f"{title} - {' | '.join(filter_info)}"

    fig = px.scatter(
        data,
        x=x,
        y=y,
        title=full_title,
        color_discrete_sequence=[color],
        size=size,
        hover_data=hover_data,
        height=height,
        log_x=log_x,
        log_y=log_y,
    )

    # Forzar color en los puntos
    fig.update_traces(marker=dict(color=color))

    # Personalizar el diseño
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=40, b=10),
        title={"y": 0.98, "x": 0.5, "xanchor": "center", "yanchor": "top"},
        title_font=dict(size=16),
    )

    # Línea de referencia para comparación
    if x in data.columns and y in data.columns:
        min_val = min(data[x].min(), data[y].min())
        max_val = max(data[x].max(), data[y].max())

        fig.add_trace(
            go.Scatter(
                x=[min_val, max_val],
                y=[min_val, max_val],
                mode="lines",
                line=dict(color="gray", dash="dash", width=1),
                name="Referencia",
                hoverinfo="skip",
            )
        )

    return fig


def create_line_chart(data, x, y, title, color, height=400, filters=None):
    """
    Crea un gráfico de líneas usando Plotly.

    Args:
        data (pd.DataFrame): Datos para el gráfico
        x (str): Columna para el eje X
        y (str): Columna para el eje Y (o lista de columnas)
        title (str): Título del gráfico
        color (str o list): Color principal de la línea o lista de colores
        height (int): Altura del gráfico
        filters (dict): Filtros aplicados para mostrar en el título

    Returns:
        fig: Figura de Plotly
    """
    # Añadir información de filtros al título si existe
    full_title = title
    if filters:
        filter_info = []
        for key, value in filters.items():
            if value != "Todos":
                filter_info.append(f"{key}: {value}")

        if filter_info:
            full_title = f"{title} - {' | '.join(filter_info)}"

    if isinstance(y, list):
        # Múltiples líneas - usar colores institucionales
        fig = go.Figure()

        institutional_colors = [
            "#AB0520",
            "#F2A900",
            "#0C234B",
            "#509E2F",
            "#F7941D",
            "#E51937",
        ]

        colors = color if isinstance(color, list) else institutional_colors

        for i, col in enumerate(y):
            fig.add_trace(
                go.Scatter(
                    x=data[x],
                    y=data[col],
                    mode="lines+markers",
                    name=col,
                    line=dict(color=colors[i % len(colors)], width=3),
                )
            )

        # Añadir título con filtros
        fig.update_layout(title=full_title)
    else:
        # Una sola línea
        fig = px.line(
            data,
            x=x,
            y=y,
            title=full_title,
            color_discrete_sequence=[color],
            height=height,
            markers=True,
        )

        # Forzar el color de la línea
        fig.update_traces(line=dict(color=color, width=3))

    # Personalizar el diseño
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=40, b=10),
        title={"y": 0.98, "x": 0.5, "xanchor": "center", "yanchor": "top"},
        title_font=dict(size=16),
    )

    return fig
