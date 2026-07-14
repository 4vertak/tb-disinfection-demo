# app/api/v1/reports/routes.py
"""REST API эндпоинты для отчётов."""
from flask import request, send_file
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.domain.models.user.entities import User
from app.core.extensions import db

from .services import ReportsApiService
from ..common.response import error_response
from ..common.decorators import admin_required

# Создание namespace
reports_ns = Namespace('reports', description='Генерация отчётов')


# ==================== SWAGGER МОДЕЛИ ====================

report_info_model = reports_ns.model('ReportInfo', {
    'type': fields.String(description='Тип отчёта'),
    'format': fields.String(description='Формат (excel, word, pdf)'),
    'period': fields.String(description='Период'),
    'year': fields.Integer(description='Год')
})


# ==================== ENDPOINTS ====================

@reports_ns.route('/applications/excel')
class ApplicationsExcelReport(Resource):
    """Excel отчёт по заявкам"""
    
    @reports_ns.doc('export_applications_excel')
    @reports_ns.response(200, 'Excel файл с заявками')
    @jwt_required()
    def get(self):
        """Экспорт заявок в Excel"""
        period = request.args.get('period', 'year')
        year = request.args.get('year', type=int)
        
        # Получаем текущего пользователя
        user_id = int(get_jwt_identity())
        user = db.session.get(User, user_id)
        
        try:
            excel_data, filename = ReportsApiService.export_applications_excel(
                period, year, user
            )
            
            return send_file(
                excel_data,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )
        except Exception as e:
            return error_response(str(e), 500)


@reports_ns.route('/applications/<int:id>/word')
class ApplicationWordReport(Resource):
    """Word документ заявки"""
    
    @reports_ns.doc('generate_application_word')
    @reports_ns.response(200, 'Word документ заявки')
    @jwt_required()
    def get(self, id):
        """Генерация Word документа заявки"""
        try:
            doc_stream, filename = ReportsApiService.generate_application_document(id)
            
            return send_file(
                doc_stream,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                as_attachment=True,
                download_name=filename
            )
        except ValueError as e:
            return error_response(str(e), 404)
        except Exception as e:
            return error_response(str(e), 500)