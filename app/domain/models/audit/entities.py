
from datetime import datetime, timezone
from ....core.extensions import db

class ApplicationAuditLog(db.Model):
    __tablename__ = 'application_audit_log'
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, nullable=False)
    changed_by = db.Column(db.Integer, nullable=False)
    change_time = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    change_type = db.Column(db.String(10), nullable=False)
    old_data = db.Column(db.JSON)
    new_data = db.Column(db.JSON)

    __table_args__ = (
        db.Index('idx_application_id', 'application_id'),
        db.Index('idx_change_time', 'change_time'),
    )


class UserAuditLog(db.Model):
    __tablename__ = 'user_audit_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(50), nullable=False)
    action_time = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    details = db.Column(db.JSON)  
    