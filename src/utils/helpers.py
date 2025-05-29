"""
src/utils/helpers.py
Utilidades simplificadas y optimizadas para el dashboard de vacunación
Compatibles con la nueva estructura unificada y división temporal automática
"""

import streamlit as st
import pandas as pd
import numpy as np
import base64
import io
from pathlib import Path
from typing import Optional, Dict, List, Union, Any
import json
import zipfile
from datetime import datetime


class DashboardHelpers:
    """
    Clase con utilidades optimizadas para el dashboard
    """
    
    def __init__(self):
        self.institutional_colors = {
            "primary": "#7D0F2B",       # Vinotinto institucional
            "secondary": "#F2A900",     # Amarillo dorado
            "accent": "#5A4214",        # Marrón dorado oscuro
            "background": "#F5F5F5",    # Fondo gris claro
            "success": "#509E2F",       # Verde
            "warning": "#F7941D",       # Naranja
            "danger": "#E51937",        # Rojo brillante
            "info": "#17a2b8",          # Azul info
            "light": "#f8f9fa",         # Gris muy claro
            "dark": "#343a40"           # Gris oscuro
        }
    
    def configure_page_optimized(self, page_title: str, page_icon: str = "💉", layout: str = "wide"):
        """
        Configuración optimizada de página con CSS mejorado
        """
        st.set_page_config(
            page_title=page_title,
            page_icon=page_icon,
            layout=layout,
            initial_sidebar_state="expanded"
        )
        
        # CSS optimizado para la nueva estructura
        css = self._get_optimized_css()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        
        # JavaScript para detección de pantalla
        self._inject_screen_detection()
    
    def _get_optimized_css(self) -> str:
        """
        CSS optimizado para el dashboard unificado
        """
        return f"""
        /* Variables CSS para colores institucionales */
        :root {{
            --primary-color: {self.institutional_colors['primary']};
            --secondary-color: {self.institutional_colors['secondary']};
            --accent-color: {self.institutional_colors['accent']};
            --success-color: {self.institutional_colors['success']};
            --warning-color: {self.institutional_colors['warning']};
            --danger-color: {self.institutional_colors['danger']};
        }}
        
        /* Estilos para métricas mejoradas */
        .metric-container {{
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-left: 4px solid var(--primary-color);
            margin-bottom: 1rem;
            transition: transform 0.2s ease;
        }}
        
        .metric-container:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        }}
        
        .metric-title {{
            font-size: 0.9rem;
            color: #666;
            margin-bottom: 0.5rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .metric-value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary-color);
            line-height: 1.2;
        }}
        
        .metric-delta {{
            font-size: 0.8rem;
            margin-top: 0.3rem;
        }}
        
        .metric-delta.positive {{ color: var(--success-color); }}
        .metric-delta.negative {{ color: var(--danger-color); }}
        .metric-delta.neutral {{ color: #666; }}
        
        /* Estilos para alerts mejorados */
        .alert-custom {{
            padding: 1rem 1.5rem;
            border-radius: 8px;
            margin: 1rem 0;
            border-left: 4px solid;
        }}
        
        .alert-info {{
            background-color: #e7f3ff;
            border-left-color: var(--primary-color);
            color: #0c5460;
        }}
        
        .alert-success {{
            background-color: #d4edda;
            border-left-color: var(--success-color);
            color: #155724;
        }}
        
        .alert-warning {{
            background-color: #fff3cd;
            border-left-color: var(--warning-color);
            color: #856404;
        }}
        
        .alert-danger {{
            background-color: #f8d7da;
            border-left-color: var(--danger-color);
            color: #721c24;
        }}
        
        /* Estilos para tablas mejoradas */
        .dataframe {{
            border-collapse: collapse;
            margin: 1rem 0;
            font-size: 0.9rem;
            width: 100%;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .dataframe thead th {{
            background-color: var(--primary-color);
            color: white;
            font-weight: 600;
            padding: 12px 8px;
            text-align: left;
            border: none;
        }}
        
        .dataframe tbody td {{
            padding: 10px 8px;
            border-bottom: 1px solid #eee;
        }}
        
        .dataframe tbody tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        
        .dataframe tbody tr:hover {{
            background-color: #e8f4f8;
        }}
        
        /* Responsivo */
        @media (max-width: 768px) {{
            .metric-container {{
                padding: 1rem;
            }}
            
            .metric-value {{
                font-size: 1.5rem;
            }}
            
            .dataframe {{
                font-size: 0.8rem;
            }}
            
            .dataframe thead th,
            .dataframe tbody td {{
                padding: 8px 6px;
            }}
        }}
        
        /* Estilos para botones de descarga */
        .download-button {{
            background-color: var(--secondary-color);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            text-decoration: none;
            display: inline-block;
            font-weight: 500;
            margin: 0.5rem 0;
            transition: background-color 0.3s ease;
        }}
        
        .download-button:hover {{
            background-color: #d18900;
            color: white;
            text-decoration: none;
        }}
        
        /* Estilos para indicadores de estado */
        .status-indicator {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        
        .status-green {{ background-color: var(--success-color); }}
        .status-yellow {{ background-color: var(--warning-color); }}
        .status-red {{ background-color: var(--danger-color); }}
        .status-gray {{ background-color: #6c757d; }}
        """
    
    def _inject_screen_detection(self):
        """
        Inyecta JavaScript para detectar tamaño de pantalla
        """
        st.markdown("""
        <script>
        function updateScreenInfo() {
            const width = window.innerWidth;
            const height = window.innerHeight;
            const isSmall = width < 768;
            const isMedium = width >= 768 && width < 1200;
            const isLarge = width >= 1200;
            
            // Almacenar en sessionStorage
            sessionStorage.setItem('screen_width', width);
            sessionStorage.setItem('screen_height', height);
            sessionStorage.setItem('is_small_screen', isSmall);
            sessionStorage.setItem('is_medium_screen', isMedium);
            sessionStorage.setItem('is_large_screen', isLarge);
            
            // Actualizar estado de Streamlit si está disponible
            if (window.streamlitSetComponentValue) {
                window.streamlitSetComponentValue({
                    width: width,
                    height: height,
                    isSmall: isSmall,
                    isMedium: isMedium,
                    isLarge: isLarge
                });
            }
        }
        
        // Ejecutar al cargar y al cambiar tamaño
        updateScreenInfo();
        window.addEventListener('resize', updateScreenInfo);
        </script>
        """, unsafe_allow_html=True)
    
    def format_number_institutional(self, number: Union[int, float], 
                                  decimal_places: int = 0, 
                                  show_thousands: bool = True) -> str:
        """
        Formatea números con estilo institucional (punto como separador de miles)
        """
        if pd.isna(number) or number is None:
            return "N/A"
        
        try:
            number = float(number)
            
            if decimal_places == 0:
                formatted = f"{number:,.0f}" if show_thousands else f"{number:.0f}"
            else:
                formatted = f"{number:,.{decimal_places}f}" if show_thousands else f"{number:.{decimal_places}f}"
            
            # Reemplazar coma por punto (estilo colombiano)
            return formatted.replace(",", ".")
        
        except (ValueError, TypeError):
            return str(number)
    
    def format_percentage(self, value: float, decimal_places: int = 1) -> str:
        """
        Formatea porcentajes con estilo institucional
        """
        if pd.isna(value) or value is None:
            return "N/A%"
        
        try:
            return f"{value:.{decimal_places}f}%"
        except:
            return f"{value}%"
    
    def create_metric_card(self, title: str, value: Union[str, int, float], 
                          delta: Optional[str] = None, 
                          delta_type: str = "neutral",
                          help_text: Optional[str] = None) -> str:
        """
        Crea una tarjeta de métrica personalizada en HTML
        """
        # Formatear valor si es numérico
        if isinstance(value, (int, float)):
            formatted_value = self.format_number_institutional(value)
        else:
            formatted_value = str(value)
        
        # Clase para delta
        delta_class = f"metric-delta {delta_type}"
        delta_html = f'<div class="{delta_class}">{delta}</div>' if delta else ""
        
        # Tooltip si hay texto de ayuda
        help_html = f'title="{help_text}"' if help_text else ""
        
        return f"""
        <div class="metric-container" {help_html}>
            <div class="metric-title">{title}</div>
            <div class="metric-value">{formatted_value}</div>
            {delta_html}
        </div>
        """
    
    def create_alert_box(self, message: str, alert_type: str = "info", 
                        title: Optional[str] = None) -> str:
        """
        Crea una caja de alerta personalizada
        """
        title_html = f"<strong>{title}</strong><br>" if title else ""
        
        return f"""
        <div class="alert-custom alert-{alert_type}">
            {title_html}{message}
        </div>
        """
    
    def create_status_indicator(self, status: str, text: str) -> str:
        """
        Crea un indicador de estado con color
        """
        status_colors = {
            "success": "green",
            "warning": "yellow", 
            "error": "red",
            "info": "gray"
        }
        
        color = status_colors.get(status, "gray")
        
        return f"""
        <span>
            <span class="status-indicator status-{color}"></span>
            {text}
        </span>
        """
    
    def create_download_link(self, data: Union[pd.DataFrame, str, bytes], 
                           filename: str, 
                           link_text: str = "Descargar",
                           file_type: str = "csv") -> str:
        """
        Crea enlace de descarga mejorado para diferentes tipos de archivo
        """
        if isinstance(data, pd.DataFrame):
            if file_type == "csv":
                csv_data = data.to_csv(index=False, encoding='utf-8')
                b64 = base64.b64encode(csv_data.encode('utf-8')).decode()
                mime_type = "text/csv"
            elif file_type == "excel":
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    data.to_excel(writer, index=False, sheet_name='Datos')
                buffer.seek(0)
                b64 = base64.b64encode(buffer.read()).decode()
                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            else:
                return "Tipo de archivo no soportado"
        
        elif isinstance(data, str):
            b64 = base64.b64encode(data.encode('utf-8')).decode()
            mime_type = "text/plain"
        
        elif isinstance(data, bytes):
            b64 = base64.b64encode(data).decode()
            mime_type = "application/octet-stream"
        
        else:
            return "Tipo de datos no soportado"
        
        return f"""
        <a href="data:{mime_type};base64,{b64}" 
           download="{filename}" 
           class="download-button">
           📥 {link_text}
        </a>
        """
    
    def create_summary_cards(self, summary_data: Dict[str, Any], 
                           columns: int = 4) -> str:
        """
        Crea múltiples tarjetas de resumen en una fila
        """
        cards_html = []
        
        for key, info in summary_data.items():
            if isinstance(info, dict):
                title = info.get('title', key)
                value = info.get('value', 'N/A')
                delta = info.get('delta')
                delta_type = info.get('delta_type', 'neutral')
                help_text = info.get('help')
            else:
                title = key
                value = info
                delta = None
                delta_type = 'neutral'
                help_text = None
            
            card_html = self.create_metric_card(title, value, delta, delta_type, help_text)
            cards_html.append(card_html)
        
        # Organizar en columnas
        cards_per_row = columns
        rows = []
        
        for i in range(0, len(cards_html), cards_per_row):
            row_cards = cards_html[i:i + cards_per_row]
            row_width = 100 / len(row_cards)
            
            row_html = '<div style="display: flex; gap: 1rem; margin-bottom: 1rem;">'
            for card in row_cards:
                row_html += f'<div style="flex: 1; min-width: {row_width-5}%;">{card}</div>'
            row_html += '</div>'
            
            rows.append(row_html)
        
        return ''.join(rows)
    
    def validate_dataframe_structure(self, df: pd.DataFrame, 
                                   required_columns: List[str],
                                   data_name: str = "DataFrame") -> Dict[str, Any]:
        """
        Valida la estructura de un DataFrame
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": {
                "total_rows": len(df) if df is not None else 0,
                "total_columns": len(df.columns) if df is not None else 0,
                "columns_found": list(df.columns) if df is not None else []
            }
        }
        
        if df is None:
            validation_result["valid"] = False
            validation_result["errors"].append(f"{data_name} es None")
            return validation_result
        
        if len(df) == 0:
            validation_result["warnings"].append(f"{data_name} está vacío")
        
        # Verificar columnas requeridas
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            validation_result["valid"] = False
            validation_result["errors"].append(
                f"{data_name}: Faltan columnas requeridas: {missing_columns}"
            )
        
        # Verificar valores nulos en columnas críticas
        for col in required_columns:
            if col in df.columns:
                null_count = df[col].isna().sum()
                null_percentage = (null_count / len(df) * 100) if len(df) > 0 else 0
                
                if null_percentage > 50:
                    validation_result["warnings"].append(
                        f"{data_name}.{col}: {null_percentage:.1f}% valores nulos"
                    )
        
        return validation_result
    
    def create_data_quality_report(self, data_dict: Dict[str, pd.DataFrame]) -> str:
        """
        Crea reporte de calidad de datos en HTML
        """
        report_html = ['<div class="alert-custom alert-info">']
        report_html.append('<h4>📊 Reporte de Calidad de Datos</h4>')
        
        for name, df in data_dict.items():
            if df is not None and len(df) > 0:
                # Estadísticas básicas
                total_rows = len(df)
                total_cols = len(df.columns)
                null_counts = df.isnull().sum()
                null_percentage = (null_counts.sum() / (total_rows * total_cols) * 100)
                
                # Crear sección para este dataset
                report_html.append(f'<h5>{name}</h5>')
                report_html.append('<ul>')
                report_html.append(f'<li><strong>Registros:</strong> {self.format_number_institutional(total_rows)}</li>')
                report_html.append(f'<li><strong>Columnas:</strong> {total_cols}</li>')
                report_html.append(f'<li><strong>Valores nulos:</strong> {null_percentage:.1f}%</li>')
                
                # Columnas con más valores nulos
                high_null_cols = null_counts[null_counts > total_rows * 0.1]
                if len(high_null_cols) > 0:
                    report_html.append('<li><strong>Columnas con >10% nulos:</strong>')
                    report_html.append('<ul>')
                    for col, count in high_null_cols.head(5).items():
                        pct = (count / total_rows * 100)
                        report_html.append(f'<li>{col}: {pct:.1f}%</li>')
                    report_html.append('</ul></li>')
                
                report_html.append('</ul>')
            else:
                report_html.append(f'<h5>{name}</h5>')
                report_html.append('<p style="color: #dc3545;">❌ Sin datos o DataFrame vacío</p>')
        
        report_html.append('</div>')
        
        return ''.join(report_html)
    
    def get_institutional_colors(self) -> Dict[str, str]:
        """
        Retorna diccionario de colores institucionales
        """
        return self.institutional_colors.copy()
    
    def create_filter_summary(self, filters: Dict[str, Any]) -> str:
        """
        Crea resumen visual de filtros aplicados
        """
        active_filters = [f"{k.replace('_', ' ').title()}: {v}" 
                         for k, v in filters.items() 
                         if v != "Todos" and v is not None]
        
        if not active_filters:
            return self.create_alert_box("No hay filtros aplicados", "info")
        
        filters_text = " | ".join(active_filters)
        return self.create_alert_box(
            f"<strong>Filtros activos:</strong> {filters_text}", 
            "warning", 
            "🔍 Datos Filtrados"
        )
    
    def safe_divide(self, numerator: float, denominator: float, 
                   default_value: float = 0) -> float:
        """
        División segura que maneja casos de división por cero
        """
        if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
            return default_value
        
        try:
            return float(numerator) / float(denominator)
        except (ValueError, TypeError, ZeroDivisionError):
            return default_value
    
    def calculate_percentage_safe(self, part: float, total: float) -> float:
        """
        Calcula porcentaje de manera segura
        """
        return self.safe_divide(part, total, 0) * 100


# Instancia global para uso en toda la aplicación
dashboard_helpers = DashboardHelpers()

# Funciones de conveniencia
def configure_page(title, icon="💉", layout="wide"):
    """Función de conveniencia para configurar página"""
    return dashboard_helpers.configure_page_optimized(title, icon, layout)

def format_number(number, decimals=0):
    """Función de conveniencia para formatear números"""
    return dashboard_helpers.format_number_institutional(number, decimals)

def format_percent(value, decimals=1):
    """Función de conveniencia para formatear porcentajes"""
    return dashboard_helpers.format_percentage(value, decimals)

def create_metric(title, value, delta=None, delta_type="neutral", help_text=None):
    """Función de conveniencia para crear métricas"""
    return dashboard_helpers.create_metric_card(title, value, delta, delta_type, help_text)

def create_alert(message, alert_type="info", title=None):
    """Función de conveniencia para crear alertas"""
    return dashboard_helpers.create_alert_box(message, alert_type, title)

def create_download(data, filename, text="Descargar", file_type="csv"):
    """Función de conveniencia para crear descargas"""
    return dashboard_helpers.create_download_link(data, filename, text, file_type)

def get_colors():
    """Función de conveniencia para obtener colores institucionales"""
    return dashboard_helpers.get_institutional_colors()

def validate_data(df, required_cols, name="DataFrame"):
    """Función de conveniencia para validar datos"""
    return dashboard_helpers.validate_dataframe_structure(df, required_cols, name)

def safe_percentage(part, total):
    """Función de conveniencia para calcular porcentajes seguros"""
    return dashboard_helpers.calculate_percentage_safe(part, total)


def test_helpers():
    """
    Función de prueba para las utilidades
    """
    st.title("🧪 Prueba de Utilidades del Dashboard")
    
    # Configurar página
    configure_page("Prueba de Helpers", "🧪")
    
    # Probar formateo de números
    st.subheader("🔢 Formateo de Números")
    test_numbers = [1234, 1234.56, 1234567, 0.1234]
    
    for num in test_numbers:
        formatted = format_number(num, 2)
        st.write(f"**{num}** → {formatted}")
    
    # Probar métricas
    st.subheader("📊 Tarjetas de Métricas")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        metric_html = create_metric("Total Vacunados", 15000, "+1.2%", "positive")
        st.markdown(metric_html, unsafe_allow_html=True)
    
    with col2:
        metric_html = create_metric("Cobertura", "85.5%", "-0.3%", "negative")
        st.markdown(metric_html, unsafe_allow_html=True)
    
    with col3:
        metric_html = create_metric("Municipios", 47, None, "neutral")
        st.markdown(metric_html, unsafe_allow_html=True)
    
    with col4:
        metric_html = create_metric("EAPB Activas", 12, "+2", "positive")
        st.markdown(metric_html, unsafe_allow_html=True)
    
    # Probar alertas
    st.subheader("🚨 Alertas Personalizadas")
    
    alerts = [
        ("Datos actualizados correctamente", "success", "✅ Éxito"),
        ("Algunos datos pueden estar desactualizados", "warning", "⚠️ Advertencia"),
        ("Error en la carga de algunos archivos", "danger", "❌ Error"),
        ("Información del sistema", "info", "ℹ️ Información")
    ]
    
    for message, alert_type, title in alerts:
        alert_html = create_alert(message, alert_type, title)
        st.markdown(alert_html, unsafe_allow_html=True)
    
    # Probar validación de datos
    st.subheader("✅ Validación de Datos")
    
    # Crear datos de prueba
    test_df = pd.DataFrame({
        'A': [1, 2, 3, None, 5],
        'B': ['a', 'b', None, 'd', 'e'],
        'C': [10, 20, 30, 40, 50]
    })
    
    validation = validate_data(test_df, ['A', 'B', 'D'], "DataFrame de Prueba")
    
    st.json(validation)
    
    # Probar descarga
    st.subheader("📥 Enlace de Descarga")
    
    download_html = create_download(test_df, "datos_prueba.csv", "Descargar CSV de Prueba")
    st.markdown(download_html, unsafe_allow_html=True)
    
    # Mostrar colores institucionales
    st.subheader("🎨 Colores Institucionales")
    
    colors = get_colors()
    cols = st.columns(len(colors))
    
    for i, (name, color) in enumerate(colors.items()):
        with cols[i % len(cols)]:
            st.markdown(
                f"""
                <div style="background-color: {color}; 
                           padding: 1rem; 
                           border-radius: 5px; 
                           text-align: center; 
                           color: {'white' if name in ['primary', 'dark'] else 'black'}">
                    <strong>{name}</strong><br>
                    {color}
                </div>
                """, 
                unsafe_allow_html=True
            )


if __name__ == "__main__":
    test_helpers()