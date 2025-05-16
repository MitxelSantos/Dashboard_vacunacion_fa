"""
Funciones y utilidades auxiliares para el dashboard.
Incluye funciones para configuración de página, formato de datos y exportación.
"""

from .helpers import (
    configure_page,
    get_image_as_base64,
    display_pdf,
    format_number,
    create_download_link,
)

__all__ = [
    "configure_page",
    "get_image_as_base64",
    "display_pdf",
    "format_number",
    "create_download_link",
    "create_download_links",
]
