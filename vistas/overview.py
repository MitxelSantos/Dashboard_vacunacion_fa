import streamlit as st
import pandas as pd
import plotly.express as px
from src.visualization.charts import create_bar_chart, create_pie_chart
from src.data.preprocessor import prepare_dashboard_data, apply_filters


def create_metrics(data, fuente_poblacion="DANE"):
    """Create main metrics with simplified calculations"""
    try:
        # Si data es un diccionario, extraer los DataFrames
        if isinstance(data, dict):
            df_vacunacion = data.get("vacunacion", pd.DataFrame())
            df_poblacion = data.get("poblacion", pd.DataFrame())
            df_metricas = data.get("metricas", pd.DataFrame())
        else:
            # Si data es un DataFrame simple, usarlo como vacunación
            df_vacunacion = data if isinstance(data, pd.DataFrame) else pd.DataFrame()
            df_poblacion = pd.DataFrame()
            df_metricas = pd.DataFrame()

        # Calcular métricas básicas
        total_vacunados = len(df_vacunacion) if not df_vacunacion.empty else 0

        # Calcular población total
        if not df_metricas.empty and fuente_poblacion in df_metricas.columns:
            total_poblacion = df_metricas[fuente_poblacion].sum()
        elif not df_poblacion.empty:
            # Buscar columna de total en población
            total_cols = [col for col in df_poblacion.columns if "total" in col.lower()]
            if total_cols:
                total_poblacion = df_poblacion[total_cols[0]].sum()
            else:
                total_poblacion = len(df_poblacion) * 100  # Estimación
        else:
            total_poblacion = total_vacunados * 2  # Estimación conservadora

        cobertura = (
            (total_vacunados / total_poblacion * 100) if total_poblacion > 0 else 0
        )
        susceptibles = max(0, total_poblacion - total_vacunados)

        return {
            "total_vacunados": total_vacunados,
            "total_poblacion": int(total_poblacion),
            "cobertura": round(cobertura, 2),
            "susceptibles": int(susceptibles),
        }

    except Exception as e:
        st.error(f"Error calculando métricas: {str(e)}")
        return {
            "total_vacunados": 0,
            "total_poblacion": 0,
            "cobertura": 0,
            "susceptibles": 0,
        }


def show(data, filters, colors, fuente_poblacion="DANE"):
    """Función principal para la vista general"""
    st.title("📊 Visión General")

    # Validar formato de datos
    if data is None:
        st.error("❌ No hay datos disponibles")
        return

    try:
        # Preparar datos en formato consistente
        if isinstance(data, pd.DataFrame):
            # Si es un DataFrame simple, convertir a formato diccionario
            dashboard_data = prepare_dashboard_data(data, None, fuente_poblacion)
        elif isinstance(data, dict):
            dashboard_data = data
        else:
            st.error("❌ Formato de datos no válido")
            return

        # Aplicar filtros si existen
        if filters:
            dashboard_data = apply_filters(dashboard_data, filters)

        # Verificar que tenemos datos después de filtros
        df_vacunacion = dashboard_data.get("vacunacion", pd.DataFrame())
        if df_vacunacion.empty:
            st.warning("⚠️ No hay datos de vacunación para mostrar")
            return

        # Calcular métricas
        metrics = create_metrics(dashboard_data, fuente_poblacion)

        # Mostrar métricas principales
        st.subheader("📊 Métricas Principales")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Población Total",
                f"{metrics['total_poblacion']:,}".replace(",", "."),
                delta=f"Fuente: {fuente_poblacion}",
            )
        with col2:
            st.metric("Vacunados", f"{metrics['total_vacunados']:,}".replace(",", "."))
        with col3:
            st.metric("Cobertura", f"{metrics['cobertura']:.1f}%", delta="del total")
        with col4:
            st.metric(
                "Susceptibles",
                f"{metrics['susceptibles']:,}".replace(",", "."),
                delta="por vacunar",
            )

        # Gráficos principales
        col1, col2 = st.columns(2)

        with col1:
            # Cobertura por municipio
            try:
                df_metricas = dashboard_data.get("metricas", pd.DataFrame())

                if not df_metricas.empty and "DPMP" in df_metricas.columns:
                    cobertura_col = f"Cobertura_{fuente_poblacion}"

                    if cobertura_col in df_metricas.columns:
                        # Top 15 municipios por cobertura
                        top_municipios = df_metricas.nlargest(15, cobertura_col)

                        fig = create_bar_chart(
                            data=top_municipios,
                            x="DPMP",
                            y=cobertura_col,
                            title="Top 15 Municipios por Cobertura",
                            color=colors.get("primary", "#7D0F2B"),
                            height=400,
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info(
                            f"📊 Datos de cobertura por {fuente_poblacion} no disponibles"
                        )
                else:
                    # Fallback: mostrar distribución por municipio
                    municipio_col = None
                    for col in ["NombreMunicipioResidencia", "Municipio", "MUNICIPIO"]:
                        if col in df_vacunacion.columns:
                            municipio_col = col
                            break

                    if municipio_col:
                        municipio_counts = (
                            df_vacunacion[municipio_col]
                            .value_counts()
                            .head(15)
                            .reset_index()
                        )
                        municipio_counts.columns = ["Municipio", "Vacunados"]

                        fig = create_bar_chart(
                            data=municipio_counts,
                            x="Municipio",
                            y="Vacunados",
                            title="Top 15 Municipios por Vacunados",
                            color=colors.get("primary", "#7D0F2B"),
                            height=400,
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("📊 Datos de municipio no disponibles")

            except Exception as e:
                st.error(f"Error creando gráfico de municipios: {str(e)}")

        with col2:
            # Distribución por edad
            try:
                edad_cols = ["Grupo_Edad", "grupo_edad", "GrupoEdad"]
                edad_col = None

                for col in edad_cols:
                    if col in df_vacunacion.columns:
                        edad_col = col
                        break

                if edad_col:
                    # Limpiar datos de edad
                    df_edad_clean = df_vacunacion.copy()
                    df_edad_clean[edad_col] = df_edad_clean[edad_col].fillna("Sin dato")

                    edad_counts = df_edad_clean[edad_col].value_counts().reset_index()
                    edad_counts.columns = ["Grupo_Edad", "Cantidad"]

                    # Tomar top 8 grupos para mejor visualización
                    edad_counts = edad_counts.head(8)

                    fig = create_pie_chart(
                        data=edad_counts,
                        names="Grupo_Edad",
                        values="Cantidad",
                        title="Distribución por Grupo de Edad",
                        color_map={},
                        height=400,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("📊 Datos de grupo de edad no disponibles")

            except Exception as e:
                st.error(f"Error creando gráfico de edad: {str(e)}")

        # Información adicional
        st.markdown("---")
        st.subheader("ℹ️ Información Adicional")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Número de municipios con datos
            municipio_col = None
            for col in ["NombreMunicipioResidencia", "Municipio", "MUNICIPIO"]:
                if col in df_vacunacion.columns:
                    municipio_col = col
                    break

            if municipio_col:
                num_municipios = df_vacunacion[municipio_col].nunique()
                st.metric(
                    "Municipios con Datos", num_municipios, delta="de 47 en Tolima"
                )

        with col2:
            # Período de datos
            fecha_cols = ["FA UNICA", "FechaVacunacion", "Fecha", "FECHA"]
            fecha_col = None

            for col in fecha_cols:
                if col in df_vacunacion.columns:
                    fecha_col = col
                    break

            if fecha_col:
                try:
                    fechas = pd.to_datetime(df_vacunacion[fecha_col], errors="coerce")
                    fechas_validas = fechas.dropna()

                    if len(fechas_validas) > 0:
                        periodo_dias = (
                            fechas_validas.max() - fechas_validas.min()
                        ).days + 1
                        st.metric(
                            "Período de Datos",
                            f"{periodo_dias} días",
                            delta=f"Del {fechas_validas.min().strftime('%d/%m/%Y')} al {fechas_validas.max().strftime('%d/%m/%Y')}",
                        )
                except:
                    st.metric("Período de Datos", "No disponible")

        with col3:
            # Promedio diario
            if fecha_col and metrics["total_vacunados"] > 0:
                try:
                    fechas = pd.to_datetime(df_vacunacion[fecha_col], errors="coerce")
                    fechas_validas = fechas.dropna()

                    if len(fechas_validas) > 0:
                        periodo_dias = (
                            fechas_validas.max() - fechas_validas.min()
                        ).days + 1
                        promedio_diario = (
                            metrics["total_vacunados"] / periodo_dias
                            if periodo_dias > 0
                            else 0
                        )
                        st.metric(
                            "Promedio Diario",
                            f"{promedio_diario:.1f}",
                            delta="vacunados/día",
                        )
                except:
                    st.metric("Promedio Diario", "No disponible")

    except Exception as e:
        st.error(f"❌ Error general en vista overview: {str(e)}")

        # Mostrar información de debug
        with st.expander("🔧 Información de debug"):
            st.write("**Tipo de datos recibidos:**", type(data))
            if isinstance(data, dict):
                st.write("**Claves en diccionario:**", list(data.keys()))
                for key, value in data.items():
                    if isinstance(value, pd.DataFrame):
                        st.write(
                            f"**{key}:** DataFrame con {len(value)} filas y {len(value.columns)} columnas"
                        )
                    else:
                        st.write(f"**{key}:** {type(value)}")
            elif isinstance(data, pd.DataFrame):
                st.write(
                    "**DataFrame:** ",
                    f"{len(data)} filas, {len(data.columns)} columnas",
                )
                st.write("**Columnas:**", list(data.columns))


def mostrar_overview(data):
    """
    Función de compatibilidad hacia atrás
    """
    st.header("📊 Overview del Dashboard de Vacunación")

    if data is None or (isinstance(data, pd.DataFrame) and data.empty):
        st.warning("No hay datos disponibles para mostrar")
        return

    try:
        # Estadísticas básicas
        if isinstance(data, pd.DataFrame):
            total_vacunados = len(data)
            st.metric("Total de Vacunados", f"{total_vacunados:,}".replace(",", "."))

            # Mostrar información adicional si está disponible
            if "NombreMunicipioResidencia" in data.columns:
                municipios = data["NombreMunicipioResidencia"].nunique()
                st.metric("Municipios", municipios)

            # Gráfico simple si hay datos de municipio
            municipio_cols = ["NombreMunicipioResidencia", "Municipio", "MUNICIPIO"]
            municipio_col = None

            for col in municipio_cols:
                if col in data.columns:
                    municipio_col = col
                    break

            if municipio_col:
                municipio_counts = data[municipio_col].value_counts().head(10)
                fig = px.bar(
                    x=municipio_counts.index,
                    y=municipio_counts.values,
                    title="Top 10 Municipios por Vacunación",
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Formato de datos no reconocido para overview básico")

    except Exception as e:
        st.error(f"Error en overview básico: {str(e)}")


# En cualquier vista, puedes mostrar esta información:
def show_temporal_info(metadata):
    if metadata and "cutoff_date" in metadata:
        cutoff_date = metadata["cutoff_date"]
        st.info(
            f"""
        📅 **División Temporal Automática:**
        - **Fecha de corte:** {cutoff_date.strftime('%d de %B de %Y')}
        - **Pre-emergencia:** Datos anteriores al {cutoff_date.strftime('%d/%m/%Y')}
        - **Emergencia:** Brigadas desde el {cutoff_date.strftime('%d/%m/%Y')}
        """
        )
