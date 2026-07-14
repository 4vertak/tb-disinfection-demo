import logging

from datetime import datetime, timedelta, timezone
from flask_socketio import emit, join_room
from flask import request
from ...core.extensions import socketio, db
from ..models.notification.entities import Notification
from ..models.user.entities import User

logger = logging.getLogger(__name__)

class NotificationService:

    @staticmethod
    def create_notification(user_id, title, message, notification_type,
                          related_entity_type=None, related_entity_id=None):
        """Создание и сохранение уведомления в БД"""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id
        )
        db.session.add(notification)
        db.session.commit()

        # Отправка через WebSocket
        NotificationService._send_ws_notification(user_id, notification)
        return notification

    @staticmethod
    def _send_ws_notification(user_id, notification):
        """Отправка уведомления через WebSocket"""
        try:
            notification_data = {
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.notification_type,
                'created_at': notification.created_at.isoformat(),
                'is_read': notification.is_read,
                'related_entity_type': notification.related_entity_type,
                'related_entity_id': notification.related_entity_id
            }

            # Отправляем пользователю
            socketio.emit('new_notification', notification_data, room=f"user_{user_id}")
            logger.debug("Notification sent to user_%s", user_id)

            # Дублируем в общую комнату для отладки
            #socketio.emit('new_notification', notification_data, room="notifications_all")

        except Exception as e:
            logger.error("Error sending WS notification: %s", str(e))

    @staticmethod
    def setup_socket_handlers():
        """Настройка обработчиков SocketIO"""

        @socketio.on('connect')
        def handle_connect():
            logger.debug("WebSocket Client connected: %s", request.sid)
            # Присоединяем к общей комнате для отладки
            # join_room("notifications_all")
            # emit('connected', {'message': 'Successfully connected to notification system', 'sid': request.sid})

        @socketio.on('disconnect')
        def handle_disconnect():
            logger.debug("WebSocket Client disconnected: %s", request.sid)

        @socketio.on('identify')
        def handle_identify(data):
            user_type = data.get('user_type')
            user_id = data.get('user_id')
            if user_id:
                # Присоединяем к персональной комнате
                room_name = f"user_{user_id}"
                join_room(room_name)
                logger.debug("User %s (%s) joined room: %s, SID: %s", user_id, user_type, room_name, request.sid)
                emit('identified', {
                    'room': room_name,
                    'user_type': user_type,
                    'message': f'Successfully joined {room_name}'
                })

        # Обработчик для автоматической очистки при прочтении
        @socketio.on('notification_read')
        def handle_notification_read(data):
            user_id = data.get('user_id')
            notification_id = data.get('notification_id')

            if user_id and notification_id:
                # Помечаем как прочитанное и сразу удаляем
                notification = Notification.query.filter_by(
                    id=notification_id,
                    user_id=user_id
                ).first()

                if notification:
                    notification.is_read = True
                    db.session.commit()

                    # Автоматически удаляем после прочтения
                    NotificationService.auto_cleanup_after_read(user_id, notification_id)

                    emit('notification_cleaned', {
                        'notification_id': notification_id,
                        'message': 'Notification read and cleaned'
                    }, room=f"user_{user_id}")

    @staticmethod
    def notify_new_application(application):
        """Уведомление дезинфекторов о новой заявке"""
        disinfectors = User.query.filter_by(user_type='disinfector').all()

        for disinfector in disinfectors:
            NotificationService.create_notification(
                user_id=disinfector.id,
                title='Новая заявка',
                message=f'Поступила новая заявка №{application.application_number}',
                notification_type='new_application',
                related_entity_type='application',
                related_entity_id=application.id
            )

    @staticmethod
    def notify_application_updated(application, updater):
        """Уведомление врача об обновлении статуса заявки"""

         # Проверяем, что статус изменился на завершенный или отказ
        if application.status in ['completed', 'refusal']:
            # Уведомляем только создателя заявки (user_id заявки)
            if application.user_id != updater.id:  # Не уведомляем самого себя, если это тот же пользователь
                status={"completed":"выполнен","refusal":"отказ"}.get(application.status,"в работе")
                NotificationService.create_notification(
                    user_id=application.user_id,
                    title='Статус заявки изменен',
                    message=f'Статус вашей заявки №{application.application_number} изменен на "{status}"',
                    notification_type='status_update',
                    related_entity_type='application',
                    related_entity_id=application.id
                )
    @staticmethod
    def cleanup_read_notifications(days_old=30):
        """Автоматическое удаление прочитанных уведомлений старше указанного количества дней"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)

            deleted_count = Notification.query.filter(
                Notification.is_read == True,
                Notification.created_at < cutoff_date
            ).delete()

            db.session.commit()
            logger.info("Удалено %d прочитанных уведомлений старше %d дней", deleted_count, days_old)
            return deleted_count

        except Exception as e:
            db.session.rollback()
            logger.error("Ошибка при очистке уведомлений: %s", str(e))
            return 0

    @staticmethod
    def auto_cleanup_after_read(user_id, notification_id=None):
        """
        Автоматическая очистка уведомлений после прочтения
        - Удаляет конкретное уведомление при прочтении ИЛИ очищает старые прочитанные уведомления при массовом прочтении
        """
        try:
            if notification_id:
                # Удаляем конкретное прочитанное уведомление
                notification = Notification.query.filter_by(
                    id=notification_id,
                    user_id=user_id,
                    is_read=True
                ).first()

                if notification:
                    db.session.delete(notification)
                    db.session.commit()
                    logger.debug("Удалено прочитанное уведомление %s", notification_id)
            else:
                # При массовом прочтении удаляем все прочитанные уведомления пользователя
                # или только старые (например, старше 7 дней)
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)

                deleted_count = Notification.query.filter(
                    Notification.user_id == user_id,
                    Notification.is_read == True,
                    Notification.created_at < cutoff_date
                ).delete()

                db.session.commit()
                logger.debug("Удалено %d старых прочитанных уведомлений пользователя %s", deleted_count, user_id)

        except Exception as e:
            db.session.rollback()
            logger.error("Ошибка при автоматической очистке уведомлений: %s", str(e))
