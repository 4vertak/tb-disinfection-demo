"""Бизнес-логика для логов аудита."""

from app.domain.models.audit.entities import ApplicationAuditLog, UserAuditLog
from app.domain.models.user.entities import User
from app.core.extensions import db


class AuditService:
    """Сервис для работы с логами аудита"""
    
    @staticmethod
    def get_application_history(application_id: int):
        """Получить историю изменений конкретной заявки"""
        logs = ApplicationAuditLog.query.filter_by(application_id=application_id).order_by(ApplicationAuditLog.change_time.desc()).all()
        
        # Добовляем в логи информацию о пользователях
        result = []
        for log in logs:
            log_dict = {
                'id': log.id,
                'application_id': log.application_id,
                'changed_by': log.changed_by,
                'change_time': log.change_time,
                'change_type': log.change_type,
                'old_data': log.old_data,
                'new_data': log.new_data,
                'changed_by_user': None
            }
            
            if log.changed_by:
                user = db.session.get(User, log.changed_by)
                if user:
                    log_dict['changed_by_user'] = {
                        'id': user.id,
                        'name': user.name,
                        'login': user.login
                    }
            result.append(log_dict)
            
        return result

    @staticmethod
    def get_user_history(user_id: int):
        """Получить историю действий конкретного пользователя"""
        return UserAuditLog.query.filter_by(user_id=user_id).order_by(UserAuditLog.action_time.desc()).all()