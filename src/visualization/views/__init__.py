"""
Views module for the dashboard.
Contains all visualization components and pages.
"""

from .resumen import mostrar_resumen
from .cobertura import mostrar_cobertura
from .historico import mostrar_historico

__all__ = ["mostrar_resumen", "mostrar_cobertura", "mostrar_historico"]
