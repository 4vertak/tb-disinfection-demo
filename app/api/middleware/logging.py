"""
Middleware для логирования API запросов/ответов.
"""

import logging
import time
from flask import request, g
from functools import wraps

logger = logging.getLogger(__name__)


def log_api_request(fn):
    """
    Декоратор для логирования API запросов.
    
    Логирует:
    - Метод и URL
    - Время выполнения
    - Статус код ответа
    """
    
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Запись времени начала запроса
        g.start_time = time.time()
        
        # Логирование запроса
        logger.info(
            f"API Request: {request.method} {request.path} "
            f"from {request.remote_addr}"
        )
        
        # Выполнение функции
        response = fn(*args, **kwargs)
        
        # Логирование ответа
        duration = time.time() - g.start_time
        status_code = response[1] if isinstance(response, tuple) else 200
        
        logger.info(
            f"API Response: {request.method} {request.path} "
            f"status={status_code} duration={duration:.3f}s"
        )
        
        return response
    return wrapper