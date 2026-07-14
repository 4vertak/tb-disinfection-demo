from flask import render_template, jsonify, request
import logging
from .extensions import db

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Регистрирует глобальные обработчики ошибок Flask."""

    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Resource not found'}), 404
        return render_template('main/error.html', error_code=404, message='Страница не найдена'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Access forbidden'}), 403
        return render_template('main/error.html', error_code=403, message='Доступ запрещён'), 403

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        logger.error(f"Internal server error: {error}", exc_info=True)
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('main/error.html', error_code=500, message='Внутренняя ошибка сервера'), 500

    @app.errorhandler(413)
    def request_too_large(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'File too large'}), 413
        return render_template('main/error.html', error_code=413, message='Файл слишком большой'), 413

    @app.errorhandler(429)
    def ratelimit_handler(error):
        retry_after = getattr(error, 'description', None)
        if request.path.startswith('/api/'):
            message = 'Too many requests. Please try again later.'
            if retry_after:
                message += f' Retry after {retry_after} seconds.'
            return jsonify({'error': message, 'retry_after': retry_after}), 429
        
        message = 'Слишком много запросов. Попробуйте позже.'
        if retry_after:
            message += f' Повторите через {retry_after} сек.'
        return render_template('main/error.html', error_code=429, message=message), 429
