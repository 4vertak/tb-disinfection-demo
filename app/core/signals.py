from flask_login import user_logged_in, user_logged_out
from ..domain.models.audit.entities import UserAuditLog
from flask import request
from .extensions import db
import logging

logger = logging.getLogger(__name__)


def register_signals(app):
    @user_logged_in.connect_via(app)
    def on_user_logged_in(sender, user):
        try:
            log = UserAuditLog(
                user_id=user.id,
                action='login',
                details={'ip': request.remote_addr, 'user_agent': request.user_agent.string}
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to write login audit log: {e}")

    @user_logged_out.connect_via(app)
    def on_user_logged_out(sender, user):
        if user is None:
            return
        try:
            log = UserAuditLog(
                user_id=user.id,
                action='logout',
                details={'ip': request.remote_addr}
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to write logout audit log: {e}")
        