from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timezone
import io

from ...domain.services.import_export_service import ExcelImportExportService
from ...utils.date_utils import get_period_dates, to_local
from .forms import  ExportExcelForm
from ...core.extensions import db

import_export = Blueprint('import_export', __name__)

@import_export.route('/export', methods=['GET', 'POST'])
@login_required
def export_excel():
    """Страница экспорта данных в Excel"""
    form = ExportExcelForm()
    
    # Всегда получаем параметры из URL, если они есть
    period = request.args.get('period')
    selected_year = request.args.get('year', type=int)
    
    # Если параметры не переданы в URL, пробуем получить из формы
    if not period or not selected_year:
        if form.validate_on_submit():
            period = form.period.data
            selected_year = form.year.data if hasattr(form, 'year') else to_local(datetime.now(timezone.utc)).year
        else:
            # Если форма не отправлена, используем значения по умолчанию
            period = 'месяц'
            selected_year = to_local(datetime.now(timezone.utc)).year
    
    try:
        # Получаем даты периода
        start_date, end_date = get_period_dates(period, selected_year)
        
        if not start_date or not end_date:
            flash('Некорректный период', 'danger')
            return redirect(url_for('dashboard.all'))
        
        excel_file = ExcelImportExportService.export_to_excel(
            start_date, 
            end_date,
            current_user.user_type if current_user.user_type != 'admin' else None
        )
        
        filename = f'export_{start_date.strftime("%Y-%m-%d")}_{end_date.strftime("%Y-%m-%d")}.xlsx'
        
        return send_file(
            excel_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        flash(f'Ошибка при экспорте данных: {str(e)}', 'danger')
        return redirect(url_for('dashboard.all'))