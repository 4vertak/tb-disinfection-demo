"""
Сервис для построения отчётов dashboard.
"""
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import func, extract

from ...core.extensions import db
from ...domain.models.application.entities import (
    Application,
    Disinfection,
    Disinfector,
    disinfection_disinfector,
)
from ...utils.date_utils import to_utc
from ...utils.get_total_info import get_total_info, get_carry_over_count
from ...utils.functions import (
    combine_areas_data,
    combine_monthly_data,
    get_areas_data_applicates,
    get_areas_data_disinfection_completed,
    get_focus_data,
    get_monthly_data,
    get_monthly_data_disinfection_completed,
    get_top_disinfectors as _get_top_disinfectors_from_functions,
    initialize_combined_areas_data,
    initialize_combined_focus_areas_data,
    prepare_areas_labels_and_values,
    prepare_data_for_chart,
    prepare_labels_and_values,
)

MONTHS_RU = [
    "январь", "февраль", "март", "апрель", "май", "июнь",
    "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
]


class DashboardReportService:
    """Сервис для построения отчётных данных dashboard."""

    @staticmethod
    def build_report_data(
        start_date,
        end_date,
        user: Optional[Any] = None,
    ) -> dict[str, Any]:
        """
        Строит отчётные данные для dashboard.

        Args:
            start_date: Начальная дата периода
            end_date: Конечная дата периода
            user: Пользователь (для фильтрации по типу)

        Returns:
            dict с total_info, monthly_data, yearly_data,
            top_disinfectors, chart_data, areas_data, focus_data
        """
        user_type = user.user_type if user else "admin"

        # общая статистика (включает переходящие заявки)
        total_info = get_total_info(start_date, end_date)

        # месячные данные
        monthly_data_applicates = get_monthly_data(
            Application, "submission_date", start_date, end_date,
        )
        monthly_data_disinfection = get_monthly_data_disinfection_completed(
            start_date, end_date,
        )
        combined_monthly = combine_monthly_data(
            monthly_data_applicates,
            monthly_data_disinfection,
            start_date,
            end_date,
        )

        # данные для графиков участков и очагов
        areas_data_applicates = get_areas_data_applicates(start_date, end_date)
        areas_data_disinfection = get_areas_data_disinfection_completed(
            start_date, end_date,
        )
        combined_areas = combine_areas_data(
            areas_data_applicates, areas_data_disinfection,
        )
        (
            areas_labels,
            areas_total_values,
            areas_completed_values,
        ) = prepare_areas_labels_and_values(combined_areas)

        focus_data = get_focus_data(start_date, end_date)
        combined_focus = initialize_combined_focus_areas_data(focus_data)
        focus_labels, area_labelsf, focus_total_values = prepare_labels_and_values(
            combined_focus,
        )
        focus_total_values_list = prepare_data_for_chart(
            focus_total_values, focus_labels,
        )

        # yearly data
        yearly_data_applicates = DashboardReportService._get_yearly_data(
            Application, "submission_date", user_type, user,
        )
        yearly_data_disinfection = DashboardReportService._get_yearly_data_disinfection_completed(
            user_type, user,
        )

        # топ дезинфекторов
        top_disinfectors = _get_top_disinfectors_from_functions(start_date, end_date)

        # chart_data (из monthly)
        chart_data = DashboardReportService._prepare_chart_data(combined_monthly)

        return {
            "total_info": total_info,
            "monthly_data": combined_monthly,
            "yearly_data": {
                "applications": yearly_data_applicates,
                "disinfections": yearly_data_disinfection,
            },
            "top_disinfectors": top_disinfectors,
            "chart_data": chart_data,
            # areas / focus
            "areas_labels": areas_labels,
            "areas_total_values": areas_total_values,
            "areas_completed_values": areas_completed_values,
            "focus_labels": focus_labels,
            "area_labelsf": area_labelsf,
            "focus_total_values_list": focus_total_values_list,
        }

    @staticmethod
    def _get_yearly_data(
        model, date_field: str, user_type: Optional[str] = None, user: Optional[Any] = None,
    ) -> dict[int, int]:
        query = db.session.query(
            extract("year", getattr(model, date_field)).label("year"),
            func.count(model.id).label("count"),
        )

        if user_type == "doctor":
            query = query.filter(model.user_id == user.id)

        results = query.group_by("year").order_by("year").all()
        return {int(year): count for year, count in results}

    @staticmethod
    def _get_yearly_data_disinfection_completed(
        user_type: Optional[str] = None, user: Optional[Any] = None,
    ) -> dict[int, int]:
        query = db.session.query(
            extract("year", Disinfection.disinfection_date).label("year"),
            func.count(Disinfection.id).label("count"),
        ).join(Application).filter(Application.status == "completed")

        if user_type == "doctor":
            query = query.filter(Application.user_id == user.id)

        results = query.group_by("year").order_by("year").all()
        return {int(year): count for year, count in results}

    @staticmethod
    def _prepare_chart_data(combined_data: OrderedDict) -> dict[str, list]:
        """Подготовка данных для основного графика."""
        labels = list(combined_data.keys())
        applications_values = [
            data["applications"] for data in combined_data.values()
        ]
        disinfections_values = [
            data["disinfections"] for data in combined_data.values()
        ]

        return {
            "labels": labels,
            "applications": applications_values,
            "disinfections": disinfections_values,
        }