import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from scipy import stats

def create_bar_chart(data, x, y, title, color, height=400, horizontal=False, formatter=None):
    """
    Crea un gráfico de barras estándar usando Plotly.
    
    Args:
        data (pd.DataFrame): Datos para el gráfico
        x (str): Columna para el eje X
        y (str): Columna para el eje Y
        title (str): Título del gráfico
        color (str): Color principal de las barras
        height (int): Altura del gráfico
        horizontal (bool): Si es True, crea un gráfico horizontal
        formatter (func): Función para formatear los valores (ej: formato de porcentaje)
        
    Returns:
        fig: Figura de Plotly
    """
    if horizontal:
        fig = px.bar(
            data, 
            y=x, 
            x=y,
            title=title,
            color_discrete_sequence=[color],
            height=height,
            orientation='h'
        )
    else:
        fig = px.bar(
            data, 
            x=x, 
            y=y,
            title=title,
            color_discrete_sequence=[color],
            height=height
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
        title_font=dict(size=16)
    )
    
    # Aplicar formateador si se proporciona
    if formatter:
        if horizontal:
            fig.update_traces(texttemplate=formatter, textposition='inside')
        else:
            fig.update_traces(texttemplate=formatter, textposition='outside')
    
    return fig

def create_pie_chart(data, names, values, title, color_map, height=400):
    """
    Crea un gráfico circular usando Plotly.
    
    Args:
        data (pd.DataFrame): Datos para el gráfico
        names (str): Columna para las categorías
        values (str): Columna para los valores
        title (str): Título del gráfico
        color_map (dict): Mapa de colores para las categorías
        height (int): Altura del gráfico
        
    Returns:
        fig: Figura de Plotly
    """
    # Verificar si hay un mapa de colores para todas las categorías
    categories = data[names].unique()
    colors = [color_map.get(cat, '#CCCCCC') for cat in categories]
    
    fig = px.pie(
        data, 
        names=names, 
        values=values,
        title=title,
        color=names,
        color_discrete_sequence=colors,
        height=height
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
        title_font=dict(size=16)
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    return fig

def create_scatter_plot(data, x, y, title, color, size=None, hover_data=None, height=400, log_x=False, log_y=False):
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
        
    Returns:
        fig: Figura de Plotly
    """
    fig = px.scatter(
        data,
        x=x,
        y=y,
        title=title,
        color_discrete_sequence=[color],
        size=size,
        hover_data=hover_data,
        height=height,
        log_x=log_x,
        log_y=log_y
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
        title_font=dict(size=16)
    )
    
    # Línea de referencia para comparación
    if x in data.columns and y in data.columns:
        min_val = min(data[x].min(), data[y].min())
        max_val = max(data[x].max(), data[y].max())
        
        fig.add_trace(
            go.Scatter(
                x=[min_val, max_val],
                y=[min_val, max_val],
                mode='lines',
                line=dict(color='gray', dash='dash', width=1),
                name='Referencia',
                hoverinfo='skip'
            )
        )
    
    return fig

def create_line_chart(data, x, y, title, color, height=400):
    """
    Crea un gráfico de líneas usando Plotly.
    
    Args:
        data (pd.DataFrame): Datos para el gráfico
        x (str): Columna para el eje X
        y (str): Columna para el eje Y (o lista de columnas)
        title (str): Título del gráfico
        color (str o list): Color principal de la línea o lista de colores
        height (int): Altura del gráfico
        
    Returns:
        fig: Figura de Plotly
    """
    if isinstance(y, list):
        # Múltiples líneas
        fig = go.Figure()
        
        colors = color if isinstance(color, list) else [color] * len(y)
        
        for i, col in enumerate(y):
            fig.add_trace(
                go.Scatter(
                    x=data[x],
                    y=data[col],
                    mode='lines+markers',
                    name=col,
                    line=dict(color=colors[i % len(colors)])
                )
            )
    else:
        # Una sola línea
        fig = px.line(
            data, 
            x=x, 
            y=y,
            title=title,
            color_discrete_sequence=[color],
            height=height,
            markers=True
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
        title_font=dict(size=16)
    )
    
    return fig