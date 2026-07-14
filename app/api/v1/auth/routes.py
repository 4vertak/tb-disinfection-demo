"""
REST API эндпоинты для аутентификации.

Эндпоинты:
- POST /api/v1/auth/login — вход в систему
- POST /api/v1/auth/register — регистрация (только admin)
- POST /api/v1/auth/refresh — обновление access token
- POST /api/v1/auth/logout — выход из системы
- GET /api/v1/auth/me — информация о текущем пользователе
- POST /api/v1/auth/change-password — смена пароля
"""
import logging
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, get_jwt, create_access_token
)
from marshmallow import ValidationError

from .schemas import LoginSchema, RegisterSchema, TokenSchema, ChangePasswordSchema
from .services import AuthService
from ..common.response import (
    success_response, created_response, error_response, validation_error_response
)
from ..common.decorators import admin_required, validate_json
from ..common.swagger import create_pagination_model
from app.core.extensions import db



logger = logging.getLogger(__name__)

# Создание namespace
auth_ns = Namespace('auth', description='Аутентификация и авторизация')


# ==================== SWAGGER МОДЕЛИ ====================

login_model = auth_ns.model('Login', {
    'login': fields.String(required=True, description='Логин пользователя', example='admin'),
    'password': fields.String(required=True, description='Пароль', example='admin123')
})

register_model = auth_ns.model('Register', {
    'login': fields.String(required=True, description='Логин пользователя'),
    'password': fields.String(required=True, description='Пароль'),
    'name': fields.String(required=True, description='Имя пользователя'),
    'user_type': fields.String(
        required=True, 
        description='Тип пользователя', 
        enum=['doctor', 'admin', 'disinfector']
    )
})

token_model = auth_ns.model('Token', {
    'access_token': fields.String(description='JWT access token'),
    'refresh_token': fields.String(description='JWT refresh token'),
    'token_type': fields.String(description='Тип токена', example='Bearer')
})

user_info_model = auth_ns.model('UserInfo', {
    'id': fields.Integer(description='ID пользователя'),
    'login': fields.String(description='Логин'),
    'name': fields.String(description='Имя'),
    'user_type': fields.String(description='Тип пользователя', enum=['admin', 'doctor', 'disinfector']),
    'created_at': fields.DateTime(description='Дата регистрации'),
    'last_login': fields.DateTime(description='Последний вход')
})

change_password_model = auth_ns.model('ChangePassword', {
    'old_password': fields.String(required=True, description='Старый пароль'),
    'new_password': fields.String(required=True, description='Новый пароль (мин. 8 символов)')
})

# Общая модель ошибки
error_model = create_error_model(auth_ns)

response_model = create_response_model(auth_ns, 'Token', token_model)

user_response_model = create_response_model(auth_ns, 'UserInfo', user_info_model) 


# ==================== ЭНДПОИНТЫ ====================

@auth_ns.route('/login')
class Login(Resource):
    """Аутентификация пользователя"""
    
    @auth_ns.expect(login_model, validate=True)
    @auth_ns.doc('login_user')
    @auth_ns.response(200, 'Успешная аутентификация', token_model)
    @auth_ns.response(401, 'Неверные учетные данные')
    @auth_ns.response(422, 'Ошибка валидации')
    def post(self):
        """
        Вход в систему и получение JWT токенов.
        
        Возвращает access_token и refresh_token для доступа к API.
        Access token действителен 1 час, refresh token — 30 дней.
        """
        # Валидация входных данных
        try:
            data = LoginSchema().load(request.get_json())
        except ValidationError as err:
            return validation_error_response(err.messages)
        
        # Аутентификация
        user = AuthService.authenticate(data['login'], data['password'])
        
        if not user:
            return error_response('Invalid credentials', 401)
        
        # Генерация токенов
        tokens = AuthService.generate_tokens(user)
        
        return success_response(tokens)


@auth_ns.route('/register')
class Register(Resource):
    """Регистрация нового пользователя"""
    
    @auth_ns.expect(register_model, validate=True)
    @auth_ns.doc('register_user')
    @auth_ns.response(201, 'Пользователь создан', user_info_model)
    @auth_ns.response(403, 'Доступ запрещён (только admin)')
    @auth_ns.response(409, 'Логин уже существует')
    @auth_ns.response(422, 'Ошибка валидации')
    @jwt_required()
    @admin_required
    def post(self):
        """
        Регистрация нового пользователя (только для администраторов).
        
        Создаёт нового пользователя в системе. Доступно только администраторам.
        """
        # Валидация входных данных
        try:
            data = RegisterSchema().load(request.get_json())
        except ValidationError as err:
            return validation_error_response(err.messages)
        
        # Регистрация пользователя
        try:
            user = AuthService.register_user(data)
        except Exception as e:
            return error_response(str(e), 409)
        
        user_data = {
            'id': user.id,
            'login': user.login,
            'name': user.name,
            'user_type': user.user_type,
            'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
            'last_login': user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else None
        }
        
        return created_response(user_data)


@auth_ns.route('/refresh')
class Refresh(Resource):
    """Обновление access token"""
    
    @auth_ns.doc('refresh_token')
    @auth_ns.response(200, 'Токен обновлён', token_model)
    @auth_ns.response(401, 'Невалидный refresh token')
    @jwt_required(refresh=True)
    def post(self):
        """
        Обновление access token по refresh token.
        
        Используется когда access token истёк. Refresh token должен быть
        передан в заголовке Authorization.
        """
        identity = get_jwt_identity()
        
        # Получаем дополнительную информацию из claims
        claims = get_jwt()
        additional_claims = {
            'user_type': claims.get('user_type'),
            'name': claims.get('name'),
            'login': claims.get('login')
        }
        
        access_token = create_access_token(
            identity=identity,
            additional_claims=additional_claims
        )
        
        return success_response({
            'access_token': access_token,
            'token_type': 'Bearer'
        })


@auth_ns.route('/logout')
class Logout(Resource):
    """Выход из системы"""
    
    @auth_ns.doc('logout_user')
    @auth_ns.response(200, 'Успешный выход')
    @auth_ns.response(401, 'Не авторизован')
    @jwt_required()
    def post(self):
        """
        Выход из системы и отзыв токена.
        
        Текущий access token добавляется в Redis blacklist и больше не может быть использован.
        """
        from app.core.redis_client import get_redis_client
        
        # Получаем JTI токена
        jti = get_jwt()['jti']
        
        # Получаем время жизни токена
        token_exp = get_jwt()['exp']
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).timestamp()
        ttl = int(token_exp - now)
        
        # Добавляем в blacklist
        redis_client = get_redis_client()
        
        if redis_client is not None:
            try:
                # Используем set вместо устаревшего setex
                redis_client.set(f"blocklist:{jti}", "revoked", ex=ttl)
                logger.info(f"Token {jti} added to blacklist (TTL: {ttl}s)")
            except Exception as e:
                logger.error(f"Failed to add token to blacklist: {e}")
                # Продолжаем даже если Redis недоступен
        else:
            logger.warning("Redis unavailable, token not blacklisted")
        
        return success_response({'message': 'Successfully logged out'})


@auth_ns.route('/me')
class Me(Resource):
    """Информация о текущем пользователе"""
    
    @auth_ns.doc('get_current_user')
    @auth_ns.response(200, 'Информация о пользователе', user_info_model)
    @auth_ns.response(401, 'Не авторизован')
    @auth_ns.response(404, 'Пользователь не найден', error_model)
    @jwt_required()
    def get(self):
        """
        Получение информации о текущем авторизованном пользователе.
        
        Возвращает данные пользователя на основе JWT токена.
        """
        from app.domain.models.user.entities import User
        
        user_id = get_jwt_identity()
        user = db.session.get(User, int(user_id))
        
        if not user:
            return error_response('User not found', 404)
        
        user_data = {
            'id': user.id,
            'login': user.login,
            'name': user.name,
            'user_type': user.user_type,
            'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
            'last_login': user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else None
        }
        
        return success_response(user_data)


@auth_ns.route('/change-password')
class ChangePassword(Resource):
    """Смена пароля"""
    
    @auth_ns.expect(change_password_model, validate=True)
    @auth_ns.doc('change_password')
    @auth_ns.response(200, 'Пароль изменён')
    @auth_ns.response(400, 'Неверный старый пароль')
    @auth_ns.response(401, 'Не авторизован')
    @auth_ns.response(422, 'Ошибка валидации')
    @jwt_required()
    def post(self):
        """
        Смена пароля текущего пользователя.
        
        Требует указания старого пароля для подтверждения.
        """
        from app.domain.models.user.entities import User
        
        # Валидация входных данных
        try:
            data = ChangePasswordSchema().load(request.get_json())
        except ValidationError as err:
            return validation_error_response(err.messages)
        
        # Получение текущего пользователя
        user_id = get_jwt_identity()
        
        user = db.session.get(User, int(user_id))
        
        if not user:
            return error_response('User not found', 404)
        
        # Смена пароля
        try:
            AuthService.change_password(user, data['old_password'], data['new_password'])
        except ValueError as e:
            return error_response(str(e), 400)
        
        return success_response({'message': 'Password changed successfully'})