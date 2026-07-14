from datetime import datetime, timezone
import io
from typing import Optional
from ...domain.services.notification_service import NotificationService
from sqlalchemy import desc
import logging
from docxtpl import DocxTemplate
from ...core.extensions import db
from ...utils.date_utils import to_local
from ..models.application.entities import Application, Diagnosis, Disinfection, EpidemicFocus, Area, Doctor
from ..models.user.entities import User
from .application_number_service import ApplicationNumberService

logger = logging.getLogger(__name__)




class ApplicationService:

    @staticmethod
    def _get_or_create_doctor(doctor_full_name: str, area_id: Optional[int] = None) -> Doctor:
        """
        Находит врача в справочнике или создаёт нового.
        """
        if not doctor_full_name or not area_id:
            return None  # type: ignore

        # Ищем врача с таким ФИО и участком
        doctor = Doctor.query.filter_by(full_name=doctor_full_name.strip()).first()
        if doctor:
            if doctor.area_id != area_id:
                doctor.area_id = area_id
                db.session.add(doctor)
                db.session.flush()
            return doctor

        # Создаём нового врача
        doctor = Doctor(full_name=doctor_full_name.strip(), area_id=area_id)
        db.session.add(doctor)
        db.session.flush()
        return doctor

    @staticmethod
    def search_doctors(query: str, limit: int = 10):
        """Поиск врачей по ФИО"""
        if not query or len(query.strip()) < 2:
            return []

        search_term = f"%{query.strip()}%"
        doctors = Doctor.query.filter(
            Doctor.full_name.ilike(search_term)
        ).options(db.joinedload(Doctor.area)).limit(limit).all()

        return [{
            'value': doctor.full_name,
            'area_id': doctor.area_id,
            'area_name': doctor.area.name_area if doctor.area else None
        } for doctor in doctors]

    @staticmethod
    def get_applications(user_id):
        """Запрос списка заявок"""
        query = (
            db.session.query(Application, Disinfection, Area, Doctor)
            .outerjoin(Disinfection, Disinfection.application_id == Application.id)
            .outerjoin(Doctor, Doctor.id == Application.doctor_id)
            .outerjoin(Area, Area.id == Application.area_id)
        )

        applications = query.order_by(
            desc(Application.submission_date)
        ).all()

        return applications

    @staticmethod
    def create_application(form_data, user: User, doctor_obj: Optional[Doctor] = None):
        """Создание новой заявки"""
        try:
            # Получаем следующий номер заявки
            application_number = ApplicationNumberService.get_next_application_number()
            gdu_full = f"{form_data.gdu.data}-{form_data.mbt.data}" if form_data.mbt.data else form_data.gdu.data

            # Получаем или создаем врача
            doctor_obj = ApplicationService._get_or_create_doctor(
                form_data.doctor_name.data.strip(),
                form_data.area_id.data
            )

            application = Application(
                application_number=application_number,  # Устанавливаем порядковый номер
                submission_date=datetime.now(timezone.utc),
                patient_full_name=form_data.patient_full_name.data,
                birth_date=form_data.birth_date.data,
                address=form_data.address.data,
                contact_phone=form_data.contact_phone.data,
                relative_contact_phone=form_data.relative_contact_phone.data,
                workplace=form_data.workplace.data,
                position=form_data.position.data,
                diagnosis_id=form_data.diagnosis_id.data,
                gdu=gdu_full,
                registration_date=form_data.registration_date.data,
                focus_id=form_data.focus_id.data,
                user_id=user.id,
                reason_application=form_data.reason_application.data,
                status="incompleted",
                doctor_id=doctor_obj.id if doctor_obj else None,
                area_id=form_data.area_id.data,
            )

            if form_data.reason_application.data == "hospitalization":
                application.hospitalization_date = form_data.hospitalization_date.data
                application.place_of_hospitalization = form_data.place_of_hospitalization.data

            db.session.add(application)
            db.session.commit()
            # Отправка уведомления дезинфекторам
            NotificationService.notify_new_application(application)
            return application

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating application: {str(e)}")
            raise


    @staticmethod
    def update_application(application_id, form_data, user: User, doctor_obj: Optional[Doctor] = None):
        """Обновление заявки"""
        try:
            application = db.session.get(Application, application_id)

            if not application:
                raise ValueError("Application not found")

            if user.user_type == "doctor" and application.user_id != user.id:
                raise PermissionError("No rights to edit this application")

            # Получаем или создаем врача
            doctor_obj = ApplicationService._get_or_create_doctor(
                form_data.doctor_name.data.strip(),
                form_data.area_id.data
            )

            gdu_full = f"{form_data.gdu.data}-{form_data.mbt.data}" if form_data.mbt.data else form_data.gdu.data

            application.patient_full_name = form_data.patient_full_name.data
            application.birth_date = form_data.birth_date.data
            application.address = form_data.address.data
            application.contact_phone = form_data.contact_phone.data
            application.relative_contact_phone = form_data.relative_contact_phone.data
            application.workplace = form_data.workplace.data
            application.position = form_data.position.data
            application.diagnosis_id = form_data.diagnosis_id.data
            application.gdu = gdu_full
            application.registration_date = form_data.registration_date.data
            application.focus_id = form_data.focus_id.data
            application.user_id = user.id
            application.reason_application = form_data.reason_application.data
            application.doctor_id = doctor_obj.id if doctor_obj else None
            application.area_id = form_data.area_id.data

            if form_data.reason_application.data == "hospitalization":
                application.hospitalization_date = form_data.hospitalization_date.data
                application.place_of_hospitalization = form_data.place_of_hospitalization.data
            else:
                application.hospitalization_date = None
                application.place_of_hospitalization = None

            db.session.commit()
            return application
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating application {application_id}: {str(e)}")
            raise

    @staticmethod
    def delete_application(application_id, current_user):
        """Удалить заявку"""
        application = db.session.get(Application, application_id)
        if not application:
            raise ValueError("Заявка не найдена")

        if current_user.user_type != "admin":
            raise PermissionError("Нет прав на удаление этой заявки")

        db.session.delete(application)
        db.session.commit()


    @staticmethod
    def generate_application_doc(application_id):
        """Генерация документа заявки"""
        application = db.session.get(Application, application_id)
        if not application:
            raise ValueError("Application not found")

        display_id = application.application_number or application.id

        # Получаем эпидемический очаг и диагноз
        epid_focus = db.session.get(EpidemicFocus, application.focus_id)
        diagnosis = db.session.get(Diagnosis, application.diagnosis_id)

        # Получаем врача, если выбран из справочника
        doctor = Doctor.query.get(application.doctor_id) if application.doctor_id else None

        doctor_name = doctor.full_name if doctor else application.doctor_full_name or "-"

        # Название участка
        if doctor:
            # Через связь с Area, если она есть
            if hasattr(doctor, "area") and doctor.area:
                doctor_area = doctor.area.name_area
            else:
                # fallback по area_id
                area = Area.query.get(doctor.area_id)
                doctor_area = area.name_area if area else "-"
        else:
            doctor_area = "-"

        # Шаблон документа
        template_path = "app/templates_docs/application_template.docx"
        doc = DocxTemplate(template_path)

        context = {
            "focus_id": epid_focus.name if epid_focus else "-",
            "name_area": doctor_area,
            "id": str(display_id),  # Используем номер заявки
            "current_date": to_local(datetime.now(timezone.utc)).strftime("%d.%m.%Y"),
            "patient_full_name": application.patient_full_name,
            "birth_date": application.birth_date.strftime("%d.%m.%Y") if application.birth_date else "-",
            "address": application.address,
            "contact_phone": str(application.contact_phone or "-"),
            "relative_contact_phone": str(application.relative_contact_phone or "-"),
            "workplace": application.workplace or "-",
            "position": application.position or "-",
            "diagnosis_id": diagnosis.name if diagnosis else "-",
            "gdu_id": str(application.gdu or "-"),
            "registration_date": application.registration_date.strftime("%d.%m.%Y") if application.registration_date else "-",
            "doctor_name": doctor_name,
            "reason_application": (
                f"{application.hospitalization_date.strftime('%d.%m.%Y')} {application.place_of_hospitalization}"
                if application.reason_application == "hospitalization" and application.hospitalization_date
                else "планово" if application.reason_application == "sheduled" else "посмертно"
            ),
        }

        doc.render(context)

        # Возвращаем поток документа
        doc_stream = io.BytesIO()
        doc.save(doc_stream)
        doc_stream.seek(0)
        return doc_stream
