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
    st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)

    # Cargar CSS personalizado
    css_main = Path(__file__).parent.parent.parent / "assets" / "styles" / "main.css"
    css_responsive = (
        Path(__file__).parent.parent.parent / "assets" / "styles" / "responsive.css"
    )

    css = ""
    if css_main.exists():
        with open(css_main) as f:
            css += f.read()

    if css_responsive.exists():
        with open(css_responsive) as f:
            css += f.read()

    # Aplicar CSS
    st.markdown(
        f"""
    <style>
        {css}
        /* Colores institucionales */
        :root {{
            --primary-color: #7D0F2B;
            --secondary-color: #F2A900;
            --accent-color: #5A4214;
            --background-color: #F5F5F5;
        }}
        
        /* Estilos para títulos */
        h1, h2, h3 {{
            color: var(--primary-color);
        }}
        
        /* Botones primarios */
        .stButton>button {{
            background-color: var(--primary-color);
            color: white;
        }}
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


def format_number(number, responsive=False):
    """
    Formatea un número para mostrar en la interfaz.

    Args:
        number (float): Número a formatear
        responsive (bool): Si debe usar formato responsivo para pantallas pequeñas

    Returns:
        str: Número formateado
    """
    # Detectar tamaño de pantalla (aproximado)
    is_small_screen = responsive and st.session_state.get("_is_small_screen", False)

    if is_small_screen:
        # Formato más compacto para pantallas pequeñas
        if number >= 1_000_000:
            return f"{number/1_000_000:.1f}M"
        elif number >= 1_000:
            return f"{number/1_000:.0f}k"
        else:
            return f"{number:.0f}"
    else:
        # Formato normal con separadores de miles
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


def format_dataframe_for_display(df, responsive=True):
    """
    Formatea un DataFrame para mostrar en pantallas de diferentes tamaños.

    Args:
        df (pd.DataFrame): DataFrame a formatear
        responsive (bool): Si debe adaptar el formato a pantallas pequeñas

    Returns:
        pd.DataFrame: DataFrame con formato mejorado
    """
    # Detectar si estamos en pantalla pequeña
    is_small = st.session_state.get("_is_small_screen", False) and responsive

    # Crear copia para no modificar el original
    formatted_df = df.copy()

    # Aplicar formato a columnas numéricas
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            if "Cobertura" in col:
                # Para coberturas (porcentajes)
                formato = "{:.1f}%" if is_small else "{:.2f}%"
                formatted_df[col] = df[col].apply(lambda x: formato.format(x))
            elif df[col].max() > 1000:
                # Para números grandes
                formatted_df[col] = df[col].apply(
                    lambda x: (
                        f"{x/1000:.0f}k" if is_small else f"{x:,.0f}".replace(",", ".")
                    )
                )
            else:
                # Para números pequeños
                formatted_df[col] = df[col].apply(
                    lambda x: f"{x:.0f}" if is_small else f"{x:,.1f}".replace(",", ".")
                )

    # Si es pantalla muy pequeña y hay muchas columnas, seleccionar solo las principales
    if is_small and len(formatted_df.columns) > 4:
        # Identificar columnas importantes (mantener siempre la primera)
        main_cols = [formatted_df.columns[0]]

        # Añadir columnas con "Cobertura" si existen
        cob_cols = [col for col in formatted_df.columns if "Cobertura" in col]
        if cob_cols:
            main_cols.extend(cob_cols[:1])  # Solo la primera columna de cobertura

        # Añadir "Vacunados" si existe
        if "Vacunados" in formatted_df.columns:
            main_cols.append("Vacunados")

        # Limitar a máximo 4 columnas
        return formatted_df[main_cols[:4]]

    return formatted_df
