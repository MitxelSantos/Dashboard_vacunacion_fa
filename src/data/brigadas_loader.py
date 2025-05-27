"""
src/data/brigadas_loader.py
Loader para datos de brigadas territoriales del Tolima
"""

import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path
import os
from datetime import datetime


def load_brigadas_excel(file_path="data/Resumen.xlsx"):
    """
    Carga el archivo Excel de brigadas
    """
    try:
        full_path = Path(file_path)
        
        if not full_path.exists():
            st.warning(f"⚠️ Archivo no encontrado: {file_path}")
            return {}
        
        # Leer ambas hojas si existen
        excel_data = {}
        
        with pd.ExcelFile(full_path) as excel_file:
            st.info(f"📄 Hojas encontradas: {', '.join(excel_file.sheet_names)}")
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(full_path, sheet_name=sheet_name)
                excel_data[sheet_name] = df
                st.success(f"✅ Cargada hoja '{sheet_name}': {len(df)} filas, {len(df.columns)} columnas")
        
        return excel_data
        
    except Exception as e:
        st.error(f"❌ Error cargando Excel de brigadas: {str(e)}")
        return {}


def process_brigadas_data(df):
    """
    Procesa y normaliza los datos de brigadas
    """
    if df.empty:
        return df
    
    df_clean = df.copy()
    
    try:
        # Convertir fecha
        df_clean['FECHA'] = pd.to_datetime(df_clean['FECHA'], errors='coerce')
        
        # Limpiar y normalizar nombres
        df_clean['MUNICIPIO'] = df_clean['MUNICIPIO'].astype(str).str.strip().str.title()
        df_clean['VEREDAS'] = df_clean['VEREDAS'].fillna('Sin especificar')
        
        # Normalizar valores numéricos principales
        main_numeric_columns = [
            'Efectivas (E)', 'No Efectivas (NE)', 'Fallidas (F)', 'Casa renuente',
            'TPE', 'TPVP', 'TPNVP', 'TPVB'
        ]
        
        for col in main_numeric_columns:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
        
        # Normalizar todas las columnas de grupos de edad
        age_patterns = [
            '< 1 AÑO', '1-5 AÑOS', '6-10 AÑOS', '11-20 AÑOS', '21-30 AÑOS',
            '31-40 AÑOS', '41-50 AÑOS', '51-59 AÑOS', '60 Y MAS', '60-69 AÑOS', '70 AÑOS'
        ]
        
        age_columns = []
        for col in df_clean.columns:
            for pattern in age_patterns:
                if pattern in str(col):
                    age_columns.append(col)
                    break
        
        for col in age_columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
        
        # Calcular métricas derivadas
        df_clean = calculate_derived_metrics(df_clean)
        
        st.success(f"✅ Datos procesados: {len(df_clean)} brigadas")
        return df_clean
        
    except Exception as e:
        st.error(f"❌ Error procesando datos: {str(e)}")
        return df


def calculate_derived_metrics(df):
    """
    Calcula métricas derivadas útiles
    """
    df_calc = df.copy()
    
    try:
        # Tasa de efectividad
        total_intentos = df_calc['Efectivas (E)'] + df_calc['No Efectivas (NE)'] + df_calc['Fallidas (F)']
        df_calc['tasa_efectividad'] = np.where(
            total_intentos > 0,
            (df_calc['Efectivas (E)'] / total_intentos * 100).round(2),
            0
        )
        
        # Tasa de aceptación (de la población encontrada)
        df_calc['tasa_aceptacion'] = np.where(
            df_calc['TPE'] > 0,
            (df_calc['TPVB'] / df_calc['TPE'] * 100).round(2),
            0
        )
        
        # Tasa de resistencia
        df_calc['tasa_resistencia'] = np.where(
            df_calc['TPE'] > 0,
            (df_calc['Casa renuente'] / df_calc['TPE'] * 100).round(2),
            0
        )
        
        # Cobertura previa
        df_calc['cobertura_previa'] = np.where(
            df_calc['TPE'] > 0,
            (df_calc['TPVP'] / df_calc['TPE'] * 100).round(2),
            0
        )
        
        # Eficiencia de la brigada
        poblacion_susceptible = df_calc['TPE'] - df_calc['TPVP']
        df_calc['eficiencia_brigada'] = np.where(
            poblacion_susceptible > 0,
            (df_calc['TPVB'] / poblacion_susceptible * 100).round(2),
            0
        )
        
    except Exception as e:
        st.warning(f"⚠️ Error calculando métricas derivadas: {str(e)}")
    
    return df_calc


def create_brigadas_summary(df):
    """
    Crea un resumen ejecutivo de las brigadas
    """
    if df.empty:
        return {}
    
    try:
        # Métricas temporales
        fecha_inicio = df['FECHA'].min()
        fecha_fin = df['FECHA'].max()
        duracion_campana = (fecha_fin - fecha_inicio).days + 1 if pd.notna(fecha_inicio) and pd.notna(fecha_fin) else 0
        
        # Métricas de cobertura
        total_brigadas = len(df)
        municipios_visitados = df['MUNICIPIO'].nunique()
        veredas_visitadas = df['VEREDAS'].nunique()
        
        # Métricas de población
        poblacion_total_encontrada = df['TPE'].sum()
        poblacion_ya_vacunada = df['TPVP'].sum()
        poblacion_vacunada_brigada = df['TPVB'].sum()
        poblacion_resistente = df['TPNVP'].sum()
        
        # Métricas de efectividad
        total_efectivas = df['Efectivas (E)'].sum()
        total_intentos = (df['Efectivas (E)'] + df['No Efectivas (NE)'] + df['Fallidas (F)']).sum()
        efectividad_global = (total_efectivas / total_intentos * 100) if total_intentos > 0 else 0
        
        return {
            'periodo': {
                'inicio': fecha_inicio,
                'fin': fecha_fin,
                'duracion_dias': duracion_campana
            },
            'cobertura': {
                'total_brigadas': total_brigadas,
                'municipios_visitados': municipios_visitados,
                'veredas_visitadas': veredas_visitadas
            },
            'poblacion': {
                'encontrada': poblacion_total_encontrada,
                'ya_vacunada': poblacion_ya_vacunada,
                'vacunada_brigada': poblacion_vacunada_brigada,
                'resistente': poblacion_resistente,
                'cobertura_previa_pct': (poblacion_ya_vacunada / poblacion_total_encontrada * 100) if poblacion_total_encontrada > 0 else 0,
                'cobertura_brigada_pct': (poblacion_vacunada_brigada / poblacion_total_encontrada * 100) if poblacion_total_encontrada > 0 else 0
            },
            'efectividad': {
                'efectividad_global_pct': efectividad_global,
                'total_efectivas': total_efectivas,
                'total_intentos': total_intentos
            }
        }
        
    except Exception as e:
        st.error(f"❌ Error creando resumen: {str(e)}")
        return {}


@st.cache_data(ttl=3600)
def load_brigadas_for_dashboard():
    """
    Función principal para cargar datos de brigadas en Streamlit
    """
    try:
        st.info("🔄 Cargando datos de brigadas...")
        
        # Cargar Excel
        excel_data = load_brigadas_excel()
        
        if not excel_data:
            st.warning("⚠️ No se encontraron datos de brigadas")
            return None
        
        # Procesar hoja de Vacunacion
        if 'Vacunacion' in excel_data:
            df_brigadas = process_brigadas_data(excel_data['Vacunacion'])
            
            if df_brigadas.empty:
                st.warning("⚠️ No se pudieron procesar los datos de brigadas")
                return None
            
        else:
            st.error("❌ No se encontró la hoja 'Vacunacion' en el archivo Excel")
            return None
        
        # Crear resumen ejecutivo
        resumen = create_brigadas_summary(df_brigadas)
        
        result = {
            'brigadas_data': df_brigadas,
            'excel_raw': excel_data,
            'resumen_ejecutivo': resumen
        }
        
        st.success(f"✅ Datos de brigadas cargados exitosamente: {len(df_brigadas)} registros")
        
        return result
        
    except Exception as e:
        st.error(f"❌ Error cargando datos de brigadas: {str(e)}")
        return None


def show_brigadas_data_info():
    """
    Muestra información sobre los datos de brigadas cargados
    """
    result = load_brigadas_for_dashboard()
    
    if result:
        st.success("✅ Datos de brigadas disponibles")
        
        with st.expander("📊 Información de los datos"):
            df = result['brigadas_data']
            resumen = result['resumen_ejecutivo']
            
            st.write("**Dimensiones:**")
            st.write(f"- Registros: {len(df)}")
            st.write(f"- Columnas: {len(df.columns)}")
            
            if resumen:
                st.write("**Resumen:**")
                if 'cobertura' in resumen:
                    cob = resumen['cobertura']
                    st.write(f"- Brigadas: {cob.get('total_brigadas', 0)}")
                    st.write(f"- Municipios: {cob.get('municipios_visitados', 0)}")
                    st.write(f"- Veredas: {cob.get('veredas_visitadas', 0)}")
            
            st.write("**Primeras columnas:**")
            st.write(list(df.columns[:10]))
    else:
        st.warning("⚠️ No hay datos de brigadas disponibles")


if __name__ == "__main__":
    # Para probar el módulo
    st.title("Prueba del Loader de Brigadas")
    show_brigadas_data_info()