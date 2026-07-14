"""Бизнес-логика для уведомлений."""

from app.domain.models.notification.entities import Notification
from app.core.extensions import db
from sqlalchemy import desc


class NotificationApiService:
    """Сервис для работы с уведомлениями через API"""
    
    @staticmethod
    def get_user_notifications(user_id: int, unread_only: bool = False, limit: int = 50):
        """Получить уведомления пользователя"""
        query = Notification.query.filter_by(user_id=user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        return query.order_by(desc(Notification.created_at)).limit(limit).all()
    
    @staticmethod
    def get_unread_count(user_id: int):
        """Получить количество непрочитанных уведомлений"""
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()
    
    @staticmethod
    def mark_as_read(notification_id: int, user_id: int):
        """Отметить уведомление как прочитанное"""
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()
        
        if not notification:
            raise ValueError('Notification not found')
        
        notification.is_read = True
        db.session.commit()

        #вызов автоочистики 
        from app.domain.services.notification_service import NotificationService
        NotificationService.auto_cleanup_after_read(user_id, notification_id)
        
        return notification
    
    @staticmethod
    def mark_all_as_read(user_id: int):
        """Отметить все уведомления как прочитанные"""
        Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).update({'is_read': True})
        db.session.commit()
        return True
    
    @staticmethod
    def delete_notification(notification_id: int, user_id: int):
        """Удалить уведомление"""
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()
        
        if not notification:
            raise ValueError('Notification not found')
        
        db.session.delete(notification)
        db.session.commit()
        return True