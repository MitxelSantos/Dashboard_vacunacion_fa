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

# Reemplaza la función create_pie_chart en charts.py con esta versión:

def create_pie_chart(data, names, values, title, color_map, height=400, filters=None):
    """
    Crea un gráfico circular usando Plotly con mejor manejo de etiquetas.

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

    # Importante: verificar si es un gráfico de género
    is_gender_chart = (
        "genero" in title.lower()
        or "sexo" in title.lower()
        or names.lower() == "genero"
        or "genero" in names.lower()
    )

    # Si es un gráfico de género, forzar colores específicos
    if is_gender_chart:
        # Inicializar el mapa de colores
        gender_colors = {}

        # Asignar colores específicos para cada categoría de género
        for cat in categories:
            cat_str = str(cat).lower()
            if (
                "masc" in cat_str
                or cat_str == "m"
                or cat_str == "masculino"
                or cat_str == "hombre"
            ):
                gender_colors[cat] = "#7D0F2B"  # Vinotinto para masculino
            elif (
                "fem" in cat_str
                or cat_str == "f"
                or cat_str == "femenino"
                or cat_str == "mujer"
            ):
                gender_colors[cat] = "#F2A900"  # Amarillo para femenino
            elif "bin" in cat_str or cat_str == "nb" or "no binario" in cat_str:
                gender_colors[cat] = "#5A4214"  # Marrón para no binario
            else:
                gender_colors[cat] = "#A83C50"  # Vinotinto claro para otros

        # Crear una lista de colores en el mismo orden que las categorías
        colors = [gender_colors[cat] for cat in categories]
    else:
        # Para otros gráficos, usar el enfoque original
        # Caso especial para gráficos con solo dos categorías
        if len(categories) == 2:
            # Siempre usar vinotinto y amarillo para las dos primeras categorías
            colors = ["#7D0F2B", "#F2A900"]
        else:
            # Para más de dos categorías, usar la paleta completa
            colors = []
            for i, cat in enumerate(categories):
                colors.append(institutional_colors[i % len(institutional_colors)])

    # Detectar si hay muchas categorías
    many_categories = len(categories) > 4
    
    # Crear el gráfico
    fig = px.pie(
        data,
        names=names,
        values=values,
        title=full_title,
        color_discrete_sequence=colors,
        height=height,
    )

    # Personalizar el diseño y la forma en que se muestran las etiquetas
    if many_categories:
        # Para gráficos con muchas categorías, solo mostrar porcentajes dentro
        # y mover todo el texto a la leyenda
        fig.update_traces(
            textposition='inside',
            textinfo='percent',  # Solo mostrar porcentajes
            insidetextorientation='radial',  # Orientación radial para mejor ajuste
        )
        
        # Posicionar la leyenda a la izquierda y ajustar su tamaño
        fig.update_layout(
            legend=dict(
                orientation="v",  # Orientación vertical
                yanchor="middle",  # Anclaje al medio
                y=0.5,             # Centrado verticalmente
                xanchor="left",    # Anclaje a la izquierda
                x=-0.1,            # Posición un poco a la izquierda del gráfico
                font=dict(size=9), # Tamaño de fuente reducido
                itemsizing='constant',  # Tamaño constante para los íconos
                itemwidth=30,      # Ancho reducido para los ítems
            )
        )
    else:
        # Para gráficos con pocas categorías, mostrar etiquetas dentro
        fig.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            insidetextfont=dict(size=10),
        )

    # Diseño general para todos los gráficos
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=40, b=20),
        title={"y": 0.98, "x": 0.5, "xanchor": "center", "yanchor": "top"},
        title_font=dict(
            size=16 if not st.session_state.get("_is_small_screen", False) else 14
        ),
        autosize=True,  # Importante para responsividad
    )

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
