"""
Paquete principal para el Dashboard de Vacunación de Fiebre Amarilla.
Desarrollado para la Secretaría de Salud del Tolima.
"""

__version__ = "1.0.0"
__author__ = "José Miguel Santos"

from .data import load_and_combine_data
from .utils import get_image_as_base64

__all__ = ["load_and_combine_data", "get_image_as_base64"]
