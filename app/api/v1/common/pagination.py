"""
Универсальная пагинация для SQLAlchemy запросов.

Поддерживает:
- Page-based пагинацию (page, per_page)
- Offset-based пагинацию (offset, limit)
- Сортировку (sort=-created_at)
- Фильтрацию
"""
from flask import request


def paginate_query(query, schema, default_per_page=20, max_per_page=100):
    """
    Применить пагинацию к SQLAlchemy запросу.
    
    Args:
        query: SQLAlchemy query объект
        schema: Marshmallow схема для сериализации
        default_per_page: Количество элементов по умолчанию
        max_per_page: Максимальное количество элементов
    
    Returns:
        dict: Словарь с items и meta
    """
    # Определение режима пагинации
    if 'offset' in request.args or 'limit' in request.args:
        # Offset-based пагинация
        offset = request.args.get('offset', 0, type=int)
        limit = min(request.args.get('limit', default_per_page, type=int), max_per_page)
        
        # Подсчёт общего количества
        total = query.count()
        
        # Применение сортировки
        query = apply_sorting(query)
        
        # Применение пагинации
        items = query.offset(offset).limit(limit).all()
        
        # Вычисление метаданных
        page = (offset // limit) + 1 if limit > 0 else 1
        pages = (total + limit - 1) // limit if limit > 0 else 1
        has_next = offset + limit < total
        has_prev = offset > 0
        
    else:
        # Page-based пагинация
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', default_per_page, type=int), max_per_page)
        
        # Применение сортировки
        query = apply_sorting(query)
        
        # Применение пагинации
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        items = pagination.items
        total = pagination.total
        pages = pagination.pages
        has_next = pagination.has_next
        has_prev = pagination.has_prev
        offset = (page - 1) * per_page
        limit = per_page
    
    return {
        'items': schema.dump(items, many=True),
        'meta': {
            'page': page,
            'per_page': limit,
            'offset': offset,
            'limit': limit,
            'total': total,
            'pages': pages,
            'has_next': has_next,
            'has_prev': has_prev
        }
    }


def apply_sorting(query):
    """
    Применить сортировку к запросу.
    
    Формат: sort=-created_at (DESC) или sort=created_at (ASC)
    """
    sort_param = request.args.get('sort', '-created_at')
    
    if not sort_param:
        return query
    
    # Определение направления сортировки
    if sort_param.startswith('-'):
        order_col = sort_param[1:]
        descending = True
    else:
        order_col = sort_param
        descending = False
    
    # Получение модели из запроса
    try:
        model = query.column_descriptions[0]['entity']
        column = getattr(model, order_col, None)
        
        if column is not None:
            if descending:
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())
    except (IndexError, KeyError, AttributeError):
        # Если не удалось определить модель, возвращаем запрос без изменений
        pass
    
    return query


def get_pagination_params():
    """Получить параметры пагинации из запроса"""
    return {
        'page': request.args.get('page', 1, type=int),
        'per_page': request.args.get('per_page', 20, type=int),
        'offset': request.args.get('offset', type=int),
        'limit': request.args.get('limit', type=int),
        'sort': request.args.get('sort', '-created_at')
    }