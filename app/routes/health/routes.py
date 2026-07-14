"""
Health check endpoint для мониторинга работоспособности приложения.
"""
from flask import Blueprint, jsonify
from flask import current_app
from ...core.extensions import db

bp = Blueprint('health', __name__, url_prefix='/api/health')


@bp.route('/')
def health_check():
    """
    Базовый health check - проверяет, что приложение работает.
    """
    return jsonify({
        'status': 'healthy',
        'service': 'disinfection-requests-system'
    }), 200


@bp.route('/detailed')
def detailed_health_check():
    """
    Расширенный health check - проверяет подключение к базе данных.
    """
    health_status = {
        'status': 'healthy',
        'service': 'disinfection-requests-system',
        'checks': {}
    }
    
    # Проверка подключения к БД
    try:
        db.session.execute(db.text('SELECT 1'))
        health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['checks']['database'] = 'unhealthy'
        health_status['checks']['database_error'] = str(e)
        health_status['status'] = 'unhealthy'
    
    # Проверка переменных окружения
    required_configs = [
        'SECRET_KEY',
        'SQLALCHEMY_DATABASE_URI',
    ]
    
    missing_configs = [
        config for config in required_configs 
        if not current_app.config.get(config)
    ]
    
    if missing_configs:
        health_status['checks']['configuration'] = 'incomplete'
        health_status['checks']['missing_configs'] = missing_configs
        health_status['status'] = 'degraded'
    else:
        health_status['checks']['configuration'] = 'healthy'
    
    # Определяем HTTP статус код
    status_code = 200
    if health_status['status'] == 'unhealthy':
        status_code = 503
    elif health_status['status'] == 'degraded':
        status_code = 200  # Degraded, но не критично
    
    return jsonify(health_status), status_code
