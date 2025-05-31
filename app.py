"""
app.py - Dashboard de Vacunación Fiebre Amarilla - Tolima
Versión simplificada y optimizada
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import os
from pathlib import Path

# Configuración de página
st.set_page_config(
    page_title="Dashboard Fiebre Amarilla - Tolima",
    page_icon="💉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Colores institucionales del Tolima
COLORS = {
    "primary": "#7D0F2B",  # Vinotinto institucional
    "secondary": "#F2A900",  # Amarillo dorado
    "accent": "#5A4214",  # Marrón dorado
    "success": "#509E2F",  # Verde
    "warning": "#F7941D",  # Naranja
    "white": "#FFFFFF",
}


@st.cache_data
def load_brigadas_data():
    """Carga datos de brigadas de emergencia"""
    try:
        if os.path.exists("data/Resumen.xlsx"):
            # Intentar diferentes hojas
            try:
                df = pd.read_excel("data/Resumen.xlsx", sheet_name="Vacunacion")
            except:
                # Si no existe "Vacunacion", usar la primera hoja
                df = pd.read_excel("data/Resumen.xlsx", sheet_name=0)

            st.write(
                f"🔍 **Debug Brigadas:** {len(df)} filas, Columnas: {list(df.columns)}"
            )

            # Convertir fechas
            if "FECHA" in df.columns:
                df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")
                fechas_validas = df["FECHA"].notna().sum()
                st.write(f"📅 Fechas válidas en brigadas: {fechas_validas}")

            return df
    except Exception as e:
        st.error(f"Error cargando brigadas: {str(e)}")
    return pd.DataFrame()


@st.cache_data
def load_historical_data():
    """Carga datos históricos de vacunación"""
    try:
        if os.path.exists("data/vacunacion_fa.csv"):
            df = pd.read_csv("data/vacunacion_fa.csv")
            st.write(
                f"🔍 **Debug Históricos:** {len(df)} filas, Columnas: {list(df.columns)[:10]}..."
            )

            # Convertir fechas
            if "FA UNICA" in df.columns:
                df["FA UNICA"] = pd.to_datetime(df["FA UNICA"], errors="coerce")
                fechas_validas = df["FA UNICA"].notna().sum()
                st.write(f"📅 Fechas válidas en históricos: {fechas_validas}")

            return df
    except Exception as e:
        st.error(f"Error cargando datos históricos: {str(e)}")
    return pd.DataFrame()


@st.cache_data
def load_population_data():
    """Carga datos de población por EAPB"""
    try:
        if os.path.exists("data/Poblacion_aseguramiento.xlsx"):
            df = pd.read_excel("data/Poblacion_aseguramiento.xlsx")
            st.write(
                f"🔍 **Debug Población:** {len(df)} filas, Columnas: {list(df.columns)}"
            )
            return df
    except Exception as e:
        st.error(f"Error cargando población: {str(e)}")
    return pd.DataFrame()


def determine_cutoff_date(df_brigades):
    """Determina la fecha de corte automáticamente"""
    if df_brigades.empty or "FECHA" not in df_brigades.columns:
        return None

    # Buscar la fecha MÁS ANTIGUA en brigadas (inicio de emergencia)
    fechas_validas = df_brigades["FECHA"].dropna()
    if len(fechas_validas) > 0:
        fecha_corte = fechas_validas.min()
        st.info(
            f"📅 **Fecha de corte determinada:** {fecha_corte.strftime('%d/%m/%Y')}"
        )
        st.info(f"• **Pre-emergencia:** Antes del {fecha_corte.strftime('%d/%m/%Y')}")
        st.info(f"• **Emergencia:** Desde el {fecha_corte.strftime('%d/%m/%Y')}")
        return fecha_corte
    return None


def combine_vaccination_data(df_historical, df_brigades, fecha_corte):
    """Combina datos históricos y de brigadas según fecha de corte"""
    combined_data = {
        "pre_emergencia": pd.DataFrame(),
        "emergencia": pd.DataFrame(),
        "total_vacunados": 0,
        "total_pre": 0,
        "total_emergencia": 0,
    }

    if fecha_corte is None:
        if not df_historical.empty:
            combined_data["pre_emergencia"] = df_historical
            combined_data["total_pre"] = len(df_historical)
            combined_data["total_vacunados"] = len(df_historical)
        return combined_data

    # Filtrar datos históricos (antes de fecha de corte)
    if not df_historical.empty and "FA UNICA" in df_historical.columns:
        mask_pre = df_historical["FA UNICA"] < fecha_corte
        df_pre = df_historical[mask_pre].copy()
        df_pre["periodo"] = "pre_emergencia"
        combined_data["pre_emergencia"] = df_pre
        combined_data["total_pre"] = len(df_pre)

    # Datos de brigadas (desde fecha de corte)
    if not df_brigades.empty:
        # Para brigadas, asumimos que todos los registros son del período de emergencia
        df_emerg = df_brigades.copy()
        df_emerg["periodo"] = "emergencia"
        combined_data["emergencia"] = df_emerg
        combined_data["total_emergencia"] = len(df_emerg)

    combined_data["total_vacunados"] = (
        combined_data["total_pre"] + combined_data["total_emergencia"]
    )

    st.success(
        f"✅ **Datos combinados:** {combined_data['total_vacunados']} registros totales"
    )
    st.write(f"• Pre-emergencia: {combined_data['total_pre']} registros")
    st.write(f"• Emergencia: {combined_data['total_emergencia']} registros")

    return combined_data


def create_metric_card(title, value, delta=None):
    """Crea una tarjeta de métrica personalizada"""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.metric(title, value, delta=delta)


def show_overview_tab(combined_data, df_population, fecha_corte):
    """Muestra la vista general del dashboard con datos combinados"""
    st.header("📊 Resumen General")

    # Información de división temporal
    if fecha_corte:
        st.info(
            f"🔄 **División temporal activa:** Corte el {fecha_corte.strftime('%d/%m/%Y')}"
        )

    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Pre-emergencia",
            f"{combined_data['total_pre']:,}".replace(",", "."),
            delta="Vacunación regular",
        )

    with col2:
        st.metric(
            "Emergencia",
            f"{combined_data['total_emergencia']:,}".replace(",", "."),
            delta="Brigadas territoriales",
        )

    with col3:
        total_population = 0
        if not df_population.empty and "Total" in df_population.columns:
            total_population = df_population["Total"].sum()
        st.metric("Población Total", f"{total_population:,}".replace(",", "."))

    with col4:
        total_vacunados = combined_data["total_vacunados"]
        if total_population > 0:
            cobertura = total_vacunados / total_population * 100
            st.metric("Cobertura Total", f"{cobertura:.1f}%")
        else:
            st.metric("Total Vacunados", f"{total_vacunados:,}".replace(",", "."))

    # Gráficos comparativos
    col1, col2 = st.columns(2)

    with col1:
        # Comparación por períodos
        periodos_data = {
            "Período": ["Pre-emergencia", "Emergencia"],
            "Vacunados": [
                combined_data["total_pre"],
                combined_data["total_emergencia"],
            ],
        }

        fig = px.bar(
            periodos_data,
            x="Período",
            y="Vacunados",
            title="Vacunación por Período",
            color="Período",
            color_discrete_map={
                "Pre-emergencia": COLORS["primary"],
                "Emergencia": COLORS["warning"],
            },
        )
        fig.update_layout(
            plot_bgcolor=COLORS["white"], paper_bgcolor=COLORS["white"], height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Análisis de municipios si tenemos datos históricos
        if (
            not combined_data["pre_emergencia"].empty
            and "NombreMunicipioResidencia" in combined_data["pre_emergencia"].columns
        ):
            municipios = (
                combined_data["pre_emergencia"]["NombreMunicipioResidencia"]
                .value_counts()
                .head(8)
            )

            fig = px.pie(
                values=municipios.values,
                names=municipios.index,
                title="Top 8 Municipios - Vacunación Histórica",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        elif (
            not combined_data["emergencia"].empty
            and "MUNICIPIO" in combined_data["emergencia"].columns
        ):
            municipios_brig = (
                combined_data["emergencia"]["MUNICIPIO"].value_counts().head(8)
            )

            fig = px.pie(
                values=municipios_brig.values,
                names=municipios_brig.index,
                title="Top 8 Municipios - Brigadas",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)


def show_temporal_tab(combined_data, fecha_corte):
    """Muestra análisis temporal con datos combinados"""
    st.header("📅 Análisis Temporal")

    if fecha_corte:
        st.info(
            f"📅 **Fecha de corte:** {fecha_corte.strftime('%d/%m/%Y')} - Inicio de brigadas de emergencia"
        )

    # Análisis de datos históricos (pre-emergencia)
    if (
        not combined_data["pre_emergencia"].empty
        and "FA UNICA" in combined_data["pre_emergencia"].columns
    ):
        st.subheader("📈 Período Pre-emergencia (Vacunación Regular)")

        # Filtrar fechas válidas
        df_temporal = combined_data["pre_emergencia"][
            combined_data["pre_emergencia"]["FA UNICA"].notna()
        ].copy()

        if not df_temporal.empty:
            # Agrupar por día
            daily_data = (
                df_temporal.groupby(df_temporal["FA UNICA"].dt.date)
                .size()
                .reset_index()
            )
            daily_data.columns = ["Fecha", "Vacunados"]
            daily_data["Fecha"] = pd.to_datetime(daily_data["Fecha"])

            # Gráfico de línea temporal
            fig = px.line(
                daily_data,
                x="Fecha",
                y="Vacunados",
                title="Evolución Diaria - Período Pre-emergencia",
                color_discrete_sequence=[COLORS["primary"]],
            )
            fig.update_layout(
                plot_bgcolor=COLORS["white"], paper_bgcolor=COLORS["white"], height=400
            )
            st.plotly_chart(fig, use_container_width=True)

            # Estadísticas temporales
            col1, col2, col3 = st.columns(3)

            with col1:
                fecha_inicio = daily_data["Fecha"].min()
                fecha_fin = daily_data["Fecha"].max()
                duracion = (fecha_fin - fecha_inicio).days + 1
                st.metric("Duración Pre-emergencia", f"{duracion} días")

            with col2:
                promedio_diario = daily_data["Vacunados"].mean()
                st.metric("Promedio Diario", f"{promedio_diario:.1f}")

            with col3:
                max_dia = daily_data.loc[daily_data["Vacunados"].idxmax()]
                st.metric("Día Pico", f"{max_dia['Vacunados']} vac")
                st.caption(f"Fecha: {max_dia['Fecha'].strftime('%d/%m/%Y')}")

    # Análisis de brigadas (emergencia)
    if (
        not combined_data["emergencia"].empty
        and "FECHA" in combined_data["emergencia"].columns
    ):
        st.subheader("🚨 Período de Emergencia (Brigadas Territoriales)")

        df_brigadas_temporal = combined_data["emergencia"][
            combined_data["emergencia"]["FECHA"].notna()
        ].copy()

        if not df_brigadas_temporal.empty:
            # Brigadas por día
            brigadas_daily = (
                df_brigadas_temporal.groupby(df_brigadas_temporal["FECHA"].dt.date)
                .size()
                .reset_index()
            )
            brigadas_daily.columns = ["Fecha", "Brigadas"]
            brigadas_daily["Fecha"] = pd.to_datetime(brigadas_daily["Fecha"])

            fig = px.bar(
                brigadas_daily,
                x="Fecha",
                y="Brigadas",
                title="Brigadas de Emergencia por Día",
                color_discrete_sequence=[COLORS["warning"]],
            )
            fig.update_layout(
                plot_bgcolor=COLORS["white"], paper_bgcolor=COLORS["white"], height=400
            )
            st.plotly_chart(fig, use_container_width=True)

            # Estadísticas de brigadas
            col1, col2, col3 = st.columns(3)

            with col1:
                total_brigadas = len(df_brigadas_temporal)
                st.metric("Total Brigadas", total_brigadas)

            with col2:
                if "MUNICIPIO" in df_brigadas_temporal.columns:
                    municipios_brigadas = df_brigadas_temporal["MUNICIPIO"].nunique()
                    st.metric("Municipios Cubiertos", municipios_brigadas)

            with col3:
                if "VEREDAS" in df_brigadas_temporal.columns:
                    veredas_brigadas = df_brigadas_temporal["VEREDAS"].nunique()
                    st.metric("Veredas Visitadas", veredas_brigadas)


def show_geographic_tab(combined_data):
    """Muestra análisis geográfico con datos combinados"""
    st.header("🗺️ Distribución Geográfica")

    col1, col2 = st.columns(2)

    with col1:
        if (
            not combined_data["pre_emergencia"].empty
            and "NombreMunicipioResidencia" in combined_data["pre_emergencia"].columns
        ):
            st.subheader("📍 Pre-emergencia por Municipio")

            municipios_hist = (
                combined_data["pre_emergencia"]["NombreMunicipioResidencia"]
                .value_counts()
                .reset_index()
            )
            municipios_hist.columns = ["Municipio", "Vacunados"]

            # Mostrar top 15
            top_municipios = municipios_hist.head(15)

            fig = px.bar(
                top_municipios,
                x="Vacunados",
                y="Municipio",
                orientation="h",
                title="Top 15 Municipios - Vacunación Regular",
                color_discrete_sequence=[COLORS["primary"]],
            )
            fig.update_layout(
                plot_bgcolor=COLORS["white"],
                paper_bgcolor=COLORS["white"],
                height=500,
                yaxis={"categoryorder": "total ascending"},
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if (
            not combined_data["emergencia"].empty
            and "MUNICIPIO" in combined_data["emergencia"].columns
        ):
            st.subheader("🚨 Brigadas por Municipio")

            municipios_brig = (
                combined_data["emergencia"]["MUNICIPIO"].value_counts().reset_index()
            )
            municipios_brig.columns = ["Municipio", "Brigadas"]

            # Mostrar top 15
            top_brigadas = municipios_brig.head(15)

            fig = px.bar(
                top_brigadas,
                x="Brigadas",
                y="Municipio",
                orientation="h",
                title="Top 15 Municipios - Brigadas de Emergencia",
                color_discrete_sequence=[COLORS["warning"]],
            )
            fig.update_layout(
                plot_bgcolor=COLORS["white"],
                paper_bgcolor=COLORS["white"],
                height=500,
                yaxis={"categoryorder": "total ascending"},
            )
            st.plotly_chart(fig, use_container_width=True)

    # Comparación directa si tenemos ambos tipos de datos
    if (
        not combined_data["pre_emergencia"].empty
        and "NombreMunicipioResidencia" in combined_data["pre_emergencia"].columns
        and not combined_data["emergencia"].empty
        and "MUNICIPIO" in combined_data["emergencia"].columns
    ):

        st.subheader("🔄 Comparación: Regular vs Brigadas por Municipio")

        # Crear datos comparativos
        municipios_hist = combined_data["pre_emergencia"][
            "NombreMunicipioResidencia"
        ].value_counts()
        municipios_brig = combined_data["emergencia"]["MUNICIPIO"].value_counts()

        # Obtener municipios comunes
        municipios_comunes = set(municipios_hist.index) & set(municipios_brig.index)

        if municipios_comunes:
            comparison_data = []
            for municipio in list(municipios_comunes)[:10]:  # Top 10
                comparison_data.extend(
                    [
                        {
                            "Municipio": municipio,
                            "Tipo": "Regular",
                            "Cantidad": municipios_hist.get(municipio, 0),
                        },
                        {
                            "Municipio": municipio,
                            "Tipo": "Brigadas",
                            "Cantidad": municipios_brig.get(municipio, 0),
                        },
                    ]
                )

            comparison_df = pd.DataFrame(comparison_data)

            fig = px.bar(
                comparison_df,
                x="Municipio",
                y="Cantidad",
                color="Tipo",
                title="Comparación: Vacunación Regular vs Brigadas (Top 10 municipios comunes)",
                color_discrete_map={
                    "Regular": COLORS["primary"],
                    "Brigadas": COLORS["warning"],
                },
            )
            fig.update_layout(
                plot_bgcolor=COLORS["white"],
                paper_bgcolor=COLORS["white"],
                height=400,
                xaxis_tickangle=45,
            )
            st.plotly_chart(fig, use_container_width=True)


def show_population_tab(df_population):
    """Muestra análisis de población"""
    st.header("🏥 Análisis de Población por EAPB")

    if df_population.empty:
        st.warning("No hay datos de población disponibles")
        return

    # Mostrar estructura de datos
    with st.expander("🔍 Estructura de datos de población"):
        st.write("**Columnas disponibles:**")
        st.write(list(df_population.columns))
        st.write("**Muestra de datos:**")
        st.dataframe(df_population.head(), use_container_width=True)

    # Análisis básico si tenemos columnas identificables
    if "EAPB" in df_population.columns and "Total" in df_population.columns:
        st.subheader("Distribución por EAPB")

        # Agrupar por EAPB
        eapb_totals = (
            df_population.groupby("EAPB")["Total"].sum().sort_values(ascending=False)
        )

        col1, col2 = st.columns(2)

        with col1:
            # Top 10 EAPB
            top_eapb = eapb_totals.head(10)

            fig = px.bar(
                x=top_eapb.values,
                y=top_eapb.index,
                orientation="h",
                title="Top 10 EAPB por Población",
                color_discrete_sequence=[COLORS["secondary"]],
            )
            fig.update_layout(
                plot_bgcolor=COLORS["white"],
                paper_bgcolor=COLORS["white"],
                height=400,
                yaxis={"categoryorder": "total ascending"},
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Distribución porcentual
            fig = px.pie(
                values=eapb_totals.head(8).values,
                names=eapb_totals.head(8).index,
                title="Distribución Porcentual - Top 8 EAPB",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        # Métricas de población
        col1, col2, col3 = st.columns(3)

        with col1:
            total_pop = df_population["Total"].sum()
            st.metric("Población Total", f"{total_pop:,}".replace(",", "."))

        with col2:
            num_eapb = df_population["EAPB"].nunique()
            st.metric("Número de EAPB", num_eapb)

        with col3:
            if "Municipio" in df_population.columns:
                num_municipios = df_population["Municipio"].nunique()
                st.metric("Municipios Cubiertos", num_municipios)


def main():
    """Función principal del dashboard"""
    # Título principal
    st.title("🏥 Dashboard de Vacunación Fiebre Amarilla")
    st.markdown("**Departamento del Tolima**")

    # Sidebar con información
    with st.sidebar:
        st.image(
            "https://via.placeholder.com/200x100/7D0F2B/FFFFFF?text=TOLIMA", width=200
        )
        st.markdown("---")
        st.markdown("### ℹ️ Información del Sistema")
        st.markdown("- **Vacunación:** Fiebre Amarilla")
        st.markdown("- **Departamento:** Tolima")
        st.markdown("- **Período:** 2024-2025")
        st.markdown("---")

        # Control de actualización
        if st.button("🔄 Actualizar Datos"):
            st.cache_data.clear()
            st.rerun()

        # Debug toggle
        show_debug = st.checkbox("🔍 Mostrar información de debug")

    # Cargar datos
    with st.spinner("Cargando datos..."):
        # Mostrar debug info solo si está activado
        if show_debug:
            st.markdown("### 🔍 Debug Information")
            df_historical = load_historical_data()
            df_brigades = load_brigadas_data()
            df_population = load_population_data()
        else:
            # Cargar silenciosamente
            try:
                df_historical = (
                    pd.read_csv("data/vacunacion_fa.csv")
                    if os.path.exists("data/vacunacion_fa.csv")
                    else pd.DataFrame()
                )
                if not df_historical.empty and "FA UNICA" in df_historical.columns:
                    df_historical["FA UNICA"] = pd.to_datetime(
                        df_historical["FA UNICA"], errors="coerce"
                    )

                if os.path.exists("data/Resumen.xlsx"):
                    try:
                        df_brigades = pd.read_excel(
                            "data/Resumen.xlsx", sheet_name="Vacunacion"
                        )
                    except:
                        df_brigades = pd.read_excel("data/Resumen.xlsx", sheet_name=0)
                    if "FECHA" in df_brigades.columns:
                        df_brigades["FECHA"] = pd.to_datetime(
                            df_brigades["FECHA"], errors="coerce"
                        )
                else:
                    df_brigades = pd.DataFrame()

                df_population = (
                    pd.read_excel("data/Poblacion_aseguramiento.xlsx")
                    if os.path.exists("data/Poblacion_aseguramiento.xlsx")
                    else pd.DataFrame()
                )
            except Exception as e:
                st.error(f"Error cargando datos: {str(e)}")
                df_historical = df_brigades = df_population = pd.DataFrame()

    # Determinar fecha de corte y combinar datos
    fecha_corte = determine_cutoff_date(df_brigades)
    combined_data = combine_vaccination_data(df_historical, df_brigades, fecha_corte)

    # Información de estado de datos
    col1, col2, col3 = st.columns(3)

    with col1:
        status = "✅" if combined_data["total_pre"] > 0 else "❌"
        st.markdown(
            f"{status} **Pre-emergencia:** {combined_data['total_pre']} registros"
        )

    with col2:
        status = "✅" if combined_data["total_emergencia"] > 0 else "❌"
        st.markdown(
            f"{status} **Emergencia:** {combined_data['total_emergencia']} registros"
        )

    with col3:
        status = "✅" if not df_population.empty else "❌"
        st.markdown(f"{status} **Población:** {len(df_population)} registros")

    st.markdown("---")

    # Tabs principales
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Resumen", "📅 Temporal", "🗺️ Geográfico", "🏥 Población"]
    )

    with tab1:
        show_overview_tab(combined_data, df_population, fecha_corte)

    with tab2:
        show_temporal_tab(combined_data, fecha_corte)

    with tab3:
        show_geographic_tab(combined_data)

    with tab4:
        show_population_tab(df_population)

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #7D0F2B;'>"
        "<small>Dashboard de Vacunación - Secretaría de Salud del Tolima</small>"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
