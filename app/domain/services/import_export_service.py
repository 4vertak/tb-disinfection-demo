from datetime import datetime

import pandas as pd
from io import BytesIO
from sqlalchemy.orm import joinedload

import logging
from ...core.extensions import db
from ..models.application.entities import (
    Application, Disinfection, Diagnosis, EpidemicFocus,
    Area, Doctor, Disinfector, disinfection_disinfector
)
from ..models.user.entities import User
from ...utils.date_utils import to_local, to_utc

logger = logging.getLogger(__name__)


class ExcelImportExportService:

    @staticmethod
    def export_to_excel(start_date: datetime, end_date: datetime, user_type: str = None) -> BytesIO:
        """
        Экспорт заявок из БД в Excel
        """
        try:
            # Преобразуем даты в UTC для запроса
            start_utc = to_utc(start_date)
            end_utc = to_utc(end_date)

            # Базовый запрос с eager loading дезинфекторов (устранение N+1)
            query = db.session.query(
                Application,
                Disinfection,
                Diagnosis,
                EpidemicFocus,
                Area,
                Doctor,
                User
            ).join(Disinfection, Disinfection.application_id == Application.id, isouter=True)\
             .join(Diagnosis, Diagnosis.id == Application.diagnosis_id, isouter=True)\
             .join(EpidemicFocus, EpidemicFocus.id == Application.focus_id, isouter=True)\
             .join(Area, Area.id == Application.area_id, isouter=True)\
             .join(Doctor, Doctor.id == Application.doctor_id, isouter=True)\
             .join(User, User.id == Application.user_id, isouter=True)\
             .options(joinedload(Disinfection.disinfectors, innerjoin=False))\
             .filter(Application.submission_date.between(start_utc, end_utc))

            # Фильтрация по типу пользователя
            if user_type == 'doctor':
                query = query.filter(User.user_type == 'doctor')

            results = query.order_by(Application.submission_date.desc()).all()

            # Подготовка данных
            data = []
            for application, disinfection, diagnosis, focus, area, doctor, user in results:
                # Дезинфекторы уже загружены через joinedload — дополнительных запросов нет
                disinfectors = []
                if disinfection and disinfection.disinfectors:
                    disinfectors = [d.full_name for d in disinfection.disinfectors]

                # причины
                reason_text = ""
                if application.reason_application == 'hospitalization':
                    if application.hospitalization_date and application.place_of_hospitalization:
                        reason_text = f"{application.hospitalization_date.strftime('%d.%m.%Y')} {application.place_of_hospitalization}"
                elif application.reason_application == 'posthumously':
                    reason_text = 'посмертно'
                else:
                    reason_text = 'планово'

                row = {
                    '№ заявки': application.application_number,
                    'Дата подачи заявки': to_local(application.submission_date).strftime('%Y-%m-%d %H:%M:%S') if application.submission_date else '',
                    'ФИО пациента': application.patient_full_name,
                    'Дата рождения': application.birth_date.strftime('%Y-%m-%d') if application.birth_date else '',
                    'Адрес проживания': application.address,
                    'Конт.тел.:': application.contact_phone or '',
                    'Конт.тел.родственника:': application.relative_contact_phone or '',
                    'Место работы больного': application.workplace or '',
                    'Должность': application.position or '',
                    'Дата взятия на учет': application.registration_date.strftime('%Y-%m-%d') if application.registration_date else '',
                    'Диагноз': diagnosis.mkb_code if diagnosis else '',
                    'ГДУ': application.gdu or '',
                    'Причина проведения': reason_text,
                    'Очаг': focus.name if focus else '',
                    '№ участка': area.name_area if area else '',
                    'ФИО врача': doctor.full_name if doctor else '',
                    'Дата проведения дезинфекции': to_local(disinfection.disinfection_date).strftime('%Y-%m-%d %H:%M:%S') if disinfection and disinfection.disinfection_date else '',
                    'Площадь помещения, кв.м.': disinfection.area_size if disinfection else '',
                    'Объем помещения, куб.м.': disinfection.volume_size if disinfection else '',
                    'Время распыления, в мин и сек': disinfection.spraying_time if disinfection else '',
                    'ФИО дезинфектора': ', '.join(disinfectors) if disinfectors else '',
                    'Статус': application.status
                }
                data.append(row)

            df = pd.DataFrame(data)

            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Лист1', index=False)

                # Настройка ширины колонок
                worksheet = writer.sheets['Лист1']
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

            output.seek(0)
            return output

        except Exception as e:
            logger.error(f"Ошибка экспорта в Excel: {str(e)}")
            raise
