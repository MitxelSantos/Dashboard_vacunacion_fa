"""
src/data/age_calculator.py
Calculador especializado de edades actuales para datos de vacunación
Calcula edad basada en fecha de nacimiento y fecha actual (no al momento de vacunación)
"""

import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import warnings


class AgeCalculator:
    """
    Calculador de edades actuales con categorización en grupos estándar
    """

    def __init__(self):
        self.age_groups = {
            "Menor de 1 año": (0, 0),
            "1 a 4 años": (1, 4),
            "5 a 9 años": (5, 9),
            "10 a 19 años": (10, 19),
            "20 a 29 años": (20, 29),
            "30 a 39 años": (30, 39),
            "40 a 49 años": (40, 49),
            "50 a 59 años": (50, 59),
            "60 a 69 años": (60, 69),
            "70 años o más": (70, 999),
        }
        self.calculation_stats = {
            "total_processed": 0,
            "successful_calculations": 0,
            "invalid_dates": 0,
            "future_dates": 0,
            "unrealistic_ages": 0,
            "processing_date": datetime.now(),
        }

    def calculate_ages_for_dataframe(
        self,
        df,
        birth_date_column="FechaNacimiento",
        target_age_column="edad_actual",
        target_group_column="grupo_edad",
        reference_date=None,
    ):
        """
        Calcula edades actuales para todo un DataFrame

        Args:
            df: DataFrame con datos
            birth_date_column: Nombre de la columna con fechas de nacimiento
            target_age_column: Nombre para la nueva columna de edad
            target_group_column: Nombre para la nueva columna de grupo de edad
            reference_date: Fecha de referencia (por defecto fecha actual)

        Returns:
            DataFrame con columnas de edad añadidas
        """
        if df is None or len(df) == 0:
            st.warning("⚠️ DataFrame vacío para cálculo de edades")
            return df

        if birth_date_column not in df.columns:
            st.error(f"❌ Columna '{birth_date_column}' no encontrada")
            return df

        st.info(f"🔢 Calculando edades actuales para {len(df)} registros...")

        df_result = df.copy()
        reference_date = reference_date or datetime.now().date()

        # Estadísticas de procesamiento
        self.calculation_stats["total_processed"] = len(df)
        self.calculation_stats["processing_date"] = datetime.now()

        # Convertir fechas de nacimiento
        df_result[birth_date_column] = pd.to_datetime(
            df_result[birth_date_column], errors="coerce"
        )

        # Calcular edades
        ages = []
        groups = []

        for idx, birth_date in enumerate(df_result[birth_date_column]):
            age, group = self._calculate_single_age(birth_date, reference_date)
            ages.append(age)
            groups.append(group)

            # Actualizar estadísticas
            if age is not None:
                self.calculation_stats["successful_calculations"] += 1
            elif pd.isna(birth_date):
                self.calculation_stats["invalid_dates"] += 1

        # Asignar resultados
        df_result[target_age_column] = ages
        df_result[target_group_column] = groups

        # Mostrar resumen
        self._show_calculation_summary()

        st.success(
            f"✅ Edades calculadas: {self.calculation_stats['successful_calculations']} exitosas de {len(df)} registros"
        )

        return df_result

    def _calculate_single_age(self, birth_date, reference_date):
        """
        Calcula edad individual con validaciones
        """
        if pd.isna(birth_date):
            return None, "Sin dato"

        try:
            # Convertir a date si es datetime
            if isinstance(birth_date, pd.Timestamp):
                birth_date = birth_date.date()
            elif isinstance(birth_date, datetime):
                birth_date = birth_date.date()

            if isinstance(reference_date, datetime):
                reference_date = reference_date.date()

            # Validaciones
            if birth_date > reference_date:
                self.calculation_stats["future_dates"] += 1
                return None, "Fecha futura"

            # Calcular edad precisa
            age = reference_date.year - birth_date.year

            # Ajustar si el cumpleaños no ha ocurrido este año
            if (reference_date.month, reference_date.day) < (
                birth_date.month,
                birth_date.day,
            ):
                age -= 1

            # Validar rango realista
            if age < 0:
                self.calculation_stats["invalid_dates"] += 1
                return None, "Edad negativa"
            elif age > 120:
                self.calculation_stats["unrealistic_ages"] += 1
                return age, "Edad no realista"  # Mantener pero marcar

            # Categorizar en grupo
            group = self._categorize_age(age)

            return age, group

        except Exception as e:
            self.calculation_stats["invalid_dates"] += 1
            return None, "Error en cálculo"

    def _categorize_age(self, age):
        """
        Categoriza edad en grupos estándar del Tolima
        """
        if age is None:
            return "Sin dato"

        # Buscar el grupo correspondiente
        for group_name, (min_age, max_age) in self.age_groups.items():
            if min_age <= age <= max_age:
                return group_name

        # Por defecto, si es mayor a todos los rangos
        return "70 años o más"

    def _show_calculation_summary(self):
        """
        Muestra resumen del cálculo de edades
        """
        stats = self.calculation_stats

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Procesados", f"{stats['total_processed']:,}".replace(",", ".")
            )

        with col2:
            success_rate = (
                (stats["successful_calculations"] / stats["total_processed"] * 100)
                if stats["total_processed"] > 0
                else 0
            )
            st.metric(
                "Cálculos Exitosos",
                f"{stats['successful_calculations']:,}".replace(",", "."),
                delta=f"{success_rate:.1f}%",
            )

        with col3:
            st.metric("Fechas Inválidas", stats["invalid_dates"])

        with col4:
            st.metric("Fechas Futuras", stats["future_dates"])

        # Advertencias si hay problemas
        if stats["future_dates"] > 0:
            st.warning(
                f"⚠️ {stats['future_dates']} registros con fechas de nacimiento futuras"
            )

        if stats["unrealistic_ages"] > 0:
            st.warning(f"⚠️ {stats['unrealistic_ages']} registros con edades >120 años")

        if stats["invalid_dates"] > stats["total_processed"] * 0.1:  # Más del 10%
            st.error(
                f"❌ Alto porcentaje de fechas inválidas ({stats['invalid_dates']/stats['total_processed']*100:.1f}%)"
            )

    def get_age_distribution(
        self, df, age_column="edad_actual", group_column="grupo_edad"
    ):
        """
        Obtiene distribución de edades calculadas
        """
        if df is None or len(df) == 0:
            return None

        distribution = {
            "by_individual_age": (
                df[age_column].value_counts().sort_index()
                if age_column in df.columns
                else None
            ),
            "by_age_group": (
                df[group_column].value_counts() if group_column in df.columns else None
            ),
            "statistics": {
                "mean_age": df[age_column].mean() if age_column in df.columns else None,
                "median_age": (
                    df[age_column].median() if age_column in df.columns else None
                ),
                "min_age": df[age_column].min() if age_column in df.columns else None,
                "max_age": df[age_column].max() if age_column in df.columns else None,
                "std_age": df[age_column].std() if age_column in df.columns else None,
            },
        }

        return distribution

    def validate_age_data(
        self, df, age_column="edad_actual", group_column="grupo_edad"
    ):
        """
        Valida la calidad de los datos de edad calculados
        """
        if df is None or len(df) == 0 or age_column not in df.columns:
            return {"valid": False, "errors": ["DataFrame vacío o columna faltante"]}

        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {},
        }

        # Verificar valores nulos
        null_count = df[age_column].isna().sum()
        null_percentage = null_count / len(df) * 100

        if null_percentage > 20:
            validation_results["errors"].append(
                f"Alto porcentaje de edades nulas: {null_percentage:.1f}%"
            )
            validation_results["valid"] = False
        elif null_percentage > 5:
            validation_results["warnings"].append(
                f"Porcentaje moderado de edades nulas: {null_percentage:.1f}%"
            )

        # Verificar rango de edades
        valid_ages = df[df[age_column].notna()][age_column]

        if len(valid_ages) > 0:
            min_age = valid_ages.min()
            max_age = valid_ages.max()

            if min_age < 0:
                validation_results["errors"].append(
                    f"Edades negativas encontradas: mínimo {min_age}"
                )
                validation_results["valid"] = False

            if max_age > 120:
                validation_results["warnings"].append(
                    f"Edades muy altas encontradas: máximo {max_age}"
                )

            # Verificar distribución lógica
            mean_age = valid_ages.mean()
            if mean_age < 10 or mean_age > 80:
                validation_results["warnings"].append(
                    f"Edad promedio inusual: {mean_age:.1f} años"
                )

        # Verificar grupos de edad
        if group_column in df.columns:
            group_counts = df[group_column].value_counts()
            expected_groups = set(self.age_groups.keys())
            actual_groups = set(group_counts.index)

            unexpected_groups = (
                actual_groups
                - expected_groups
                - {"Sin dato", "Fecha futura", "Edad no realista", "Error en cálculo"}
            )

            if unexpected_groups:
                validation_results["warnings"].append(
                    f"Grupos de edad inesperados: {list(unexpected_groups)}"
                )

        validation_results["statistics"] = {
            "total_records": len(df),
            "valid_ages": len(valid_ages),
            "null_percentage": null_percentage,
            "mean_age": valid_ages.mean() if len(valid_ages) > 0 else None,
            "age_range": (min_age, max_age) if len(valid_ages) > 0 else None,
        }

        return validation_results

    def show_age_distribution_chart(self, df, group_column="grupo_edad"):
        """
        Muestra gráfico de distribución de edades
        """
        if df is None or len(df) == 0 or group_column not in df.columns:
            st.warning("⚠️ No hay datos suficientes para mostrar distribución")
            return

        # Preparar datos para gráfico
        distribution = df[group_column].value_counts().reset_index()
        distribution.columns = ["Grupo de Edad", "Cantidad"]

        # Ordenar grupos lógicamente
        ordered_groups = []
        for group_name in self.age_groups.keys():
            if group_name in distribution["Grupo de Edad"].values:
                ordered_groups.append(group_name)

        # Añadir grupos adicionales al final
        for group in distribution["Grupo de Edad"].values:
            if group not in ordered_groups:
                ordered_groups.append(group)

        # Reordenar DataFrame
        distribution["Grupo de Edad"] = pd.Categorical(
            distribution["Grupo de Edad"], categories=ordered_groups, ordered=True
        )
        distribution = distribution.sort_values("Grupo de Edad")

        # Mostrar gráfico usando Streamlit
        st.subheader("📊 Distribución por Grupos de Edad")
        st.bar_chart(distribution.set_index("Grupo de Edad"))

        # Mostrar tabla
        distribution["Porcentaje"] = (
            distribution["Cantidad"] / distribution["Cantidad"].sum() * 100
        ).round(1)
        st.dataframe(distribution, use_container_width=True)

    def get_calculation_stats(self):
        """
        Retorna estadísticas del cálculo
        """
        return self.calculation_stats.copy()


def calculate_current_ages(
    df,
    birth_date_column="FechaNacimiento",
    target_age_column="edad_actual",
    target_group_column="grupo_edad",
    reference_date=None,
):
    """
    Función de conveniencia para calcular edades actuales
    """
    calculator = AgeCalculator()
    result_df = calculator.calculate_ages_for_dataframe(
        df, birth_date_column, target_age_column, target_group_column, reference_date
    )

    return {
        "dataframe": result_df,
        "distribution": calculator.get_age_distribution(
            result_df, target_age_column, target_group_column
        ),
        "validation": calculator.validate_age_data(
            result_df, target_age_column, target_group_column
        ),
        "stats": calculator.get_calculation_stats(),
    }


def test_age_calculator():
    """
    Función de prueba del calculador de edades
    """
    st.title("🧪 Prueba del Calculador de Edades")

    # Crear datos de prueba
    test_dates = [
        "1990-05-15",  # ~33 años
        "2000-12-25",  # ~23 años
        "1975-08-10",  # ~48 años
        "2010-03-20",  # ~13 años
        "1960-01-01",  # ~63 años
        None,  # Sin dato
        "2025-01-01",  # Fecha futura
        "1920-01-01",  # Edad no realista
    ]

    test_df = pd.DataFrame(
        {
            "ID": range(1, len(test_dates) + 1),
            "FechaNacimiento": test_dates,
            "Nombre": [f"Persona {i}" for i in range(1, len(test_dates) + 1)],
        }
    )

    st.subheader("📋 Datos de Prueba")
    st.dataframe(test_df, use_container_width=True)

    # Calcular edades
    result = calculate_current_ages(test_df)

    if result:
        st.subheader("📊 Resultados del Cálculo")
        st.dataframe(result["dataframe"], use_container_width=True)

        # Mostrar distribución
        calculator = AgeCalculator()
        calculator.show_age_distribution_chart(result["dataframe"])

        # Mostrar validación
        validation = result["validation"]
        if validation["valid"]:
            st.success("✅ Validación exitosa")
        else:
            st.error("❌ Errores en validación:")
            for error in validation["errors"]:
                st.write(f"  • {error}")

        if validation["warnings"]:
            st.warning("⚠️ Advertencias:")
            for warning in validation["warnings"]:
                st.write(f"  • {warning}")


if __name__ == "__main__":
    test_age_calculator()
