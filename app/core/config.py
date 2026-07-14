import os
from datetime import timedelta
from dotenv import load_dotenv

env = os.environ.get('FLASK_ENV', 'development')
if env == 'production':
    load_dotenv('.env.production')
else:
    load_dotenv('.env')


class Config:
    """Базовая конфигурация"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Environment
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    TESTING = os.environ.get('TESTING', 'False').lower() == 'true'
    
    # SocketIO config
    SOCKETIO_ASYNC_MODE = os.environ.get('SOCKETIO_ASYNC_MODE', 'gevent')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/disinfection_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = os.environ.get(
        'SQLALCHEMY_TRACK_MODIFICATIONS', 'False'
    ).lower() == 'true'
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        seconds=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', 2592000))
    )
    JWT_TOKEN_LOCATION = os.environ.get('JWT_TOKEN_LOCATION', 'headers').split(',')
    JWT_HEADER_NAME = os.environ.get('JWT_HEADER_NAME', 'Authorization')
    JWT_HEADER_TYPE = os.environ.get('JWT_HEADER_TYPE', 'Bearer')
    JWT_BLACKLIST_ENABLED = os.environ.get(
        'JWT_BLACKLIST_ENABLED', 'True'
    ).lower() == 'true'
    JWT_BLACKLIST_TOKEN_CHECKS = os.environ.get(
        'JWT_BLACKLIST_TOKEN_CHECKS', 'access,refresh'
    ).split(',')
    
    # CORS
    CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '*').split(',')
    
    # Cache (Redis)
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'RedisCache')
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
    
    # Rate Limiting
    RATELIMIT_ENABLED = os.environ.get('FLASK_ENV', 'development') == 'production'
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', ' ')
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')
    
    # Feature Flags
    FEATURE_FLAG_API_V1_ENABLED = os.environ.get(
        'FEATURE_FLAG_API_V1_ENABLED', 'True'
    ).lower() == 'true'
    FEATURE_FLAG_JWT_AUTH_ENABLED = os.environ.get(
        'FEATURE_FLAG_JWT_AUTH_ENABLED', 'True'
    ).lower() == 'true'
    
    # Session Security
    SESSION_COOKIE_SECURE = os.environ.get(
        'SESSION_COOKIE_SECURE', 'False'
    ).lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.environ.get(
        'SESSION_COOKIE_HTTPONLY', 'True'
    ).lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')


class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True
    TESTING = False
    RATELIMIT_ENABLED = False  # Отключаем rate limiting в development


class ProductionConfig(Config):
    """Конфигурация для production"""
    DEBUG = False
    TESTING = False
    RATELIMIT_ENABLED = True  # Включаем rate limiting в production
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '200 per day, 50 per hour')
    
    # Дополнительные production настройки
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PREFERRED_URL_SCHEME = 'https'
    
    # В production логируем только INFO и выше
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')


class TestingConfig(Config):
    """Конфигурация для тестирования"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    CACHE_TYPE = 'SimpleCache'
    CACHE_REDIS_URL = None
    RATELIMIT_ENABLED = False  # Отключаем rate limiting в тестах
    RATELIMIT_DEFAULT = ''  # Нет глобальных лимитов
    RATELIMIT_STORAGE_URL = 'memory://'


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}