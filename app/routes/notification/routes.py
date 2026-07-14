
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from ...domain.models.notification.entities import Notification
from ...domain.services.notification_service import NotificationService
from ...core.extensions import db

notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/api/notifications')
@login_required
def get_notifications():
    limit = request.args.get('limit', 10, type=int)
    offset = request.args.get('offset', 0, type=int)
    unread_only = request.args.get('unread_only', False, type=bool)
    
    query = Notification.query.filter_by(user_id=current_user.id)
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    notifications = query.order_by(
        Notification.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    unread_count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    
    return jsonify({
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.notification_type,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat(),
            'related_entity_type': n.related_entity_type,
            'related_entity_id': n.related_entity_id
        } for n in notifications],
        'unread_count': unread_count
    })

@notification_bp.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first_or_404()
    
    notification.is_read = True
    db.session.commit()
    
    # Автоматически удаляем прочитанное уведомление
    NotificationService.auto_cleanup_after_read(current_user.id, notification_id)
    
    return jsonify({'success': True})

@notification_bp.route('/api/notifications/read-all', methods=['POST'])
@login_required
def mark_all_read():
    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    
    db.session.commit()
    
    # Автоматически очищаем старые прочитанные уведомления
    NotificationService.auto_cleanup_after_read(current_user.id)
    
    return jsonify({'success': True})

@notification_bp.route('/api/notifications/unread-count')
@login_required
def get_unread_count():
    count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    
    return jsonify({'unread_count': count})

@notification_bp.route('/api/notifications/<int:notification_id>')
@login_required
def get_notification(notification_id):
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first_or_404()
    
    return jsonify({
        'id': notification.id,
        'title': notification.title,
        'message': notification.message,
        'type': notification.notification_type,
        'is_read': notification.is_read,
        'created_at': notification.created_at.isoformat(),
        'related_entity_type': notification.related_entity_type,
        'related_entity_id': notification.related_entity_id
    })
    


@notification_bp.route('/api/notifications/cleanup', methods=['POST'])
@login_required
def cleanup_notifications():
    """Ручная очистка прочитанных уведомлений"""
    try:
        # Удаляем все прочитанные уведомления пользователя
        deleted_count = Notification.query.filter_by(
            user_id=current_user.id,
            is_read=True
        ).delete()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Удалено {deleted_count} прочитанных уведомлений'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Ошибка при очистке уведомлений: {str(e)}'
        }), 500