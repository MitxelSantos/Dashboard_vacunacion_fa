"""
quick_fix.py - Script de corrección rápida para los errores detectados
"""

import os
from pathlib import Path

def fix_setup_assets_error():
    """Corrige el error de setup_assets.py creando el directorio docs"""
    print("🔧 Corrigiendo setup_assets.py...")
    
    # Crear directorio docs
    Path("docs").mkdir(exist_ok=True)
    print("✅ Directorio 'docs' creado")
    
    # Ejecutar setup_assets.py nuevamente
    try:
        import subprocess
        result = subprocess.run(["python", "setup_assets.py"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ setup_assets.py ejecutado correctamente")
        else:
            print(f"⚠️ setup_assets.py con advertencias: {result.stderr}")
    except Exception as e:
        print(f"❌ Error ejecutando setup_assets.py: {str(e)}")

def install_pillow():
    """Instala Pillow si no está instalado"""
    print("🔧 Instalando Pillow...")
    
    try:
        import PIL
        print("✅ Pillow ya está instalado")
    except ImportError:
        try:
            import subprocess
            result = subprocess.run(["pip", "install", "Pillow"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Pillow instalado correctamente")
            else:
                print(f"❌ Error instalando Pillow: {result.stderr}")
        except Exception as e:
            print(f"❌ Error ejecutando pip: {str(e)}")
            print("💡 Ejecuta manualmente: pip install Pillow")

def verify_data_structure():
    """Verifica la estructura de los datos para entender mejor los problemas"""
    print("🔍 Analizando estructura de datos...")
    
    try:
        import pandas as pd
        
        # Verificar datos históricos
        if os.path.exists("data/vacunacion_fa.csv"):
            print("\n📊 DATOS HISTÓRICOS:")
            df_hist = pd.read_csv("data/vacunacion_fa.csv", nrows=1000)  # Solo muestra
            print(f"   Registros (muestra): {len(df_hist)}")
            
            if "FechaNacimiento" in df_hist.columns:
                print("   ✅ Columna 'FechaNacimiento' encontrada")
            else:
                print("   ❌ Columna 'FechaNacimiento' NO encontrada")
                print(f"   Columnas disponibles: {list(df_hist.columns)[:10]}...")
        
        # Verificar datos de barridos
        if os.path.exists("data/Resumen.xlsx"):
            print("\n📊 DATOS BARRIDOS:")
            df_barr = pd.read_excel("data/Resumen.xlsx", sheet_name="Vacunacion", nrows=100)
            print(f"   Registros (muestra): {len(df_barr)}")
            
            # Encontrar columnas de edad
            edad_cols = []
            for col in df_barr.columns:
                if any(patron in str(col).upper() for patron in ["AÑO", "AÑOS", "<", ">"]):
                    edad_cols.append(col)
            
            print(f"   ✅ Columnas de edad encontradas: {len(edad_cols)}")
            for col in edad_cols[:5]:  # Mostrar solo las primeras 5
                # Verificar tipo de datos
                sample_val = df_barr[col].iloc[0] if len(df_barr) > 0 else None
                print(f"      • {col}: tipo = {type(sample_val)}, valor = {sample_val}")
        
        # Verificar datos de población
        if os.path.exists("data/Poblacion_aseguramiento.xlsx"):
            print("\n📊 DATOS POBLACIÓN:")
            df_pop = pd.read_excel("data/Poblacion_aseguramiento.xlsx", nrows=100)
            print(f"   Registros (muestra): {len(df_pop)}")
            print(f"   Columnas: {list(df_pop.columns)}")
            
            if "Nombre Entidad" in df_pop.columns:
                print("   ✅ Columna 'Nombre Entidad' encontrada (equivale a EAPB)")
                entidades_unicas = df_pop["Nombre Entidad"].nunique()
                print(f"   📈 Entidades únicas: {entidades_unicas}")
            
    except Exception as e:
        print(f"❌ Error analizando datos: {str(e)}")

def test_numeric_conversion():
    """Prueba la conversión numérica en una muestra de datos de barridos"""
    print("🧪 Probando conversión numérica...")
    
    try:
        import pandas as pd
        
        if os.path.exists("data/Resumen.xlsx"):
            df = pd.read_excel("data/Resumen.xlsx", sheet_name="Vacunacion", nrows=10)
            
            # Buscar una columna de edad para probar
            edad_col = None
            for col in df.columns:
                if "< 1 AÑO" in str(col).upper():
                    edad_col = col
                    break
            
            if edad_col:
                print(f"   Probando columna: '{edad_col}'")
                
                # Mostrar valores originales
                valores_orig = df[edad_col].head()
                print(f"   Valores originales: {list(valores_orig)}")
                print(f"   Tipos originales: {[type(x) for x in valores_orig]}")
                
                # Convertir a numérico
                valores_num = pd.to_numeric(df[edad_col], errors='coerce').fillna(0)
                print(f"   Valores numéricos: {list(valores_num.head())}")
                print(f"   Suma: {valores_num.sum()}")
                
                print("   ✅ Conversión numérica exitosa")
            else:
                print("   ⚠️ No se encontró columna de edad para probar")
        
    except Exception as e:
        print(f"❌ Error en prueba numérica: {str(e)}")

def create_corrected_validate_script():
    """Crea una versión corregida del script de validación"""
    print("📝 Creando validate_data_fixed.py...")
    
    corrected_script = '''"""
validate_data_fixed.py - Versión corregida del validador
"""

import pandas as pd
import os
from datetime import datetime

def safe_numeric_sum(series):
    """Suma segura convirtiendo a numérico"""
    return pd.to_numeric(series, errors='coerce').fillna(0).sum()

def validate_barridos_corrected():
    """Validación corregida de barridos"""
    print("🔧 VALIDACIÓN BARRIDOS CORREGIDA")
    
    file_path = "data/Resumen.xlsx"
    
    if not os.path.exists(file_path):
        print("❌ Archivo no encontrado")
        return False
    
    try:
        df = pd.read_excel(file_path, sheet_name="Vacunacion")
        print(f"✅ Archivo cargado: {len(df):,} registros")
        
        # Buscar columnas de edad con conversión segura
        edad_patterns = ["< 1 AÑO", "1-5 AÑOS", "6-10 AÑOS", "11-20 AÑOS", 
                        "21-30 AÑOS", "31-40 AÑOS", "41-50 AÑOS", "51-59 AÑOS", "60 Y MAS"]
        
        found_cols = {}
        for pattern in edad_patterns:
            for col in df.columns:
                if pattern in str(col).upper():
                    found_cols[pattern] = col
                    break
        
        print(f"✅ Columnas de edad encontradas: {len(found_cols)}")
        
        total_general = 0
        for pattern, col in found_cols.items():
            total = safe_numeric_sum(df[col])
            total_general += total
            print(f"   • {col}: {total:,.0f} vacunados")
        
        # Buscar columnas de consolidación
        consolidation_patterns = ["60-69", "70 AÑOS Y MAS"]
        consolidation_total = 0
        
        for col in df.columns:
            for pattern in consolidation_patterns:
                if pattern in str(col).upper():
                    total = safe_numeric_sum(df[col])
                    consolidation_total += total
                    print(f"   • {col} (→60+): {total:,.0f} vacunados")
        
        total_general += consolidation_total
        
        print(f"✅ TOTAL GENERAL: {total_general:,.0f} vacunados")
        print(f"✅ Total consolidado en 60+: {consolidation_total:,.0f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 VALIDADOR CORREGIDO")
    validate_barridos_corrected()
'''
    
    with open("validate_data_fixed.py", "w", encoding="utf-8") as f:
        f.write(corrected_script)
    
    print("✅ validate_data_fixed.py creado")

def main():
    """Función principal de corrección"""
    print("🚀 CORRECCIÓN RÁPIDA DE ERRORES")
    print("="*50)
    
    # 1. Instalar Pillow
    install_pillow()
    
    # 2. Corregir setup_assets
    fix_setup_assets_error()
    
    # 3. Analizar estructura de datos
    verify_data_structure()
    
    # 4. Probar conversión numérica
    test_numeric_conversion()
    
    # 5. Crear script corregido
    create_corrected_validate_script()
    
    print("\n✅ CORRECCIONES COMPLETADAS")
    print("\n📋 Próximos pasos:")
    print("1. Ejecuta: python validate_data_fixed.py")
    print("2. Si funciona bien, ejecuta: streamlit run app.py")
    print("3. Los archivos actualizados manejan conversión numérica segura")

if __name__ == "__main__":
    main()