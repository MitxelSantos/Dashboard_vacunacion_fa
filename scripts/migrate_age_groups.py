#!/usr/bin/env python3
"""
Script para migrar grupos de edad existentes a los nuevos rangos
Dashboard de Vacunación - Fiebre Amarilla del Tolima
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd


def migrate_age_groups():
    """
    Migra los grupos de edad existentes a los nuevos rangos
    """
    print("🔄 Migrando Grupos de Edad a Nuevos Rangos")
    print("=" * 50)

    try:
        # Cargar datos
        print("1️⃣ Cargando datos...")
        from src.data.loader import load_datasets

        data = load_datasets()

        if "vacunacion" not in data:
            print("❌ No se encontraron datos de vacunación")
            return False

        df = data["vacunacion"]

        # Verificar columnas de edad
        if "Edad_Vacunacion" not in df.columns:
            print("❌ No se encontró columna 'Edad_Vacunacion'")
            return False

        print(f"   📊 Total de registros: {len(df):,}".replace(",", "."))

        # Analizar grupos de edad actuales
        print("\n2️⃣ Analizando grupos de edad actuales...")

        if "Grupo_Edad" in df.columns:
            current_groups = df["Grupo_Edad"].value_counts()
            print("   Grupos de edad actuales:")
            for group, count in current_groups.items():
                print(f"     {group}: {count:,} registros".replace(",", "."))

        # Aplicar nueva categorización
        print("\n3️⃣ Aplicando nueva categorización...")

        def categorize_age_new(age):
            """Nueva función de categorización"""
            try:
                age_num = float(age)
                if pd.isna(age_num):
                    return "Sin dato"
                elif age_num < 1:
                    return "Menor de 1 año"
                elif age_num < 5:
                    return "1 a 4 años"
                elif age_num < 10:
                    return "5 a 9 años"
                elif age_num < 20:
                    return "10 a 19 años"
                elif age_num < 30:
                    return "20 a 29 años"
                elif age_num < 40:
                    return "30 a 39 años"
                elif age_num < 50:
                    return "40 a 49 años"
                elif age_num < 60:
                    return "50 a 59 años"
                elif age_num < 70:
                    return "60 a 69 años"
                else:  # 70 años o más
                    return "70 años o más"
            except (ValueError, TypeError):
                return "Sin dato"

        # Crear nueva columna
        df["Grupo_Edad_Nuevo"] = df["Edad_Vacunacion"].apply(categorize_age_new)

        # Analizar nuevos grupos
        new_groups = df["Grupo_Edad_Nuevo"].value_counts()
        print("   Nuevos grupos de edad:")
        for group, count in new_groups.items():
            print(f"     {group}: {count:,} registros".replace(",", "."))

        # Comparar distribuciones
        print("\n4️⃣ Comparando distribuciones...")

        if "Grupo_Edad" in df.columns:
            # Crear tabla de migración
            migration_table = pd.crosstab(
                df["Grupo_Edad"], df["Grupo_Edad_Nuevo"], margins=True
            )

            print("   Tabla de migración (Anterior → Nuevo):")
            print(migration_table)

        # Estadísticas finales
        print(f"\n5️⃣ Estadísticas finales...")

        if "Grupo_Edad" in df.columns:
            old_unique = df["Grupo_Edad"].nunique()
            new_unique = df["Grupo_Edad_Nuevo"].nunique()
            print(f"   Grupos únicos antes: {old_unique}")
            print(f"   Grupos únicos después: {new_unique}")

        # Verificar que no se perdieron registros
        total_original = len(df)
        total_new = df["Grupo_Edad_Nuevo"].notna().sum()
        missing = total_original - total_new

        if missing == 0:
            print("   ✅ No se perdieron registros en la migración")
        else:
            print(f"   ⚠️ Se perdieron {missing} registros en la migración")

        print("\n" + "=" * 50)
        print("🎉 MIGRACIÓN COMPLETADA")
        print("✅ Los nuevos rangos de edad están listos para usar")
        print("\n💡 Próximos pasos:")
        print("   1. Reiniciar el dashboard")
        print("   2. Verificar que los filtros muestren los nuevos rangos")
        print("   3. Revisar los gráficos de distribución por edad")

        return True

    except Exception as e:
        print(f"\n❌ Error durante la migración: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def validate_new_age_groups():
    """
    Valida que los nuevos grupos de edad estén funcionando correctamente
    """
    print("\n🔍 Validando nuevos grupos de edad...")

    try:
        from src.data.loader import load_datasets

        data = load_datasets()
        df = data["vacunacion"]

        if "Grupo_Edad" not in df.columns:
            print("❌ No se encontró columna Grupo_Edad")
            return False

        # Verificar que se usen los nuevos rangos
        expected_ranges = [
            "Menor de 1 año",
            "1 a 4 años",
            "5 a 9 años",
            "10 a 19 años",
            "20 a 29 años",
            "30 a 39 años",
            "40 a 49 años",
            "50 a 59 años",
            "60 a 69 años",
            "70 años o más",
        ]

        actual_ranges = df["Grupo_Edad"].unique()

        print("✅ Rangos encontrados en los datos:")
        for range_name in actual_ranges:
            if range_name in expected_ranges:
                count = (df["Grupo_Edad"] == range_name).sum()
                print(f"   ✅ {range_name}: {count:,} registros".replace(",", "."))
            elif str(range_name) != "Sin dato":
                count = (df["Grupo_Edad"] == range_name).sum()
                print(
                    f"   ⚠️ {range_name}: {count:,} registros (inesperado)".replace(
                        ",", "."
                    )
                )

        # Contar "Sin dato"
        sin_dato = (df["Grupo_Edad"] == "Sin dato").sum()
        if sin_dato > 0:
            print(f"   ℹ️ Sin dato: {sin_dato:,} registros".replace(",", "."))

        return True

    except Exception as e:
        print(f"❌ Error en validación: {str(e)}")
        return False


def main():
    """
    Función principal del script de migración
    """
    print("🚀 Script de Migración - Nuevos Rangos de Edad")
    print("Dashboard de Vacunación - Fiebre Amarilla del Tolima")
    print("=" * 60)

    # Migración
    migration_success = migrate_age_groups()

    if migration_success:
        # Validación
        validate_new_age_groups()
    else:
        print("\n❌ La migración falló. Revisa los errores anteriores.")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
