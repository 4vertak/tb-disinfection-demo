"""REST API эндпоинты для логов аудита."""
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from .schemas import ApplicationAuditLogSchema, UserAuditLogSchema
from .services import AuditService
from ..common.response import success_response, error_response

# Создание namespace
audit_ns = Namespace('audit', description='Логи аудита и история изменений')

# ==================== SWAGGER МОДЕЛИ ====================
audit_log_model = audit_ns.model('AuditLog', {
    'id': fields.Integer(description='ID записи лога'),
    'application_id': fields.Integer(description='ID заявки'),
    'changed_by': fields.Integer(description='ID пользователя'),
    'change_time': fields.DateTime(description='Время изменения'),
    'change_type': fields.String(description='Тип изменения', enum=['INSERT', 'UPDATE', 'DELETE']),
    'old_data': fields.Raw(description='Старые данные'),
    'new_data': fields.Raw(description='Новые данные'),
})

# ==================== ENDPOINTS ====================

@audit_ns.route('/applications/<int:id>')
@audit_ns.param('id', 'ID заявки')
class ApplicationAuditHistory(Resource):
    @audit_ns.doc('get_application_audit_history')
    @audit_ns.response(200, 'История изменений заявки')
    @jwt_required()
    def get(self, id):
        """
        Получить историю изменений конкретной заявки.
        Доступно администраторам и владельцу заявки.
        """
        from app.domain.models.application.entities import Application
        from app.core.extensions import db
        
        claims = get_jwt()
        user_id = int(get_jwt_identity())
        
        # Проверка прав: админ или владелец заявки
        if claims.get('user_type') != 'admin':
            application = db.session.get(Application, id)
            if not application or application.user_id != user_id:
                return error_response('Access denied', 403)
        
        history = AuditService.get_application_history(id)
        return success_response(ApplicationAuditLogSchema(many=True).dump(history))


@audit_ns.route('/users/<int:id>')
@audit_ns.param('id', 'ID пользователя')
class UserAuditHistory(Resource):
    @audit_ns.doc('get_user_audit_history')
    @audit_ns.response(200, 'История действий пользователя')
    @jwt_required()
    def get(self, id):
        """
        Получить историю действий пользователя.
        Доступно администраторам и самому пользователю.
        """
        claims = get_jwt()
        current_user_id = int(get_jwt_identity())
        
        # Проверка прав: админ или сам пользователь
        if claims.get('user_type') != 'admin' and current_user_id != id:
            return error_response('Access denied', 403)
        
        history = AuditService.get_user_history(id)
        return success_response(UserAuditLogSchema(many=True).dump(history))