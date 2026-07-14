# app/api/v1/notifications/schemas.py
"""Marshmallow схемы для уведомлений."""
from marshmallow import Schema, fields, validate


class NotificationSchema(Schema):
    """Схема для сериализации уведомления"""
    id = fields.Integer(dump_only=True)
    user_id = fields.Integer(dump_only=True)
    title = fields.String(metadata={'description': 'Заголовок уведомления'})
    message = fields.String(metadata={'description': 'Текст уведомления'})
    notification_type = fields.String(
        metadata={'description': 'Тип уведомления'},
        validate=validate.OneOf(['new_application', 'status_update', 'info', 'warning', 'error'])
    )
    is_read = fields.Boolean(metadata={'description': 'Прочитано ли уведомление'})
    created_at = fields.DateTime(dump_only=True, metadata={'description': 'Дата создания'})
    related_entity_type = fields.String(metadata={'description': 'Тип связанной сущности'}, allow_none=True)
    related_entity_id = fields.Integer(metadata={'description': 'ID связанной сущности'}, allow_none=True)


class NotificationUpdateSchema(Schema):
    """Схема для обновления уведомления"""
    is_read = fields.Boolean()