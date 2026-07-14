from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, Inches
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.shared import OxmlElement
from docx.oxml.ns import qn
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, send_file, url_for, jsonify
from sqlalchemy import func
from flask_login import login_required, current_user
from io import BytesIO

from ...domain.models.user.entities import User
from ...domain.models.application.entities import Application, Disinfection, EpidemicFocus, Area, Doctor
from ...domain.models.audit.entities import ApplicationAuditLog
from ...core.extensions import db


from ...utils.date_utils import get_period_dates, to_local, to_utc, get_available_years, LOCAL_TZ
from ...utils.get_total_info import get_total_info, get_total_info_for_report, get_carry_over_count
from ...utils.functions import (
    get_monthly_data_logs,
)
from ...domain.services.dashboard_report_service import DashboardReportService


from datetime import date, datetime, time, timezone


dashboard = Blueprint('dashboard', __name__)


# фспомогательная фнукция на определение необходимости считать переходящие заявки
def _need_carry_over(period: str, start_date: datetime) -> bool:
    """Возвращает True, если отчёт годовой и начало периода — 1 января."""
    return period == 'год' and start_date.month == 1 and start_date.day == 1

@dashboard.route('/admin', methods=['POST', 'GET'])
@login_required
def admin():

    if not hasattr(current_user, 'user_type') or current_user.user_type != 'admin':
        abort(403)

    # Получаем год из параметров запроса, по умолчанию текущий
    selected_year  = request.args.get('year', default=to_local(datetime.now(timezone.utc)).year, type=int)
    # year = to_local(datetime.now(timezone.utc)).year
    period = request.args.get('period', default='год')

    # Получаем доступные годы для выбора
    available_years = get_available_years()
    count_admins = User.query.filter_by(user_type="admin").count()
    count_doctors = User.query.filter_by(user_type="doctor").count()
    count_disinfectors = User.query.filter_by(user_type="disinfector").count()
    total_users = count_doctors + count_disinfectors + count_admins
    total_applications = Application.query.count()
    total_changes = ApplicationAuditLog.query.count()



    start_date, end_date = get_period_dates(period, selected_year)

    monthly_data_changes = get_monthly_data_logs(
        ApplicationAuditLog, 'change_time', start_date, end_date)

    audit_logs = (
        db.session.query(
            ApplicationAuditLog,
            User.login.label("login"),
            User.user_type.label("user_type"),
        )
        .outerjoin(User, User.id == ApplicationAuditLog.changed_by)
        .order_by(ApplicationAuditLog.change_time.desc())
        .all()
    )


    months = list(monthly_data_changes.keys())
    insert_data = [monthly_data_changes[month]['INSERT'] for month in months]
    update_data = [monthly_data_changes[month]['UPDATE'] for month in months]
    delete_data = [monthly_data_changes[month]['DELETE'] for month in months]

    total_info = {
        'total_users': total_users,
        'count_admins': count_admins,
        'count_doctors': count_doctors,
        'count_disinfectors': count_disinfectors,
        'total_applications': total_applications,
        'total_changes': total_changes
    }

    query_apllications = (db.session.query(Application, Disinfection, Area, Doctor).join(Disinfection, Disinfection.application_id == Application.id).join(Doctor, Doctor.id == Application.user_id).join(Area, Area.id == Doctor.area_id))

    applications = query_apllications.order_by(Application.submission_date.asc()).all()

    return render_template(
        'application/admin.html',
        total_info=total_info,
        monthly_data_changes=monthly_data_changes,
        months=months,
        insert_data=insert_data,
        update_data=update_data,
        delete_data=delete_data,
        period=period,
        selected_year=selected_year,
        available_years=available_years,
        audit_logs=audit_logs,
        applications = applications
    )



@dashboard.route('/dashboard', methods=['POST', 'GET'])
@login_required
def all():
    selected_year = request.args.get('year', default=to_local(datetime.now(timezone.utc)).year, type=int)
    period = request.args.get('period', default='год')

    available_years = get_available_years()
    start_date, end_date = get_period_dates(period, selected_year)

    #отчёт через сервис 
    report_data = DashboardReportService.build_report_data(
        start_date, end_date, current_user,
    )

    total_info = report_data['total_info']
    monthly_data = report_data['monthly_data']
    top_disinfectors = report_data['top_disinfectors']

    all_months = list(monthly_data.keys())
    total_values_full = [data['applications'] for data in monthly_data.values()]
    completed_values_full = [data['disinfections'] for data in monthly_data.values()]

    areas_labels = report_data['areas_labels']
    areas_total_values = report_data['areas_total_values']
    areas_completed_values = report_data['areas_completed_values']

    focus_labels = report_data['focus_labels']
    area_labelsf = report_data['area_labelsf']
    focus_total_values_list = report_data['focus_total_values_list']

    #таблица по эпидемиологическим группам
    all_areas = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'ДПДО', 'РПТД']
    epidemic_groups = ['I', 'II', 'III', 'IV', 'V', 'безадресные']

    start_utc = to_utc(start_date)
    end_utc = to_utc(end_date)

    square_disinfection = 0

    if current_user.user_type == 'doctor':
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

        square_disinfection_query = db.session.query(func.sum(Disinfection.area_size))\
            .join(Application, Application.id == Disinfection.application_id)\
            .filter(
                Disinfection.disinfection_date.between(start_utc, end_utc),
                Application.status == 'completed'
            ).scalar()

        square_disinfection = square_disinfection_query or 0

    total_info['square_disinfection'] = square_disinfection

    # Переходящие заявки (только для годового отчёта, начинающегося с 1 января)
    if _need_carry_over(period, start_date):
        carry_over = get_carry_over_count(start_date, end_date)
        total_info['carry_over'] = carry_over
        total_info['total_with_carry_over'] = total_info['total'] + carry_over

    show_square_info = current_user.user_type in ['admin', 'disinfector']

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

    return render_template(
        'application/dashboard.html',
        total_info=total_info,
        months=all_months,
        total_values=total_values_full,
        completed_values=completed_values_full,
        areas_labels=areas_labels,
        areas_total_values=areas_total_values,
        areas_completed_values=areas_completed_values,
        focus_labels=focus_labels,
        area_labelsf=area_labelsf,
        focus_total_values_list=focus_total_values_list,
        period=period,
        selected_year=selected_year,
        available_years=available_years,
        table_data=table_data,
        areas=all_areas,
        top_disinfectors=top_disinfectors,
        current_view='monthly',
        show_table=True,
        show_square_info=show_square_info
    )


@dashboard.route('/dashboard/data')
@login_required
def dashboard_data():
    """API endpoint для получения данных дашборда в формате JSON"""
    selected_year = request.args.get('year', default=to_local(datetime.now(timezone.utc)).year, type=int)
    period = request.args.get('period', default='год')

    start_date, end_date = get_period_dates(period, selected_year)

    report_data = DashboardReportService.build_report_data(
        start_date, end_date, current_user,
    )

    total_info = report_data['total_info']
    monthly_data = report_data['monthly_data']
    top_disinfectors = report_data['top_disinfectors']

    all_months = list(monthly_data.keys())
    total_values_full = [data['applications'] for data in monthly_data.values()]
    completed_values_full = [data['disinfections'] for data in monthly_data.values()]

    areas_labels = report_data['areas_labels']
    areas_total_values = report_data['areas_total_values']
    areas_completed_values = report_data['areas_completed_values']

    focus_labels = report_data['focus_labels']
    area_labelsf = report_data['area_labelsf']
    focus_total_values_list = report_data['focus_total_values_list']

    all_areas = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'ДПДО', 'РПТД']
    epidemic_groups = ['I', 'II', 'III', 'IV', 'V', 'безадресные']

    start_utc = to_utc(start_date)
    end_utc = to_utc(end_date)

    square_disinfection = 0

    if current_user.user_type == 'doctor':
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

        square_disinfection_query = db.session.query(func.sum(Disinfection.area_size))\
            .join(Application, Application.id == Disinfection.application_id)\
            .filter(
                Disinfection.disinfection_date.between(start_utc, end_utc),
                Application.status == 'completed'
            ).scalar()

        square_disinfection = square_disinfection_query or 0

    total_info['square_disinfection'] = square_disinfection

    if _need_carry_over(period, start_date):
        carry_over = get_carry_over_count(start_date, end_date)
        total_info['carry_over'] = carry_over
        total_info['total_with_carry_over'] = total_info['total'] + carry_over

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

    return jsonify({
        'total_info': total_info,
        'months': all_months,
        'total_values': total_values_full,
        'completed_values': completed_values_full,
        'areas_labels': areas_labels,
        'areas_total_values': areas_total_values,
        'areas_completed_values': areas_completed_values,
        'focus_labels': focus_labels,
        'area_labelsf': area_labelsf,
        'focus_total_values_list': focus_total_values_list,
        'table_data': table_data,
        'top_disinfectors': top_disinfectors,
        'show_square_info': current_user.user_type in ['admin', 'disinfector']
    })


@dashboard.route('/generate_word_report')
def generate_word_report():
    try:
        selected_year = request.args.get('year', default=to_local(datetime.now(timezone.utc)).year, type=int)
        period = request.args.get('period', default='год')

        start_date, end_date = get_period_dates(period, selected_year)

        # Преобразуем end_date в datetime с максимальным временем, если это только дата
        if isinstance(end_date, date) and not isinstance(end_date, datetime):
            end_date_with_time = datetime.combine(end_date, time.max, tzinfo=LOCAL_TZ)
        else:
            end_date_with_time = end_date

        all_areas = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'ДПДО', 'РПТД']
        epidemic_groups = ['I', 'II', 'III', 'IV', 'V', 'безадресные']

        # Формируем таблицу (аналогично дашборду, но только для completed заявок)
        query = (
            db.session.query(
                EpidemicFocus.name.label("epidemic_focus"),
                Area.name_area.label("area"),
                func.count(Application.id).label("count"),
            )
            .join(Application, Application.focus_id == EpidemicFocus.id)
            .join(Disinfection, Disinfection.application_id == Application.id)
            .outerjoin(Area, Area.id == Application.area_id)
            .filter(Disinfection.disinfection_date.between(start_date, end_date_with_time))
            .filter(Application.status == 'completed')
            .filter(Area.name_area.in_(all_areas))
            .group_by(EpidemicFocus.name, Area.name_area)
        )
        results = query.all()

        posthumous_query = (
            db.session.query(
                EpidemicFocus.name.label("epidemic_focus"),
                Area.name_area.label("area"),
                func.count(Application.id).label("posthumous_count"),
            )
            .join(Application, Application.focus_id == EpidemicFocus.id)
            .join(Disinfection, Disinfection.application_id == Application.id)
            .outerjoin(Area, Area.id == Application.area_id)
            .filter(Disinfection.disinfection_date.between(start_date, end_date_with_time))
            .filter(Application.reason_application == "posthumously")
            .filter(Application.status == 'completed')
            .filter(Area.name_area.in_(all_areas))
            .group_by(EpidemicFocus.name, Area.name_area)
        )
        posthumous_results = posthumous_query.all()

        table_data = []
        col_totals = {area: 0 for area in all_areas}
        posthumous_col_totals = {area: 0 for area in all_areas}

        for group in epidemic_groups:
            row = {'focus': group}
            row_total = 0
            for area in all_areas:
                count = next((r.count for r in results if r.epidemic_focus == group and r.area == area), 0)
                row[area] = count
                row_total += count
                col_totals[area] += count

                posth = next((r.posthumous_count for r in posthumous_results if r.epidemic_focus == group and r.area == area), 0)
                posthumous_col_totals[area] += posth
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

        # Получаем общую статистику через get_total_info (уже включает переходящие)
        total_info = get_total_info(start_date, end_date_with_time)

        # Для отчёта нужны дополнительные показатели (посмертно, отказы, площадь)
        # Их можно взять из total_info, но там нет посмертных отдельно. Добавим:
        count_posthumously = Application.query.filter(
            Application.submission_date.between(start_date, end_date_with_time),
            Application.reason_application == 'posthumously'
        ).count()

        count_refusal = Application.query.filter(
            Application.submission_date.between(start_date, end_date_with_time),
            Application.status == 'refusal'
        ).count()

        square_disinfection = db.session.query(func.sum(Disinfection.area_size))\
            .filter(Disinfection.disinfection_date.between(start_date, end_date_with_time))\
            .scalar() or 0

        # Переходящие заявки (для годового отчёта)
        carry_over = get_carry_over_count(start_date, end_date_with_time)

        # Формирование Word
        doc = Document()
        title = doc.add_heading('Отчет по заключительной дезинфекции в очагах туберкулеза', level=1)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        period_paragraph = doc.add_paragraph()
        period_paragraph.add_run(f"Период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}").bold = True
        doc.add_paragraph()

        doc.add_heading("Исполнение заявок на заключительную дезинфекцию", level=2)

        if carry_over:
            info_items = [
                f"Всего заявок: {total_info['total'] + carry_over},",
                f"в том числе:",
                f"             переходящие: {carry_over},",
                f"             посмертно: {count_posthumously}.",
                f"Отказ: {count_refusal}.",
                f"Обработано кв.м.: {round(square_disinfection, 2)}.",
                f"Взято смывов: {total_info.get('washes', 0)}."
            ]
        else:
            info_items = [
                f"Всего заявок: {total_info['total']},",
                f"в том числе посмертно: {count_posthumously}.",
                f"Отказ: {count_refusal}.",
                f"Обработано кв.м.: {round(square_disinfection, 2)}.",
                f"Взято смывов: {total_info.get('washes', 0)}."
            ]

        for item in info_items:
            doc.add_paragraph(item)

        doc.add_paragraph(f"Исполнено: {total_info['completed']}", style='Heading3')
        doc.add_paragraph()

        doc.add_heading("Количество выполненных заявок на заключительную дезинфекцию в разрезе противотуберкулезных диспансеров", level=2)
        table = doc.add_table(rows=1, cols=len(all_areas) + 2)
        table.style = 'Table Grid'

        hdr_cells = table.rows[0].cells
        headers = ['Группы очагов/участки'] + all_areas + ['ВСЕГО']
        for i, header in enumerate(headers):
            hdr_cells[i].text = header
            hdr_cells[i].paragraphs[0].runs[0].font.bold = True
            hdr_cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        for row in table_data:
            row_cells = table.add_row().cells
            row_cells[0].text = row['focus']
            row_cells[0].paragraphs[0].runs[0].font.bold = row['focus'] in ['в том числе посмертно', 'ВСЕГО']

            for i, area in enumerate(all_areas, 1):
                row_cells[i].text = str(row.get(area, 0))
                row_cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

            row_cells[-1].text = str(row.get('total', 0))
            row_cells[-1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_paragraph()
        date_paragraph = doc.add_paragraph(f"Дата формирования: {to_local(datetime.now(timezone.utc)).strftime('%d.%m.%Y')}")
        date_paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        byte_stream = BytesIO()
        doc.save(byte_stream)
        byte_stream.seek(0)

        filename = f"epid_report_{start_date.strftime('%Y-%m-%d')}_to_{end_date.strftime('%Y-%m-%d')}.docx"
        return send_file(
            byte_stream,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        current_app.logger.error(f"Error generating report: {str(e)}", exc_info=True)
        flash('Произошла ошибка при генерации отчета', 'danger')
        return redirect(url_for('dashboard.all'))