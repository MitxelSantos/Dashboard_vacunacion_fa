import streamlit as st
from pathlib import Path
import base64


def configure_page(page_title, page_icon, layout="wide"):
    """
    Configura el estilo y el tema de la página.

    Args:
        page_title (str): Título de la página
        page_icon (str): Icono de la página
        layout (str): Diseño de la página ('wide' o 'centered')
    """
    # Configuración básica
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout=layout,
        initial_sidebar_state="expanded",
    )

    # CSS básico en línea
    st.markdown(
        """
    <style>
        /* Colores institucionales */
        :root {
            --primary-color: #7D0F2B;
            --secondary-color: #CFB53B;
            --accent-color: #215E8F;
            --background-color: #F5F5F5;
        }
        
        /* Estilos para títulos */
        h1, h2, h3 {
            color: var(--primary-color);
        }
        
        /* Botones primarios */
        .stButton>button {
            background-color: var(--primary-color);
            color: white;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


def get_image_as_base64(file_path):
    """
    Convierte una imagen a base64 para incrustarla en HTML.

    Args:
        file_path (str): Ruta del archivo de imagen

    Returns:
        str: Cadena base64 de la imagen
    """
    with open(file_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


def display_pdf(file_path):
    """
    Muestra un PDF en la aplicación.

    Args:
        file_path (str): Ruta del archivo PDF
    """
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8")
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)


def format_number(number):
    """
    Formatea un número para mostrar en la interfaz.

    Args:
        number (float): Número a formatear

    Returns:
        str: Número formateado
    """
    if number >= 1_000_000:
        return f"{number/1_000_000:.2f} M"
    elif number >= 1_000:
        return f"{number/1_000:.1f} k"
    else:
        return f"{number:.0f}"


def create_download_link(df, filename, text):
    """
    Crea un enlace para descargar un DataFrame como CSV.

    Args:
        df (pd.DataFrame): DataFrame a descargar
        filename (str): Nombre del archivo
        text (str): Texto del enlace

    Returns:
        str: Enlace HTML para descargar
    """
    import pandas as pd

    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href
