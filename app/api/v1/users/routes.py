"""
REST API эндпоинты для управления пользователями.

Эндпоинты:
- GET /api/v1/users — список пользователей
- GET /api/v1/users/<id> — детали пользователя
- POST /api/v1/users — создание пользователя (admin)
- PATCH /api/v1/users/<id> — обновление пользователя (admin)
- DELETE /api/v1/users/<id> — удаление пользователя (admin)
- GET /api/v1/users/doctors — список врачей
- GET /api/v1/users/disinfectors — список дезинфекторов
"""

from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from .schemas import UserSchema, UserCreateSchema, UserUpdateSchema, UserFilterSchema
from .services import UserService
from ..common.response import (
    success_response, created_response, no_content_response, 
    error_response, validation_error_response, list_response
)
from ..common.decorators import admin_required
from ..common.pagination import paginate_query

# Создание namespace
users_ns = Namespace('users', description='Управление пользователями')


# Swagger модели
user_model = users_ns.model('User', {
    'id': fields.Integer(description='ID пользователя'),
    'login': fields.String(description='Логин'),
    'name': fields.String(description='Имя'),
    'user_type': fields.String(description='Тип пользователя', enum=['doctor', 'admin', 'disinfector']),
    'created_at': fields.DateTime(description='Дата создания'),
    'updated_at': fields.DateTime(description='Дата обновления'),
    'last_login': fields.DateTime(description='Последний вход')
})

user_create_model = users_ns.model('UserCreate', {
    'login': fields.String(required=True, description='Логин'),
    'password': fields.String(required=True, description='Пароль'),
    'name': fields.String(required=True, description='Имя'),
    'user_type': fields.String(required=True, description='Тип пользователя', enum=['doctor', 'admin', 'disinfector'])
})

user_update_model = users_ns.model('UserUpdate', {
    'name': fields.String(description='Имя'),
    'user_type': fields.String(description='Тип пользователя', enum=['doctor', 'admin', 'disinfector']),
    'password': fields.String(description='Новый пароль')
})


@users_ns.route('/')
class UserList(Resource):
    """Список пользователей и создание нового"""
    
    @users_ns.doc('list_users')
    @users_ns.response(200, 'Список пользователей')
    @users_ns.response(401, 'Не авторизован')
    @jwt_required()
    def get(self):
        """
        Получение списка пользователей с пагинацией и фильтрацией.
        
        Query параметры:
        - page: Номер страницы (по умолчанию 1)
        - per_page: Элементов на странице (по умолчанию 20, макс 100)
        - user_type: Фильтр по типу пользователя (doctor, admin, disinfector)
        - area_id: Фильтр по ID участка
        - search: Поиск по логину или имени
        - sort: Сортировка (-created_at, name, etc.)
        """

        # Получение фильтров
        filters = {
            'user_type': request.args.get('user_type'),
            'area_id': request.args.get('area_id', type=int),
            'search': request.args.get('search')
        }
        
        query = UserService.get_all_users(filters)
        result = paginate_query(query, UserSchema())
        
        return list_response(result['items'], result['meta'])
    
    @users_ns.expect(user_create_model, validate=True)
    @users_ns.doc('create_user')
    @users_ns.response(201, 'Пользователь создан', user_model)
    @users_ns.response(403, 'Доступ запрещён (только admin)')
    @users_ns.response(409, 'Логин уже существует')
    @users_ns.response(422, 'Ошибка валидации')
    @jwt_required()
    @admin_required
    def post(self):
        """
        Создание нового пользователя (только для администраторов).
        
        Создаёт нового пользователя в системе. Требует прав администратора.
        """

        # Валидация входных данных
        try:
            data = UserCreateSchema().load(request.get_json())
        except ValidationError as err:
            return validation_error_response(err.messages)
        
        # Создание пользователя
        try:
            user = UserService.create_user(data)
        except Exception as e:
            return error_response(str(e), 409)
        
        return created_response(UserSchema().dump(user))


@users_ns.route('/<int:id>')
@users_ns.param('id', 'ID пользователя')
class UserResource(Resource):
    """Детали, обновление и удаление пользователя"""
    
    @users_ns.doc('get_user')
    @users_ns.response(200, 'Детали пользователя', user_model)
    @users_ns.response(404, 'Пользователь не найден')
    @jwt_required()
    def get(self, id):
        """
        Получение деталей пользователя по ID.
        
        Возвращает полную информацию о пользователе.
        """

        user = UserService.get_user_by_id(id)
        
        if not user:
            return error_response('User not found', 404)
        
        return success_response(UserSchema().dump(user))
    
    @users_ns.expect(user_update_model, validate=True)
    @users_ns.doc('update_user')
    @users_ns.response(200, 'Пользователь обновлён', user_model)
    @users_ns.response(403, 'Доступ запрещён (только admin)')
    @users_ns.response(404, 'Пользователь не найден')
    @users_ns.response(422, 'Ошибка валидации')
    @jwt_required()
    @admin_required
    def patch(self, id):
        """
        Частичное обновление пользователя (только для администраторов).
        
        Позволяет обновить отдельные поля пользователя.
        """

        # Валидация входных данных
        try:
            data = UserUpdateSchema().load(request.get_json(), partial=True)
        except ValidationError as err:
            return validation_error_response(err.messages)
        
        # Обновление пользователя
        try:
            user = UserService.update_user(id, data)
        except ValueError as e:
            return error_response(str(e), 404)
        
        return success_response(UserSchema().dump(user))
    
    @users_ns.doc('delete_user')
    @users_ns.response(204, 'Пользователь удалён')
    @users_ns.response(403, 'Доступ запрещён (только admin)')
    @users_ns.response(404, 'Пользователь не найден')
    @jwt_required()
    @admin_required
    def delete(self, id):
        """
        Удаление пользователя (только для администраторов).
        
        Полностью удаляет пользователя из системы.
        """
        
        try:
            UserService.delete_user(id)
        except ValueError as e:
            return error_response(str(e), 404)
        
        return no_content_response()


@users_ns.route('/doctors')
class DoctorList(Resource):
    """Список врачей"""
    
    @users_ns.doc('list_doctors')
    @users_ns.response(200, 'Список врачей')
    @jwt_required()
    def get(self):
        """
        Получение списка всех врачей.
        
        Возвращает пользователей с user_type='doctor'.
        """
        query = UserService.get_doctors()
        result = paginate_query(query, UserSchema())
        
        return list_response(result['items'], result['meta'])


@users_ns.route('/disinfectors')
class DisinfectorList(Resource):
    """Список дезинфекторов"""
    
    @users_ns.doc('list_disinfectors')
    @users_ns.response(200, 'Список дезинфекторов')
    @jwt_required()
    def get(self):
        """
        Получение списка всех дезинфекторов.
        
        Возвращает пользователей с user_type='disinfector'.
        """
        query = UserService.get_disinfectors()
        result = paginate_query(query, UserSchema())
        
        return list_response(result['items'], result['meta'])