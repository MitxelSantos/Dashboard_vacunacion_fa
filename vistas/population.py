"""
vistas/population.py - Análisis poblacional con normalización de municipios
VERSIÓN CORREGIDA - Maneja diferentes formatos de nombres
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import unicodedata
import re


def normalize_municipality_name(name):
    """
    Normaliza nombres de municipios para hacer matching
    - Extrae nombre del formato 'CÓDIGO - NOMBRE'
    - Elimina acentos y caracteres especiales
    - Convierte a mayúsculas
    """
    if pd.isna(name):
        return None

    name_str = str(name).strip()

    # Si tiene formato 'CÓDIGO - NOMBRE', extraer solo el nombre
    if " - " in name_str:
        name_str = name_str.split(" - ", 1)[1]

    # Eliminar acentos y normalizar
    normalized = unicodedata.normalize("NFD", name_str)
    normalized = "".join(c for c in normalized if unicodedata.category(c) != "Mn")

    # Limpiar y convertir a mayúsculas
    normalized = re.sub(r"[^\w\s]", "", normalized)
    normalized = normalized.upper().strip()

    return normalized


def create_municipality_mapping(population_dict, vaccination_dict):
    """
    Crea mapeo entre nombres de municipios de población y vacunación
    """
    mapping = {}

    # Normalizar nombres de población
    pop_normalized = {}
    for pop_name in population_dict.keys():
        norm_name = normalize_municipality_name(pop_name)
        if norm_name:
            pop_normalized[norm_name] = pop_name

    # Normalizar nombres de vacunación y crear mapping
    for vac_name in vaccination_dict.keys():
        norm_name = normalize_municipality_name(vac_name)
        if norm_name and norm_name in pop_normalized:
            pop_original = pop_normalized[norm_name]
            mapping[pop_original] = vac_name

    return mapping


def show_population_tab(combined_data, COLORS):
    """Muestra análisis poblacional con normalización de municipios"""
    st.header("🏘️ Análisis Poblacional por Municipios")

    # Verificar si tenemos datos de población
    if not combined_data["population"]["por_municipio"]:
        st.info("📊 **Sin archivo de población** - Mostrando análisis básico")
        show_basic_population_analysis(combined_data, COLORS)
        return

    # Calcular datos de cobertura por municipio
    coverage_data = calculate_municipal_coverage(combined_data)

    if not coverage_data:
        st.error("❌ **Error al calcular cobertura municipal**")
        st.info("Mostrando análisis básico como respaldo")
        show_basic_population_analysis(combined_data, COLORS)
        return

    st.success(
        f"✅ **Datos de cobertura calculados para {len(coverage_data)} municipios**"
    )

    # Mostrar información de normalización
    with st.expander("🔧 Ver detalles de normalización de municipios"):
        show_normalization_details(combined_data)

    # Mostrar métricas principales
    show_main_metrics(combined_data, coverage_data, COLORS)

    # Mostrar distribución poblacional
    show_population_distribution(coverage_data, COLORS)

    # Mostrar análisis de cobertura
    show_coverage_analysis(coverage_data, COLORS)


def show_normalization_details(combined_data):
    """Muestra detalles del proceso de normalización"""
    population_by_mun = combined_data["population"]["por_municipio"]
    individual_by_mun = combined_data["individual_pre"]["por_municipio"]
    barridos_by_mun = combined_data["barridos"]["vacunados_barrido"]["por_municipio"]

    # Crear mappings
    individual_mapping = create_municipality_mapping(
        population_by_mun, individual_by_mun
    )
    barridos_mapping = create_municipality_mapping(population_by_mun, barridos_by_mun)

    st.write(f"**📊 Resultados de normalización:**")
    st.write(f"- Municipios en población: {len(population_by_mun)}")
    st.write(f"- Coincidencias con individual: {len(individual_mapping)}")
    st.write(f"- Coincidencias con barridos: {len(barridos_mapping)}")

    # Mostrar ejemplos de mapping
    st.write("**🔄 Ejemplos de normalización:**")
    for i, (pop_name, vac_name) in enumerate(list(individual_mapping.items())[:5]):
        st.write(f"{i+1}. `{pop_name}` → `{vac_name}`")

    # Municipios sin coincidencia
    all_mappings = set(individual_mapping.keys()) | set(barridos_mapping.keys())
    sin_datos = set(population_by_mun.keys()) - all_mappings

    if sin_datos:
        st.write(f"**⚠️ Municipios sin datos de vacunación ({len(sin_datos)}):**")
        for municipio in list(sin_datos)[:5]:
            st.write(f"- {municipio}")


def calculate_municipal_coverage(combined_data):
    """Calcula cobertura real por municipio con normalización"""
    population_by_mun = combined_data["population"]["por_municipio"]
    individual_by_mun = combined_data["individual_pre"]["por_municipio"]
    barridos_by_mun = combined_data["barridos"]["vacunados_barrido"]["por_municipio"]
    renuentes_by_mun = combined_data["barridos"]["renuentes"]["por_municipio"]

    # Crear mappings de nombres normalizados
    individual_mapping = create_municipality_mapping(
        population_by_mun, individual_by_mun
    )
    barridos_mapping = create_municipality_mapping(population_by_mun, barridos_by_mun)
    renuentes_mapping = create_municipality_mapping(population_by_mun, renuentes_by_mun)

    coverage_data = []

    for municipio_pob, poblacion_asegurada in population_by_mun.items():
        # Obtener nombres correspondientes en vacunación usando mapping
        municipio_individual = individual_mapping.get(municipio_pob)
        municipio_barridos = barridos_mapping.get(municipio_pob)
        municipio_renuentes = renuentes_mapping.get(municipio_pob)

        # Contar vacunados del municipio (combinación temporal sin duplicados)
        individual_count = (
            individual_by_mun.get(municipio_individual, 0)
            if municipio_individual
            else 0
        )
        barridos_count = (
            barridos_by_mun.get(municipio_barridos, 0) if municipio_barridos else 0
        )
        renuentes_count = (
            renuentes_by_mun.get(municipio_renuentes, 0) if municipio_renuentes else 0
        )

        # Manejar valores numpy
        if hasattr(barridos_count, "item"):
            barridos_count = int(barridos_count.item())
        if hasattr(renuentes_count, "item"):
            renuentes_count = int(renuentes_count.item())

        total_vacunados = individual_count + barridos_count

        # Solo procesar municipios con población válida
        if poblacion_asegurada > 0:
            # Calcular métricas
            cobertura_real = (total_vacunados / poblacion_asegurada) * 100
            meta_80 = poblacion_asegurada * 0.8
            avance_meta = (total_vacunados / meta_80) * 100 if meta_80 > 0 else 0
            faltante_meta = max(0, meta_80 - total_vacunados)

            # Calcular tasa de contacto y aceptación
            total_contactados = total_vacunados + renuentes_count
            tasa_contacto = (total_contactados / poblacion_asegurada) * 100
            tasa_aceptacion = (
                (total_vacunados / total_contactados) * 100
                if total_contactados > 0
                else 0
            )

            coverage_data.append(
                {
                    "Municipio": municipio_pob,  # Usar nombre original de población
                    "Municipio_Display": (
                        municipio_pob.split(" - ")[1]
                        if " - " in municipio_pob
                        else municipio_pob
                    ),
                    "Poblacion_Asegurada": poblacion_asegurada,
                    "PRE_Emergencia": individual_count,
                    "DURANTE_Emergencia": barridos_count,
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
    total_vacunados = combined_data["total_real_combinado"]
    total_renuentes = combined_data["total_renuentes"]

    with col1:
        st.metric("Población Asegurada Total", f"{total_poblacion:,}")

    with col2:
        cobertura_general = (
            (total_vacunados / total_poblacion) * 100 if total_poblacion > 0 else 0
        )
        st.metric("Cobertura Real General", f"{cobertura_general:.1f}%")

    with col3:
        meta_general = total_poblacion * 0.8
        avance_general = (
            (total_vacunados / meta_general) * 100 if meta_general > 0 else 0
        )
        st.metric("Avance Meta 80%", f"{avance_general:.1f}%")

    with col4:
        municipios_count = len(coverage_data)
        municipios_con_datos = len(
            [d for d in coverage_data if d["Total_Vacunados"] > 0]
        )
        st.metric("Municipios con Datos", f"{municipios_con_datos}/{municipios_count}")

    # Información adicional sobre la lógica
    st.info(
        f"💡 **Cobertura calculada con normalización de nombres:** "
        f"PRE-emergencia ({combined_data['total_individual_pre']:,}) + "
        f"DURANTE emergencia ({combined_data['total_barridos']:,}) = "
        f"Total Real ({total_vacunados:,})"
    )


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
            y="Municipio_Display",
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
    """Muestra análisis de cobertura temporal"""
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
            x=df_coverage["Municipio_Display"][:20],  # Top 20
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

    # Análisis temporal de cobertura
    st.subheader("⏰ Análisis Temporal de Cobertura")

    # Gráfico de barras apiladas temporal - solo municipios con datos
    df_con_datos = df_coverage[df_coverage["Total_Vacunados"] > 0].head(15)

    if not df_con_datos.empty:
        fig_temporal = go.Figure()

        fig_temporal.add_trace(
            go.Bar(
                name="PRE-Emergencia",
                x=df_con_datos["Municipio_Display"],
                y=[
                    (pre / pob) * 100 if pob > 0 else 0
                    for pre, pob in zip(
                        df_con_datos["PRE_Emergencia"],
                        df_con_datos["Poblacion_Asegurada"],
                    )
                ],
                marker_color=COLORS["primary"],
            )
        )

        fig_temporal.add_trace(
            go.Bar(
                name="DURANTE Emergencia",
                x=df_con_datos["Municipio_Display"],
                y=[
                    (durante / pob) * 100 if pob > 0 else 0
                    for durante, pob in zip(
                        df_con_datos["DURANTE_Emergencia"],
                        df_con_datos["Poblacion_Asegurada"],
                    )
                ],
                marker_color=COLORS["warning"],
            )
        )

        fig_temporal.update_layout(
            title="Cobertura por Período Temporal - Top 15 Municipios con Datos",
            xaxis_title="Municipio",
            yaxis_title="Cobertura (%)",
            barmode="stack",
            plot_bgcolor=COLORS["white"],
            paper_bgcolor=COLORS["white"],
            height=400,
            xaxis={"tickangle": 45},
        )

        st.plotly_chart(fig_temporal, use_container_width=True)
    else:
        st.warning("⚠️ No hay municipios con datos de vacunación para mostrar")

    # Tabla detallada
    st.subheader("📋 Detalle de Cobertura por Municipios")

    # Preparar tabla con métricas claras
    tabla_display = df_coverage[
        [
            "Municipio_Display",
            "Poblacion_Asegurada",
            "PRE_Emergencia",
            "DURANTE_Emergencia",
            "Total_Vacunados",
            "Cobertura_Real",
            "Avance_Meta",
            "Renuentes",
        ]
    ].copy()

    # Redondear valores
    tabla_display["Cobertura_Real"] = tabla_display["Cobertura_Real"].round(1)
    tabla_display["Avance_Meta"] = tabla_display["Avance_Meta"].round(1)

    # Renombrar columnas para claridad
    tabla_display = tabla_display.rename(
        columns={
            "Municipio_Display": "Municipio",
            "Poblacion_Asegurada": "Población Asegurada",
            "PRE_Emergencia": "PRE-Emergencia",
            "DURANTE_Emergencia": "DURANTE Emergencia",
            "Total_Vacunados": "Total Vacunados",
            "Cobertura_Real": "Cobertura Real (%)",
            "Avance_Meta": "Avance Meta 80% (%)",
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
            "PRE-Emergencia": st.column_config.NumberColumn(
                "PRE-Emergencia", format="%d"
            ),
            "DURANTE Emergencia": st.column_config.NumberColumn(
                "DURANTE Emergencia", format="%d"
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
            "Renuentes": st.column_config.NumberColumn("Renuentes", format="%d"),
        },
        hide_index=True,
    )

    # Insights de cobertura
    st.subheader("💡 Insights de Cobertura")

    municipios_meta = len(df_coverage[df_coverage["Avance_Meta"] >= 100])
    municipios_alta = len(df_coverage[df_coverage["Cobertura_Real"] >= 60])
    municipio_mejor = df_coverage.iloc[0]
    municipios_con_datos = len(df_coverage[df_coverage["Total_Vacunados"] > 0])

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Alcanzaron Meta 80%", f"{municipios_meta}")

    with col2:
        st.metric("Cobertura >60%", f"{municipios_alta}")

    with col3:
        st.metric("Con Datos Vacunación", f"{municipios_con_datos}")

    with col4:
        st.metric(
            "Mejor Cobertura",
            f"{municipio_mejor['Cobertura_Real']:.1f}%",
            delta=municipio_mejor["Municipio_Display"],
        )


def show_basic_population_analysis(combined_data, COLORS):
    """Muestra análisis básico cuando no hay datos de población"""
    st.subheader("📊 Análisis Básico - Sin Datos de Población")

    st.info(
        "💡 Para análisis de cobertura completo, incluye el archivo `data/Poblacion_aseguramiento.xlsx`"
    )

    # Mostrar datos disponibles
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("PRE-Emergencia", f"{combined_data['total_individual_pre']:,}")

    with col2:
        st.metric("DURANTE Emergencia", f"{combined_data['total_barridos']:,}")

    with col3:
        st.metric("Total Real Combinado", f"{combined_data['total_real_combinado']:,}")

    # Análisis de municipios sin datos poblacionales
    st.subheader("🗺️ Distribución Territorial (Sin Población)")

    individual_municipios = combined_data["individual_pre"]["por_municipio"]
    barridos_municipios = combined_data["barridos"]["vacunados_barrido"][
        "por_municipio"
    ]

    if individual_municipios or barridos_municipios:
        # Combinar municipios
        all_municipios = set(individual_municipios.keys()) | set(
            barridos_municipios.keys()
        )

        municipio_data = []
        for municipio in all_municipios:
            pre_count = individual_municipios.get(municipio, 0)
            durante_count = barridos_municipios.get(municipio, 0)
            total = pre_count + durante_count

            if total > 0:
                municipio_data.append(
                    {
                        "Municipio": municipio,
                        "PRE-Emergencia": pre_count,
                        "DURANTE Emergencia": durante_count,
                        "Total": total,
                    }
                )

        if municipio_data:
            df_municipios = pd.DataFrame(municipio_data)
            df_municipios = df_municipios.sort_values("Total", ascending=False)

            # Top 10 municipios
            top_10 = df_municipios.head(10)

            fig_municipios = px.bar(
                top_10,
                x="Total",
                y="Municipio",
                orientation="h",
                title="Top 10 Municipios - Total Vacunados (Sin Duplicados)",
                color_discrete_sequence=[COLORS["success"]],
                text="Total",
            )

            fig_municipios.update_traces(
                texttemplate="%{text:,}", textposition="outside"
            )
            fig_municipios.update_layout(
                plot_bgcolor=COLORS["white"],
                paper_bgcolor=COLORS["white"],
                height=400,
                yaxis={"categoryorder": "total ascending"},
            )

            st.plotly_chart(fig_municipios, use_container_width=True)
        else:
            st.warning("⚠️ No hay datos municipales para mostrar")
    else:
        st.warning("⚠️ No hay datos de municipios disponibles")
