"""Бизнес-логика управления заявками и дезинфекцией"""

from datetime import datetime, timezone
import logging
from sqlalchemy import or_
from app.domain.models.application.entities import Application, Disinfection
from app.core.extensions import db, socketio

logger = logging.getLogger(__name__)

class ApplicationService:
    """Сервис управления заявками"""
    
    @staticmethod
    def get_all_applications(filters=None):
        """Получить список всех заявок с фильтрацией"""
        query = Application.query
        
        if filters:
            if 'status' in filters and filters['status']:
                query = query.filter(Application.status == filters['status'])
            if 'doctor_id' in filters and filters['doctor_id']:
                query = query.filter(Application.user_id == filters['doctor_id'])
            if 'area_id' in filters and filters['area_id']:
                query = query.filter(Application.area_id == filters['area_id'])
            if 'focus_id' in filters and filters['focus_id']:
                query = query.filter(Application.focus_id == filters['focus_id'])
            if 'diagnosis_id' in filters and filters['diagnosis_id']:
                query = query.filter(Application.diagnosis_id == filters['diagnosis_id'])
            
            # Фильтрация по дате подачи (submission_date)
            if 'date_from' in filters and filters['date_from']:
                query = query.filter(Application.submission_date >= filters['date_from'])
            if 'date_to' in filters and filters['date_to']:
                query = query.filter(Application.submission_date <= filters['date_to'])
            
            # Поиск по ФИО или адресу
            if 'search' in filters and filters['search']:
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        Application.patient_full_name.ilike(search_term),
                        Application.address.ilike(search_term),
                        Application.contact_phone.ilike(search_term)
                    )
                )
        
        return query.order_by(Application.submission_date.desc())
    
    @staticmethod
    def get_application_by_id(application_id: int):
        """Получить заявку по ID"""
        return db.session.get(Application, application_id)
    
    @staticmethod
    def create_application(data: dict, user_id: int):
        """
        Создать новую заявку.
        
        Legacy-логика:
        - Disinfection создается автоматически в Application.__init__
        - Генерируется application_number через ApplicationNumberService
        - Отправляются уведомления дезинфекторам
        """
        application = Application(
            user_id=user_id,
            submission_date=datetime.now(timezone.utc),
            patient_full_name=data['patient_full_name'],
            birth_date=data['birth_date'],
            address=data['address'],
            contact_phone=data.get('contact_phone'),
            relative_contact_phone=data.get('relative_contact_phone'),
            workplace=data.get('workplace'),
            position=data.get('position'),
            registration_date=data.get('registration_date'),
            diagnosis_id=data['diagnosis_id'],
            gdu=data.get('gdu'),
            focus_id=data['focus_id'],
            area_id=data['area_id'],
            reason_application=data.get('reason_application', 'hospitalization'),
            doctor_id=data.get('doctor_id'),
            doctor_full_name=data.get('doctor_full_name'),
            hospitalization_date=data.get('hospitalization_date'),
            place_of_hospitalization=data.get('place_of_hospitalization'),
            status='incompleted'
        )

        if data.get('doctor_full_name') and not data.get('doctor_id'):
            from app.domain.services.application_service import ApplicationService as LegacyAppService
            doctor_obj = LegacyAppService._get_or_create_doctor(
                data['doctor_full_name'].strip(),
                data.get('area_id')
            )
            if doctor_obj:
                application.doctor_id = doctor_obj.id
        
        db.session.add(application)
        db.session.commit()
        
        # Генерация номера заявки
        try:
            from app.domain.services.application_number_service import ApplicationNumberService
            application.application_number = ApplicationNumberService.get_next_application_number()
            db.session.commit()
        except Exception as e:
            # Если сервис не доступен, продолжаем без номера
            logger.warning(f"Failed to generate application number: {e}")
        
        # Уведомление дезинфекторов
        try:
            from app.domain.services.notification_service import NotificationService
            NotificationService.notify_new_application(application)
        except Exception as e:
            # Если уведомления не работают, продолжаем
            logger.warning(f"Failed to send notifications: {e}")
        
        socketio.emit('application_created', {
            'application_id': application.id,
            'application_number': application.application_number,
            'patient_full_name': application.patient_full_name
        })
        
        return application
    
    @staticmethod
    def update_application(application_id: int, data: dict):
        """Обновить заявку"""
        application = db.session.get(Application, application_id)
        if not application:
            raise ValueError('Application not found')
        
        old_status = application.status
        
        for field, value in data.items():
            if hasattr(application, field):
                setattr(application, field, value)
        
        db.session.commit()
        
        socketio.emit('application_updated', {
            'application_id': application.id,
            'status': application.status,
            'old_status': old_status
        })
        
        return application
    
    @staticmethod
    def delete_application(application_id: int):
        """Удалить заявку (cascade удалит Disinfection)"""
        application = db.session.get(Application, application_id)
        if not application:
            raise ValueError('Application not found')
        
        db.session.delete(application)
        db.session.commit()
        
        socketio.emit('application_deleted', {'application_id': application_id})
        
        return True
    
    @staticmethod
    def get_applications_by_doctor(doctor_id: int, filters=None):
        """Получить заявки врача (фильтр по user_id)"""
        query = Application.query.filter_by(user_id=doctor_id)
        if filters and 'status' in filters and filters['status']:
            query = query.filter(Application.status == filters['status'])
        return query.order_by(Application.submission_date.desc())


class DisinfectionService:
    """Сервис управления данными дезинфекции"""
    
    @staticmethod
    def get_disinfection_data(application_id: int):
        """Получить данные дезинфекции для заявки"""
        application = db.session.get(Application, application_id)
        if not application or not application.disinfection:
            return None
        
        # Возвращаем первый (и единственный) Disinfection
        return application.disinfection[0]
    
    @staticmethod
    def create_or_update_disinfection_data(application_id: int, data: dict, user_id: int):
        """
        Обновить данные дезинфекции.
        
        Логика:
        - Disinfection уже создан автоматически в Application.__init__
        - При заполнении данных заявка автоматически завершается
        - M2M связь с дезинфекторами
        """
        application = db.session.get(Application, application_id)
        if not application:
            raise ValueError('Application not found')
        
        if not application.disinfection:
            raise ValueError('Disinfection data not found')
        
        disinfection = application.disinfection[0]
        
        # Заполняем поля модели Disinfection
        for field, value in data.items():
            if field != 'disinfector_ids' and hasattr(disinfection, field):
                setattr(disinfection, field, value)
        
        # Устанавливаем user_id (кто заполнил данные)
        disinfection.user_id = user_id
        
        # Обработка M2M связи с дезинфекторами
        if 'disinfector_ids' in data and data['disinfector_ids']:
            from app.domain.models.application.entities import Disinfector
            disinfectors = []
            for disinfector_id in data['disinfector_ids']:
                disinfector = db.session.get(Disinfector, disinfector_id)
                if disinfector:
                    disinfectors.append(disinfector)
            disinfection.disinfectors = disinfectors
        
        # При заполнении данных дезинфекции заявка автоматически завершается
        rejection_reason = data.get('rejection_reason')
        if rejection_reason and rejection_reason != 'completed':
            disinfection.rejection_reason = rejection_reason
            application.status = 'refusal'
        else:
            disinfection.rejection_reason = 'completed'
            application.status = 'completed'
        
        db.session.commit()
        
        socketio.emit('disinfection_completed', {
            'application_id': application_id,
            'disinfection_id': disinfection.id
        })
        
        return disinfection