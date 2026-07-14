"""
Бизнес-логика управления пользователями.
"""
from sqlalchemy import or_
from app.domain.models.user.entities import User
from app.core.extensions import db


class UserService:
    """Сервис управления пользователями"""
    
    @staticmethod
    def get_all_users(filters=None):
        """
        Получить список всех пользователей с фильтрацией.
        
        Args:
            filters: Словарь с фильтрами (user_type, area_id, search)
        
        Returns:
            Query: SQLAlchemy query объект
        """
        query = User.query
        
        if filters:
            # Фильтрация по типу пользователя
            if 'user_type' in filters and filters['user_type']:
                query = query.filter(User.user_type == filters['user_type'])
            
            # Фильтрация по участку
            if 'area_id' in filters and filters['area_id']:
                query = query.filter(User.area_id == filters['area_id'])
            
            # Поиск по логину или имени
            if 'search' in filters and filters['search']:
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        User.login.ilike(search_term),
                        User.name.ilike(search_term)
                    )
                )
        
        return query
    
    @staticmethod
    def get_user_by_id(user_id: int):
        """
        Получить пользователя по ID.
        
        Args:
            user_id: ID пользователя
        
        Returns:
            User or None: Пользователь или None
        """
        return db.session.get(User, user_id)
    
    @staticmethod
    def get_user_by_login(login: str):
        """
        Получить пользователя по логину.
        
        Args:
            login: Логин пользователя
        
        Returns:
            User or None: Пользователь или None
        """
        return User.query.filter_by(login=login).first()
    
    @staticmethod
    def create_user(data: dict):
        """
        Создать нового пользователя.
        
        Args:
            data: Данные пользователя
        
        Returns:
            User: Созданный пользователь
        """
        user = User(
            login=data['login'],
            name=data['name'],
            user_type=data['user_type'],
        )
        
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return user
    
    @staticmethod
    def update_user(user_id: int, data: dict):
        """
        Обновить данные пользователя.
        
        Args:
            user_id: ID пользователя
            data: Данные для обновления
        
        Returns:
            User: Обновлённый пользователь
        
        Raises:
            ValueError: Если пользователь не найден
        """
        user = db.session.get(User, user_id)
        
        if not user:
            raise ValueError('User not found')
        
        # Обновление полей
        if 'name' in data:
            user.name = data['name']
        
        if 'user_type' in data:
            user.user_type = data['user_type']
        
        if 'password' in data:
            user.set_password(data['password'])
        
        db.session.commit()
        
        return user
    
    @staticmethod
    def delete_user(user_id: int):
        """
        Удалить пользователя.
        
        Args:
            user_id: ID пользователя
        
        Returns:
            bool: True если пользователь удалён
        
        Raises:
            ValueError: Если пользователь не найден
        """
        user = db.session.get(User, user_id)
        
        if not user:
            raise ValueError('User not found')
        
        db.session.delete(user)
        db.session.commit()
        
        return True
    
    @staticmethod
    def get_users_by_area(area_id: int):
        """
        Получить пользователей по участку.
        
        Args:
            area_id: ID участка
        
        Returns:
            list: Список пользователей
        """
        return User.query.filter_by(area_id=area_id).all()
    
    @staticmethod
    def get_doctors():
        """
        Получить список всех врачей.
        
        Returns:
            Query: SQLAlchemy query объект
        """
        return User.query.filter_by(user_type='doctor')
    
    @staticmethod
    def get_disinfectors():
        """
        Получить список всех дезинфекторов.
        
        Returns:
            Query: SQLAlchemy query объект
        """
        return User.query.filter_by(user_type='disinfector')