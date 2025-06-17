"""
vistas/population.py - Análisis poblacional
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def show_population_tab(combined_data, COLORS):
    """Muestra análisis poblacional"""
    st.header("🏘️ Análisis Poblacional por Municipios")

    # Verificar si tenemos datos de población
    if not combined_data["population"]["por_municipio"]:
        show_basic_population_analysis(combined_data, COLORS)
        return

    # Calcular datos de cobertura por municipio
    coverage_data = calculate_municipal_coverage(combined_data)

    if not coverage_data:
        st.warning("⚠️ No se pudo calcular cobertura municipal")
        show_basic_population_analysis(combined_data, COLORS)
        return

    # Mostrar métricas principales
    show_main_metrics(combined_data, coverage_data, COLORS)

    # Mostrar distribución poblacional
    show_population_distribution(coverage_data, COLORS)

    # Mostrar análisis de cobertura
    show_coverage_analysis(coverage_data, COLORS)


def calculate_municipal_coverage(combined_data):
    """Calcula cobertura real por municipio"""
    population_by_mun = combined_data["population"]["por_municipio"]
    individual_by_mun = combined_data["individual"]["por_municipio"]
    barridos_by_mun = combined_data["barridos"]["vacunados_barrido"]["por_municipio"]
    renuentes_by_mun = combined_data["barridos"]["renuentes"]["por_municipio"]

    coverage_data = []

    for municipio, poblacion_asegurada in population_by_mun.items():
        # Contar vacunados del municipio
        individual_count = individual_by_mun.get(municipio, 0)
        barridos_count = barridos_by_mun.get(municipio, 0)
        renuentes_count = renuentes_by_mun.get(municipio, 0)

        total_vacunados = individual_count + barridos_count

        # Calcular métricas
        cobertura_real = (
            (total_vacunados / poblacion_asegurada) * 100
            if poblacion_asegurada > 0
            else 0
        )
        meta_80 = poblacion_asegurada * 0.8
        avance_meta = (total_vacunados / meta_80) * 100 if meta_80 > 0 else 0
        faltante_meta = max(0, meta_80 - total_vacunados)

        # Calcular tasa de contacto y aceptación
        total_contactados = total_vacunados + renuentes_count
        tasa_contacto = (
            (total_contactados / poblacion_asegurada) * 100
            if poblacion_asegurada > 0
            else 0
        )
        tasa_aceptacion = (
            (total_vacunados / total_contactados) * 100 if total_contactados > 0 else 0
        )

        coverage_data.append(
            {
                "Municipio": municipio,
                "Poblacion_Asegurada": poblacion_asegurada,
                "Individual": individual_count,
                "Barridos": barridos_count,
                "Total_Vacunados": total_vacunados,
                "Renuentes": renuentes_count,
                "Cobertura_Real": cobertura_real,
                "Meta_80": meta_80,
                "Avance_Meta": avance_meta,
                "Faltante_Meta": faltante_meta,
                "Tasa_Contacto": tasa_contacto,
                "Tasa_Aceptacion": tasa_aceptacion,
            }
        )

    return coverage_data


def show_main_metrics(combined_data, coverage_data, COLORS):
    """Muestra métricas principales"""
    col1, col2, col3, col4 = st.columns(4)

    total_poblacion = combined_data["population"]["total"]
    total_vacunados = combined_data["total_general"]
    total_renuentes = combined_data["total_renuentes"]

    with col1:
        st.metric("Población Asegurada Total", f"{total_poblacion:,}")

    with col2:
        cobertura_general = (
            (total_vacunados / total_poblacion) * 100 if total_poblacion > 0 else 0
        )
        st.metric("Cobertura General", f"{cobertura_general:.1f}%")

    with col3:
        meta_general = total_poblacion * 0.8
        avance_general = (
            (total_vacunados / meta_general) * 100 if meta_general > 0 else 0
        )
        st.metric("Avance Meta 80%", f"{avance_general:.1f}%")

    with col4:
        municipios_count = len(coverage_data)
        st.metric("Municipios Analizados", f"{municipios_count}")


def show_population_distribution(coverage_data, COLORS):
    """Muestra distribución poblacional por municipios"""
    st.subheader("📊 Distribución de Población Asegurada")

    df_coverage = pd.DataFrame(coverage_data)
    df_coverage = df_coverage.sort_values("Poblacion_Asegurada", ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        # Top 15 municipios por población
        top_15 = df_coverage.head(15)

        fig = px.bar(
            top_15,
            x="Poblacion_Asegurada",
            y="Municipio",
            orientation="h",
            title="Top 15 Municipios por Población Asegurada",
            color_discrete_sequence=[COLORS["secondary"]],
            text="Poblacion_Asegurada",
        )

        fig.update_traces(
            texttemplate="%{text:,}",
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>" + "Población: %{x:,}<extra></extra>",
        )

        fig.update_layout(
            plot_bgcolor=COLORS["white"],
            paper_bgcolor=COLORS["white"],
            height=500,
            yaxis={"categoryorder": "total ascending"},
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Categorización por tamaño poblacional
        df_coverage["Categoria"] = df_coverage["Poblacion_Asegurada"].apply(
            lambda x: (
                "Grandes (>50k)"
                if x >= 50000
                else (
                    "Medianos (20k-50k)"
                    if x >= 20000
                    else "Pequeños (10k-20k)" if x >= 10000 else "Rurales (<10k)"
                )
            )
        )

        categoria_counts = df_coverage["Categoria"].value_counts()

        fig_pie = px.pie(
            values=categoria_counts.values,
            names=categoria_counts.index,
            title="Distribución de Municipios por Tamaño",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )

        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(height=500)

        st.plotly_chart(fig_pie, use_container_width=True)


def show_coverage_analysis(coverage_data, COLORS):
    """Muestra análisis de cobertura corregido"""
    st.subheader("🎯 Análisis de Cobertura por Municipios")

    df_coverage = pd.DataFrame(coverage_data)
    df_coverage = df_coverage.sort_values("Cobertura_Real", ascending=False)

    # Gráfico de cobertura vs meta
    fig = go.Figure()

    # Línea de meta 80%
    fig.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="Meta 80%")

    # Barras de cobertura real
    fig.add_trace(
        go.Bar(
            name="Cobertura Real",
            x=df_coverage["Municipio"][:20],  # Top 20
            y=df_coverage["Cobertura_Real"][:20],
            marker_color=COLORS["primary"],
            text=df_coverage["Cobertura_Real"][:20].round(1),
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>"
            + "Cobertura: %{y:.1f}%<br>"
            + "<extra></extra>",
        )
    )

    fig.update_layout(
        title="Cobertura Real vs Meta 80% - Top 20 Municipios",
        xaxis_title="Municipio",
        yaxis_title="Cobertura (%)",
        plot_bgcolor=COLORS["white"],
        paper_bgcolor=COLORS["white"],
        height=500,
        xaxis={"tickangle": 45},
    )

    st.plotly_chart(fig, use_container_width=True)

    # Tabla detallada SIN duplicaciones
    st.subheader("📋 Detalle de Cobertura por Municipios")

    # Preparar tabla con métricas claras y diferentes
    tabla_display = df_coverage[
        [
            "Municipio",
            "Poblacion_Asegurada",
            "Total_Vacunados",
            "Cobertura_Real",
            "Avance_Meta",
            "Faltante_Meta",
            "Renuentes",
        ]
    ].copy()

    # Redondear valores
    tabla_display["Cobertura_Real"] = tabla_display["Cobertura_Real"].round(1)
    tabla_display["Avance_Meta"] = tabla_display["Avance_Meta"].round(1)

    # Renombrar columnas para claridad
    tabla_display = tabla_display.rename(
        columns={
            "Poblacion_Asegurada": "Población Asegurada",
            "Total_Vacunados": "Total Vacunados",
            "Cobertura_Real": "Cobertura Real (%)",
            "Avance_Meta": "Avance Meta 80% (%)",
            "Faltante_Meta": "Faltante para Meta",
            "Renuentes": "Renuentes",
        }
    )

    st.dataframe(
        tabla_display,
        use_container_width=True,
        column_config={
            "Población Asegurada": st.column_config.NumberColumn(
                "Población Asegurada", format="%d"
            ),
            "Total Vacunados": st.column_config.NumberColumn(
                "Total Vacunados", format="%d"
            ),
            "Cobertura Real (%)": st.column_config.NumberColumn(
                "Cobertura Real (%)", format="%.1f%%"
            ),
            "Avance Meta 80% (%)": st.column_config.NumberColumn(
                "Avance Meta 80% (%)", format="%.1f%%"
            ),
            "Faltante para Meta": st.column_config.NumberColumn(
                "Faltante para Meta", format="%d"
            ),
            "Renuentes": st.column_config.NumberColumn("Renuentes", format="%d"),
        },
    )

    # Insights de cobertura
    st.subheader("💡 Insights de Cobertura")

    municipios_meta = len(df_coverage[df_coverage["Avance_Meta"] >= 100])
    municipios_alta = len(df_coverage[df_coverage["Cobertura_Real"] >= 60])
    municipio_mejor = df_coverage.iloc[0]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Municipios que Alcanzaron Meta", f"{municipios_meta}")

    with col2:
        st.metric("Municipios con Cobertura >60%", f"{municipios_alta}")

    with col3:
        st.metric(
            "Mejor Cobertura",
            f"{municipio_mejor['Cobertura_Real']:.1f}%",
            delta=municipio_mejor["Municipio"],
        )


def show_basic_population_analysis(combined_data, COLORS):
    """Muestra análisis básico cuando no hay datos de población"""
    st.subheader("📊 Análisis Básico - Sin Datos de Población")

    st.info(
        "💡 Para análisis de cobertura completo, incluye el archivo de población por municipios"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Individual", f"{combined_data['total_individual']:,}")

    with col2:
        st.metric("Total Barridos", f"{combined_data['total_barridos']:,}")

    with col3:
        st.metric("Total General", f"{combined_data['total_general']:,}")

    # Mostrar distribución por rangos de edad si disponible
    individual_edad = combined_data["individual"]["por_edad"]
    barridos_edad = combined_data["barridos"]["vacunados_barrido"]["por_edad"]

    if individual_edad or barridos_edad:
        st.subheader("📈 Distribución por Rangos de Edad")

        # Combinar datos de edad
        age_data = []
        all_ranges = set(individual_edad.keys()) | set(barridos_edad.keys())

        for rango in sorted(all_ranges):
            individual_count = individual_edad.get(rango, 0)
            barridos_count = barridos_edad.get(rango, 0)

            if individual_count > 0 or barridos_count > 0:
                age_data.append(
                    {
                        "Rango": rango,
                        "Individual": individual_count,
                        "Barridos": barridos_count,
                        "Total": individual_count + barridos_count,
                    }
                )

        if age_data:
            df_age = pd.DataFrame(age_data)

            fig = px.bar(
                df_age,
                x="Rango",
                y=["Individual", "Barridos"],
                title="Distribución por Rango de Edad",
                color_discrete_map={
                    "Individual": COLORS["primary"],
                    "Barridos": COLORS["warning"],
                },
            )

            fig.update_layout(
                plot_bgcolor=COLORS["white"], paper_bgcolor=COLORS["white"], height=400
            )

            st.plotly_chart(fig, use_container_width=True)
