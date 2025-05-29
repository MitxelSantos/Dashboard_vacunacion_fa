"""
src/utils/helpers.py
Utilidades simplificadas y optimizadas para el dashboard de vacunación
Compatibles con la nueva estructura unificada y división temporal automática
"""

import streamlit as st
import pandas as pd
import base64
import io
from typing import Union, Dict, Any


def format_number(number: Union[int, float], decimals: int = 0) -> str:
    """Format numbers with institutional style"""
    try:
        if pd.isna(number):
            return "N/A"
        return f"{float(number):,.{decimals}f}".replace(",", ".")
    except:
        return str(number)


def create_metric_card(
    title: str, value: Union[str, int, float], delta: str = None
) -> str:
    """Create simple metric card"""
    if isinstance(value, (int, float)):
        value = format_number(value)

    delta_html = f'<div class="metric-delta">{delta}</div>' if delta else ""

    return f"""
    <div class="metric-container">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """


def get_institutional_colors() -> Dict[str, str]:
    """Get institutional colors"""
    return {
        "primary": "#7D0F2B",
        "secondary": "#F2A900",
        "accent": "#5A4214",
        "success": "#509E2F",
        "warning": "#F7941D",
    }


# Funciones de conveniencia
def configure_page(title, icon="💉", layout="wide"):
    """Función de conveniencia para configurar página"""
    return dashboard_helpers.configure_page_optimized(title, icon, layout)


def format_number_convenience(number, decimals=0):
    """Función de conveniencia para formatear números"""
    return dashboard_helpers.format_number_institutional(number, decimals)


def create_metric(title, value, delta=None):
    """Función de conveniencia para crear métricas"""
    return dashboard_helpers.create_metric_card(title, value, delta)


def get_colors():
    """Función de conveniencia para obtener colores institucionales"""
    return dashboard_helpers.get_institutional_colors()


def get_image_as_base64(image_path):
    """
    Convert an image file to base64 string

    Args:
        image_path (str): Path to the image file

    Returns:
        str: Base64 encoded string of the image
    """
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            return encoded_string
    except Exception as e:
        print(f"Error converting image to base64: {e}")
        return ""
