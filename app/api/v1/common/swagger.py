"""
Конфигурация Swagger/OpenAPI документации.
"""
from flask_restx import fields


# Базовые модели для Swagger
pagination_model = None  # Будет инициализирована после создания api


def create_pagination_model(api):
    """Создать модель пагинации для Swagger"""

    global pagination_model
    pagination_model = api.model('Pagination', {
        'page': fields.Integer(description='Текущая страница'),
        'per_page': fields.Integer(description='Элементов на странице'),
        'total': fields.Integer(description='Всего элементов'),
        'pages': fields.Integer(description='Всего страниц'),
        'has_next': fields.Boolean(description='Есть следующая страница'),
        'has_prev': fields.Boolean(description='Есть предыдущая страница')
    })
    return pagination_model


def create_error_model(api):
    """Создать модель ошибки для Swagger"""

    return api.model('Error', {
        'code': fields.Integer(description='HTTP статус код'),
        'message': fields.String(description='Сообщение об ошибке'),
        'details': fields.Raw(description='Детали ошибки')
    })


def create_response_model(api, data_model_name, data_model):
    """Создать унифицированную модель ответа"""
    
    return api.model(f'{data_model_name}Response', {
        'data': fields.Nested(data_model, description='Данные'),
        'meta': fields.Raw(description='Метаданные'),
        'errors': fields.List(fields.Nested(create_error_model(api)), description='Ошибки')
    })