"""Marshmallow схемы для логов аудита."""
from marshmallow import Schema, fields
from ..applications.schemas_references import UserReferenceSchema


class ApplicationAuditLogSchema(Schema):
    """Схема для лога изменений заявки"""
    id = fields.Integer(dump_only=True)
    application_id = fields.Integer()
    changed_by = fields.Integer()
    change_time = fields.DateTime(metadata={'description': 'Время изменения (UTC)'})
    change_type = fields.String(metadata={'description': 'Тип изменения (INSERT, UPDATE, DELETE)'})
    old_data = fields.Raw(metadata={'description': 'Предыдущие данные (JSON)'})
    new_data = fields.Raw(metadata={'description': 'Новые данные (JSON)'})
    
    # Подтягиваем информацию о том, кто изменил
    changed_by_user = fields.Nested(
        UserReferenceSchema, 
        dump_only=True, 
        only=('id', 'name', 'login'),
        metadata={'description': 'Пользователь, внесший изменения'}
    )


class UserAuditLogSchema(Schema):
    """Схема для лога действий пользователя"""
    id = fields.Integer(dump_only=True)
    user_id = fields.Integer()
    action = fields.String(metadata={'description': 'Действие (login, logout, change_password, delete_user)'})
    action_time = fields.DateTime(metadata={'description': 'Время действия (UTC)'})
    details = fields.Raw(metadata={'description': 'Детали действия (JSON)'})