"""
Унифицированный формат ответов REST API.

Все эндпоинты возвращают JSON в формате:
{
    "data": {...},
    "meta": {...},
    "errors": [...]
}
"""

def api_response(data=None, meta=None, errors=None, status_code=200):
    """
    Создать унифицированный ответ API.
    Возвращает dict + status_code для совместимости с Flask-RESTX.
    """
    response = {
        'data': data,
        'meta': meta,
        'errors': errors
    }
    
    return response, status_code


def success_response(data, meta=None, status_code=200):
    """Успешный ответ с данными"""
    return api_response(data=data, meta=meta, status_code=status_code)

def list_response(items, meta, status_code=200):
    """Ответ со списком элементов (для пагинации)"""
    response = {
        'data': {
            'items': items,
            'meta': meta
        },
        'errors': None
    }
    return response, status_code


def created_response(data, meta=None):
    """Ответ при создании ресурса (201)"""
    return api_response(data=data, meta=meta, status_code=201)


def no_content_response():
    """Ответ без содержимого (204)"""
    return '', 204


def error_response(message, status_code=400, errors=None):
    """Ответ с ошибкой"""
    error_list = [{
        'code': status_code,
        'message': message,
        'details': errors
    }]
    return api_response(data=None, meta=None, errors=error_list, status_code=status_code)


def validation_error_response(validation_errors):
    """Ответ с ошибками валидации (422)"""
    error_list = [{
        'code': 422,
        'message': 'Validation failed',
        'details': validation_errors
    }]
    return api_response(data=None, meta=None, errors=error_list, status_code=422)