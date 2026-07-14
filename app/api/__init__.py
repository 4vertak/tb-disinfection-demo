"""
Инициализация REST API.
Регистрирует все API Blueprint'ы и настраивает middleware.
"""
from flask import Flask, Blueprint, jsonify
from werkzeug.exceptions import BadRequest
from flask_restx import Api
from app.core.extensions import cors, cache, limiter, jwt, API_AUTHORIZATIONS
from app.api.v1.common.errors import register_api_error_handlers
from app.core.redis_client import get_redis_client
import logging

logger = logging.getLogger(__name__)


def register_api(app: Flask):
    """Зарегистрировать REST API в Flask приложении."""
    
    # Проверяем feature flag
    if not app.config.get('FEATURE_FLAG_API_V1_ENABLED', True):
        return
    
    app.url_map.strict_slashes = False
    app.config['PRESERVE_TRAILING_SLASH'] = False
    app.config['APPEND_SLASH'] = False
    
    # Инициализация расширений
    # Обрабатываем CORS_ALLOWED_ORIGINS как строку или список
    cors_origins = app.config.get('CORS_ALLOWED_ORIGINS', '*')
    if isinstance(cors_origins, str):
        if cors_origins == '*':
            cors_origins_final = '*'
        else:
            cors_origins_final = [origin.strip() for origin in cors_origins.split(',')]
    else:
        cors_origins_final = cors_origins

    cors.init_app(app, resources={
        r"/api/*": {
            "origins": cors_origins_final,
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Authorization", "Content-Type", "X-Requested-With", "Accept"],
            "expose_headers": ["X-Total-Count", "X-Page-Count"],
            "supports_credentials": True,
            "max_age": 600
        }
    })
    
    cache.init_app(app, config={
        'CACHE_TYPE': app.config.get('CACHE_TYPE', 'RedisCache'),
        'CACHE_REDIS_URL': app.config.get('CACHE_REDIS_URL', 'redis://localhost:6379/0'),
        'CACHE_DEFAULT_TIMEOUT': app.config.get('CACHE_DEFAULT_TIMEOUT', 300)
    })
    
    limiter.init_app(app)
    jwt.init_app(app)
    
    # Создаём Blueprint для API
    from app.core import extensions
    extensions.api_bp = Blueprint('api', __name__)
    extensions.api = Api(
        extensions.api_bp,
        version='1.0',
        title='АИС Дезинфекция API',
        description='REST API для системы дезинфекции медицинской службы',
        doc='/api/docs',
        authorizations=API_AUTHORIZATIONS,
        security='Bearer Auth',
        prefix='/api/v1'
    )
    
    # ==================== КРИТИЧНО: Flask-RESTX error handlers ====================
    # Flask-RESTX перехватывает ошибки ДО app.errorhandler!
    # Нужно использовать api.errorhandler для API-путей
    _register_flask_restx_error_handlers(extensions.api, app)
    
    # Импорт и регистрация namespaces
    from app.api.v1.auth.routes import auth_ns
    from app.api.v1.users.routes import users_ns
    from app.api.v1.applications.routes import applications_ns
    from app.api.v1.references.routes import references_ns
    from app.api.v1.notifications.routes import notifications_ns
    from app.api.v1.dashboard.routes import dashboard_ns
    from app.api.v1.reports.routes import reports_ns
    from app.api.v1.blog.routes import blog_ns
    from app.api.v1.search.routes import search_ns
    from app.api.v1.audit.routes import audit_ns
    
    extensions.api.add_namespace(auth_ns, path='/auth')
    extensions.api.add_namespace(users_ns, path='/users')
    extensions.api.add_namespace(applications_ns, path='/applications')
    extensions.api.add_namespace(references_ns, path='/references')
    extensions.api.add_namespace(notifications_ns, path='/notifications')
    extensions.api.add_namespace(dashboard_ns, path='/dashboard')
    extensions.api.add_namespace(reports_ns, path='/reports')
    extensions.api.add_namespace(blog_ns, path='/blog')
    extensions.api.add_namespace(search_ns, path='/search')
    extensions.api.add_namespace(audit_ns, path='/audit')
    
    app.register_blueprint(extensions.api_bp)
    
    # ==================== JWT CALLBACKS ====================
    # Регистрируем только один раз
    if not hasattr(app, '_jwt_api_callbacks_registered'):
        
        @jwt.token_in_blocklist_loader
        def check_if_token_revoked(jwt_header, jwt_payload):
            """
            Проверить, отозван ли токен через Redis blacklist.
            
            Returns:
                bool: True если токен отозван, False если действителен
            """
            redis_client = get_redis_client()
            
            # Если Redis недоступен, разрешаем токен (graceful degradation)
            if redis_client is None:
                logger.warning("Redis unavailable, allowing token (blacklist disabled)")
                return False
            
            try:
                jti = jwt_payload['jti']
                # Проверяем наличие JTI в blacklist
                token_in_blacklist = redis_client.get(f"blocklist:{jti}")
                return token_in_blacklist is not None
            except Exception as e:
                logger.error(f"Error checking token blacklist: {e}")
                # При ошибке Redis разрешаем токен
                return False
        
        @jwt.expired_token_loader
        def expired_token_callback(jwt_header, jwt_payload):
            """Обработка истёкшего токена"""
            return _make_api_error_response('Token has expired', 401)
        
        @jwt.invalid_token_loader
        def invalid_token_callback(error):
            """Обработка невалидного токена"""
            return _make_api_error_response(f'Invalid token: {error}', 401)
        
        @jwt.unauthorized_loader
        def missing_token_callback(error):
            """Обработка отсутствия токена"""
            return _make_api_error_response('Authorization token is required', 401)
        
        app._jwt_api_callbacks_registered = True
    
    # Регистрируем также общие обработчики (для не-API путей)
    register_api_error_handlers(app)
    
    logger.info("REST API зарегистрирован с Flask-RESTX error handlers")


def _make_api_error_response(message, status_code, details=None):
    """
    Создать унифицированный ответ с ошибкой для Flask-RESTX.
    
    ⚠️ ВАЖНО: Flask-RESTX требует dict, а НЕ Flask Response объект!
    В отличие от Flask @app.errorhandler, который принимает (Response, status_code),
    Flask-RESTX @api.errorhandler принимает (dict, status_code) и сам сериализует dict в JSON.
    
    Если вернуть jsonify(...), Flask-RESTX попытается вызвать .get() на Response
    и упадёт с AttributeError: 'Response' object has no attribute 'get'
    """
    error_item = {'code': status_code, 'message': message}
    if details is not None:
        error_item['details'] = details

    # Возвращаем dict + status_code (НЕ jsonify!)
    # Flask-RESTX сам обернёт это в Response с JSON
    return {
        'data': None,
        'meta': None,
        'errors': [error_item]
    }, status_code


def _register_flask_restx_error_handlers(api, app):
    """Регистрация обработчиков ошибок через Flask-RESTX API."""
    
    # === PyJWT исключения (КРИТИЧНО!) ===
    try:
        from jwt.exceptions import (
            DecodeError, InvalidSignatureError, ExpiredSignatureError,
            InvalidTokenError, InvalidKeyError, InvalidAlgorithmError,
            InvalidAudienceError, InvalidIssuerError, ImmatureSignatureError,
        )

        @api.errorhandler(DecodeError)
        def handle_decode_error(error):
            logger.warning(f"JWT DecodeError caught: {error}")
            return _make_api_error_response('Invalid token format', 401,
                                            details='Token is malformed')

        @api.errorhandler(InvalidSignatureError)
        def handle_invalid_signature(error):
            return _make_api_error_response('Invalid token signature', 401)

        @api.errorhandler(ExpiredSignatureError)
        def handle_expired_signature(error):
            return _make_api_error_response('Token has expired', 401)

        @api.errorhandler(InvalidTokenError)
        def handle_invalid_token(error):
            return _make_api_error_response('Invalid token', 401)

        @api.errorhandler(InvalidKeyError)
        def handle_invalid_key(error):
            return _make_api_error_response('Invalid token key', 401)

        @api.errorhandler(InvalidAlgorithmError)
        def handle_invalid_algorithm(error):
            return _make_api_error_response('Invalid token algorithm', 401)

        @api.errorhandler(InvalidAudienceError)
        def handle_invalid_audience(error):
            return _make_api_error_response('Invalid token audience', 401)

        @api.errorhandler(InvalidIssuerError)
        def handle_invalid_issuer(error):
            return _make_api_error_response('Invalid token issuer', 401)

        @api.errorhandler(ImmatureSignatureError)
        def handle_immature_signature(error):
            return _make_api_error_response('Token not yet valid', 401)

        logger.info("PyJWT exception handlers registered (Flask-RESTX)")
    except ImportError:
        logger.warning("jwt library not found")

    # === Flask-JWT-Extended исключения ===
    try:
        from flask_jwt_extended.exceptions import (
            NoAuthorizationError, InvalidHeaderError, WrongTokenError,
            RevokedTokenError, FreshTokenRequired, CSRFError, UserLookupError,
        )

        @api.errorhandler(NoAuthorizationError)
        def handle_no_auth(error):
            return _make_api_error_response('Authorization token is required', 401)

        @api.errorhandler(InvalidHeaderError)
        def handle_invalid_header(error):
            return _make_api_error_response('Invalid Authorization header format', 401)

        @api.errorhandler(WrongTokenError)
        def handle_wrong_token(error):
            return _make_api_error_response('Wrong token type', 401)

        @api.errorhandler(RevokedTokenError)
        def handle_revoked_token(error):
            return _make_api_error_response('Token has been revoked', 401)

        @api.errorhandler(FreshTokenRequired)
        def handle_fresh_token(error):
            return _make_api_error_response('Fresh token required', 401)

        @api.errorhandler(CSRFError)
        def handle_csrf(error):
            return _make_api_error_response('CSRF validation failed', 401)

        @api.errorhandler(UserLookupError)
        def handle_user_lookup(error):
            return _make_api_error_response('User not found', 401)

        logger.info("Flask-JWT-Extended handlers registered (Flask-RESTX)")
    except ImportError:
        pass

    # === Marshmallow ===
    try:
        from marshmallow import ValidationError as MarshmallowValidationError

        @api.errorhandler(MarshmallowValidationError)
        def handle_marshmallow(error):
            return _make_api_error_response(
                'Validation failed', 422,
                details=error.messages if hasattr(error, 'messages') else None
            )
    except ImportError:
        pass
    
    @api.errorhandler(BadRequest)
    def handle_bad_request(error):
        logger.warning(f"BadRequest caught: {error}")
        return _make_api_error_response('Bad request', 400, details=str(error))

    # === Глобальный fallback для Exception ===
    @api.errorhandler(Exception)
    def handle_unhandled_exception(error):
        """Ловит ВСЕ необработанные исключения в API."""
        import sys
        
        # Получаем оригинальное исключение из стека
        exc_type, exc_value, exc_tb = sys.exc_info()
        original_error = exc_value if exc_value else error
        
        logger.error(
            f"API Exception caught: {type(original_error).__name__}: {original_error}",
            exc_info=True
        )

        # Проверяем PyJWT
        try:
            import jwt.exceptions
            jwt_exceptions = (
                jwt.exceptions.DecodeError,
                jwt.exceptions.InvalidTokenError,
                jwt.exceptions.ExpiredSignatureError,
                jwt.exceptions.InvalidSignatureError,
            )
            if isinstance(original_error, jwt_exceptions):
                logger.warning(f"JWT caught in fallback: {type(original_error).__name__}")
                return _make_api_error_response('Invalid token', 401,
                                                details=str(original_error))
        except ImportError:
            pass

        # Проверяем Flask-JWT-Extended
        try:
            import flask_jwt_extended.exceptions as fje
            fje_exceptions = (
                fje.NoAuthorizationError,
                fje.InvalidHeaderError,
                fje.WrongTokenError,
                fje.RevokedTokenError,
            )
            if isinstance(original_error, fje_exceptions):
                logger.warning(f"Flask-JWT caught in fallback: {type(original_error).__name__}")
                return _make_api_error_response('Unauthorized', 401,
                                                details=str(original_error))
        except ImportError:
            pass

        # Для всех остальных — 500
        return _make_api_error_response(
            'Internal server error', 500,
            details=str(original_error) if app.debug else None
        )

    logger.info("All Flask-RESTX error handlers registered")