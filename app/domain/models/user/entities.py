from datetime import datetime, timezone

from ....core.extensions import db, login_manager
from ..notification.entities import Notification
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(100), unique=False, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.String(50), nullable=False)  # doctor, admin, disinfector
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime(timezone=True), nullable=True)


    applications = db.relationship("Application", back_populates="user")
    
    def get_unread_notifications_count(self):
        return Notification.query.filter_by(user_id=self.id, is_read=False).count()

    def get_recent_notifications(self, limit=10):
        return Notification.query.filter_by(user_id=self.id)\
            .order_by(Notification.created_at.desc())\
            .limit(limit).all()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)





