"""
src/utils/date_utils.py
Utilidades especializadas para manejo de fechas en el dashboard de vacunación
Optimizado para la nueva estructura con división temporal automática
"""

import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import locale
from typing import Optional, Tuple, List, Union


class DateUtils:
    """
    Utilidades especializadas para manejo de fechas
    """

    def __init__(self):
        self.spanish_months = {
            1: "Enero",
            2: "Febrero",
            3: "Marzo",
            4: "Abril",
            5: "Mayo",
            6: "Junio",
            7: "Julio",
            8: "Agosto",
            9: "Septiembre",
            10: "Octubre",
            11: "Noviembre",
            12: "Diciembre",
        }

        self.spanish_days = {
            0: "Lunes",
            1: "Martes",
            2: "Miércoles",
            3: "Jueves",
            4: "Viernes",
            5: "Sábado",
            6: "Domingo",
        }

        # Intentar configurar locale español
        try:
            locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
        except:
            try:
                locale.setlocale(locale.LC_TIME, "Spanish_Spain.1252")
            except:
                pass  # Usar configuración por defecto

    def format_date_spanish(
        self, date_obj: Union[datetime, date, pd.Timestamp], format_type: str = "full"
    ) -> str:
        """
        Formatea fecha en español con diferentes opciones

        Args:
            date_obj: Objeto de fecha
            format_type: 'full', 'short', 'month_year', 'day_month'

        Returns:
            Fecha formateada en español
        """
        if pd.isna(date_obj) or date_obj is None:
            return "Sin fecha"

        # Convertir a datetime si es necesario
        if isinstance(date_obj, pd.Timestamp):
            date_obj = date_obj.to_pydatetime()
        elif isinstance(date_obj, date) and not isinstance(date_obj, datetime):
            date_obj = datetime.combine(date_obj, datetime.min.time())

        try:
            if format_type == "full":
                # "15 de enero de 2024"
                return f"{date_obj.day} de {self.spanish_months[date_obj.month].lower()} de {date_obj.year}"

            elif format_type == "short":
                # "15/01/2024"
                return date_obj.strftime("%d/%m/%Y")

            elif format_type == "month_year":
                # "Enero 2024"
                return f"{self.spanish_months[date_obj.month]} {date_obj.year}"

            elif format_type == "day_month":
                # "15 de enero"
                return (
                    f"{date_obj.day} de {self.spanish_months[date_obj.month].lower()}"
                )

            elif format_type == "weekday":
                # "Lunes 15 de enero"
                weekday = self.spanish_days[date_obj.weekday()]
                return f"{weekday} {date_obj.day} de {self.spanish_months[date_obj.month].lower()}"

            else:
                return date_obj.strftime("%d/%m/%Y")

        except Exception as e:
            return "Fecha inválida"

    def parse_date_flexible(
        self, date_str: Union[str, datetime, date]
    ) -> Optional[datetime]:
        """
        Parser flexible que maneja múltiples formatos de fecha
        """
        if pd.isna(date_str) or date_str is None:
            return None

        # Si ya es datetime, retornar
        if isinstance(date_str, (datetime, pd.Timestamp)):
            return pd.to_datetime(date_str)

        if isinstance(date_str, date):
            return datetime.combine(date_str, datetime.min.time())

        # Limpiar string
        date_str = str(date_str).strip()

        if date_str == "" or date_str.lower() in ["nan", "null", "none"]:
            return None

        # Formatos comunes a probar
        formats = [
            "%Y-%m-%d",  # 2024-01-15
            "%d/%m/%Y",  # 15/01/2024
            "%d-%m-%Y",  # 15-01-2024
            "%Y/%m/%d",  # 2024/01/15
            "%d/%m/%y",  # 15/01/24
            "%Y-%m-%d %H:%M:%S",  # 2024-01-15 10:30:00
            "%d/%m/%Y %H:%M:%S",  # 15/01/2024 10:30:00
            "%Y-%m-%d %H:%M",  # 2024-01-15 10:30
            "%d/%m/%Y %H:%M",  # 15/01/2024 10:30
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # Como último recurso, usar pandas
        try:
            return pd.to_datetime(date_str, errors="raise")
        except:
            return None

    def get_date_range_info(self, dates: pd.Series) -> dict:
        """
        Obtiene información completa sobre un rango de fechas
        """
        valid_dates = dates.dropna()

        if len(valid_dates) == 0:
            return {
                "count": 0,
                "min_date": None,
                "max_date": None,
                "range_days": 0,
                "range_text": "Sin fechas válidas",
                "period_months": 0,
                "period_years": 0,
            }

        min_date = valid_dates.min()
        max_date = valid_dates.max()
        range_days = (max_date - min_date).days

        # Calcular meses y años
        if isinstance(min_date, pd.Timestamp):
            min_date_dt = min_date.to_pydatetime()
            max_date_dt = max_date.to_pydatetime()
        else:
            min_date_dt = min_date
            max_date_dt = max_date

        period_months = (max_date_dt.year - min_date_dt.year) * 12 + (
            max_date_dt.month - min_date_dt.month
        )
        period_years = round(period_months / 12, 1)

        # Texto descriptivo del rango
        range_text = f"{self.format_date_spanish(min_date, 'short')} - {self.format_date_spanish(max_date, 'short')}"

        return {
            "count": len(valid_dates),
            "min_date": min_date,
            "max_date": max_date,
            "range_days": range_days,
            "range_text": range_text,
            "period_months": period_months,
            "period_years": period_years,
            "min_date_formatted": self.format_date_spanish(min_date, "full"),
            "max_date_formatted": self.format_date_spanish(max_date, "full"),
        }

    def detect_period_from_date(self, date_obj: datetime, cutoff_date: datetime) -> str:
        """
        Detecta si una fecha pertenece al período pre-emergencia o emergencia
        """
        if pd.isna(date_obj) or date_obj is None:
            return "sin_fecha"

        if pd.isna(cutoff_date) or cutoff_date is None:
            return "sin_referencia"

        if date_obj < cutoff_date:
            return "pre_emergencia"
        else:
            return "emergencia"

    def calculate_days_between(self, start_date: datetime, end_date: datetime) -> int:
        """
        Calcula días entre dos fechas
        """
        if pd.isna(start_date) or pd.isna(end_date):
            return 0

        try:
            return abs((end_date - start_date).days)
        except:
            return 0

    def get_month_boundaries(self, date_obj: datetime) -> Tuple[datetime, datetime]:
        """
        Obtiene primer y último día del mes para una fecha dada
        """
        if pd.isna(date_obj):
            return None, None

        # Primer día del mes
        first_day = date_obj.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Último día del mes
        if date_obj.month == 12:
            last_day = date_obj.replace(
                year=date_obj.year + 1, month=1, day=1
            ) - timedelta(days=1)
        else:
            last_day = date_obj.replace(month=date_obj.month + 1, day=1) - timedelta(
                days=1
            )

        last_day = last_day.replace(hour=23, minute=59, second=59, microsecond=999999)

        return first_day, last_day

    def create_date_series(
        self, start_date: datetime, end_date: datetime, freq: str = "D"
    ) -> pd.DatetimeIndex:
        """
        Crea serie de fechas entre dos puntos

        Args:
            start_date: Fecha inicio
            end_date: Fecha fin
            freq: Frecuencia ('D'=diario, 'W'=semanal, 'M'=mensual)
        """
        try:
            return pd.date_range(start=start_date, end=end_date, freq=freq)
        except:
            return pd.DatetimeIndex([])

    def get_vaccination_phases_info(
        self, vaccination_dates: pd.Series, cutoff_date: datetime
    ) -> dict:
        """
        Analiza las fases de vacunación basado en fecha de corte
        """
        if cutoff_date is None:
            return {
                "error": "Fecha de corte no disponible",
                "total_records": len(vaccination_dates),
            }

        # Convertir fechas
        valid_dates = pd.to_datetime(vaccination_dates, errors="coerce").dropna()

        if len(valid_dates) == 0:
            return {
                "error": "No hay fechas válidas",
                "total_records": len(vaccination_dates),
            }

        # Separar por fases
        pre_emergency = valid_dates[valid_dates < cutoff_date]
        emergency = valid_dates[valid_dates >= cutoff_date]

        # Información de fase histórica
        historical_info = (
            self.get_date_range_info(pre_emergency)
            if len(pre_emergency) > 0
            else {"count": 0, "range_text": "Sin datos históricos"}
        )

        # Información de fase emergencia
        emergency_info = (
            self.get_date_range_info(emergency)
            if len(emergency) > 0
            else {"count": 0, "range_text": "Sin datos de emergencia"}
        )

        return {
            "cutoff_date": cutoff_date,
            "cutoff_date_formatted": self.format_date_spanish(cutoff_date, "full"),
            "total_records": len(vaccination_dates),
            "valid_dates": len(valid_dates),
            "historical_phase": {
                "count": len(pre_emergency),
                "percentage": (
                    (len(pre_emergency) / len(valid_dates) * 100)
                    if len(valid_dates) > 0
                    else 0
                ),
                **historical_info,
            },
            "emergency_phase": {
                "count": len(emergency),
                "percentage": (
                    (len(emergency) / len(valid_dates) * 100)
                    if len(valid_dates) > 0
                    else 0
                ),
                **emergency_info,
            },
        }

    def format_duration(self, days: int) -> str:
        """
        Formatea duración en días a texto legible
        """
        if days == 0:
            return "0 días"
        elif days == 1:
            return "1 día"
        elif days < 7:
            return f"{days} días"
        elif days < 30:
            weeks = round(days / 7, 1)
            return f"{weeks} semanas" if weeks != 1 else "1 semana"
        elif days < 365:
            months = round(days / 30, 1)
            return f"{months} meses" if months != 1 else "1 mes"
        else:
            years = round(days / 365, 1)
            return f"{years} años" if years != 1 else "1 año"

    def get_current_date_info(self) -> dict:
        """
        Información de la fecha actual para el dashboard
        """
        now = datetime.now()

        return {
            "current_date": now,
            "formatted_full": self.format_date_spanish(now, "full"),
            "formatted_short": self.format_date_spanish(now, "short"),
            "formatted_weekday": self.format_date_spanish(now, "weekday"),
            "year": now.year,
            "month": now.month,
            "month_name": self.spanish_months[now.month],
            "day": now.day,
            "weekday": self.spanish_days[now.weekday()],
            "is_weekend": now.weekday() >= 5,
            "quarter": f"Q{(now.month - 1) // 3 + 1}",
        }

    def validate_date_consistency(self, dates_dict: dict) -> dict:
        """
        Valida consistencia entre múltiples fechas

        Args:
            dates_dict: Diccionario con fechas {'name': date_series}
        """
        validation_results = {
            "consistent": True,
            "errors": [],
            "warnings": [],
            "date_ranges": {},
        }

        for name, dates in dates_dict.items():
            if dates is not None and len(dates) > 0:
                range_info = self.get_date_range_info(dates)
                validation_results["date_ranges"][name] = range_info

                # Validar fechas futuras
                future_dates = dates[dates > datetime.now()]
                if len(future_dates) > 0:
                    validation_results["warnings"].append(
                        f"{name}: {len(future_dates)} fechas futuras encontradas"
                    )

                # Validar fechas muy antiguas (antes de 2020)
                old_dates = dates[dates < datetime(2020, 1, 1)]
                if len(old_dates) > 0:
                    validation_results["warnings"].append(
                        f"{name}: {len(old_dates)} fechas anteriores a 2020"
                    )

        return validation_results

    def create_temporal_summary_for_dashboard(
        self,
        vaccination_data: pd.DataFrame,
        date_column: str = "fecha_vacunacion",
        cutoff_date: datetime = None,
    ) -> dict:
        """
        Crea resumen temporal completo para el dashboard
        """
        if vaccination_data is None or len(vaccination_data) == 0:
            return {
                "error": "No hay datos de vacunación",
                "current_date": self.get_current_date_info(),
            }

        if date_column not in vaccination_data.columns:
            return {
                "error": f"Columna {date_column} no encontrada",
                "available_columns": list(vaccination_data.columns),
                "current_date": self.get_current_date_info(),
            }

        # Información básica
        dates = vaccination_data[date_column]
        general_info = self.get_date_range_info(dates)

        # Información de fases si hay fecha de corte
        phases_info = {}
        if cutoff_date:
            phases_info = self.get_vaccination_phases_info(dates, cutoff_date)

        # Información actual
        current_info = self.get_current_date_info()

        # Calcular días desde última actualización
        if general_info["max_date"]:
            days_since_update = (datetime.now() - general_info["max_date"]).days
        else:
            days_since_update = None

        return {
            "current_date": current_info,
            "data_range": general_info,
            "phases": phases_info,
            "days_since_update": days_since_update,
            "update_status": self._get_update_status(days_since_update),
            "summary_text": self._create_summary_text(
                general_info, phases_info, current_info
            ),
        }

    def _get_update_status(self, days_since_update: Optional[int]) -> dict:
        """
        Determina el estado de actualización de los datos
        """
        if days_since_update is None:
            return {
                "status": "unknown",
                "message": "Fecha de actualización desconocida",
                "color": "gray",
            }

        if days_since_update == 0:
            return {
                "status": "current",
                "message": "Datos actualizados hoy",
                "color": "green",
            }
        elif days_since_update <= 3:
            return {
                "status": "recent",
                "message": f"Actualizado hace {days_since_update} días",
                "color": "green",
            }
        elif days_since_update <= 7:
            return {
                "status": "weekly",
                "message": f"Actualizado hace {days_since_update} días",
                "color": "yellow",
            }
        elif days_since_update <= 30:
            return {
                "status": "monthly",
                "message": f"Actualizado hace {days_since_update} días",
                "color": "orange",
            }
        else:
            return {
                "status": "outdated",
                "message": f"Desactualizado ({days_since_update} días)",
                "color": "red",
            }

    def _create_summary_text(
        self, general_info: dict, phases_info: dict, current_info: dict
    ) -> str:
        """
        Crea texto de resumen para mostrar en el dashboard
        """
        summary_parts = []

        # Información general
        if general_info["count"] > 0:
            summary_parts.append(
                f"Datos de vacunación desde {general_info['min_date_formatted']} "
                f"hasta {general_info['max_date_formatted']} "
                f"({general_info['period_months']} meses, {general_info['count']:,} registros)".replace(
                    ",", "."
                )
            )

        # Información de fases si disponible
        if phases_info and "historical_phase" in phases_info:
            hist = phases_info["historical_phase"]
            emerg = phases_info["emergency_phase"]

            if hist["count"] > 0 and emerg["count"] > 0:
                summary_parts.append(
                    f"Período histórico: {hist['count']:,} registros ({hist['percentage']:.1f}%)".replace(
                        ",", "."
                    )
                )
                summary_parts.append(
                    f"Período emergencia: {emerg['count']:,} registros ({emerg['percentage']:.1f}%)".replace(
                        ",", "."
                    )
                )

        return (
            " | ".join(summary_parts)
            if summary_parts
            else "Sin información de fechas disponible"
        )


# Instancia global para uso en toda la aplicación
date_utils = DateUtils()


# Funciones de conveniencia
def format_date(date_obj, format_type="short"):
    """Función de conveniencia para formatear fechas"""
    return date_utils.format_date_spanish(date_obj, format_type)


def parse_date(date_str):
    """Función de conveniencia para parsear fechas"""
    return date_utils.parse_date_flexible(date_str)


def get_vaccination_summary(
    vaccination_df, date_col="fecha_vacunacion", cutoff_date=None
):
    """Función de conveniencia para resumen temporal"""
    return date_utils.create_temporal_summary_for_dashboard(
        vaccination_df, date_col, cutoff_date
    )


def detect_period(date_obj, cutoff_date):
    """Función de conveniencia para detectar período"""
    return date_utils.detect_period_from_date(date_obj, cutoff_date)


def test_date_utils():
    """
    Función de prueba para las utilidades de fecha
    """
    st.title("🧪 Prueba de Utilidades de Fecha")

    # Prueba de formateo
    st.subheader("📅 Prueba de Formateo")
    test_date = datetime(2024, 3, 15, 14, 30, 0)

    formats = ["full", "short", "month_year", "day_month", "weekday"]
    for fmt in formats:
        formatted = date_utils.format_date_spanish(test_date, fmt)
        st.write(f"**{fmt}:** {formatted}")

    # Prueba de parsing
    st.subheader("🔍 Prueba de Parsing")
    test_dates = [
        "2024-01-15",
        "15/01/2024",
        "15-01-2024",
        "2024/01/15",
        "15/01/24",
        "fecha_invalida",
    ]

    for date_str in test_dates:
        parsed = date_utils.parse_date_flexible(date_str)
        st.write(f"**'{date_str}'** → {parsed}")

    # Información actual
    st.subheader("📊 Información Fecha Actual")
    current_info = date_utils.get_current_date_info()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Fecha Completa", current_info["formatted_full"])
    with col2:
        st.metric("Día de la Semana", current_info["weekday"])
    with col3:
        st.metric("Mes", current_info["month_name"])

    # Crear datos de prueba para análisis de fases
    st.subheader("📈 Análisis de Fases de Vacunación")

    # Datos sintéticos
    cutoff_test = datetime(2024, 9, 1)
    test_vaccination_dates = pd.Series(
        [
            datetime(2024, 6, 15),  # Pre-emergencia
            datetime(2024, 7, 20),  # Pre-emergencia
            datetime(2024, 8, 10),  # Pre-emergencia
            datetime(2024, 9, 5),  # Emergencia
            datetime(2024, 10, 12),  # Emergencia
            datetime(2024, 11, 8),  # Emergencia
        ]
    )

    phases_analysis = date_utils.get_vaccination_phases_info(
        test_vaccination_dates, cutoff_test
    )

    st.json(phases_analysis)


if __name__ == "__main__":
    test_date_utils()
