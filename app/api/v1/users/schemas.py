"""
Marshmallow схемы для валидации данных пользователей.
"""
from marshmallow import Schema, fields, validate, validates, ValidationError
from app.core.extensions import db
from ..applications.schemas_references import AreaSchema


class UserSchema(Schema):
    """Схема для сериализации пользователя"""
    id = fields.Integer(dump_only=True)
    login = fields.String()
    name = fields.String()
    user_type = fields.String()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    last_login = fields.DateTime(dump_only=True)


class UserCreateSchema(Schema):
    """Схема для создания пользователя"""
    login = fields.String(
        required=True,
        validate=validate.Length(min=3, max=150, error='Login must be between 3 and 150 characters')
    )
    password = fields.String(
        required=True,
        load_only=True,
        validate=validate.Length(min=6, error='Password must be at least 6 characters')
    )
    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100, error='Name must be between 1 and 100 characters')
    )
    user_type = fields.String(
        required=True,
        validate=validate.OneOf(['doctor', 'admin', 'disinfector'], 
                               error='User type must be one of: doctor, admin, disinfector')
    )
    
    @validates('login')
    def validate_login_unique(self, value):
        """Проверка уникальности логина"""
        from app.domain.models.user.entities import User
        if User.query.filter_by(login=value).first():
            raise ValidationError('Login already exists')


class UserUpdateSchema(Schema):
    """Схема для обновления пользователя"""
    name = fields.String(
        validate=validate.Length(min=1, max=100)
    )
    user_type = fields.String(
        validate=validate.OneOf(['doctor', 'admin', 'disinfector'])
    )
    password = fields.String(
        load_only=True,
        validate=validate.Length(min=6)
    )


class UserFilterSchema(Schema):
    """Схема для фильтрации пользователей"""
    user_type = fields.String(validate=validate.OneOf(['doctor', 'admin', 'disinfector']))
    area_id = fields.Integer()
    search = fields.String()


