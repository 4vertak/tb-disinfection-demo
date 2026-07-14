"""
REST API эндпоинты для поиска (autocomplete для select2).
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required

from .services import SearchApiService
from ..common.response import success_response

search_ns = Namespace('search', description='Поиск и autocomplete для форм')

# ==================== SWAGGER МОДЕЛИ ====================
doctor_search_model = search_ns.model('DoctorSearchResult', {
    'value': fields.String(description='ФИО врача (для select2)'),
    'area_id': fields.Integer(description='ID участка'),
    'area_name': fields.String(description='Название участка')
})

disinfector_search_model = search_ns.model('DisinfectorSearchResult', {
    'id': fields.Integer(description='ID дезинфектора'),
    'full_name': fields.String(description='ФИО дезинфектора'),
    'value': fields.String(description='Значение для select2 (ФИО)')
})

# ==================== ЭНДПОИНТЫ ====================

@search_ns.route('/doctors')
class SearchDoctors(Resource):
    @search_ns.doc('search_doctors')
    @search_ns.response(200, 'Результаты поиска врачей')
    @jwt_required()
    def get(self):
        """
        Поиск врачей по ФИО для autocomplete (select2).
        
        Query параметры:
        - q: Поисковый запрос (минимум 2 символа)
        - limit: Максимальное количество результатов (по умолчанию 10)
        """
        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 10, type=int)
        
        # Возвращаем пустой список, если запрос слишком короткий
        if len(query) < 2:
            return success_response([])
            
        results = SearchApiService.search_doctors(query, limit)
        return success_response(results)


@search_ns.route('/disinfectors')
class SearchDisinfectors(Resource):
    @search_ns.doc('search_disinfectors')
    @search_ns.response(200, 'Результаты поиска дезинфекторов')
    @jwt_required()
    def get(self):
        """
        Поиск дезинфекторов по ФИО для autocomplete (select2).
        
        Query параметры:
        - q: Поисковый запрос (минимум 2 символа)
        - limit: Максимальное количество результатов (по умолчанию 10)
        """
        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 10, type=int)
        
        # Возвращаем пустой список, если запрос короткий
        if len(query) < 2:
            return success_response([])
            
        results = SearchApiService.search_disinfectors(query, limit)
        return success_response(results)