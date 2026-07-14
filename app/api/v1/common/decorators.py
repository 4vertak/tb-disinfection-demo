"""
Декораторы для REST API.

Используются для:
- Проверки прав доступа (RBAC)
- Валидации данных
- Логирования
"""
from functools import wraps
from flask import request
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity
from .response import error_response
from app.core.extensions import db


def admin_required(fn):
    """
    Декоратор для проверки прав администратора.
    
    Использование:
        @admin_required
        def delete_user(user_id):
            ...
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get('user_type') != 'admin':
            return error_response('Admin access required', 403)
        return fn(*args, **kwargs)
    return wrapper


def doctor_required(fn):
    """
    Декоратор для проверки прав врача.
    
    Доступно для: admin, doctor
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get('user_type') not in ['admin', 'doctor']:
            return error_response('Doctor access required', 403)
        return fn(*args, **kwargs)
    return wrapper


def disinfector_required(fn):
    """
    Декоратор для проверки прав дезинфектора.
    
    Доступно для: admin, doctor, disinfector
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get('user_type') not in ['admin', 'doctor', 'disinfector']:
            return error_response('Disinfector access required', 403)
        return fn(*args, **kwargs)
    return wrapper


def validate_json(fn):
    """
    Декоратор для проверки Content-Type: application/json.
    
    Использование:
        @validate_json
        def create_user():
            ...
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not request.is_json:
            return error_response('Request must be JSON', 400)
        return fn(*args, **kwargs)
    return wrapper


def validate_schema(schema_class):
    """
    Декоратор для валидации данных через Marshmallow схему.
    
    Использование:
        @validate_schema(UserCreateSchema)
        def create_user():
            data = request.get_json()
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            schema = schema_class()
            try:
                # Валидация данных
                validated_data = schema.load(request.get_json())
                # Передаём валидированные данные в функцию
                request.validated_data = validated_data
            except Exception as e:
                return error_response('Validation failed', 422, errors=str(e))
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def owner_or_admin_required(model_class, id_param='id'):
    """
    Декоратор для проверки, что пользователь является владельцем ресурса или админом.
    
    Использование:
        @owner_or_admin_required(Application, 'application_id')
        def update_application(application_id):
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_id = int(get_jwt_identity())
            
            # Админ имеет доступ ко всему
            if claims.get('user_type') == 'admin':
                return fn(*args, **kwargs)
            
            # Проверяем, является ли пользователь владельцем
            resource_id = kwargs.get(id_param)
            resource = db.session.get(model_class, resource_id)
            
            if not resource:
                return error_response('Resource not found', 404)
            
            # Проверяем владельца (предполагается, что у модели есть поле user_id или doctor_id)
            owner_id = getattr(resource, 'user_id', None) or getattr(resource, 'doctor_id', None)
            
            if owner_id != user_id:
                return error_response('Access denied', 403)
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator