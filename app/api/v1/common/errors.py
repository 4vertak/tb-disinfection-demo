"""
Единая система обработки ошибок REST API.

Все ошибки возвращаются в унифицированном JSON-формате:
{
    "data": null,
    "meta": null,
    "errors": [{"code": ..., "message": ..., "details": ...}]
}
"""
from flask import jsonify, request
import logging

logger = logging.getLogger(__name__)


def _make_error_response(message, status_code, details=None):
    """Создать унифицированный JSON-ответ с ошибкой."""
    error_item = {
        'code': status_code,
        'message': message,
    }
    if details is not None:
        error_item['details'] = details

    return jsonify({
        'data': None,
        'meta': None,
        'errors': [error_item]
    }), status_code


# ==================== КАСТОМНЫЕ API ОШИБКИ ====================

class APIError(Exception):
    """Базовый класс для API ошибок"""
    def __init__(self, message, status_code=400, errors=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.errors = errors or []

    def to_dict(self):
        return {
            'data': None,
            'meta': None,
            'errors': [{
                'code': self.status_code,
                'message': self.message,
                'details': self.errors
            }]
        }


class ValidationError(APIError):
    def __init__(self, errors):
        super().__init__('Validation failed', 422, errors)


class NotFoundError(APIError):
    def __init__(self, resource, resource_id):
        super().__init__(f'{resource} with id {resource_id} not found', 404)


class UnauthorizedError(APIError):
    def __init__(self, message='Authentication required'):
        super().__init__(message, 401)


class ForbiddenError(APIError):
    def __init__(self, message='Insufficient permissions'):
        super().__init__(message, 403)


class BadRequestError(APIError):
    def __init__(self, message='Bad request', errors=None):
        super().__init__(message, 400, errors)


class ConflictError(APIError):
    def __init__(self, message='Resource already exists'):
        super().__init__(message, 409)


class TooManyRequestsError(APIError):
    def __init__(self, message='Too many requests'):
        super().__init__(message, 429)


# ==================== РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ ====================

def register_api_error_handlers(app):
    """Зарегистрировать обработчики ошибок API."""

    # === PyJWT исключения (КРИТИЧНО!) ===
    try:
        from jwt.exceptions import (
            DecodeError, InvalidSignatureError, ExpiredSignatureError,
            InvalidTokenError, InvalidKeyError, InvalidAlgorithmError,
            InvalidAudienceError, InvalidIssuerError, ImmatureSignatureError,
        )

        @app.errorhandler(DecodeError)
        def _handle_decode_error(error):
            logger.warning(f"JWT DecodeError: {error}")
            return _make_error_response(
                'Invalid token format', 401,
                details='The token is malformed or has invalid format'
            )

        @app.errorhandler(InvalidSignatureError)
        def _handle_invalid_signature(error):
            return _make_error_response('Invalid token signature', 401)

        @app.errorhandler(ExpiredSignatureError)
        def _handle_expired_signature(error):
            return _make_error_response('Token has expired', 401)

        @app.errorhandler(InvalidTokenError)
        def _handle_invalid_token(error):
            return _make_error_response('Invalid token', 401)

        @app.errorhandler(InvalidKeyError)
        def _handle_invalid_key(error):
            return _make_error_response('Invalid token key', 401)

        @app.errorhandler(InvalidAlgorithmError)
        def _handle_invalid_algorithm(error):
            return _make_error_response('Invalid token algorithm', 401)

        @app.errorhandler(InvalidAudienceError)
        def _handle_invalid_audience(error):
            return _make_error_response('Invalid token audience', 401)

        @app.errorhandler(InvalidIssuerError)
        def _handle_invalid_issuer(error):
            return _make_error_response('Invalid token issuer', 401)

        @app.errorhandler(ImmatureSignatureError)
        def _handle_immature_signature(error):
            return _make_error_response('Token not yet valid', 401)

        logger.info("PyJWT exception handlers registered")
    except ImportError:
        logger.warning("jwt library not found, JWT handlers not registered")

    # === Flask-JWT-Extended исключения ===
    try:
        from flask_jwt_extended.exceptions import (
            NoAuthorizationError, InvalidHeaderError, WrongTokenError,
            RevokedTokenError, FreshTokenRequired, CSRFError, UserLookupError,
        )

        @app.errorhandler(NoAuthorizationError)
        def _handle_no_auth(error):
            return _make_error_response('Authorization token is required', 401)

        @app.errorhandler(InvalidHeaderError)
        def _handle_invalid_header(error):
            return _make_error_response('Invalid Authorization header format', 401)

        @app.errorhandler(WrongTokenError)
        def _handle_wrong_token(error):
            return _make_error_response('Wrong token type', 401)

        @app.errorhandler(RevokedTokenError)
        def _handle_revoked_token(error):
            return _make_error_response('Token has been revoked', 401)

        @app.errorhandler(FreshTokenRequired)
        def _handle_fresh_token(error):
            return _make_error_response('Fresh token required', 401)

        @app.errorhandler(CSRFError)
        def _handle_csrf(error):
            return _make_error_response('CSRF validation failed', 401)

        @app.errorhandler(UserLookupError)
        def _handle_user_lookup(error):
            return _make_error_response('User not found', 401)

        logger.info("Flask-JWT-Extended exception handlers registered")
    except ImportError:
        pass

    # === Marshmallow ===
    try:
        from marshmallow import ValidationError as MarshmallowValidationError

        @app.errorhandler(MarshmallowValidationError)
        def _handle_marshmallow(error):
            return _make_error_response(
                'Validation failed', 422,
                details=error.messages if hasattr(error, 'messages') else None
            )
    except ImportError:
        pass

    # === Кастомные API ошибки ===
    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    # === HTTP ошибки ===
    @app.errorhandler(400)
    def handle_400(error):
        return _make_error_response('Bad request', 400)

    @app.errorhandler(401)
    def handle_401(error):
        return _make_error_response('Unauthorized', 401)

    @app.errorhandler(403)
    def handle_403(error):
        return _make_error_response('Access forbidden', 403)

    @app.errorhandler(404)
    def handle_404(error):
        return _make_error_response('Resource not found', 404)

    @app.errorhandler(405)
    def handle_405(error):
        return _make_error_response('Method not allowed', 405)

    @app.errorhandler(422)
    def handle_422(error):
        return _make_error_response(
            'Unprocessable entity', 422,
            details=getattr(error, 'description', None)
        )

    @app.errorhandler(429)
    def handle_429(error):
        return _make_error_response('Too many requests', 429)

    # === ПЕРЕЗАПИСЬ обработчика 500 для API-путей ===
    # Перекрывает legacy обработчик из app/core/errors.py
    @app.errorhandler(500)
    def handle_api_500_override(error):
        """Перехватывает все 500 ошибки для API и проверяет JWT-исключения."""
        import sys

        # Получаем оригинальное исключение из стека Python
        # Это работает даже если Flask преобразовал его в HTTPException
        exc_type, exc_value, exc_tb = sys.exc_info()
        original_error = exc_value if exc_value else error

        # Также проверяем атрибут original_exception (Flask 2.3+)
        if hasattr(error, 'original_exception') and error.original_exception:
            original_error = error.original_exception

        logger.error(
            f"API 500 handler: {type(original_error).__name__}: {original_error}",
            exc_info=True
        )

        # === Проверяем PyJWT исключения ===
        try:
            import jwt.exceptions
            jwt_exceptions = (
                jwt.exceptions.DecodeError,
                jwt.exceptions.InvalidTokenError,
                jwt.exceptions.ExpiredSignatureError,
                jwt.exceptions.InvalidSignatureError,
                jwt.exceptions.InvalidKeyError,
                jwt.exceptions.InvalidAlgorithmError,
                jwt.exceptions.InvalidAudienceError,
                jwt.exceptions.InvalidIssuerError,
            )
            if hasattr(jwt.exceptions, 'ImmatureSignatureError'):
                jwt_exceptions = jwt_exceptions + (
                    jwt.exceptions.ImmatureSignatureError,
                )

            if isinstance(original_error, jwt_exceptions):
                logger.warning(
                    f"✅ JWT error caught: {type(original_error).__name__}"
                )
                return _make_error_response(
                    'Invalid token', 401, details=str(original_error)
                )
        except ImportError:
            pass

        # === Проверяем Flask-JWT-Extended исключения ===
        try:
            import flask_jwt_extended.exceptions as fje
            fje_exceptions = (
                fje.NoAuthorizationError,
                fje.InvalidHeaderError,
                fje.WrongTokenError,
                fje.RevokedTokenError,
                fje.FreshTokenRequired,
                fje.UserLookupError,
            )
            if hasattr(fje, 'CSRFError'):
                fje_exceptions = fje_exceptions + (fje.CSRFError,)

            if isinstance(original_error, fje_exceptions):
                logger.warning(
                    f"✅ Flask-JWT error caught: {type(original_error).__name__}"
                )
                return _make_error_response(
                    'Unauthorized', 401, details=str(original_error)
                )
        except ImportError:
            pass

        # === Если путь не /api/ — возвращаем HTML (legacy поведение) ===
        if not request.path.startswith('/api/'):
            try:
                from flask import render_template
                from app.core.extensions import db
                db.session.rollback()
                return render_template(
                    'main/error.html',
                    error_code=500,
                    message='Внутренняя ошибка сервера'
                ), 500
            except Exception:
                pass

        # === Для всех остальных API ошибок — JSON 500 ===
        return _make_error_response(
            'Internal server error', 500,
            details=str(original_error) if app.debug else None
        )

        # === FALLBACK для Exception (перехватывает до преобразования в 500) ===
    @app.errorhandler(Exception)
    def handle_unhandled_exception(error):
        """Ловит все необработанные исключения ДО преобразования Flask."""
        import sys

        logger.error(
            f"Unhandled exception caught: {type(error).__name__}: {error}",
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
            if isinstance(error, jwt_exceptions):
                logger.warning(f"✅ JWT caught in fallback: {type(error).__name__}")
                return _make_error_response('Invalid token', 401, details=str(error))
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
            if isinstance(error, fje_exceptions):
                logger.warning(f"✅ Flask-JWT caught in fallback: {type(error).__name__}")
                return _make_error_response('Unauthorized', 401, details=str(error))
        except ImportError:
            pass

        # Если путь не /api/ — пробрасываем для legacy HTML обработчика
        if not request.path.startswith('/api/'):
            raise error

        # Для API возвращаем JSON 500
        return _make_error_response(
            'Internal server error', 500,
            details=str(error) if app.debug else None
        )

    logger.info("All API error handlers registered (with sys.exc_info)")