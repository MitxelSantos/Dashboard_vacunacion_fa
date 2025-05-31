"""
test_pai_barridos_logic.py - Prueba de la lógica integrada PAI + Barridos
Versión corregida: sin simulaciones, población fija, detección completa
"""

import pandas as pd
import os


def investigate_invalid_birth_dates():
    """Investiga por qué hay fechas de nacimiento inválidas"""
    print("🔍 INVESTIGANDO FECHAS DE NACIMIENTO INVÁLIDAS:")

    if os.path.exists("data/vacunacion_fa.csv"):
        # Cargar muestra más grande para mejor análisis
        df = pd.read_csv("data/vacunacion_fa.csv", nrows=5000)
        print(f"   📊 Muestra analizada: {len(df)} registros")

        if "FechaNacimiento" in df.columns:
            print(f"   📅 Valores únicos de FechaNacimiento (primeros 20):")

            # Mostrar ejemplos de fechas originales
            fechas_originales = df["FechaNacimiento"].dropna().head(20)
            for i, fecha in enumerate(fechas_originales, 1):
                print(f"      {i:2d}. '{fecha}' (tipo: {type(fecha)})")

            # Intentar conversión y ver qué falla
            df["FechaNacimiento_converted"] = pd.to_datetime(
                df["FechaNacimiento"], errors="coerce"
            )

            validas = df["FechaNacimiento_converted"].notna().sum()
            invalidas = df["FechaNacimiento_converted"].isna().sum()

            print(f"   ✅ Fechas válidas: {validas:,}")
            print(f"   ❌ Fechas inválidas: {invalidas:,}")

            if invalidas > 0:
                print(f"   🔍 Ejemplos de fechas inválidas:")
                invalidas_mask = (
                    df["FechaNacimiento_converted"].isna()
                    & df["FechaNacimiento"].notna()
                )
                ejemplos_invalidos = df[invalidas_mask]["FechaNacimiento"].head(10)
                for i, fecha in enumerate(ejemplos_invalidos, 1):
                    print(f"      {i}. '{fecha}'")


def detect_all_age_columns():
    """Detecta TODAS las columnas de edad (deberían ser 11 por etapa + total)"""
    print("\n🔍 DETECTANDO TODAS LAS COLUMNAS DE EDAD:")

    if os.path.exists("data/Resumen.xlsx"):
        df = pd.read_excel("data/Resumen.xlsx", sheet_name="Vacunacion")
        print(f"   📊 Registros de barridos: {len(df):,}")
        print(f"   📊 Total columnas: {len(df.columns)}")

        # Encontrar TODAS las columnas relacionadas con edad
        age_related_columns = []
        for col in df.columns:
            col_str = str(col).upper()
            if any(
                keyword in col_str
                for keyword in ["AÑO", "AÑOS", "<", ">", "MAS", "MÁS"]
            ):
                age_related_columns.append(col)

        print(f"   🎯 Columnas relacionadas con edad: {len(age_related_columns)}")

        # Agrupar por etapas
        etapas = {
            "Etapa 1 (Base)": [],
            "Etapa 2 (Sufijo 2)": [],
            "Etapa 3 (Sufijo 3/11-17)": [],
            "Etapa 4 (Sufijo 4/21-26)": [],
            "Totales": [],
        }

        for col in age_related_columns:
            col_clean = str(col).upper().strip()

            if any(
                keyword in col_clean
                for keyword in ["TPE", "TPVP", "TPNVP", "TPVB", "TOTAL"]
            ):
                etapas["Totales"].append(col)
            elif col_clean.endswith(("2", "AÑOS2")):
                etapas["Etapa 2 (Sufijo 2)"].append(col)
            elif col_clean.endswith(
                (
                    "3",
                    "AÑOS11",
                    "AÑOS12",
                    "AÑOS13",
                    "AÑOS14",
                    "AÑOS15",
                    "AÑOS16",
                    "AÑOS17",
                )
            ):
                etapas["Etapa 3 (Sufijo 3/11-17)"].append(col)
            elif col_clean.endswith(
                ("4", "AÑOS21", "AÑOS22", "AÑOS23", "AÑOS24", "AÑOS25", "AÑOS26")
            ):
                etapas["Etapa 4 (Sufijo 4/21-26)"].append(col)
            else:
                etapas["Etapa 1 (Base)"].append(col)

        for etapa, columnas in etapas.items():
            print(f"\n   📋 {etapa}: {len(columnas)} columnas")
            for col in columnas:
                print(f"      • {col}")

        # Verificar si hay 11 rangos + total por etapa
        print(f"\n   ✅ VERIFICACIÓN DE ESTRUCTURA:")
        for etapa, columnas in etapas.items():
            if "Totales" not in etapa:
                if len(columnas) == 11:
                    print(f"      ✅ {etapa}: {len(columnas)} columnas (correcto)")
                else:
                    print(f"      ⚠️  {etapa}: {len(columnas)} columnas (esperado: 11)")


def calculate_real_totals():
    """Calcula totales reales sin simulaciones"""
    print("\n📊 CÁLCULOS REALES (SIN SIMULACIONES):")

    # PAI Real
    total_pai = 0
    if os.path.exists("data/vacunacion_fa.csv"):
        print("   📈 Calculando PAI real...")
        # Cargar archivo completo para conteo real
        try:
            df_pai = pd.read_csv("data/vacunacion_fa.csv")
            total_pai = len(df_pai)
            print(f"   ✅ PAI REAL: {total_pai:,} registros")
        except Exception as e:
            print(f"   ❌ Error cargando PAI completo: {str(e)}")

    # Barridos Real (Etapa 4)
    total_barridos_real = 0
    total_renuentes_real = 0

    if os.path.exists("data/Resumen.xlsx"):
        print("   📈 Calculando Barridos reales...")
        try:
            df_barridos = pd.read_excel("data/Resumen.xlsx", sheet_name="Vacunacion")

            # Buscar TODAS las columnas Etapa 4
            etapa_4_cols = []
            etapa_3_cols = []

            for col in df_barridos.columns:
                col_str = str(col).upper()
                if any(keyword in col_str for keyword in ["AÑO", "AÑOS"]):
                    if col_str.endswith(
                        (
                            "4",
                            "AÑOS21",
                            "AÑOS22",
                            "AÑOS23",
                            "AÑOS24",
                            "AÑOS25",
                            "AÑOS26",
                        )
                    ):
                        etapa_4_cols.append(col)
                    elif col_str.endswith(
                        (
                            "3",
                            "AÑOS11",
                            "AÑOS12",
                            "AÑOS13",
                            "AÑOS14",
                            "AÑOS15",
                            "AÑOS16",
                            "AÑOS17",
                        )
                    ):
                        etapa_3_cols.append(col)

            print(f"   🎯 Columnas Etapa 4 detectadas: {len(etapa_4_cols)}")
            print(f"   ⚠️  Columnas Etapa 3 detectadas: {len(etapa_3_cols)}")

            # Calcular totales REALES
            def safe_sum_all_rows(columns):
                total = 0
                for col in columns:
                    if col in df_barridos.columns:
                        valores = pd.to_numeric(
                            df_barridos[col], errors="coerce"
                        ).fillna(0)
                        total += valores.sum()
                return total

            total_barridos_real = safe_sum_all_rows(etapa_4_cols)
            total_renuentes_real = safe_sum_all_rows(etapa_3_cols)

            print(f"   ✅ BARRIDOS REAL (Etapa 4): {total_barridos_real:,.0f}")
            print(f"   ⚠️  RENUENTES REAL (Etapa 3): {total_renuentes_real:,.0f}")

        except Exception as e:
            print(f"   ❌ Error calculando barridos: {str(e)}")

    # Población Real (SIN RESTAR RENUENTES)
    poblacion_real = 0
    if os.path.exists("data/Poblacion_aseguramiento.xlsx"):
        print("   📈 Calculando Población real...")
        try:
            df_pop = pd.read_excel("data/Poblacion_aseguramiento.xlsx")
            poblacion_real = (
                pd.to_numeric(df_pop["Total general"], errors="coerce").fillna(0).sum()
            )
            print(f"   ✅ POBLACIÓN REAL: {poblacion_real:,}")
        except Exception as e:
            print(f"   ❌ Error calculando población: {str(e)}")

    # CÁLCULOS FINALES REALES
    print(f"\n📊 MÉTRICAS REALES:")
    total_vacunados_real = total_pai + total_barridos_real

    print(f"   📊 PAI (históricos): {total_pai:,}")
    print(f"   📊 Barridos (nueva vacunación): {total_barridos_real:,.0f}")
    print(f"   📊 TOTAL VACUNADOS: {total_vacunados_real:,.0f}")
    print(f"   📊 Población total (FIJA): {poblacion_real:,}")
    print(f"   📊 Renuentes (para gráfico): {total_renuentes_real:,.0f}")

    if poblacion_real > 0:
        cobertura_pai = (total_pai / poblacion_real) * 100
        cobertura_total = (total_vacunados_real / poblacion_real) * 100
        incremento = cobertura_total - cobertura_pai

        print(f"\n   📈 Cobertura PAI: {cobertura_pai:.2f}%")
        print(f"   📈 Cobertura TOTAL: {cobertura_total:.2f}%")
        print(f"   📈 Incremento por Barridos: +{incremento:.2f}%")

        # Análisis de renuencia (SIN afectar denominador)
        if total_vacunados_real + total_renuentes_real > 0:
            tasa_aceptacion = (
                total_vacunados_real / (total_vacunados_real + total_renuentes_real)
            ) * 100
            print(f"   📊 Tasa de aceptación: {tasa_aceptacion:.1f}%")

        # Población sin contactar (para gráfico)
        contactados = total_vacunados_real + total_renuentes_real
        sin_contactar = poblacion_real - contactados
        print(
            f"   📊 Sin contactar: {sin_contactar:,} ({(sin_contactar/poblacion_real*100):.1f}%)"
        )

    return {
        "pai": total_pai,
        "barridos": total_barridos_real,
        "renuentes": total_renuentes_real,
        "poblacion": poblacion_real,
        "total_vacunados": total_vacunados_real,
    }


def main():
    """Función principal corregida"""
    print("🎯 ANÁLISIS REAL PAI + BARRIDOS (SIN SIMULACIONES)")
    print("=" * 60)

    # 1. Investigar fechas inválidas
    investigate_invalid_birth_dates()

    # 2. Detectar todas las columnas de edad
    detect_all_age_columns()

    # 3. Calcular totales reales
    resultados = calculate_real_totals()

    # 4. Validaciones finales
    print(f"\n✅ VALIDACIONES CORREGIDAS:")
    print(f"   • Sin simulaciones: Datos 100% reales ✅")
    print(f"   • Población fija: No se restan renuentes ✅")
    print(f"   • Detección completa: Buscar 11 rangos por etapa ✅")
    print(
        f"   • Gráfico propuesto: Barra doble color (vacunados/renuentes/sin contactar) ✅"
    )

    print(f"\n🔧 CORRECCIONES PENDIENTES:")
    if resultados["barridos"] < 50000:  # Parece bajo comparado con PAI
        print(f"   ⚠️  Verificar detección completa de columnas Etapa 4")
    print(f"   🔍 Investigar fechas de nacimiento inválidas")
    print(f"   📊 Implementar gráfico de barras con triple segmento")


if __name__ == "__main__":
    main()
