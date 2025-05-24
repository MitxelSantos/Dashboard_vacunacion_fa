#!/usr/bin/env python3
"""
Script para validar la normalización de EAPB
Desarrollado para Dashboard de Vacunación - Fiebre Amarilla del Tolima
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd


def validate_eapb_normalization():
    """
    Valida que la normalización de EAPB esté funcionando correctamente
    """
    print("🔍 Validando Normalización de EAPB")
    print("=" * 50)

    try:
        # 1. Validar que los módulos se importen correctamente
        print("1️⃣ Validando importación de módulos...")

        try:
            from src.data.eapb_mappings import ALL_EAPB_MAPPINGS, get_eapb_stats

            print("   ✅ Módulo eapb_mappings importado correctamente")
        except ImportError as e:
            print(f"   ❌ Error importando eapb_mappings: {e}")
            return False

        try:
            from src.data.eapb_normalizer import (
                normalize_eapb_names,
                validate_eapb_mapping,
            )

            print("   ✅ Módulo eapb_normalizer importado correctamente")
        except ImportError as e:
            print(f"   ❌ Error importando eapb_normalizer: {e}")
            return False

        # 2. Validar mapeos
        print("\n2️⃣ Validando mapeos de EAPB...")

        stats = get_eapb_stats()
        print(f"   📊 Total de mapeos: {stats['total_mappings']}")
        print(f"   📊 Nombres canónicos únicos: {stats['unique_canonical_names']}")
        print(
            f"   📊 Registros estimados afectados: {stats['affected_records_estimate']:,}".replace(
                ",", "."
            )
        )

        # Validar consistencia de mapeos
        validate_result = validate_eapb_mapping()
        if validate_result:
            print("   ✅ Mapeos validados correctamente")
        else:
            print("   ⚠️ Advertencias en validación de mapeos")

        # 3. Probar carga de datos (si están disponibles)
        print("\n3️⃣ Probando carga de datos...")

        try:
            from src.data.loader import load_datasets

            # Intentar cargar datos
            data = load_datasets()

            if (
                "vacunacion" in data
                and "NombreAseguradora" in data["vacunacion"].columns
            ):
                # Analizar el impacto de la normalización
                vacunacion_df = data["vacunacion"]

                # Verificar si se aplicó la normalización
                if "NombreAseguradora_original" in vacunacion_df.columns:
                    print(
                        "   ✅ Normalización aplicada (se encontró columna de respaldo)"
                    )

                    # Analizar cambios
                    original_unique = vacunacion_df[
                        "NombreAseguradora_original"
                    ].nunique()
                    normalized_unique = vacunacion_df["NombreAseguradora"].nunique()

                    print(f"   📊 EAPB únicas antes: {original_unique}")
                    print(f"   📊 EAPB únicas después: {normalized_unique}")
                    print(
                        f"   📊 Reducción: {original_unique - normalized_unique} ({((original_unique - normalized_unique) / original_unique * 100):.1f}%)"
                    )

                    # Mostrar algunos ejemplos de normalización
                    changes = vacunacion_df[
                        vacunacion_df["NombreAseguradora"]
                        != vacunacion_df["NombreAseguradora_original"]
                    ]

                    if len(changes) > 0:
                        print(
                            f"   📊 Total de registros normalizados: {len(changes):,}".replace(
                                ",", "."
                            )
                        )

                        # Mostrar ejemplos
                        print("\n   📋 Ejemplos de normalización aplicada:")
                        examples = (
                            changes.groupby(
                                ["NombreAseguradora_original", "NombreAseguradora"]
                            )
                            .size()
                            .reset_index()
                        )
                        examples.columns = ["Original", "Normalizado", "Registros"]
                        examples = examples.sort_values(
                            "Registros", ascending=False
                        ).head(5)

                        for _, row in examples.iterrows():
                            print(
                                f"      '{row['Original']}' → '{row['Normalizado']}' ({row['Registros']:,} registros)".replace(
                                    ",", "."
                                )
                            )

                else:
                    print("   ⚠️ No se encontró evidencia de normalización aplicada")
                    print(
                        "   💡 Verificar que la normalización esté habilitada en loader.py"
                    )

            else:
                print("   ⚠️ No se pudieron cargar datos de vacunación para validación")

        except Exception as e:
            print(f"   ⚠️ Error cargando datos para validación: {str(e)}")

        # 4. Validar algunas normalizaciones específicas
        print("\n4️⃣ Probando normalización en datos de ejemplo...")

        # Crear datos de prueba
        test_data = pd.DataFrame(
            {
                "NombreAseguradora": [
                    "LA NUEVA EPS S.A.",
                    "LA NUEVA EPS S.A.-CM",
                    "SALUD TOTAL S.A. E.P.S.",
                    "SALUD TOTAL S.A. E.P.S. CM",
                    "MEDIMAS EPS S.A.S",
                    "MEDIMÁS EPS S.A.S. -CM",
                    "Sin dato",
                    "OTRA EPS NO MAPEADA",
                ]
            }
        )

        # Aplicar normalización
        test_normalized = normalize_eapb_names(
            test_data, "NombreAseguradora", ALL_EAPB_MAPPINGS
        )

        # Verificar resultados
        expected_results = {
            "LA NUEVA EPS S.A.": "LA NUEVA EPS S.A.",
            "LA NUEVA EPS S.A.-CM": "LA NUEVA EPS S.A.",
            "SALUD TOTAL S.A. E.P.S.": "SALUD TOTAL S.A. E.P.S.",
            "SALUD TOTAL S.A. E.P.S. CM": "SALUD TOTAL S.A. E.P.S.",
            "MEDIMAS EPS S.A.S": "MEDIMAS EPS S.A.S",
            "MEDIMÁS EPS S.A.S. -CM": "MEDIMAS EPS S.A.S",
            "Sin dato": "Sin dato",
            "OTRA EPS NO MAPEADA": "OTRA EPS NO MAPEADA",
        }

        all_correct = True
        for i, row in test_data.iterrows():
            original = row["NombreAseguradora"]
            normalized = test_normalized.iloc[i]["NombreAseguradora"]
            expected = expected_results[original]

            if normalized == expected:
                print(f"   ✅ '{original}' → '{normalized}'")
            else:
                print(f"   ❌ '{original}' → '{normalized}' (esperado: '{expected}')")
                all_correct = False

        if all_correct:
            print("   ✅ Todas las normalizaciones de prueba funcionaron correctamente")
        else:
            print("   ❌ Algunas normalizaciones de prueba fallaron")
            return False

        # 5. Resumen final
        print("\n" + "=" * 50)
        print("🎉 VALIDACIÓN COMPLETADA")
        print("✅ La normalización de EAPB está funcionando correctamente")
        print("\n💡 Próximos pasos:")
        print(
            "   1. Ejecutar el dashboard y verificar que los datos se muestren correctamente"
        )
        print(
            "   2. Revisar las vistas de aseguramiento para confirmar la consolidación"
        )
        print("   3. Verificar que los filtros funcionen con los nombres normalizados")

        return True

    except Exception as e:
        print(f"\n❌ Error durante la validación: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def analyze_eapb_impact():
    """
    Analiza el impacto de la normalización en los datos reales
    """
    print("\n🔍 Analizando impacto de la normalización...")

    try:
        from src.data.loader import load_datasets

        data = load_datasets()

        if (
            "vacunacion" not in data
            or "NombreAseguradora" not in data["vacunacion"].columns
        ):
            print("❌ No se pudieron cargar los datos para análisis")
            return

        df = data["vacunacion"]

        if "NombreAseguradora_original" not in df.columns:
            print(
                "⚠️ No se encontró columna de respaldo - no se puede analizar el impacto"
            )
            return

        # Análisis detallado
        print("\n📊 ANÁLISIS DE IMPACTO:")

        # 1. EAPB más afectadas por la normalización
        changes = df[df["NombreAseguradora"] != df["NombreAseguradora_original"]]

        if len(changes) > 0:
            print(
                f"\n1️⃣ Total de registros normalizados: {len(changes):,}".replace(
                    ",", "."
                )
            )
            print(f"   Porcentaje del total: {len(changes)/len(df)*100:.1f}%")

            # Agrupaciones más importantes
            major_changes = (
                changes.groupby(["NombreAseguradora_original", "NombreAseguradora"])
                .size()
                .reset_index()
            )
            major_changes.columns = ["Original", "Normalizado", "Registros"]
            major_changes = major_changes.sort_values("Registros", ascending=False)

            print("\n2️⃣ Top 10 normalizaciones por impacto:")
            for i, row in major_changes.head(10).iterrows():
                print(
                    f"   {row['Registros']:6,} registros: '{row['Original']}' → '{row['Normalizado']}'".replace(
                        ",", "."
                    )
                )

            # Análisis por grupo de normalización
            print("\n3️⃣ Consolidaciones más significativas:")
            consolidated = (
                df.groupby("NombreAseguradora")
                .agg(
                    {
                        "NombreAseguradora_original": "nunique",
                        "IdPaciente": "count",  # Usar IdPaciente en lugar de NombreAseguradora
                    }
                )
                .reset_index()
            )
            consolidated.columns = [
                "EAPB_Normalizada",
                "Variantes_Originales",
                "Total_Registros",
            ]
            consolidated["Beneficio"] = consolidated["Variantes_Originales"] - 1

            # Mostrar solo las que tuvieron consolidación
            significant = consolidated[consolidated["Beneficio"] > 0].sort_values(
                "Beneficio", ascending=False
            )

            for _, row in significant.head(10).iterrows():
                print(
                    f"   '{row['EAPB_Normalizada']}': {row['Variantes_Originales']} variantes → 1 nombre ({row['Total_Registros']:,} registros)".replace(
                        ",", "."
                    )
                )

        else:
            print("ℹ️ No se detectaron cambios por normalización")

        # 4. Estadísticas finales
        original_unique = df["NombreAseguradora_original"].nunique()
        final_unique = df["NombreAseguradora"].nunique()

        print(f"\n4️⃣ Resumen final:")
        print(f"   EAPB únicas antes: {original_unique}")
        print(f"   EAPB únicas después: {final_unique}")
        print(f"   Reducción absoluta: {original_unique - final_unique}")
        print(
            f"   Reducción porcentual: {(original_unique - final_unique)/original_unique*100:.1f}%"
        )

    except Exception as e:
        print(f"❌ Error en análisis de impacto: {str(e)}")


def main():
    """
    Función principal del script de validación
    """
    print("🚀 Script de Validación - Normalización EAPB")
    print("Dashboard de Vacunación - Fiebre Amarilla del Tolima")
    print("=" * 60)

    # Validación principal
    validation_success = validate_eapb_normalization()

    if validation_success:
        # Análisis de impacto si la validación fue exitosa
        analyze_eapb_impact()
    else:
        print("\n❌ La validación falló. Revisa los errores anteriores.")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
