"""
app.py - Dashboard de Vacunación Fiebre Amarilla - Tolima
Version optimizada y simplificada
"""

import streamlit as st
import logging
from pathlib import Path

# Single set_page_config call
st.set_page_config(
    page_title="Dashboard Fiebre Amarilla",
    page_icon="💉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Simplified logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("dashboard.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Simplified configuration
ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Core imports
from src.data.unified_loader import load_and_combine_data
from vistas import overview, geographic, insurance

COLORS = {"primary": "#7D0F2B", "secondary": "#F2A900"}


@st.cache_data(ttl=1800)  # Reduced cache time
def load_data():
    """Simplified data loading with caching"""
    try:
        return load_and_combine_data(
            "data/Resumen.xlsx",
            "data/vacunacion_fa.csv",
            "data/Poblacion_aseguramiento.xlsx",
        )
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        return None, None, None


def main():
    """Simplified main function"""
    try:
        # Load data
        df_combined, df_aseguramiento, fecha_corte = load_data()

        if df_combined is None:
            st.error("Error loading data")
            return

        # Create tabs
        tab_general, tab_geo, tab_insurance = st.tabs(
            ["General", "Geográfico", "Aseguramiento"]
        )

        with tab_general:
            overview.show(df_combined, {}, COLORS)

        with tab_geo:
            geographic.show(df_combined, {}, COLORS)

        with tab_insurance:
            insurance.show(df_combined, {}, COLORS)

    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error("An error occurred running the application")


if __name__ == "__main__":
    main()
