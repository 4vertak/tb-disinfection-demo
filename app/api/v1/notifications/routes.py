"""REST API эндпоинты для уведомлений."""

from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from .schemas import NotificationSchema, NotificationUpdateSchema
from .services import NotificationApiService
from ..common.response import (
    success_response, no_content_response,
    error_response, validation_error_response, list_response
)

# Создание namespace
notifications_ns = Namespace('notifications', description='Управление уведомлениями')


# ==================== SWAGGER МОДЕЛИ ====================

notification_model = notifications_ns.model('Notification', {
    'id': fields.Integer(description='ID уведомления'),
    'user_id': fields.Integer(description='ID пользователя'),
    'title': fields.String(description='Заголовок'),
    'message': fields.String(description='Текст'),
    'notification_type': fields.String(description='Тип уведомления'),
    'is_read': fields.Boolean(description='Прочитано'),
    'created_at': fields.DateTime(description='Дата создания'),
    'related_entity_type': fields.String(description='Тип связанной сущности'),
    'related_entity_id': fields.Integer(description='ID связанной сущности')
})


# ==================== ENDPOINTS ====================

@notifications_ns.route('/')
class NotificationList(Resource):
    """Список уведомлений"""
    
    @notifications_ns.doc('list_notifications')
    @notifications_ns.response(200, 'Список уведомлений')
    @jwt_required()
    def get(self):
        """Получить список уведомлений текущего пользователя"""
        user_id = int(get_jwt_identity())
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        limit = request.args.get('limit', 50, type=int)
        
        notifications = NotificationApiService.get_user_notifications(
            user_id, unread_only, limit
        )
        
        return list_response(
            NotificationSchema(many=True).dump(notifications),
            meta={'total': len(notifications)}
        )


@notifications_ns.route('/unread-count')
class UnreadCount(Resource):
    """Количество непрочитанных"""
    
    @notifications_ns.doc('get_unread_count')
    @notifications_ns.response(200, 'Количество непрочитанных уведомлений')
    @jwt_required()
    def get(self):
        """Получить количество непрочитанных уведомлений"""
        user_id = int(get_jwt_identity())
        count = NotificationApiService.get_unread_count(user_id)
        return success_response({'unread_count': count})


@notifications_ns.route('/mark-all-read')
class MarkAllRead(Resource):
    """Отметить все как прочитанные"""
    
    @notifications_ns.doc('mark_all_read')
    @notifications_ns.response(200, 'Все уведомления отмечены как прочитанные')
    @jwt_required()
    def post(self):
        """Отметить все уведомления как прочитанные"""
        user_id = int(get_jwt_identity())
        NotificationApiService.mark_all_as_read(user_id)
        return success_response({'message': 'All notifications marked as read'})


@notifications_ns.route('/<int:id>')
@notifications_ns.param('id', 'ID уведомления')
class NotificationResource(Resource):
    """Детали уведомления"""
    
    @notifications_ns.doc('mark_as_read')
    @notifications_ns.response(200, 'Уведомление отмечено как прочитанное')
    @jwt_required()
    def patch(self, id):
        """Отметить уведомление как прочитанное"""
        user_id = int(get_jwt_identity())
        
        try:
            notification = NotificationApiService.mark_as_read(id, user_id)
        except ValueError as e:
            return error_response(str(e), 404)
        
        return success_response(NotificationSchema().dump(notification))
    
    @notifications_ns.doc('delete_notification')
    @notifications_ns.response(204, 'Уведомление удалено')
    @jwt_required()
    def delete(self, id):
        """Удалить уведомление"""
        user_id = int(get_jwt_identity())
        
        try:
            NotificationApiService.delete_notification(id, user_id)
        except ValueError as e:
            return error_response(str(e), 404)
        
        return no_content_response()