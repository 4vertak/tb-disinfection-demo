"""Бизнес-логика аутентификации."""

from datetime import datetime, timezone
from flask_jwt_extended import create_access_token, create_refresh_token
from app.domain.models.user.entities import User
from app.core.extensions import db


class AuthService:
    """Сервис аутентификации"""
    
    @staticmethod
    def authenticate(login: str, password: str):
        """
        Аутентификация пользователя.
        
        Args:
            login: Логин пользователя
            password: Пароль
        
        Returns:
            User or None: Пользователь если аутентификация успешна
        """
        user = User.query.filter_by(login=login).first()
        
        if not user:
            return None
        
        if not user.check_password(password):
            return None
        
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()
        
        return user
    
    @staticmethod
    def generate_tokens(user: User):
        """
        Генерация access и refresh токенов.
        
        Args:
            user: Пользователь
        
        Returns:
            dict: Словарь с токенами
        """

        additional_claims = {
            'user_type': user.user_type,
            'name': user.name,
            'login': user.login
        }
        
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )
        
        refresh_token = create_refresh_token(
            identity=str(user.id)
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer'
        }
    
    @staticmethod
    def register_user(data: dict):
        """
        Регистрация нового пользователя.
        
        Args:
            data: Данные пользователя
        
        Returns:
            User: Созданный пользователь
        """
        user = User(
            login=data['login'],
            name=data['name'],
            user_type=data['user_type']
        )
        
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return user
    
    @staticmethod
    def change_password(user: User, old_password: str, new_password: str):
        """
        Смена пароля пользователя.
        
        Args:
            user: Пользователь
            old_password: Старый пароль
            new_password: Новый пароль
        
        Returns:
            bool: True если пароль успешно изменён
        
        Raises:
            ValueError: Если старый пароль неверный
        """
        if not user.check_password(old_password):
            raise ValueError('Invalid old password')
        
        user.set_password(new_password)
        db.session.commit()
        
        return True