"""
vistas/comparison.py - NUEVA VISTA DE COMPARACIÓN
Vista especializada para comparar períodos pre-emergencia vs emergencia
Compatible con el sistema unificado y división temporal automática
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from src.visualization.charts import create_bar_chart, create_pie_chart


def normalize_comparison_data(df):
    """
    Normaliza los datos para análisis comparativo
    """
    df_clean = df.copy()

    # Columnas a normalizar
    columns_to_clean = [
        "municipio_residencia",
        "sexo",
        "grupo_edad_actual",
        "regimen_afiliacion",
        "nombre_aseguradora",
        "periodo",
    ]

    for col in columns_to_clean:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna("Sin dato")
            df_clean[col] = df_clean[col].replace(
                ["", "nan", "NaN", "null", "NULL"], "Sin dato"
            )

    return df_clean


def calculate_period_metrics(data, cutoff_date):
    """
    Calcula métricas comparativas entre períodos
    """
    if "periodo" not in data.columns:
        st.warning("⚠️ Columna 'periodo' no encontrada en los datos")
        return None

    # Separar por períodos
    pre_emergency = data[data["periodo"] == "pre_emergencia"]
    emergency = data[data["periodo"] == "emergencia"]

    # Calcular métricas básicas
    metrics = {
        "cutoff_date": cutoff_date,
        "pre_emergency": {
            "count": len(pre_emergency),
            "start_date": (
                pre_emergency["fecha_vacunacion"].min()
                if "fecha_vacunacion" in pre_emergency.columns
                else None
            ),
            "end_date": (
                pre_emergency["fecha_vacunacion"].max()
                if "fecha_vacunacion" in pre_emergency.columns
                else None
            ),
            "municipalities": (
                pre_emergency["municipio_residencia"].nunique()
                if "municipio_residencia" in pre_emergency.columns
                else 0
            ),
            "daily_avg": 0,
        },
        "emergency": {
            "count": len(emergency),
            "start_date": (
                emergency["fecha_vacunacion"].min()
                if "fecha_vacunacion" in emergency.columns
                else None
            ),
            "end_date": (
                emergency["fecha_vacunacion"].max()
                if "fecha_vacunacion" in emergency.columns
                else None
            ),
            "municipalities": (
                emergency["municipio_residencia"].nunique()
                if "municipio_residencia" in emergency.columns
                else 0
            ),
            "daily_avg": 0,
        },
    }

    # Calcular promedios diarios
    if metrics["pre_emergency"]["start_date"] and metrics["pre_emergency"]["end_date"]:
        days_pre = (
            metrics["pre_emergency"]["end_date"]
            - metrics["pre_emergency"]["start_date"]
        ).days + 1
        if days_pre > 0:
            metrics["pre_emergency"]["daily_avg"] = (
                metrics["pre_emergency"]["count"] / days_pre
            )

    if metrics["emergency"]["start_date"] and metrics["emergency"]["end_date"]:
        days_emergency = (
            metrics["emergency"]["end_date"] - metrics["emergency"]["start_date"]
        ).days + 1
        if days_emergency > 0:
            metrics["emergency"]["daily_avg"] = (
                metrics["emergency"]["count"] / days_emergency
            )

    return metrics, pre_emergency, emergency


def create_comparison_timeline(data, cutoff_date, colors):
    """
    Crea línea temporal comparativa
    """
    if "fecha_vacunacion" not in data.columns:
        return None

    # Crear serie temporal diaria
    daily_data = (
        data.groupby(
            [
                data["fecha_vacunacion"].dt.date,
                (
                    "periodo"
                    if "periodo" in data.columns
                    else pd.Series(["sin_periodo"] * len(data))
                ),
            ]
        )
        .size()
        .reset_index()
    )

    daily_data.columns = ["fecha", "periodo", "count"]
    daily_data["fecha"] = pd.to_datetime(daily_data["fecha"])

    # Crear gráfico
    fig = go.Figure()

    # Línea para período pre-emergencia
    pre_data = daily_data[daily_data["periodo"] == "pre_emergencia"]
    if len(pre_data) > 0:
        fig.add_trace(
            go.Scatter(
                x=pre_data["fecha"],
                y=pre_data["count"],
                mode="lines+markers",
                name="Pre-emergencia",
                line=dict(color=colors.get("primary", "#7D0F2B"), width=2),
                hovertemplate="%{x}<br>Vacunados: %{y}<extra></extra>",
            )
        )

    # Línea para período emergencia
    emergency_data = daily_data[daily_data["periodo"] == "emergencia"]
    if len(emergency_data) > 0:
        fig.add_trace(
            go.Scatter(
                x=emergency_data["fecha"],
                y=emergency_data["count"],
                mode="lines+markers",
                name="Emergencia",
                line=dict(color=colors.get("danger", "#E51937"), width=2),
                hovertemplate="%{x}<br>Vacunados: %{y}<extra></extra>",
            )
        )

    # Línea vertical en fecha de corte
    if cutoff_date:
        fig.add_vline(
            x=cutoff_date,
            line_dash="dash",
            line_color="gray",
            annotation_text="Inicio Emergencia",
            annotation_position="top",
        )

    fig.update_layout(
        title="Evolución Temporal: Pre-emergencia vs Emergencia",
        xaxis_title="Fecha",
        yaxis_title="Vacunados por Día",
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=500,
        hovermode="x unified",
    )

    return fig


def create_demographic_comparison(
    pre_data, emergency_data, demographic_col, title, colors
):
    """
    Crea comparación demográfica entre períodos
    """
    if (
        demographic_col not in pre_data.columns
        or demographic_col not in emergency_data.columns
    ):
        return None

    # Contar por categoría demográfica
    pre_counts = pre_data[demographic_col].value_counts().reset_index()
    pre_counts.columns = [demographic_col, "count"]
    pre_counts["periodo"] = "Pre-emergencia"
    pre_counts["percentage"] = (
        pre_counts["count"] / pre_counts["count"].sum() * 100
    ).round(1)

    emergency_counts = emergency_data[demographic_col].value_counts().reset_index()
    emergency_counts.columns = [demographic_col, "count"]
    emergency_counts["periodo"] = "Emergencia"
    emergency_counts["percentage"] = (
        emergency_counts["count"] / emergency_counts["count"].sum() * 100
    ).round(1)

    # Combinar datos
    combined_data = pd.concat([pre_counts, emergency_counts], ignore_index=True)

    # Tomar top categorías para evitar saturación visual
    top_categories = (
        combined_data.groupby(demographic_col)["count"].sum().nlargest(8).index
    )
    filtered_data = combined_data[combined_data[demographic_col].isin(top_categories)]

    # Crear gráfico de barras agrupadas
    fig = px.bar(
        filtered_data,
        x=demographic_col,
        y="percentage",
        color="periodo",
        title=title,
        labels={
            "percentage": "Porcentaje (%)",
            demographic_col: demographic_col.replace("_", " ").title(),
        },
        height=400,
        barmode="group",
        color_discrete_map={
            "Pre-emergencia": colors.get("primary", "#7D0F2B"),
            "Emergencia": colors.get("danger", "#E51937"),
        },
    )

    fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", xaxis_tickangle=45)

    return fig


def create_intensity_heatmap(pre_data, emergency_data, colors):
    """
    Crea mapa de calor de intensidad por municipio
    """
    if (
        "municipio_residencia" not in pre_data.columns
        or "municipio_residencia" not in emergency_data.columns
    ):
        return None

    # Contar por municipio
    pre_by_mun = pre_data["municipio_residencia"].value_counts().reset_index()
    pre_by_mun.columns = ["municipio", "pre_count"]

    emergency_by_mun = (
        emergency_data["municipio_residencia"].value_counts().reset_index()
    )
    emergency_by_mun.columns = ["municipio", "emergency_count"]

    # Combinar y calcular ratios
    combined = pd.merge(
        pre_by_mun, emergency_by_mun, on="municipio", how="outer"
    ).fillna(0)
    combined["total"] = combined["pre_count"] + combined["emergency_count"]
    combined["emergency_ratio"] = np.where(
        combined["total"] > 0, combined["emergency_count"] / combined["total"], 0
    )
    combined["change_factor"] = np.where(
        combined["pre_count"] > 0,
        combined["emergency_count"] / combined["pre_count"],
        np.inf if combined["emergency_count"] > 0 else 0,
    )

    # Tomar top 15 municipios por total
    top_municipalities = combined.nlargest(15, "total")

    # Preparar datos para heatmap
    heatmap_data = (
        top_municipalities[["municipio", "pre_count", "emergency_count"]]
        .set_index("municipio")
        .T
    )

    # Crear heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=["Pre-emergencia", "Emergencia"],
            colorscale="RdYlBu_r",
            hovertemplate="Municipio: %{x}<br>Período: %{y}<br>Vacunados: %{z}<extra></extra>",
            colorbar=dict(title="Número de Vacunados"),
        )
    )

    fig.update_layout(
        title="Intensidad de Vacunación por Municipio y Período",
        height=400,
        xaxis_tickangle=45,
    )

    return fig


def create_efficiency_analysis(metrics, colors):
    """
    Crea análisis de eficiencia comparativa
    """
    # Preparar datos para visualización
    periods = ["Pre-emergencia", "Emergencia"]
    counts = [metrics["pre_emergency"]["count"], metrics["emergency"]["count"]]
    daily_avgs = [
        metrics["pre_emergency"]["daily_avg"],
        metrics["emergency"]["daily_avg"],
    ]
    municipalities = [
        metrics["pre_emergency"]["municipalities"],
        metrics["emergency"]["municipalities"],
    ]

    # Crear subplots
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Total Vacunados",
            "Promedio Diario",
            "Municipios Activos",
            "Eficiencia Territorial",
        ),
        specs=[
            [{"type": "bar"}, {"type": "bar"}],
            [{"type": "bar"}, {"type": "scatter"}],
        ],
    )

    # Total vacunados
    fig.add_trace(
        go.Bar(
            x=periods,
            y=counts,
            name="Total",
            marker_color=[
                colors.get("primary", "#7D0F2B"),
                colors.get("danger", "#E51937"),
            ],
        ),
        row=1,
        col=1,
    )

    # Promedio diario
    fig.add_trace(
        go.Bar(
            x=periods,
            y=daily_avgs,
            name="Diario",
            marker_color=[
                colors.get("secondary", "#F2A900"),
                colors.get("warning", "#F7941D"),
            ],
        ),
        row=1,
        col=2,
    )

    # Municipios activos
    fig.add_trace(
        go.Bar(
            x=periods,
            y=municipalities,
            name="Municipios",
            marker_color=[
                colors.get("success", "#509E2F"),
                colors.get("accent", "#5A4214"),
            ],
        ),
        row=2,
        col=1,
    )

    # Eficiencia territorial (vacunados por municipio)
    efficiency = [
        counts[i] / municipalities[i] if municipalities[i] > 0 else 0 for i in range(2)
    ]
    fig.add_trace(
        go.Scatter(
            x=periods,
            y=efficiency,
            mode="lines+markers",
            name="Eficiencia",
            line=dict(color=colors.get("info", "#17a2b8"), width=3),
            marker=dict(size=10),
        ),
        row=2,
        col=2,
    )

    fig.update_layout(
        height=600, showlegend=False, title_text="Análisis de Eficiencia Comparativa"
    )

    return fig


def show(data, filters, colors, fuente_poblacion="EAPB"):
    """
    Vista principal de comparación pre-emergencia vs emergencia

    Args:
        data (dict): Diccionario con los dataframes del sistema unificado
        filters (dict): Filtros seleccionados
        colors (dict): Colores institucionales
        fuente_poblacion (str): Fuente de datos de población (nuevo sistema usa EAPB)
    """
    st.title("🔄 Comparación Pre-emergencia vs Emergencia")

    st.markdown(
        """
    Esta vista compara los dos períodos de vacunación identificados automáticamente por el sistema:
    - **Pre-emergencia:** Vacunación regular antes de brigadas
    - **Emergencia:** Vacunación intensiva con brigadas territoriales
    """
    )

    # Verificar que tenemos datos del sistema unificado
    if not data or "vacunacion_unificada" not in data:
        st.error("❌ Esta vista requiere datos del sistema unificado")
        st.info("🔄 Asegúrate de que el sistema unificado esté cargado correctamente")
        return

    # Obtener datos unificados
    unified_data = data["vacunacion_unificada"]
    metadata = data.get("metadata", {})
    cutoff_date = metadata.get("cutoff_date")

    if unified_data is None or len(unified_data) == 0:
        st.warning("⚠️ No hay datos de vacunación unificados para comparar")
        return

    # Normalizar datos
    unified_data = normalize_comparison_data(unified_data)

    # Verificar que tenemos datos de ambos períodos
    if "periodo" not in unified_data.columns:
        st.error("❌ Los datos no contienen información de períodos")
        st.info(
            "💡 Esta vista requiere que el sistema de combinación de datos esté funcionando"
        )
        return

    # Información de fecha de corte
    if cutoff_date:
        st.info(
            f"📅 **Fecha de corte automática:** {cutoff_date.strftime('%d de %B de %Y')}"
        )
    else:
        st.warning("⚠️ Fecha de corte no disponible")

    # Calcular métricas comparativas
    result = calculate_period_metrics(unified_data, cutoff_date)
    if result is None:
        return

    metrics, pre_emergency, emergency = result

    # =====================================================================
    # SECCIÓN 1: MÉTRICAS PRINCIPALES DE COMPARACIÓN
    # =====================================================================
    st.subheader("📊 Métricas Principales de Comparación")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        pre_count = metrics["pre_emergency"]["count"]
        emergency_count = metrics["emergency"]["count"]
        total_count = pre_count + emergency_count

        pre_percentage = (pre_count / total_count * 100) if total_count > 0 else 0

        st.metric(
            "Pre-emergencia",
            f"{pre_count:,}".replace(",", "."),
            delta=f"{pre_percentage:.1f}% del total",
        )

    with col2:
        emergency_percentage = (
            (emergency_count / total_count * 100) if total_count > 0 else 0
        )

        st.metric(
            "Emergencia",
            f"{emergency_count:,}".replace(",", "."),
            delta=f"{emergency_percentage:.1f}% del total",
        )

    with col3:
        pre_daily = metrics["pre_emergency"]["daily_avg"]
        emergency_daily = metrics["emergency"]["daily_avg"]

        if pre_daily > 0:
            daily_increase = (emergency_daily - pre_daily) / pre_daily * 100
            delta_text = f"{daily_increase:+.1f}% vs pre-emergencia"
        else:
            delta_text = "Nueva actividad"

        st.metric(
            "Promedio Diario (Emergencia)", f"{emergency_daily:.1f}", delta=delta_text
        )

    with col4:
        pre_municipalities = metrics["pre_emergency"]["municipalities"]
        emergency_municipalities = metrics["emergency"]["municipalities"]

        if pre_municipalities > 0:
            mun_change = emergency_municipalities - pre_municipalities
            delta_text = f"{mun_change:+d} municipios"
        else:
            delta_text = f"{emergency_municipalities} municipios"

        st.metric(
            "Municipios (Emergencia)", f"{emergency_municipalities}", delta=delta_text
        )

    # =====================================================================
    # SECCIÓN 2: LÍNEA TEMPORAL COMPARATIVA
    # =====================================================================
    st.subheader("📈 Evolución Temporal Comparativa")

    timeline_fig = create_comparison_timeline(unified_data, cutoff_date, colors)
    if timeline_fig:
        st.plotly_chart(timeline_fig, use_container_width=True)

        # Análisis de la evolución
        if pre_emergency["daily_avg"] > 0 and emergency_daily > 0:
            acceleration_factor = emergency_daily / pre_emergency["daily_avg"]

            if acceleration_factor > 2:
                st.success(
                    f"🚀 **Aceleración significativa:** {acceleration_factor:.1f}x más vacunación diaria en emergencia"
                )
            elif acceleration_factor > 1.5:
                st.info(
                    f"📈 **Incremento moderado:** {acceleration_factor:.1f}x más vacunación diaria en emergencia"
                )
            elif acceleration_factor < 0.8:
                st.warning(
                    f"📉 **Desaceleración:** {acceleration_factor:.1f}x vacunación diaria en emergencia"
                )
            else:
                st.info(
                    f"➡️ **Ritmo similar:** {acceleration_factor:.1f}x vacunación diaria en emergencia"
                )
    else:
        st.warning("⚠️ No se pudo generar la línea temporal comparativa")

    # =====================================================================
    # SECCIÓN 3: ANÁLISIS DEMOGRÁFICO COMPARATIVO
    # =====================================================================
    st.subheader("👥 Análisis Demográfico Comparativo")

    # Selector de análisis demográfico
    demographic_options = []
    demographic_mapping = {
        "Género": "sexo",
        "Grupo de Edad": "grupo_edad_actual",
        "Régimen": "regimen_afiliacion",
        "EAPB/Aseguradora": "nombre_aseguradora",
    }

    # Verificar qué columnas están disponibles
    for label, col in demographic_mapping.items():
        if col in unified_data.columns:
            demographic_options.append(label)

    if demographic_options:
        selected_demographic = st.selectbox(
            "Selecciona el análisis demográfico:", demographic_options
        )

        demographic_col = demographic_mapping[selected_demographic]

        # Crear gráfico comparativo
        demo_fig = create_demographic_comparison(
            pre_emergency,
            emergency,
            demographic_col,
            f"Comparación por {selected_demographic}",
            colors,
        )

        if demo_fig:
            st.plotly_chart(demo_fig, use_container_width=True)

            # Análisis automático de cambios demográficos
            pre_demo = pre_emergency[demographic_col].value_counts(normalize=True) * 100
            emergency_demo = (
                emergency_data[demographic_col].value_counts(normalize=True) * 100
            )

            # Encontrar los cambios más significativos
            demo_changes = []
            for category in pre_demo.index:
                if category in emergency_demo.index:
                    change = emergency_demo[category] - pre_demo[category]
                    if abs(change) > 5:  # Cambios > 5%
                        demo_changes.append((category, change))

            if demo_changes:
                st.markdown("**Cambios demográficos significativos:**")
                for category, change in sorted(
                    demo_changes, key=lambda x: abs(x[1]), reverse=True
                )[:3]:
                    direction = "📈" if change > 0 else "📉"
                    st.write(
                        f"- {direction} **{category}:** {change:+.1f} puntos porcentuales"
                    )
        else:
            st.warning(f"⚠️ No se pudo generar comparación para {selected_demographic}")

    # =====================================================================
    # SECCIÓN 4: ANÁLISIS TERRITORIAL COMPARATIVO
    # =====================================================================
    st.subheader("🗺️ Análisis Territorial Comparativo")

    col1, col2 = st.columns(2)

    with col1:
        # Mapa de calor de intensidad
        heatmap_fig = create_intensity_heatmap(pre_emergency, emergency, colors)
        if heatmap_fig:
            st.plotly_chart(heatmap_fig, use_container_width=True)
        else:
            st.info("📊 Datos territoriales insuficientes para mapa de calor")

    with col2:
        # Top municipios con mayor cambio
        if "municipio_residencia" in unified_data.columns:
            pre_by_mun = pre_emergency["municipio_residencia"].value_counts()
            emergency_by_mun = emergency_data["municipio_residencia"].value_counts()

            # Calcular cambios
            all_municipalities = set(pre_by_mun.index) | set(emergency_by_mun.index)
            changes = []

            for municipality in all_municipalities:
                pre_count = pre_by_mun.get(municipality, 0)
                emergency_count = emergency_by_mun.get(municipality, 0)

                if pre_count > 0:
                    change_factor = emergency_count / pre_count
                    absolute_change = emergency_count - pre_count
                else:
                    change_factor = float("inf") if emergency_count > 0 else 0
                    absolute_change = emergency_count

                changes.append(
                    {
                        "municipio": municipality,
                        "pre_count": pre_count,
                        "emergency_count": emergency_count,
                        "change_factor": change_factor,
                        "absolute_change": absolute_change,
                    }
                )

            # Top municipios por cambio absoluto
            changes_df = pd.DataFrame(changes)
            top_changes = changes_df.nlargest(10, "absolute_change")

            if len(top_changes) > 0:
                fig_changes = px.bar(
                    top_changes,
                    x="municipio",
                    y="absolute_change",
                    title="Top 10 Municipios por Incremento Absoluto",
                    color="absolute_change",
                    color_continuous_scale="RdYlGn",
                    height=400,
                )

                fig_changes.update_layout(
                    xaxis_tickangle=45, plot_bgcolor="white", paper_bgcolor="white"
                )

                st.plotly_chart(fig_changes, use_container_width=True)

    # =====================================================================
    # SECCIÓN 5: ANÁLISIS DE EFICIENCIA COMPARATIVA
    # =====================================================================
    st.subheader("⚡ Análisis de Eficiencia Comparativa")

    efficiency_fig = create_efficiency_analysis(metrics, colors)
    if efficiency_fig:
        st.plotly_chart(efficiency_fig, use_container_width=True)

    # =====================================================================
    # SECCIÓN 6: INSIGHTS Y RECOMENDACIONES
    # =====================================================================
    st.markdown("---")
    st.subheader("💡 Insights Clave de la Comparación")

    insights = []

    # Insight sobre efectividad de la emergencia
    if metrics["emergency"]["count"] > 0 and metrics["pre_emergency"]["count"] > 0:
        emergency_effectiveness = (
            metrics["emergency"]["count"] / metrics["pre_emergency"]["count"]
        )

        if emergency_effectiveness > 2:
            insights.append(
                "🎯 **Emergencia muy efectiva:** Más del doble de vacunación que período regular"
            )
        elif emergency_effectiveness > 1.5:
            insights.append(
                "✅ **Emergencia efectiva:** 50% más vacunación que período regular"
            )
        elif emergency_effectiveness < 0.8:
            insights.append(
                "⚠️ **Eficiencia reducida:** Menor vacunación en emergencia vs período regular"
            )

    # Insight sobre velocidad de respuesta
    if metrics["emergency"]["daily_avg"] > metrics["pre_emergency"]["daily_avg"] * 1.5:
        insights.append(
            "🚀 **Respuesta rápida:** Ritmo diario significativamente acelerado en emergencia"
        )

    # Insight sobre cobertura territorial
    if (
        metrics["emergency"]["municipalities"]
        > metrics["pre_emergency"]["municipalities"]
    ):
        new_municipalities = (
            metrics["emergency"]["municipalities"]
            - metrics["pre_emergency"]["municipalities"]
        )
        insights.append(
            f"🗺️ **Expansión territorial:** {new_municipalities} municipios adicionales en emergencia"
        )

    # Insight sobre sostenibilidad
    if len(emergency) > 0 and "fecha_vacunacion" in emergency.columns:
        emergency_duration = (
            emergency["fecha_vacunacion"].max() - emergency["fecha_vacunacion"].min()
        ).days
        if emergency_duration > 0:
            emergency_intensity = len(emergency) / emergency_duration
            if emergency_intensity > metrics["pre_emergency"]["daily_avg"] * 3:
                insights.append(
                    "⚡ **Alta intensidad:** Ritmo de emergencia podría ser insostenible a largo plazo"
                )

    # Mostrar insights
    if insights:
        for insight in insights:
            st.markdown(f"- {insight}")
    else:
        st.info(
            "📊 Ambos períodos muestran patrones similares sin diferencias significativas"
        )

    # Información del sistema unificado
    st.markdown("---")
    st.info(
        f"""
    **ℹ️ Información del Sistema Unificado:**
    - **Fuente de población:** {fuente_poblacion} (Abril 2025)
    - **División temporal:** Automática basada en fecha más antigua de brigadas
    - **Edades:** Calculadas a fecha actual (no momento de vacunación)
    - **Total registros procesados:** {len(unified_data):,}".replace(",", ".")
    """
    )
