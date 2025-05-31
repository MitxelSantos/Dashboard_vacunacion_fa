"""
validate_data.py - Script de validación para datos del dashboard
Versión actualizada con rangos de edad correctos y validación de cálculo de edad
"""

import pandas as pd
import os
from datetime import datetime
import sys

RANGOS_EDAD_ESPERADOS = {
    "<1": "< 1 año",
    "1-5": "1-5 años",
    "6-10": "6-10 años",
    "11-20": "11-20 años",
    "21-30": "21-30 años",
    "31-40": "31-40 años",
    "41-50": "41-50 años",
    "51-59": "51-59 años",
    "60+": "60 años y más",
    "60-69": "60-69 años",
    "70+": "70 años y más",
}


def print_header(title):
    """Imprime un encabezado formateado"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_status(message, status="info"):
    """Imprime mensaje con estado"""
    icons = {"success": "✅", "error": "❌", "warning": "⚠️", "info": "ℹ️"}
    print(f"{icons.get(status, 'ℹ️')} {message}")


def calculate_age_sample(fecha_nacimiento, fecha_referencia):
    """Función de prueba para calcular edad"""
    try:
        if pd.isna(fecha_nacimiento) or pd.isna(fecha_referencia):
            return None

        edad = fecha_referencia.year - fecha_nacimiento.year

        if (fecha_referencia.month, fecha_referencia.day) < (
            fecha_nacimiento.month,
            fecha_nacimiento.day,
        ):
            edad -= 1

        return max(0, edad)
    except:
        return None


def validate_historical_data():
    """Valida datos históricos de vacunación individual"""
    print_header("VALIDACIÓN DATOS HISTÓRICOS")

    file_path = "data/vacunacion_fa.csv"

    if not os.path.exists(file_path):
        print_status(f"Archivo no encontrado: {file_path}", "warning")
        return False

    try:
        df = pd.read_csv(file_path)
        print_status(f"Archivo cargado: {len(df):,} registros", "success")

        # Validar columnas críticas
        required_cols = ["FA UNICA", "NombreMunicipioResidencia", "FechaNacimiento"]
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            print_status(f"Columnas faltantes: {missing_cols}", "error")
            if "FechaNacimiento" in missing_cols:
                print_status(
                    "CRÍTICO: Sin FechaNacimiento no se puede calcular edad", "error"
                )
            return False

        # Validar fechas de vacunación
        df["FA UNICA"] = pd.to_datetime(df["FA UNICA"], errors="coerce")
        fechas_vac_validas = df["FA UNICA"].notna().sum()
        fechas_vac_invalidas = len(df) - fechas_vac_validas

        print_status(f"Fechas de vacunación válidas: {fechas_vac_validas:,}", "success")
        if fechas_vac_invalidas > 0:
            print_status(
                f"Fechas de vacunación inválidas: {fechas_vac_invalidas:,}", "warning"
            )

        # Validar fechas de nacimiento
        df["FechaNacimiento"] = pd.to_datetime(df["FechaNacimiento"], errors="coerce")
        fechas_nac_validas = df["FechaNacimiento"].notna().sum()
        fechas_nac_invalidas = len(df) - fechas_nac_validas

        print_status(f"Fechas de nacimiento válidas: {fechas_nac_validas:,}", "success")
        if fechas_nac_invalidas > 0:
            print_status(
                f"Fechas de nacimiento inválidas: {fechas_nac_invalidas:,}", "warning"
            )

        # Probar cálculo de edades en una muestra
        if fechas_vac_validas > 0 and fechas_nac_validas > 0:
            print_status("Probando cálculo de edades...", "info")

            # Tomar muestra de registros con ambas fechas válidas
            mask_ambas_fechas = df["FA UNICA"].notna() & df["FechaNacimiento"].notna()
            df_muestra = df[mask_ambas_fechas].head(100).copy()

            if len(df_muestra) > 0:
                # Calcular edades de muestra
                df_muestra["edad_calculada"] = df_muestra.apply(
                    lambda row: calculate_age_sample(
                        row["FechaNacimiento"], row["FA UNICA"]
                    ),
                    axis=1,
                )

                edades_calculadas = df_muestra["edad_calculada"].notna().sum()
                print_status(
                    f"Edades calculadas en muestra: {edades_calculadas}/{len(df_muestra)}",
                    "success",
                )

                if edades_calculadas > 0:
                    edad_min = df_muestra["edad_calculada"].min()
                    edad_max = df_muestra["edad_calculada"].max()
                    edad_promedio = df_muestra["edad_calculada"].mean()

                    print_status(
                        f"Rango de edades: {edad_min:.0f} - {edad_max:.0f} años", "info"
                    )
                    print_status(f"Edad promedio: {edad_promedio:.1f} años", "info")

                    # Validar rangos lógicos
                    if edad_min < 0:
                        print_status(
                            "ADVERTENCIA: Se encontraron edades negativas", "warning"
                        )
                    if edad_max > 120:
                        print_status(
                            "ADVERTENCIA: Se encontraron edades > 120 años", "warning"
                        )

                    # Mostrar distribución por rangos esperados
                    print_status("Distribución por rangos de edad (muestra):", "info")
                    for edad in df_muestra["edad_calculada"].dropna():
                        if edad < 1:
                            rango = "<1"
                        elif 1 <= edad <= 5:
                            rango = "1-5"
                        elif 6 <= edad <= 10:
                            rango = "6-10"
                        elif 11 <= edad <= 20:
                            rango = "11-20"
                        elif 21 <= edad <= 30:
                            rango = "21-30"
                        elif 31 <= edad <= 40:
                            rango = "31-40"
                        elif 41 <= edad <= 50:
                            rango = "41-50"
                        elif 51 <= edad <= 59:
                            rango = "51-59"
                        else:
                            rango = "60+"
                        break  # Solo mostrar clasificación de un caso

                    print(
                        f"  • Ejemplo: edad {edad:.0f} años → rango '{rango}' ({RANGOS_EDAD_ESPERADOS[rango]})"
                    )

        # Estadísticas básicas
        if fechas_vac_validas > 0:
            fecha_min = df["FA UNICA"].min()
            fecha_max = df["FA UNICA"].max()
            print_status(
                f"Período de vacunación: {fecha_min.strftime('%d/%m/%Y')} - {fecha_max.strftime('%d/%m/%Y')}",
                "info",
            )

        municipios = df["NombreMunicipioResidencia"].nunique()
        print_status(f"Municipios únicos: {municipios}", "info")

        return True

    except Exception as e:
        print_status(f"Error procesando archivo: {str(e)}", "error")
        return False


def validate_barridos_data():
    """Valida datos de barridos territoriales"""
    print_header("VALIDACIÓN DATOS BARRIDOS")

    file_path = "data/Resumen.xlsx"

    if not os.path.exists(file_path):
        print_status(f"Archivo no encontrado: {file_path}", "warning")
        return False

    try:
        # Intentar diferentes hojas
        sheet_names = ["Barridos", "Vacunacion", 0]
        df = None
        sheet_used = None

        for sheet in sheet_names:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet)
                sheet_used = sheet
                break
            except:
                continue

        if df is None:
            print_status("No se pudo leer ninguna hoja del archivo", "error")
            return False

        print_status(
            f"Archivo cargado (hoja: {sheet_used}): {len(df):,} registros", "success"
        )

        # Mostrar columnas disponibles
        print_status(f"Columnas encontradas: {list(df.columns)}", "info")

        # Buscar columnas esperadas
        expected_patterns = {
            "fecha": ["FECHA", "DATE"],
            "municipio": ["MUNICIPIO", "MUNICIPALITY"],
            "vereda": ["VEREDA", "VEREDAS"],
            # Rangos de edad actualizados
            "edad_<1": ["<1", "< 1", "MENOR 1", "LACTANTE"],
            "edad_1_5": ["1-5", "1 A 5", "1A5", "PREESCOLAR"],
            "edad_6_10": ["6-10", "6 A 10", "6A10", "ESCOLAR"],
            "edad_11_20": ["11-20", "11 A 20", "11A20", "ADOLESCENTE"],
            "edad_21_30": ["21-30", "21 A 30", "21A30"],
            "edad_31_40": ["31-40", "31 A 40", "31A40"],
            "edad_41_50": ["41-50", "41 A 50", "41A50"],
            "edad_51_59": ["51-59", "51 A 59", "51A59"],
            "edad_60_mas": ["60+", "60 +", "60 Y MAS", "60 Y MÁS", "60MAS", "MAYOR 60"],
        }

        found_columns = {}
        for category, patterns in expected_patterns.items():
            for col in df.columns:
                if any(pattern.upper() in str(col).upper() for pattern in patterns):
                    found_columns[category] = col
                    break

        print_status("Columnas identificadas:", "info")
        for category, col_name in found_columns.items():
            print(f"  • {category}: {col_name}")

        # Buscar columnas adicionales para consolidar en 60+
        consolidation_patterns = ["60-69", "70+", "70 Y MAS", "70 Y MÁS", "MAYOR 70"]
        consolidation_cols = []

        for col in df.columns:
            for pattern in consolidation_patterns:
                if pattern.upper() in str(col).upper():
                    consolidation_cols.append(col)
                    break

        if consolidation_cols:
            print_status(
                f"Columnas para consolidar en 60+: {consolidation_cols}", "warning"
            )

        # Validar fechas si existe columna
        if "fecha" in found_columns:
            fecha_col = found_columns["fecha"]
            df[fecha_col] = pd.to_datetime(df[fecha_col], errors="coerce")
            fechas_validas = df[fecha_col].notna().sum()
            print_status(f"Fechas válidas: {fechas_validas:,}", "success")

            if fechas_validas > 0:
                fecha_min = df[fecha_col].min()
                fecha_max = df[fecha_col].max()
                print_status(
                    f"Período barridos: {fecha_min.strftime('%d/%m/%Y')} - {fecha_max.strftime('%d/%m/%Y')}",
                    "info",
                )

        # Contar municipios y veredas
        if "municipio" in found_columns:
            municipios = df[found_columns["municipio"]].nunique()
            print_status(f"Municipios con barridos: {municipios}", "info")

        if "vereda" in found_columns:
            veredas = df[found_columns["vereda"]].nunique()
            print_status(f"Veredas visitadas: {veredas}", "info")

        # Validar columnas de edad y calcular totales
        edad_cols = [
            found_columns[k]
            for k in found_columns.keys()
            if k.startswith("edad_") and k in found_columns
        ]
        if edad_cols:
            print_status(f"Columnas de edad encontradas: {len(edad_cols)}", "success")

            total_general = 0
            # Calcular totales por edad
            for col in edad_cols:
                if col in df.columns:
                    # Convertir a numérico de forma segura
                    valores_numericos = pd.to_numeric(df[col], errors="coerce").fillna(
                        0
                    )
                    total = valores_numericos.sum()
                    total_general += total
                    print(f"  • {col}: {total:,.0f} vacunados")

            # Agregar totales de consolidación
            total_consolidacion = 0
            for col in consolidation_cols:
                if col in df.columns:
                    # Convertir a numérico de forma segura
                    valores_numericos = pd.to_numeric(df[col], errors="coerce").fillna(
                        0
                    )
                    total_consolidacion += valores_numericos.sum()

            if total_consolidacion > 0:
                print_status(
                    f"Total a consolidar en 60+: {total_consolidacion:,}", "warning"
                )
                total_general += total_consolidacion

            print_status(
                f"TOTAL GENERAL BARRIDOS: {total_general:,} vacunados", "success"
            )
        else:
            print_status("No se encontraron columnas de rangos de edad", "warning")

        # Verificar calidad de datos
        registros_completos = 0
        for idx, row in df.iterrows():
            tiene_fecha = pd.notna(row.get(found_columns.get("fecha")))
            tiene_municipio = pd.notna(row.get(found_columns.get("municipio")))

            # Verificar datos de edad de forma segura
            tiene_datos_edad = False
            for col in edad_cols:
                try:
                    valor = row.get(col, 0)
                    if pd.notna(valor):
                        # Convertir a numérico de forma segura
                        valor_num = pd.to_numeric(valor, errors="coerce")
                        if not pd.isna(valor_num) and valor_num > 0:
                            tiene_datos_edad = True
                            break
                except:
                    continue

            if tiene_fecha and tiene_municipio and tiene_datos_edad:
                registros_completos += 1

        porcentaje_completos = (
            (registros_completos / len(df)) * 100 if len(df) > 0 else 0
        )
        print_status(
            f"Registros completos: {registros_completos}/{len(df)} ({porcentaje_completos:.1f}%)",
            "success" if porcentaje_completos > 80 else "warning",
        )

        return True

    except Exception as e:
        print_status(f"Error procesando archivo: {str(e)}", "error")
        return False


def validate_population_data():
    """Valida datos de población por EAPB"""
    print_header("VALIDACIÓN DATOS POBLACIÓN")

    file_path = "data/Poblacion_aseguramiento.xlsx"

    if not os.path.exists(file_path):
        print_status(f"Archivo no encontrado: {file_path}", "warning")
        return False

    try:
        df = pd.read_excel(file_path)
        print_status(f"Archivo cargado: {len(df):,} registros", "success")

        # Mostrar columnas
        print_status(f"Columnas: {list(df.columns)}", "info")

        # Buscar columnas clave
        municipio_col = None
        eapb_col = None
        poblacion_col = None

        for col in df.columns:
            col_upper = str(col).upper()
            if "MUNICIPIO" in col_upper:
                municipio_col = col
            elif (
                "EAPB" in col_upper
                or "ASEGURADORA" in col_upper
                or "NOMBRE ENTIDAD" in col_upper
                or "ENTIDAD" in col_upper
            ):
                eapb_col = col
            elif "TOTAL" in col_upper or "POBLACION" in col_upper:
                poblacion_col = col

        if municipio_col:
            municipios = df[municipio_col].nunique()
            print_status(f"Municipios únicos: {municipios}", "success")
        else:
            print_status("No se encontró columna de municipio", "warning")

        if eapb_col:
            eapb_count = df[eapb_col].nunique()
            print_status(f"EAPB únicas: {eapb_count}", "success")

            # Verificar múltiples EAPB por municipio
            if municipio_col:
                eapb_por_municipio = df.groupby(municipio_col)[eapb_col].nunique()
                max_eapb = eapb_por_municipio.max()
                avg_eapb = eapb_por_municipio.mean()
                municipios_multiples = (eapb_por_municipio > 1).sum()

                print_status(f"Máximo EAPB por municipio: {max_eapb}", "info")
                print_status(f"Promedio EAPB por municipio: {avg_eapb:.1f}", "info")
                print_status(
                    f"Municipios con múltiples EAPB: {municipios_multiples}", "info"
                )

                if max_eapb > 1:
                    print_status(
                        "✅ Estructura correcta: Múltiples EAPB por municipio detectada",
                        "success",
                    )
        else:
            print_status("No se encontró columna de EAPB", "warning")

        if poblacion_col:
            total_poblacion = df[poblacion_col].sum()
            print_status(f"Población total: {total_poblacion:,}", "success")

            # Estadísticas de población
            poblacion_min = df[poblacion_col].min()
            poblacion_max = df[poblacion_col].max()
            poblacion_promedio = df[poblacion_col].mean()

            print_status(
                f"Rango población: {poblacion_min:,} - {poblacion_max:,}", "info"
            )
            print_status(f"Promedio por registro: {poblacion_promedio:,.0f}", "info")
        else:
            print_status("No se encontró columna de población", "warning")

        return True

    except Exception as e:
        print_status(f"Error procesando archivo: {str(e)}", "error")
        return False


def validate_assets():
    """Valida archivos de assets"""
    print_header("VALIDACIÓN ASSETS")

    logo_path = "assets/images/logo_gobernacion.png"

    if os.path.exists(logo_path):
        size = os.path.getsize(logo_path)
        print_status(f"Logo encontrado: {logo_path} ({size:,} bytes)", "success")
    else:
        print_status(f"Logo no encontrado: {logo_path}", "warning")
        print_status("Ejecuta: python setup_assets.py", "info")

    # Verificar estructura de directorios
    required_dirs = ["data", "assets/images", "logs"]
    for directory in required_dirs:
        if os.path.exists(directory):
            print_status(f"Directorio existe: {directory}", "success")
        else:
            print_status(f"Directorio faltante: {directory}", "warning")


def validate_age_calculation_logic():
    """Valida la lógica de cálculo de edades"""
    print_header("VALIDACIÓN LÓGICA DE CÁLCULO DE EDAD")

    # Casos de prueba
    test_cases = [
        {
            "descripcion": "Bebé de 6 meses",
            "fecha_nacimiento": "2024-06-01",
            "fecha_vacunacion": "2024-12-01",
            "edad_esperada": 0,
            "rango_esperado": "<1",
        },
        {
            "descripcion": "Niño de 3 años",
            "fecha_nacimiento": "2021-01-15",
            "fecha_vacunacion": "2024-03-15",
            "edad_esperada": 3,
            "rango_esperado": "1-5",
        },
        {
            "descripcion": "Niño de 8 años",
            "fecha_nacimiento": "2016-05-10",
            "fecha_vacunacion": "2024-07-10",
            "edad_esperada": 8,
            "rango_esperado": "6-10",
        },
        {
            "descripcion": "Adolescente de 15 años",
            "fecha_nacimiento": "2009-02-20",
            "fecha_vacunacion": "2024-04-20",
            "edad_esperada": 15,
            "rango_esperado": "11-20",
        },
        {
            "descripcion": "Adulto de 35 años",
            "fecha_nacimiento": "1989-08-12",
            "fecha_vacunacion": "2024-10-12",
            "edad_esperada": 35,
            "rango_esperado": "31-40",
        },
        {
            "descripcion": "Adulto mayor de 65 años",
            "fecha_nacimiento": "1959-03-05",
            "fecha_vacunacion": "2024-06-05",
            "edad_esperada": 65,
            "rango_esperado": "60+",
        },
    ]

    print_status("Ejecutando casos de prueba...", "info")

    errores = 0
    for i, case in enumerate(test_cases, 1):
        try:
            fecha_nac = pd.to_datetime(case["fecha_nacimiento"])
            fecha_vac = pd.to_datetime(case["fecha_vacunacion"])

            edad_calculada = calculate_age_sample(fecha_nac, fecha_vac)

            # Determinar rango
            if edad_calculada < 1:
                rango_calculado = "<1"
            elif 1 <= edad_calculada <= 5:
                rango_calculado = "1-5"
            elif 6 <= edad_calculada <= 10:
                rango_calculado = "6-10"
            elif 11 <= edad_calculada <= 20:
                rango_calculado = "11-20"
            elif 21 <= edad_calculada <= 30:
                rango_calculado = "21-30"
            elif 31 <= edad_calculada <= 40:
                rango_calculado = "31-40"
            elif 41 <= edad_calculada <= 50:
                rango_calculado = "41-50"
            elif 51 <= edad_calculada <= 59:
                rango_calculado = "51-59"
            else:
                rango_calculado = "60+"

            # Verificar resultados
            edad_correcta = edad_calculada == case["edad_esperada"]
            rango_correcto = rango_calculado == case["rango_esperado"]

            if edad_correcta and rango_correcto:
                print_status(f"Caso {i}: {case['descripcion']} ✅", "success")
            else:
                print_status(f"Caso {i}: {case['descripcion']} ❌", "error")
                print(
                    f"  Esperado: {case['edad_esperada']} años, rango {case['rango_esperado']}"
                )
                print(f"  Calculado: {edad_calculada} años, rango {rango_calculado}")
                errores += 1

        except Exception as e:
            print_status(f"Caso {i}: Error - {str(e)}", "error")
            errores += 1

    if errores == 0:
        print_status("✅ Todos los casos de prueba pasaron correctamente", "success")
    else:
        print_status(f"❌ {errores} casos de prueba fallaron", "error")

    return errores == 0


def generate_summary_report():
    """Genera reporte resumen"""
    print_header("REPORTE RESUMEN")

    files_status = {
        "Históricos": os.path.exists("data/vacunacion_fa.csv"),
        "Barridos": os.path.exists("data/Resumen.xlsx"),
        "Población": os.path.exists("data/Poblacion_aseguramiento.xlsx"),
        "Logo": os.path.exists("assets/images/logo_gobernacion.png"),
    }

    print("Estado de archivos críticos:")
    for name, exists in files_status.items():
        status = "success" if exists else "error"
        print_status(f"{name}: {'Disponible' if exists else 'Faltante'}", status)

    missing_count = sum(1 for exists in files_status.values() if not exists)

    # Mostrar rangos de edad configurados
    print_status("Rangos de edad configurados:", "info")
    for codigo, descripcion in RANGOS_EDAD_ESPERADOS.items():
        print(f"  • {codigo}: {descripcion}")

    if missing_count == 0:
        print_status("¡Todos los archivos están disponibles!", "success")
        print_status("Puedes ejecutar: streamlit run app.py", "info")
    else:
        print_status(f"{missing_count} archivo(s) faltante(s)", "warning")
        print_status(
            "Revisa la documentación para obtener los archivos necesarios", "info"
        )


def main():
    """Función principal de validación"""
    print("🔍 VALIDADOR DE DATOS - DASHBOARD FIEBRE AMARILLA")
    print("📊 Versión con rangos de edad actualizados")
    print(f"Ejecutado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    # Ejecutar validaciones
    validations = [
        validate_historical_data,
        validate_barridos_data,
        validate_population_data,
        validate_assets,
        validate_age_calculation_logic,
    ]

    results = []
    for validation in validations:
        try:
            result = validation()
            results.append(result)
        except Exception as e:
            print_status(f"Error en validación: {str(e)}", "error")
            results.append(False)

    # Reporte final
    generate_summary_report()

    # Código de salida
    if all(results):
        print_status("✅ Validación completada exitosamente", "success")
        print_status(
            "El dashboard está listo para calcular edades desde fecha de nacimiento",
            "info",
        )
        sys.exit(0)
    else:
        print_status("⚠️ Validación completada con advertencias", "warning")
        print_status("Revisa los errores antes de ejecutar el dashboard", "info")
        sys.exit(1)


if __name__ == "__main__":
    main()
