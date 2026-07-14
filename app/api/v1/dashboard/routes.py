# app/api/v1/dashboard/routes.py
"""REST API эндпоинты для dashboard."""
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.domain.models.user.entities import User
from app.core.extensions import db

from .services import DashboardApiService
from ..common.response import success_response

# Создание namespace
dashboard_ns = Namespace('dashboard', description='Статистика и аналитика')


# ==================== SWAGGER МОДЕЛИ ====================

dashboard_model = dashboard_ns.model('Dashboard', {
    'period': fields.String(description='Период (year, month, quarter)'),
    'year': fields.Integer(description='Год'),
    'start_date': fields.String(description='Дата начала периода'),
    'end_date': fields.String(description='Дата конца периода'),
    'total_info': fields.Raw(description='Общая статистика'),
    'monthly_data': fields.Raw(description='Месячные данные'),
    'top_disinfectors': fields.Raw(description='Топ дезинфекторов'),
    'areas_labels': fields.List(fields.String, description='Метки участков'),
    'areas_total_values': fields.List(fields.Integer, description='Всего заявок по участкам'),
    'areas_completed_values': fields.List(fields.Integer, description='Выполнено по участкам'),
    'chart_data': fields.Raw(description='Данные для графиков')
})


# ==================== ENDPOINTS ====================

@dashboard_ns.route('/')
class DashboardData(Resource):
    """Данные dashboard"""
    
    @dashboard_ns.doc('get_dashboard_data')
    @dashboard_ns.response(200, 'Данные dashboard', dashboard_model)
    @jwt_required()
    def get(self):
        """Получить данные dashboard за указанный период"""
        period = request.args.get('period', 'year')
        year = request.args.get('year', type=int)
        
        # Получаем текущего пользователя для фильтрации
        user_id = int(get_jwt_identity())
        user = db.session.get(User, user_id)
        
        data = DashboardApiService.get_dashboard_data(period, year, user)
        return success_response(data)