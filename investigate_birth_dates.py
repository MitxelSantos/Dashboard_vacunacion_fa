"""
investigate_birth_dates.py - Investigación específica de fechas de nacimiento inválidas
"""

import pandas as pd
import os
from datetime import datetime


def analyze_birth_date_formats():
    """Analiza formatos de fechas de nacimiento para identificar problemas"""
    print("🔍 INVESTIGACIÓN DETALLADA: FECHAS DE NACIMIENTO INVÁLIDAS")
    print("=" * 70)

    if not os.path.exists("data/vacunacion_fa.csv"):
        print("❌ Archivo data/vacunacion_fa.csv no encontrado")
        return

    try:
        # Cargar muestra grande para análisis representativo
        print("📊 Cargando muestra para análisis...")
        df = pd.read_csv("data/vacunacion_fa.csv", nrows=10000)
        print(f"   ✅ Muestra cargada: {len(df):,} registros")

        if "FechaNacimiento" not in df.columns:
            print("❌ Columna 'FechaNacimiento' no encontrada")
            return

        # 1. Análisis de valores únicos
        print(f"\n📋 ANÁLISIS DE FORMATOS DE FECHA:")
        fechas_unicas = df["FechaNacimiento"].dropna().unique()
        print(f"   📊 Fechas únicas en muestra: {len(fechas_unicas):,}")

        # Mostrar ejemplos de diferentes formatos
        print(f"\n🔍 EJEMPLOS DE FORMATOS ENCONTRADOS (primeros 30):")
        for i, fecha in enumerate(fechas_unicas[:30], 1):
            tipo_dato = type(fecha).__name__
            longitud = len(str(fecha))
            print(f"   {i:2d}. '{fecha}' (tipo: {tipo_dato}, longitud: {longitud})")

        # 2. Análisis de tipos de datos
        print(f"\n📊 ANÁLISIS DE TIPOS DE DATOS:")
        tipos_datos = (
            df["FechaNacimiento"].apply(lambda x: type(x).__name__).value_counts()
        )
        for tipo, count in tipos_datos.items():
            print(f"   • {tipo}: {count:,} registros ({count/len(df)*100:.1f}%)")

        # 3. Intentar conversión y categorizar errores
        print(f"\n🧪 ANÁLISIS DE CONVERSIÓN A DATETIME:")

        # Conversión con diferentes formatos
        formatos_a_probar = [
            "%Y-%m-%d",  # 2020-01-15
            "%d/%m/%Y",  # 15/01/2020
            "%m/%d/%Y",  # 01/15/2020
            "%Y/%m/%d",  # 2020/01/15
            "%d-%m-%Y",  # 15-01-2020
            "%Y-%m-%d %H:%M:%S",  # 2020-01-15 10:30:00
            "%d/%m/%Y %H:%M:%S",  # 15/01/2020 10:30:00
        ]

        conversiones_exitosas = {}

        for formato in formatos_a_probar:
            try:
                convertidas = pd.to_datetime(
                    df["FechaNacimiento"], format=formato, errors="coerce"
                )
                validas = convertidas.notna().sum()
                if validas > 0:
                    conversiones_exitosas[formato] = validas
                    print(
                        f"   ✅ Formato '{formato}': {validas:,} conversiones exitosas"
                    )
            except Exception as e:
                print(f"   ❌ Formato '{formato}': Error - {str(e)}")

        # Conversión automática de pandas
        print(f"\n🤖 CONVERSIÓN AUTOMÁTICA DE PANDAS:")
        df["FechaNacimiento_auto"] = pd.to_datetime(
            df["FechaNacimiento"], errors="coerce"
        )

        validas_auto = df["FechaNacimiento_auto"].notna().sum()
        invalidas_auto = df["FechaNacimiento_auto"].isna().sum()

        print(
            f"   ✅ Fechas válidas (automático): {validas_auto:,} ({validas_auto/len(df)*100:.1f}%)"
        )
        print(
            f"   ❌ Fechas inválidas (automático): {invalidas_auto:,} ({invalidas_auto/len(df)*100:.1f}%)"
        )

        # 4. Análizar las fechas inválidas específicamente
        if invalidas_auto > 0:
            print(f"\n🔍 ANÁLISIS DE FECHAS INVÁLIDAS:")

            # Filtrar solo las fechas que fallaron en conversión
            mask_invalidas = (
                df["FechaNacimiento_auto"].isna() & df["FechaNacimiento"].notna()
            )
            fechas_problematicas = df[mask_invalidas]["FechaNacimiento"]

            print(f"   📊 Total de fechas problemáticas: {len(fechas_problematicas):,}")

            if len(fechas_problematicas) > 0:
                print(f"   🔍 Ejemplos de fechas problemáticas:")
                for i, fecha in enumerate(fechas_problematicas.head(20), 1):
                    print(f"      {i:2d}. '{fecha}' (tipo: {type(fecha).__name__})")

                # Categorizar tipos de problemas
                print(f"\n📋 CATEGORIZACIÓN DE PROBLEMAS:")

                problemas = {
                    "Valores nulos/NaN": 0,
                    "Strings vacíos": 0,
                    "Formatos no estándar": 0,
                    "Fechas futuras": 0,
                    "Fechas muy antiguas": 0,
                    "Caracteres especiales": 0,
                    "Otros": 0,
                }

                for fecha in fechas_problematicas:
                    fecha_str = str(fecha).strip()

                    if pd.isna(fecha) or fecha_str.lower() in ["nan", "none", "null"]:
                        problemas["Valores nulos/NaN"] += 1
                    elif fecha_str == "" or fecha_str == " ":
                        problemas["Strings vacíos"] += 1
                    elif any(char in fecha_str for char in ["#", "@", "?", "*", "&"]):
                        problemas["Caracteres especiales"] += 1
                    elif len(fecha_str) < 8 or len(fecha_str) > 25:
                        problemas["Formatos no estándar"] += 1
                    else:
                        problemas["Otros"] += 1

                for problema, count in problemas.items():
                    if count > 0:
                        print(f"   • {problema}: {count:,} casos")

        # 5. Verificar rango de fechas válidas
        if validas_auto > 0:
            print(f"\n📅 ANÁLISIS DE RANGO DE FECHAS VÁLIDAS:")

            fechas_validas = df["FechaNacimiento_auto"].dropna()
            fecha_min = fechas_validas.min()
            fecha_max = fechas_validas.max()

            print(f"   📊 Fecha más antigua: {fecha_min.strftime('%d/%m/%Y')}")
            print(f"   📊 Fecha más reciente: {fecha_max.strftime('%d/%m/%Y')}")

            # Verificar fechas extrañas
            hoy = datetime.now()
            fechas_futuras = (fechas_validas > hoy).sum()
            fechas_muy_antiguas = (fechas_validas < datetime(1900, 1, 1)).sum()

            if fechas_futuras > 0:
                print(f"   ⚠️  Fechas futuras encontradas: {fechas_futuras:,}")

            if fechas_muy_antiguas > 0:
                print(f"   ⚠️  Fechas antes de 1900: {fechas_muy_antiguas:,}")

            # Distribución por décadas
            print(f"\n📊 DISTRIBUCIÓN POR DÉCADAS:")
            fechas_validas_df = pd.DataFrame({"fecha": fechas_validas})
            fechas_validas_df["decada"] = (
                fechas_validas_df["fecha"].dt.year // 10
            ) * 10
            distribucion_decadas = (
                fechas_validas_df["decada"].value_counts().sort_index()
            )

            for decada, count in distribucion_decadas.items():
                if count > 0:
                    print(f"   • {decada}s: {count:,} registros")

        # 6. Recomendaciones
        print(f"\n💡 RECOMENDACIONES:")
        if invalidas_auto > 0:
            print(f"   🔧 Considerar limpieza previa de datos")
            print(f"   🔧 Aplicar validaciones de formato antes de conversión")
            print(f"   🔧 Establecer filtros de rango de fechas lógicas")

        if validas_auto / len(df) > 0.95:
            print(
                f"   ✅ Calidad de datos buena ({validas_auto/len(df)*100:.1f}% válidas)"
            )
        else:
            print(
                f"   ⚠️  Calidad de datos mejorable ({validas_auto/len(df)*100:.1f}% válidas)"
            )

        print(f"   📊 El dashboard puede proceder con {validas_auto:,} fechas válidas")

    except Exception as e:
        print(f"❌ Error en análisis: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    analyze_birth_date_formats()
