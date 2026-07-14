from datetime import datetime, timezone
import json

from ....utils.date_utils import to_local

from ..audit.entities import ApplicationAuditLog
from ....utils.serializers import json_serializer
from sqlalchemy.orm import relationship
from sqlalchemy import event
from sqlalchemy.orm.session import Session
from ....core.extensions import db


class Area(db.Model):
    __tablename__ = 'area'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name_area = db.Column(db.String(50), unique=True, nullable=False)

    # Связь с врачами и заявками
    doctors = db.relationship('Doctor', back_populates='area', lazy=True)
    applications = db.relationship('Application', back_populates='area', lazy=True)

class Doctor(db.Model):
    __tablename__ = 'doctor'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(100), unique=True, nullable=False)
    
    # Связь с участком
    area_id = db.Column(db.Integer, db.ForeignKey('area.id'), nullable=False)
    area = db.relationship('Area', back_populates='doctors')

    # Связь с заявками
    applications = db.relationship("Application", back_populates="doctor")

class Disinfector(db.Model):
    __tablename__ = 'disinfector'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(255), unique=True, nullable=False)
    
    # Связь с дезинфекциями (многие-ко-многим)
    disinfections = db.relationship(
        'Disinfection', 
        secondary='disinfection_disinfector', 
        back_populates='disinfectors'
    )

# Таблица для связи многие-ко-многим между Disinfection и Disinfector
disinfection_disinfector = db.Table('disinfection_disinfector',
    db.Column('disinfection_id', db.Integer, db.ForeignKey('disinfection.id'), primary_key=True),
    db.Column('disinfector_id', db.Integer, db.ForeignKey('disinfector.id'), primary_key=True)
)


class Diagnosis(db.Model):
    __tablename__ = 'diagnosis'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    mkb_code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)

    applications = db.relationship('Application', backref='diagnosis', lazy=True)


class EpidemicFocus(db.Model):
    __tablename__ = 'epidemic_focus'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    applications = db.relationship('Application', backref='epidemic_focus', lazy=True)

class ApplicationCounter(db.Model):
    __tablename__ = 'application_counter'
    
    year = db.Column(db.Integer, primary_key=True)
    last_number = db.Column(db.Integer, default=0)


class Application(db.Model):
    __tablename__ = 'application'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    application_number = db.Column(db.Integer, nullable=True) 
    submission_date = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    patient_full_name = db.Column(db.String(255), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=True)
    relative_contact_phone = db.Column(db.String(100))
    workplace = db.Column(db.String(255))
    position = db.Column(db.String(100))
    registration_date = db.Column(db.Date)

    diagnosis_id = db.Column(db.Integer, db.ForeignKey('diagnosis.id'))
    gdu = db.Column(db.String(20))
    focus_id = db.Column(db.Integer, db.ForeignKey('epidemic_focus.id'))

    reason_application = db.Column(db.String(255), nullable=False, default='hospitalization')
    status = db.Column(db.String(20), default='incompleted', nullable=False)
    
    # ОСНОВНЫЕ ИЗМЕНЕНИЯ
    # связь с пользователем (кто подал заявку)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", back_populates="applications")
    
    # Врач (если есть в справочнике)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=True)
    doctor = db.relationship('Doctor', back_populates='applications')

    # Для нового врача (если его нет в справочнике)
    doctor_full_name = db.Column(db.String(255), nullable=True)

    # Участок (берется из справочника, не изменяется)
    area_id = db.Column(db.Integer, db.ForeignKey('area.id'), nullable=False)
    area = db.relationship('Area', back_populates='applications')

    hospitalization_date = db.Column(db.Date, nullable=True)
    place_of_hospitalization = db.Column(db.String(255), nullable=True)

    disinfection = relationship(
        'Disinfection', back_populates='application', cascade='all, delete-orphan'
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        new_disinfection = Disinfection(application=self)
        self.disinfection.append(new_disinfection)

    def to_dict(self):
        data = {
            'id': self.id,
            'application_number': self.application_number, 
            'submission_date': to_local(self.submission_date).strftime("%Y-%m-%d %H:%M:%S") if self.submission_date else None,
            'patient_full_name': self.patient_full_name,
            'birth_date': self.birth_date,
            'address': self.address,
            'contact_phone': self.contact_phone,
            'relative_contact_phone': self.relative_contact_phone,
            'workplace': self.workplace,
            'position': self.position,
            'registration_date': self.registration_date,
            'diagnosis_id': self.diagnosis_id,
            'gdu': self.gdu,
            'focus_id': self.focus_id,
            'reason_application': self.reason_application,
            'status': self.status,
            'user_id': self.user_id,
            'hospitalization_date': self.hospitalization_date,
            'place_of_hospitalization': self.place_of_hospitalization,
            'doctor_id': self.doctor_id,
            'doctor_full_name': self.doctor_full_name,
            'area_id': self.area_id
        }
        return json.loads(json.dumps(data, ensure_ascii=False, default=json_serializer))

class Disinfection(db.Model):
    __tablename__ = 'disinfection'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    rejection_reason = db.Column(db.String(255))
    disinfection_date = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    area_size = db.Column(db.Float)
    volume_size = db.Column(db.Float)
    spraying_time = db.Column(db.String(255))
    swab_testing = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)

    application = relationship('Application', back_populates='disinfection')
    
    # Связь со справочником дезинфекторов (многие-ко-многим)
    disinfectors = db.relationship(
        'Disinfector', 
        secondary=disinfection_disinfector, 
        back_populates='disinfections',
        lazy=True
    )



@event.listens_for(Application, 'after_insert')
def log_application_insert(mapper, connection, target):
    audit_log = ApplicationAuditLog(
        application_id=target.id,
        changed_by=target.user_id,
        change_type='INSERT',
        new_data=target.to_dict()
    )
    
    session = Session(bind=connection)
    session.add(audit_log)
    session.flush()
    
    
@event.listens_for(Application, 'after_update')
def log_application_update(mapper, connection, target):
    previous_state = {}
    for key, value in db.inspect(target).attrs.items():
        if key != 'id' and key != 'user_id':
            previous_state[key] = value.history.unchanged[0] if value.history.unchanged else None
    
    audit_log = ApplicationAuditLog(
        application_id=target.id, 
        change_type='UPDATE', 
        old_data=json.loads(json.dumps(previous_state, default=json_serializer)),
        new_data=target.to_dict()
    )
    
    if target.user_id:
        audit_log.changed_by = target.user_id 
    else:  
        audit_log.changed_by = 104
        
    session = Session(bind=connection)
    session.add(audit_log)
    session.flush()