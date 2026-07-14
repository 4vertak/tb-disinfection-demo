"""Бизнес-логика для dashboard."""

from datetime import datetime, timezone
from sqlalchemy import func
from app.domain.services.dashboard_report_service import DashboardReportService
from app.utils.date_utils import get_period_dates, to_utc, get_available_years
from app.domain.models.application.entities import Application, Disinfection, EpidemicFocus, Area
from app.core.extensions import db


def _need_carry_over(period: str, start_date: datetime) -> bool:
    """Возвращает True, если отчёт годовой и начало периода — 1 января."""
    return period == 'год' and start_date.month == 1 and start_date.day == 1


class DashboardApiService:
    """Сервис для dashboard через API"""

    @staticmethod
    def get_dashboard_data(period: str = 'year', year: int = None, user=None):
        """Получить данные dashboard"""
        if year is None:
            year = datetime.now(timezone.utc).year

        start_date, end_date = get_period_dates(period, year)

        # Если даты None, используем значения по умолчанию
        if start_date is None:
            start_date = datetime(year, 1, 1, tzinfo=timezone.utc)
        if end_date is None:
            end_date = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

        # Используем существующий сервис
        report_data = DashboardReportService.build_report_data(
            start_date, end_date, user
        )

        total_info = report_data['total_info']
        
        # Вычисляем square_disinfection с учетом типа пользователя (как в legacy)
        start_utc = to_utc(start_date)
        end_utc = to_utc(end_date)
        
        square_disinfection = 0
        user_type = user.user_type if user else "admin"
        
        if user_type in ['admin', 'disinfector']:
            # Для admin и disinfector считаем площадь только completed заявок
            square_disinfection_query = db.session.query(func.sum(Disinfection.area_size))\
                .join(Application, Application.id == Disinfection.application_id)\
                .filter(
                    Disinfection.disinfection_date.between(start_utc, end_utc),
                    Application.status == 'completed'
                ).scalar()
            square_disinfection = float(square_disinfection_query or 0.0)
        
        total_info['square_disinfection'] = square_disinfection
        
        # Переходящие заявки (только для годового отчёта, начинающегося с 1 января)
        if _need_carry_over(period, start_date):
            from app.utils.get_total_info import get_carry_over_count
            carry_over = get_carry_over_count(start_date, end_date)
            total_info['carry_over'] = carry_over
            total_info['total_with_carry_over'] = total_info['total'] + carry_over
        
        # Построение таблицы эпидгрупп (как в legacy)
        table_data = DashboardApiService._build_epidemic_table(start_utc, end_utc, user_type)
        
        return {
            'period': period,
            'year': year,
            'available_years': get_available_years(),
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_info': total_info,
            'monthly_data': report_data['monthly_data'],
            'top_disinfectors': report_data['top_disinfectors'],
            'areas_labels': report_data.get('areas_labels', []),
            'areas_total_values': report_data.get('areas_total_values', []),
            'areas_completed_values': report_data.get('areas_completed_values', []),
            'chart_data': report_data.get('chart_data', {}),
            'table_data': table_data,
            'show_square_info': user_type in ['admin', 'disinfector']
        }
    
    @staticmethod
    def _build_epidemic_table(start_utc, end_utc, user_type):
        """Построение таблицы по эпидемическим группам (как в legacy)"""
        all_areas = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'ДПДО', 'РПТД']
        epidemic_groups = ['I', 'II', 'III', 'IV', 'V', 'безадресные']
        
        # Для doctor'ов считаем по submission_date, для остальных по disinfection_date
        if user_type == 'doctor':
            query = db.session.query(
                EpidemicFocus.name.label('epidemic_focus'),
                Area.name_area.label('area'),
                func.count(Application.id).label('count')
            ).join(Application, Application.focus_id == EpidemicFocus.id)\
             .outerjoin(Area, Area.id == Application.area_id)\
             .filter(Application.submission_date.between(start_utc, end_utc))\
             .filter(Area.name_area.in_(all_areas))\
             .group_by(EpidemicFocus.name, Area.name_area)
            
            results = query.all()
            
            posthumous_query = db.session.query(
                EpidemicFocus.name.label('epidemic_focus'),
                Area.name_area.label('area'),
                func.count(Application.id).label('posthumous_count')
            ).join(Application, Application.focus_id == EpidemicFocus.id)\
             .outerjoin(Area, Area.id == Application.area_id)\
             .filter(Application.submission_date.between(start_utc, end_utc))\
             .filter(Application.reason_application == 'posthumously')\
             .filter(Area.name_area.in_(all_areas))\
             .group_by(EpidemicFocus.name, Area.name_area)
            
            posthumous_results = posthumous_query.all()
        else:
            query = db.session.query(
                EpidemicFocus.name.label('epidemic_focus'),
                Area.name_area.label('area'),
                func.count(Application.id).label('count')
            ).join(Application, Application.focus_id == EpidemicFocus.id)\
             .join(Disinfection, Disinfection.application_id == Application.id)\
             .outerjoin(Area, Area.id == Application.area_id)\
             .filter(Disinfection.disinfection_date.between(start_utc, end_utc))\
             .filter(Application.status == 'completed')\
             .filter(Area.name_area.in_(all_areas))\
             .group_by(EpidemicFocus.name, Area.name_area)
            
            results = query.all()
            
            posthumous_query = db.session.query(
                EpidemicFocus.name.label('epidemic_focus'),
                Area.name_area.label('area'),
                func.count(Application.id).label('posthumous_count')
            ).join(Application, Application.focus_id == EpidemicFocus.id)\
             .join(Disinfection, Disinfection.application_id == Application.id)\
             .outerjoin(Area, Area.id == Application.area_id)\
             .filter(Disinfection.disinfection_date.between(start_utc, end_utc))\
             .filter(Application.reason_application == 'posthumously')\
             .filter(Application.status == 'completed')\
             .filter(Area.name_area.in_(all_areas))\
             .group_by(EpidemicFocus.name, Area.name_area)
            
            posthumous_results = posthumous_query.all()
        
        # Построение таблицы
        table_data = []
        col_totals = {area: 0 for area in all_areas}
        posthumous_col_totals = {area: 0 for area in all_areas}
        
        for group in epidemic_groups:
            row = {'focus': group}
            row_total = 0
            
            for area in all_areas:
                count = next((r.count for r in results
                             if r.epidemic_focus == group and r.area == area), 0)
                row[area] = count
                row_total += count
                col_totals[area] += count
                
                posthumous_count = next((r.posthumous_count for r in posthumous_results
                                       if r.epidemic_focus == group and r.area == area), 0)
                posthumous_col_totals[area] += posthumous_count
            
            row['total'] = row_total
            table_data.append(row)
        
        posthumous_row = {'focus': 'в том числе посмертно'}
        for area in all_areas:
            posthumous_row[area] = posthumous_col_totals[area]
        posthumous_row['total'] = sum(posthumous_col_totals.values())
        table_data.append(posthumous_row)
        
        total_row = {'focus': 'ВСЕГО'}
        for area in all_areas:
            total_row[area] = col_totals[area]
        total_row['total'] = sum(col_totals.values())
        table_data.append(total_row)
        
        return table_data