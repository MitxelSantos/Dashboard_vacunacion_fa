import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from scipy import stats


def create_bar_chart(
    data, x, y, title, color, height=400, horizontal=False, formatter=None, filters=None
):
    """
    Crea un gráfico de barras estándar usando Plotly.
    """
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
            xaxis=dict(tickangle=-45)  # Rotar etiquetas para mejor lectura
        )

    # Forzar colores en cada barra individualmente
    fig.update_traces(marker_color=color)

    # Personalizar el diseño
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=40, b=10),
        title={"y": 0.98, "x": 0.5, "xanchor": "center", "yanchor": "top"},
        title_font=dict(size=16),
    )

    # Aplicar formateador si se proporciona
    if formatter:
        if horizontal:
            fig.update_traces(texttemplate=formatter, textposition="inside")
        else:
            fig.update_traces(texttemplate=formatter, textposition="outside")

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

    # Caso especial para gráficos con solo dos categorías
    if len(categories) == 2:
        # Siempre usar vinotinto y amarillo para las dos primeras categorías
        colors = ["#7D0F2B", "#F2A900"]

        # Forzar diferentes colores para sexo
        if "sexo" in title.lower():
            # Intentar detectar sexo por nombre de categoría
            cat_list = [str(cat).lower() for cat in categories]

            # Si encontramos indicadores de masculino/femenino, asignar colores específicos
            for i, cat in enumerate(cat_list):
                if "masc" in cat or "m" in cat and len(cat) < 3:
                    # Primero encontramos masculino - ordenar correctamente
                    if i == 0:
                        colors = [
                            "#7D0F2B",
                            "#F2A900",
                        ]  # Vinotinto para masculino, amarillo para femenino
                    else:
                        colors = [
                            "#F2A900",
                            "#7D0F2B",
                        ]  # Amarillo para femenino, vinotinto para masculino
                    break
    else:
        # Para más de dos categorías, usar la paleta completa
        colors = []
        for i, cat in enumerate(categories):
            colors.append(institutional_colors[i % len(institutional_colors)])

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
        title_font=dict(size=16),
    )

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
