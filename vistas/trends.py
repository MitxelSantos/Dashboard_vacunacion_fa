import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from src.visualization.charts import create_line_chart, create_bar_chart
from datetime import datetime, timedelta


def normalize_temporal_data(df):
    """
    Normaliza los datos temporales reemplazando valores NaN con "Sin dato"
    """
    df_clean = df.copy()
    
    # Normalizar columnas relevantes para análisis temporal
    temporal_columns = ['NombreMunicipioResidencia', 'Sexo', 'Grupo_Edad', 'RegimenAfiliacion']
    
    for col in temporal_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna("Sin dato")
            df_clean[col] = df_clean[col].replace(["", "nan", "NaN", "null", "NULL"], "Sin dato")
    
    return df_clean


def calculate_moving_averages(data, window_size=7):
    """
    Calcula promedios móviles para suavizar las tendencias
    """
    if len(data) < window_size:
        return data
    
    return data.rolling(window=window_size, center=True).mean()


def detect_trends_and_patterns(daily_data):
    """
    Detecta tendencias y patrones en los datos diarios de vacunación
    """
    if len(daily_data) < 7:
        return {}
    
    # Calcular tendencia general (regresión linear)
    x = np.arange(len(daily_data))
    y = daily_data['Vacunados'].values
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    # Detectar picos y valles
    # Calcular percentiles para identificar valores atípicos
    q75 = daily_data['Vacunados'].quantile(0.75)
    q25 = daily_data['Vacunados'].quantile(0.25)
    iqr = q75 - q25
    upper_bound = q75 + 1.5 * iqr
    lower_bound = q25 - 1.5 * iqr
    
    picos = daily_data[daily_data['Vacunados'] > upper_bound]
    valles = daily_data[daily_data['Vacunados'] < lower_bound]
    
    # Detectar periodos de alta y baja actividad
    promedio = daily_data['Vacunados'].mean()
    std_dev = daily_data['Vacunados'].std()
    
    periodos_altos = daily_data[daily_data['Vacunados'] > (promedio + std_dev)]
    periodos_bajos = daily_data[daily_data['Vacunados'] < (promedio - std_dev)]
    
    return {
        'trend_slope': slope,
        'trend_r_squared': r_value**2,
        'trend_p_value': p_value,
        'picos': picos,
        'valles': valles,
        'periodos_altos': periodos_altos,
        'periodos_bajos': periodos_bajos,
        'promedio': promedio,
        'std_dev': std_dev
    }


def create_advanced_time_series(data, title, colors, show_trend=True, show_anomalies=True):
    """
    Crea una serie temporal avanzada con tendencias y anomalías
    """
    fig = go.Figure()
    
    # Serie principal
    fig.add_trace(go.Scatter(
        x=data['Fecha'],
        y=data['Vacunados'],
        mode='lines+markers',
        name='Vacunados diarios',
        line=dict(color=colors["primary"], width=2),
        marker=dict(size=4),
        hovertemplate='Fecha: %{x}<br>Vacunados: %{y}<extra></extra>'
    ))
    
    # Promedio móvil de 7 días
    if len(data) >= 7:
        promedio_movil = calculate_moving_averages(data['Vacunados'], 7)
        fig.add_trace(go.Scatter(
            x=data['Fecha'],
            y=promedio_movil,
            mode='lines',
            name='Promedio móvil (7 días)',
            line=dict(color=colors["secondary"], width=3, dash='dash'),
            hovertemplate='Fecha: %{x}<br>Promedio: %{y:.1f}<extra></extra>'
        ))
    
    # Añadir línea de tendencia si se solicita
    if show_trend and len(data) >= 7:
        try:
            x_numeric = np.arange(len(data))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_numeric, data['Vacunados'])
            trend_line = slope * x_numeric + intercept
            
            fig.add_trace(go.Scatter(
                x=data['Fecha'],
                y=trend_line,
                mode='lines',
                name=f'Tendencia (R²={r_value**2:.3f})',
                line=dict(color=colors["accent"], width=2, dash='dot'),
                hovertemplate='Fecha: %{x}<br>Tendencia: %{y:.1f}<extra></extra>'
            ))
        except:
            pass
    
    # Detectar y marcar anomalías si se solicita
    if show_anomalies and len(data) >= 14:
        try:
            analysis = detect_trends_and_patterns(data)
            
            # Marcar picos
            if len(analysis['picos']) > 0:
                fig.add_trace(go.Scatter(
                    x=analysis['picos']['Fecha'],
                    y=analysis['picos']['Vacunados'],
                    mode='markers',
                    name='Picos de vacunación',
                    marker=dict(
                        color=colors["success"],
                        size=8,
                        symbol='triangle-up'
                    ),
                    hovertemplate='Pico - Fecha: %{x}<br>Vacunados: %{y}<extra></extra>'
                ))
            
            # Marcar valles
            if len(analysis['valles']) > 0:
                fig.add_trace(go.Scatter(
                    x=analysis['valles']['Fecha'],
                    y=analysis['valles']['Vacunados'],
                    mode='markers',
                    name='Valles de vacunación',
                    marker=dict(
                        color=colors["warning"],
                        size=8,
                        symbol='triangle-down'
                    ),
                    hovertemplate='Valle - Fecha: %{x}<br>Vacunados: %{y}<extra></extra>'
                ))
        except:
            pass
    
    fig.update_layout(
        title=title,
        xaxis_title="Fecha",
        yaxis_title="Número de Vacunados",
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=500,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def show(data, filters, colors, fuente_poblacion="DANE"):
    """
    Muestra la página de tendencias del dashboard.
    VERSIÓN MEJORADA: Análisis temporal avanzado con detección de patrones,
    tendencias estadísticas y proyecciones mejoradas.

    Args:
        data (dict): Diccionario con los dataframes
        filters (dict): Filtros seleccionados
        colors (dict): Colores institucionales
        fuente_poblacion (str): Fuente de datos de población ("DANE" o "SISBEN")
    """
    st.title("Tendencias Temporales")

    # Aplicar filtros a los datos
    from src.data.preprocessor import apply_filters

    filtered_data = apply_filters(data, filters, fuente_poblacion)

    # Normalizar datos temporales
    filtered_data["vacunacion"] = normalize_temporal_data(filtered_data["vacunacion"])

    # Usar directamente FA UNICA como fecha de vacunación
    if "FA UNICA" in filtered_data["vacunacion"].columns:
        try:
            # Convertir a datetime
            filtered_data["vacunacion"]["FechaVacunacion"] = pd.to_datetime(
                filtered_data["vacunacion"]["FA UNICA"], errors="coerce"
            )

            # Filtrar registros con fechas válidas
            fechas_validas = ~filtered_data["vacunacion"]["FechaVacunacion"].isna()
            if fechas_validas.sum() > 0:
                filtered_data["vacunacion"] = filtered_data["vacunacion"][fechas_validas]
                process_temporal_analysis(filtered_data, colors, fuente_poblacion, filters)
            else:
                st.error("No se pudieron obtener fechas válidas de la columna 'FA UNICA'")
        except Exception as e:
            st.error(f"Error al procesar fechas de 'FA UNICA': {str(e)}")
    else:
        st.error("La columna 'FA UNICA' no se encuentra en los datos")


def process_temporal_analysis(filtered_data, colors, fuente_poblacion, filters):
    """
    Procesa los datos temporales y muestra análisis avanzado de tendencias.
    """
    # =====================================================================
    # SECCIÓN 1: RESUMEN TEMPORAL GENERAL
    # =====================================================================
    st.subheader(f"Resumen Temporal (Población {fuente_poblacion})")

    # Calcular estadísticas temporales básicas
    fecha_inicio = filtered_data["vacunacion"]["FechaVacunacion"].min()
    fecha_fin = filtered_data["vacunacion"]["FechaVacunacion"].max()
    dias_campana = (fecha_fin - fecha_inicio).days + 1
    total_vacunados = len(filtered_data["vacunacion"])
    promedio_diario = total_vacunados / dias_campana if dias_campana > 0 else 0

    # Métricas temporales principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Duración de la campaña",
            f"{dias_campana} días",
            delta=f"Del {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}"
        )
    
    with col2:
        st.metric(
            "Promedio diario",
            f"{promedio_diario:.1f} vac/día",
            delta=f"Total: {total_vacunados:,}".replace(",", ".")
        )
    
    with col3:
        # Encontrar el día más activo
        vacunacion_diaria = filtered_data["vacunacion"].groupby(
            filtered_data["vacunacion"]["FechaVacunacion"].dt.date
        ).size()
        
        dia_mas_activo = vacunacion_diaria.idxmax()
        max_vacunados_dia = vacunacion_diaria.max()
        
        st.metric(
            "Día más activo",
            dia_mas_activo.strftime('%d/%m/%Y'),
            delta=f"{max_vacunados_dia} vacunados"
        )
    
    with col4:
        # Calcular eficiencia (vacunados por día hábil, asumiendo 5 días hábiles por semana)
        dias_habiles_aprox = dias_campana * 5/7
        eficiencia = total_vacunados / dias_habiles_aprox if dias_habiles_aprox > 0 else 0
        
        st.metric(
            "Eficiencia estimada",
            f"{eficiencia:.1f} vac/día hábil",
            delta="Lun-Vie"
        )

    # =====================================================================
    # SECCIÓN 2: SERIE TEMPORAL AVANZADA
    # =====================================================================
    st.subheader("📈 Análisis de Serie Temporal Avanzado")

    # Agrupar por fecha y crear serie temporal completa
    vacunacion_diaria = (
        filtered_data["vacunacion"]
        .groupby(filtered_data["vacunacion"]["FechaVacunacion"].dt.date)
        .size()
        .reset_index()
    )
    vacunacion_diaria.columns = ["Fecha", "Vacunados"]
    vacunacion_diaria["Fecha"] = pd.to_datetime(vacunacion_diaria["Fecha"])

    # Calcular acumulados
    vacunacion_diaria["Vacunados_Acumulados"] = vacunacion_diaria["Vacunados"].cumsum()

    # Calcular cobertura acumulada si hay datos de población
    total_poblacion = filtered_data["metricas"][fuente_poblacion].sum()
    if total_poblacion > 0:
        vacunacion_diaria["Cobertura_Acumulada"] = (
            vacunacion_diaria["Vacunados_Acumulados"] / total_poblacion * 100
        ).round(2)

    # Crear gráfico avanzado de serie temporal
    fig_avanzado = create_advanced_time_series(
        vacunacion_diaria,
        "Evolución Diaria de Vacunación con Análisis de Tendencias",
        colors,
        show_trend=True,
        show_anomalies=True
    )
    
    st.plotly_chart(fig_avanzado, use_container_width=True)

    # Análisis estadístico de la serie temporal
    if len(vacunacion_diaria) >= 7:
        analysis = detect_trends_and_patterns(vacunacion_diaria)
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("### 📊 Análisis Estadístico de Tendencias")
            
            # Interpretación de la tendencia
            if analysis['trend_slope'] > 0:
                trend_interpretation = "📈 **Tendencia ascendente**"
                trend_description = f"Incremento promedio de {analysis['trend_slope']:.1f} vacunados por día"
            elif analysis['trend_slope'] < 0:
                trend_interpretation = "📉 **Tendencia descendente**"
                trend_description = f"Decremento promedio de {abs(analysis['trend_slope']):.1f} vacunados por día"
            else:
                trend_interpretation = "➡️ **Tendencia neutral**"
                trend_description = "Sin cambios significativos en el ritmo de vacunación"
            
            # Calidad del ajuste
            r_squared = analysis['trend_r_squared']
            if r_squared > 0.7:
                fit_quality = "Muy buena"
            elif r_squared > 0.4:
                fit_quality = "Moderada"
            else:
                fit_quality = "Baja"
            
            st.info(f"""
            **{trend_interpretation}**
            - {trend_description}
            - Calidad del ajuste: {fit_quality} (R² = {r_squared:.3f})
            - Significancia estadística: {"Significativa" if analysis['trend_p_value'] < 0.05 else "No significativa"}
            """)
        
        with col_right:
            st.markdown("### 🎯 Detección de Patrones")
            
            st.info(f"""
            **Patrones identificados:**
            - Picos de actividad: {len(analysis['picos'])} días
            - Valles de actividad: {len(analysis['valles'])} días
            - Promedio diario: {analysis['promedio']:.1f} vacunados
            - Desviación típica: {analysis['std_dev']:.1f} vacunados
            - Coeficiente de variación: {(analysis['std_dev']/analysis['promedio']*100):.1f}%
            """)

    # =====================================================================
    # SECCIÓN 3: ANÁLISIS POR PERÍODOS
    # =====================================================================
    st.subheader("📅 Análisis por Períodos")

    col1, col2 = st.columns(2)

    # Análisis semanal
    with col1:
        # Extraer día de la semana
        filtered_data["vacunacion"]["DiaSemana"] = filtered_data["vacunacion"]["FechaVacunacion"].dt.day_name()
        
        # Mapear días al español
        dias_mapping = {
            'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
            'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
        }
        filtered_data["vacunacion"]["DiaSemana_ES"] = filtered_data["vacunacion"]["DiaSemana"].map(dias_mapping)
        
        # Agrupar por día de la semana
        vacunacion_semanal = (
            filtered_data["vacunacion"].groupby("DiaSemana_ES").size().reset_index()
        )
        vacunacion_semanal.columns = ["DiaSemana", "Vacunados"]
        
        # Ordenar días de la semana
        orden_dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        vacunacion_semanal["DiaSemana"] = pd.Categorical(
            vacunacion_semanal["DiaSemana"],
            categories=orden_dias,
            ordered=True
        )
        vacunacion_semanal = vacunacion_semanal.sort_values("DiaSemana")
        
        # Crear gráfico
        fig_semanal = create_bar_chart(
            data=vacunacion_semanal,
            x="DiaSemana",
            y="Vacunados",
            title="Distribución por día de la semana",
            color=colors["secondary"],
            height=400,
            filters=None,
        )
        
        st.plotly_chart(fig_semanal, use_container_width=True)
        
        # Análisis de días más activos
        dia_mas_activo = vacunacion_semanal.loc[vacunacion_semanal["Vacunados"].idxmax(), "DiaSemana"]
        dia_menos_activo = vacunacion_semanal.loc[vacunacion_semanal["Vacunados"].idxmin(), "DiaSemana"]
        
        st.info(f"""
        **Análisis semanal:**
        - Día más activo: {dia_mas_activo}
        - Día menos activo: {dia_menos_activo}
        """)

    # Análisis mensual
    with col2:
        # Extraer mes y año
        filtered_data["vacunacion"]["MesAño"] = filtered_data["vacunacion"][
            "FechaVacunacion"
        ].dt.strftime("%Y-%m")

        # Agrupar por mes
        vacunacion_mensual = (
            filtered_data["vacunacion"].groupby("MesAño").size().reset_index()
        )
        vacunacion_mensual.columns = ["MesAño", "Vacunados"]

        # Ordenar por fecha
        vacunacion_mensual = vacunacion_mensual.sort_values("MesAño")

        # Crear gráfico
        fig_mensual = create_bar_chart(
            data=vacunacion_mensual,
            x="MesAño",
            y="Vacunados",
            title="Evolución mensual de vacunación",
            color=colors["accent"],
            height=400,
            filters=None,
        )

        st.plotly_chart(fig_mensual, use_container_width=True)
        
        # Análisis de crecimiento mensual
        if len(vacunacion_mensual) > 1:
            vacunacion_mensual["Crecimiento"] = vacunacion_mensual["Vacunados"].pct_change() * 100
            crecimiento_promedio = vacunacion_mensual["Crecimiento"].mean()
            
            st.info(f"""
            **Análisis mensual:**
            - Crecimiento promedio: {crecimiento_promedio:.1f}% mensual
            - Mejor mes: {vacunacion_mensual.loc[vacunacion_mensual["Vacunados"].idxmax(), "MesAño"]}
            """)

    # =====================================================================
    # SECCIÓN 4: ANÁLISIS DEMOGRÁFICO TEMPORAL
    # =====================================================================
    st.subheader("👥 Análisis Demográfico Temporal")

    # Selector para análisis demográfico
    analisis_demografico_opciones = [
        "Evolución por Género",
        "Evolución por Grupo de Edad", 
        "Evolución por Régimen",
        "Evolución por Municipio (Top 5)"
    ]
    
    analisis_demografico = st.selectbox(
        "Seleccione el análisis demográfico temporal:",
        analisis_demografico_opciones
    )

    try:
        if analisis_demografico == "Evolución por Género":
            if "Sexo" in filtered_data["vacunacion"].columns:
                # Crear serie temporal por género
                genero_temporal = filtered_data["vacunacion"].groupby([
                    filtered_data["vacunacion"]["FechaVacunacion"].dt.date,
                    "Sexo"
                ]).size().reset_index()
                genero_temporal.columns = ["Fecha", "Genero", "Vacunados"]
                genero_temporal["Fecha"] = pd.to_datetime(genero_temporal["Fecha"])
                
                # Crear gráfico
                fig_genero_temp = px.line(
                    genero_temporal,
                    x="Fecha",
                    y="Vacunados",
                    color="Genero",
                    title="Evolución temporal por género",
                    height=500,
                    color_discrete_map={
                        "Masculino": colors["primary"],
                        "Femenino": colors["secondary"],
                        "No Binario": colors["accent"],
                        "Sin dato": colors["warning"]
                    }
                )
                
                fig_genero_temp.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white"
                )
                
                st.plotly_chart(fig_genero_temp, use_container_width=True)

        elif analisis_demografico == "Evolución por Grupo de Edad":
            if "Grupo_Edad" in filtered_data["vacunacion"].columns:
                # Crear serie temporal por grupo de edad
                edad_temporal = filtered_data["vacunacion"].groupby([
                    filtered_data["vacunacion"]["FechaVacunacion"].dt.date,
                    "Grupo_Edad"
                ]).size().reset_index()
                edad_temporal.columns = ["Fecha", "GrupoEdad", "Vacunados"]
                edad_temporal["Fecha"] = pd.to_datetime(edad_temporal["Fecha"])
                
                # Tomar solo los 6 grupos más representativos para evitar saturación visual
                top_grupos = filtered_data["vacunacion"]["Grupo_Edad"].value_counts().head(6).index
                edad_temporal_filtrada = edad_temporal[edad_temporal["GrupoEdad"].isin(top_grupos)]
                
                # Crear gráfico
                fig_edad_temp = px.line(
                    edad_temporal_filtrada,
                    x="Fecha",
                    y="Vacunados",
                    color="GrupoEdad",
                    title="Evolución temporal por grupo de edad (Top 6 grupos)",
                    height=500
                )
                
                fig_edad_temp.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white"
                )
                
                st.plotly_chart(fig_edad_temp, use_container_width=True)

        elif analisis_demografico == "Evolución por Régimen":
            if "RegimenAfiliacion" in filtered_data["vacunacion"].columns:
                # Crear serie temporal por régimen
                regimen_temporal = filtered_data["vacunacion"].groupby([
                    filtered_data["vacunacion"]["FechaVacunacion"].dt.date,
                    "RegimenAfiliacion"
                ]).size().reset_index()
                regimen_temporal.columns = ["Fecha", "Regimen", "Vacunados"]
                regimen_temporal["Fecha"] = pd.to_datetime(regimen_temporal["Fecha"])
                
                # Crear gráfico
                fig_regimen_temp = px.line(
                    regimen_temporal,
                    x="Fecha",
                    y="Vacunados",
                    color="Regimen",
                    title="Evolución temporal por régimen de afiliación",
                    height=500
                )
                
                fig_regimen_temp.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white"
                )
                
                st.plotly_chart(fig_regimen_temp, use_container_width=True)

        elif analisis_demografico == "Evolución por Municipio (Top 5)":
            if "NombreMunicipioResidencia" in filtered_data["vacunacion"].columns:
                # Obtener top 5 municipios
                top_municipios = filtered_data["vacunacion"]["NombreMunicipioResidencia"].value_counts().head(5).index
                
                # Crear serie temporal por municipio
                municipio_temporal = filtered_data["vacunacion"][
                    filtered_data["vacunacion"]["NombreMunicipioResidencia"].isin(top_municipios)
                ].groupby([
                    filtered_data["vacunacion"]["FechaVacunacion"].dt.date,
                    "NombreMunicipioResidencia"
                ]).size().reset_index()
                
                municipio_temporal.columns = ["Fecha", "Municipio", "Vacunados"]
                municipio_temporal["Fecha"] = pd.to_datetime(municipio_temporal["Fecha"])
                
                # Crear gráfico
                fig_municipio_temp = px.line(
                    municipio_temporal,
                    x="Fecha",
                    y="Vacunados",
                    color="Municipio",
                    title="Evolución temporal por municipio (Top 5)",
                    height=500
                )
                
                fig_municipio_temp.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white"
                )
                
                st.plotly_chart(fig_municipio_temp, use_container_width=True)

    except Exception as e:
        st.error(f"Error al crear análisis demográfico temporal: {str(e)}")

    # =====================================================================
    # SECCIÓN 5: PROYECCIONES Y MODELADO PREDICTIVO
    # =====================================================================
    st.subheader("🔮 Proyecciones y Análisis Predictivo")

    if len(vacunacion_diaria) > 14:  # Necesitamos suficientes datos para proyecciones
        
        col_proj1, col_proj2 = st.columns(2)
        
        with col_proj1:
            st.markdown("### Proyección Lineal Simple")
            
            # Calcular proyección lineal
            ultimos_30_dias = vacunacion_diaria.tail(min(30, len(vacunacion_diaria)))
            
            # Calcular tendencia de los últimos 30 días
            x_recent = np.arange(len(ultimos_30_dias))
            y_recent = ultimos_30_dias["Vacunados"].values
            
            if len(ultimos_30_dias) >= 7:
                slope_recent, intercept_recent, r_value_recent, _, _ = stats.linregress(x_recent, y_recent)
                
                # Proyectar próximos 30 días
                dias_proyeccion = 30
                x_future = np.arange(len(vacunacion_diaria), len(vacunacion_diaria) + dias_proyeccion)
                
                # Usar la tendencia reciente para proyección
                x_for_projection = np.arange(len(ultimos_30_dias), len(ultimos_30_dias) + dias_proyeccion)
                y_projection = slope_recent * x_for_projection + intercept_recent
                
                # Evitar valores negativos
                y_projection = np.maximum(y_projection, 0)
                
                # Crear fechas futuras
                ultima_fecha = vacunacion_diaria["Fecha"].max()
                fechas_futuras = pd.date_range(
                    start=ultima_fecha + timedelta(days=1),
                    periods=dias_proyeccion,
                    freq='D'
                )
                
                # Calcular métricas de proyección
                promedio_reciente = ultimos_30_dias["Vacunados"].mean()
                proyeccion_total_30_dias = y_projection.sum()
                
                st.info(f"""
                **Proyección para próximos 30 días:**
                - Promedio reciente: {promedio_reciente:.1f} vac/día
                - Tendencia: {slope_recent:+.2f} vac/día²
                - Total proyectado: {proyeccion_total_30_dias:.0f} vacunados
                - Confianza: {"Alta" if abs(r_value_recent) > 0.7 else "Media" if abs(r_value_recent) > 0.4 else "Baja"}
                """)
        
        with col_proj2:
            st.markdown("### Estimación para Meta de Cobertura")
            
            if total_poblacion > 0:
                # Calcular días para diferentes metas de cobertura
                cobertura_actual = (vacunacion_diaria["Vacunados_Acumulados"].iloc[-1] / total_poblacion * 100)
                
                metas_cobertura = [80, 90, 95]
                
                # Usar promedio de últimos días para estimación
                promedio_ultimos_dias = ultimos_30_dias["Vacunados"].mean()
                
                estimaciones = []
                for meta in metas_cobertura:
                    vacunados_necesarios = (total_poblacion * meta / 100) - vacunacion_diaria["Vacunados_Acumulados"].iloc[-1]
                    
                    if vacunados_necesarios > 0 and promedio_ultimos_dias > 0:
                        dias_necesarios = vacunados_necesarios / promedio_ultimos_dias
                        fecha_estimada = ultima_fecha + timedelta(days=int(dias_necesarios))
                        
                        estimaciones.append({
                            'meta': meta,
                            'dias': int(dias_necesarios),
                            'fecha': fecha_estimada,
                            'vacunados_faltantes': int(vacunados_necesarios)
                        })
                
                if estimaciones:
                    info_text = f"**Cobertura actual: {cobertura_actual:.1f}%**\n\n"
                    for est in estimaciones:
                        if est['dias'] > 0:
                            info_text += f"- **{est['meta']}% cobertura:** {est['dias']} días ({est['fecha'].strftime('%d/%m/%Y')})\n"
                        else:
                            info_text += f"- **{est['meta']}% cobertura:** ¡Ya alcanzada!\n"
                    
                    st.info(info_text)
                else:
                    st.info("Las metas de cobertura ya han sido alcanzadas o no se pueden calcular.")

    else:
        st.info("Se necesitan más datos históricos (>14 días) para generar proyecciones confiables.")

    # =====================================================================
    # INSIGHTS FINALES Y RECOMENDACIONES
    # =====================================================================
    st.markdown("---")
    st.subheader("💡 Insights Temporales Clave")

    try:
        insights_temporales = []
        
        # Insight sobre estacionalidad semanal
        if len(vacunacion_semanal) >= 5:  # Al menos datos de 5 días
            dias_laborales = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
            dias_weekend = ['Sábado', 'Domingo']
            
            promedio_laborales = vacunacion_semanal[
                vacunacion_semanal['DiaSemana'].isin(dias_laborales)
            ]['Vacunados'].mean()
            
            promedio_weekend = vacunacion_semanal[
                vacunacion_semanal['DiaSemana'].isin(dias_weekend)
            ]['Vacunados'].mean()
            
            if promedio_laborales > promedio_weekend * 1.5:
                insights_temporales.append("📈 **Fuerte patrón laboral** - 50% más vacunación en días hábiles")
            elif promedio_weekend > promedio_laborales:
                insights_temporales.append("🏖️ **Patrón de fin de semana** - mayor actividad los fines de semana")
        
        # Insight sobre consistencia
        if len(vacunacion_diaria) >= 14:
            cv = (vacunacion_diaria["Vacunados"].std() / vacunacion_diaria["Vacunados"].mean()) * 100
            if cv > 50:
                insights_temporales.append(f"⚠️ **Alta variabilidad diaria** (CV: {cv:.1f}%) - considerar estandarizar proceso")
            elif cv < 25:
                insights_temporales.append(f"✅ **Ritmo consistente** (CV: {cv:.1f}%) - proceso bien establecido")
        
        # Insight sobre aceleración/desaceleración
        if len(vacunacion_diaria) >= 14 and 'analysis' in locals():
            if analysis['trend_slope'] > 1 and analysis['trend_p_value'] < 0.05:
                insights_temporales.append("🚀 **Aceleración significativa** en el ritmo de vacunación")
            elif analysis['trend_slope'] < -1 and analysis['trend_p_value'] < 0.05:
                insights_temporales.append("📉 **Desaceleración significativa** - revisar estrategia")
        
        # Mostrar insights
        if insights_temporales:
            for insight in insights_temporales:
                st.markdown(f"- {insight}")
        else:
            st.info("📊 Los patrones temporales muestran un comportamiento estable sin alertas significativas.")

    except Exception as e:
        st.warning(f"No se pudieron calcular todos los insights temporales: {str(e)}")