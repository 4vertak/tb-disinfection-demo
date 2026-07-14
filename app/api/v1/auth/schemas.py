"""
Marshmallow схемы для валидации данных аутентификации.
"""
from marshmallow import Schema, fields, validate, validates, ValidationError


class LoginSchema(Schema):
    """Схема для входа в систему"""
    login = fields.String(
        required=True,
        validate=validate.Length(min=3, max=150, error='Login must be between 3 and 150 characters')
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=6, error='Password must be at least 6 characters')
    )


class RegisterSchema(Schema):
    """Схема для регистрации нового пользователя"""
    login = fields.String(
        required=True,
        validate=validate.Length(min=3, max=150)
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=6)
    )
    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100)
    )
    user_type = fields.String(
        required=True,
        validate=validate.OneOf(['doctor', 'admin', 'disinfector'])
    )
    
    @validates('login')
    def validate_login_unique(self, value):
        """Проверка уникальности логина"""
        from app.domain.models.user.entities import User
        if User.query.filter_by(login=value).first():
            raise ValidationError('Login already exists')


class TokenSchema(Schema):
    """Схема для JWT токенов"""
    access_token = fields.String()
    refresh_token = fields.String()
    token_type = fields.String(dump_default='Bearer')


class RefreshTokenSchema(Schema):
    """Схема для обновления токена"""
    refresh_token = fields.String(required=True)


class ChangePasswordSchema(Schema):
    """Схема для смены пароля"""
    old_password = fields.String(required=True)
    new_password = fields.String(
        required=True,
        validate=validate.Length(min=6)
    )