"""Marshmallow схемы для валидации данных заявок.
Поля строго соответствуют SQLAlchemy модели Application.
"""
from marshmallow import Schema, fields, validate, validates, ValidationError, pre_load

# Импорт справочных схем для nested полей
from .schemas_references import (
    DiagnosisSchema,
    EpidemicFocusSchema,
    AreaSchema,
    DoctorSchema,
    UserReferenceSchema,
    DisinfectorSchema,
)


class DisinfectionCreateSchema(Schema):
    """Схема для обновления данных дезинфекции"""
    rejection_reason = fields.String(
        allow_none=True,
        metadata={'description': 'Причина отказа или "completed"'}
    )
    disinfection_date = fields.DateTime(
        required=True,
        metadata={'description': 'Дата и время дезинфекции (UTC)'}
    )
    area_size = fields.Float(
        validate=validate.Range(min=0, error='Площадь не может быть отрицательной'),
        allow_none=True,
        metadata={'description': 'Площадь обработки (кв.м)'}
    )
    volume_size = fields.Float(
        validate=validate.Range(min=0, error='Объем не может быть отрицательным'),
        allow_none=True,
        metadata={'description': 'Объем обработки (куб.м)'}
    )
    spraying_time = fields.String(
        allow_none=True,
        validate=validate.Length(max=255),
        metadata={'description': 'Время распыления'}
    )
    swab_testing = fields.Integer(
        validate=validate.Range(min=0, error='Количество смывов не может быть отрицательным'),
        allow_none=True,
        metadata={'description': 'Количество смывов'}
    )
    disinfector_ids = fields.List(
        fields.Integer(),
        metadata={'description': 'Список ID дезинфекторов'},
        allow_none=True
    )
    # Поддержка legacy формата (строка ФИО через запятую)
    disinfectors = fields.String(
        allow_none=True,
        metadata={'description': 'Строка с ФИО дезинфекторов (legacy формат)'}
    )

    @validates('disinfector_ids')
    def validate_disinfectors_exist(self, value):
        """Проверка существования дезинфекторов"""
        if not value:
            return
        from app.domain.models.application.entities import Disinfector
        from app.core.extensions import db
        for disinfector_id in value:
            disinfector = db.session.get(Disinfector, disinfector_id)
            if not disinfector:
                raise ValidationError(f'Дезинфектор с ID {disinfector_id} не найден')


class DisinfectionSchema(Schema):
    """Схема для отображения данных дезинфекции"""
    id = fields.Integer(dump_only=True)
    application_id = fields.Integer(dump_only=True)
    rejection_reason = fields.String(
        metadata={'description': 'Причина отказа'},
        allow_none=True
    )
    disinfection_date = fields.DateTime(
        metadata={'description': 'Дата дезинфекции (UTC)'},
        allow_none=True
    )
    area_size = fields.Float(
        metadata={'description': 'Площадь (кв.м)'},
        allow_none=True
    )
    volume_size = fields.Float(
        metadata={'description': 'Объем (куб.м)'},
        allow_none=True
    )
    spraying_time = fields.String(
        metadata={'description': 'Время распыления'},
        allow_none=True
    )
    swab_testing = fields.Integer(
        metadata={'description': 'Количество смывов'},
        allow_none=True
    )
    user_id = fields.Integer(
        metadata={'description': 'ID пользователя, заполнившего данные'},
        dump_only=True,
        allow_none=True
    )

    # Дезинфекторы
    disinfectors = fields.Nested(
        DisinfectorSchema,
        many=True,
        dump_only=True,
        only=('id', 'full_name'),
        metadata={'description': 'Список дезинфекторов'}
    )

    # Метаданные
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class ApplicationCreateSchema(Schema):
    """Схема для создания новой заявки."""
    
    patient_full_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255, error='ФИО пациента обязательно')
    )
    birth_date = fields.Date(
        required=True,
        metadata={'description': 'Дата рождения пациента'}
    )
    address = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255, error='Адрес обязателен')
    )
    contact_phone = fields.String(
        allow_none=True,
        validate=validate.Length(max=50)
    )
    relative_contact_phone = fields.String(
        allow_none=True,
        validate=validate.Length(max=50),
        metadata={'description': 'Телефон родственников'}
    )
    
    # Рабочая информация
    workplace = fields.String(
        allow_none=True,
        validate=validate.Length(max=255),
        metadata={'description': 'Место работы'}
    )
    position = fields.String(
        allow_none=True,
        validate=validate.Length(max=255),
        metadata={'description': 'Должность'}
    )
    registration_date = fields.Date(
        allow_none=True,
        metadata={'description': 'Дата регистрации'}
    )

    # Связи
    diagnosis_id = fields.Integer(
        required=True,
        metadata={'description': 'ID диагноза из справочника'}
    )
    gdu = fields.String(
        allow_none=True,
        validate=validate.Length(max=255),
        metadata={'description': 'ГДУ'}
    )
    mbt = fields.String(
        allow_none=True,
        validate=validate.Length(max=255),
        metadata={'description': 'МБТ'}
    )
    focus_id = fields.Integer(
        required=True,
        metadata={'description': 'ID эпидемического очага'}
    )
    area_id = fields.Integer(
        required=True,
        metadata={'description': 'ID участка'}
    )

    # Причина заявки
    reason_application = fields.String(
        validate=validate.OneOf(
            ['hospitalization', 'scheduled', 'posthumously'],
            error='Недопустимая причина заявки'
        ),
        load_default='hospitalization'
    )

    # Врач
    doctor_id = fields.Integer(
        allow_none=True,
        metadata={'description': 'ID врача из справочника'}
    )
    doctor_full_name = fields.String(
        validate=validate.Length(max=255),
        allow_none=True,
        metadata={'description': 'ФИО врача (если doctor_id не указан)'}
    )

    # Госпитализация
    hospitalization_date = fields.Date(
        allow_none=True,
        metadata={'description': 'Дата госпитализации'}
    )
    place_of_hospitalization = fields.String(
        validate=validate.Length(max=255),
        allow_none=True,
        metadata={'description': 'Место госпитализации'}
    )

    # Валидаторы
    @validates('diagnosis_id')
    def validate_diagnosis_exists(self, value):
        """Проверка существования диагноза"""
        from app.domain.models.application.entities import Diagnosis
        from app.core.extensions import db
        if not db.session.get(Diagnosis, value):
            raise ValidationError(f'Диагноз с ID {value} не найден')

    @validates('focus_id')
    def validate_focus_exists(self, value):
        """Проверка существования очага"""
        from app.domain.models.application.entities import EpidemicFocus
        from app.core.extensions import db
        if not db.session.get(EpidemicFocus, value):
            raise ValidationError(f'Очаг с ID {value} не найден')

    @validates('area_id')
    def validate_area_exists(self, value):
        """Проверка существования участка"""
        from app.domain.models.application.entities import Area
        from app.core.extensions import db
        if not db.session.get(Area, value):
            raise ValidationError(f'Участок с ID {value} не найден')

    @validates('doctor_id')
    def validate_doctor_exists(self, value):
        """Проверка существования врача"""
        if value is None:
            return
        from app.domain.models.application.entities import Doctor
        from app.core.extensions import db
        if not db.session.get(Doctor, value):
            raise ValidationError(f'Врач с ID {value} не найден')

    @pre_load
    def handle_legacy_fields(self, data, **kwargs):
        """Обработка legacy полей для обратной совместимости"""
        # Поддержка опечатки 'sheduled' -> 'scheduled'
        if 'reason_application' in data:
            if data['reason_application'] == 'sheduled':
                data['reason_application'] = 'scheduled'
        return data


class ApplicationUpdateSchema(Schema):
    """Схема для обновления заявки."""
    
    patient_full_name = fields.String(validate=validate.Length(min=1, max=255))
    birth_date = fields.Date(allow_none=True)
    address = fields.String(validate=validate.Length(min=1, max=255))
    contact_phone = fields.String(allow_none=True, validate=validate.Length(max=50))
    relative_contact_phone = fields.String(allow_none=True, validate=validate.Length(max=50))
    
    workplace = fields.String(allow_none=True, validate=validate.Length(max=255))
    position = fields.String(allow_none=True, validate=validate.Length(max=255))
    registration_date = fields.Date(allow_none=True)

    diagnosis_id = fields.Integer()
    gdu = fields.String(allow_none=True, validate=validate.Length(max=255))
    mbt = fields.String(allow_none=True, validate=validate.Length(max=255))
    focus_id = fields.Integer()
    area_id = fields.Integer()

    reason_application = fields.String(
        validate=validate.OneOf(['hospitalization', 'scheduled', 'posthumously'])
    )

    doctor_id = fields.Integer(allow_none=True)
    doctor_full_name = fields.String(validate=validate.Length(max=255), allow_none=True)

    hospitalization_date = fields.Date(allow_none=True)
    place_of_hospitalization = fields.String(validate=validate.Length(max=255), allow_none=True)
    
    # Статус заявки (для админов/дезинфекторов)
    status = fields.String(
        validate=validate.OneOf(['incompleted', 'completed', 'refusal'])
    )

    @pre_load
    def handle_legacy_fields(self, data, **kwargs):
        """Обработка legacy полей"""
        if 'reason_application' in data:
            if data['reason_application'] == 'sheduled':
                data['reason_application'] = 'scheduled'
        return data


class ApplicationSchema(Schema):
    """Полная схема заявки для отображения"""
    id = fields.Integer(dump_only=True)
    application_number = fields.String(
        dump_only=True,
        metadata={'description': 'Номер заявки'}
    )
    status = fields.String(
        dump_only=True,
        metadata={'description': 'Статус заявки'}
    )
    submission_date = fields.DateTime(
        dump_only=True,
        metadata={'description': 'Дата подачи заявки (UTC)'}
    )
    
    patient_full_name = fields.String(metadata={'description': 'ФИО пациента'})
    birth_date = fields.Date(
        allow_none=True,
        metadata={'description': 'Дата рождения'}
    )
    address = fields.String(metadata={'description': 'Адрес'})
    contact_phone = fields.String(
        allow_none=True,
        metadata={'description': 'Телефон пациента'}
    )
    relative_contact_phone = fields.String(
        allow_none=True,
        metadata={'description': 'Телефон родственников'}
    )
    
    workplace = fields.String(
        allow_none=True,
        metadata={'description': 'Место работы'}
    )
    position = fields.String(
        allow_none=True,
        metadata={'description': 'Должность'}
    )
    registration_date = fields.Date(
        allow_none=True,
        metadata={'description': 'Дата регистрации'}
    )

    diagnosis_id = fields.Integer(metadata={'description': 'ID диагноза'})
    gdu = fields.String(
        allow_none=True,
        metadata={'description': 'ГДУ'}
    )
    mbt = fields.String(
        allow_none=True,
        metadata={'description': 'МБТ'}
    )
    focus_id = fields.Integer(metadata={'description': 'ID очага'})
    area_id = fields.Integer(metadata={'description': 'ID участка'})

    reason_application = fields.String(metadata={'description': 'Причина заявки'})
    hospitalization_date = fields.Date(
        allow_none=True,
        metadata={'description': 'Дата госпитализации'}
    )
    place_of_hospitalization = fields.String(
        allow_none=True,
        metadata={'description': 'Место госпитализации'}
    )

    doctor_id = fields.Integer(
        allow_none=True,
        metadata={'description': 'ID врача'}
    )
    doctor_full_name = fields.String(
        allow_none=True,
        metadata={'description': 'ФИО врача'}
    )
    user_id = fields.Integer(
        dump_only=True,
        metadata={'description': 'ID пользователя, создавшего заявку'}
    )

    # Вложенные объекты
    diagnosis = fields.Nested(
        DiagnosisSchema,
        dump_only=True,
        metadata={'description': 'Диагноз'}
    )
    focus = fields.Nested(
        EpidemicFocusSchema,
        dump_only=True,
        metadata={'description': 'Эпидемический очаг'}
    )
    area = fields.Nested(
        AreaSchema,
        dump_only=True,
        metadata={'description': 'Участок'}
    )
    doctor = fields.Nested(
        DoctorSchema,
        dump_only=True,
        metadata={'description': 'Врач'}
    )
    user = fields.Nested(
        UserReferenceSchema,
        dump_only=True,
        metadata={'description': 'Пользователь, создавший заявку'}
    )

    # Данные дезинфекции
    disinfection = fields.Nested(
        DisinfectionSchema,
        dump_only=True,
        allow_none=True,
        metadata={'description': 'Данные дезинфекции'}
    )

    # Метаданные
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class ApplicationListSchema(Schema):
    """Упрощенная схема для списка заявок"""
    id = fields.Integer(dump_only=True)
    application_number = fields.String(dump_only=True)
    status = fields.String(dump_only=True)
    patient_full_name = fields.String()
    address = fields.String()
    submission_date = fields.DateTime(dump_only=True)

    # Краткая информация о связанных объектах
    diagnosis = fields.Nested(
        DiagnosisSchema,
        dump_only=True,
        only=('id', 'name', 'mkb_code')
    )
    area = fields.Nested(
        AreaSchema,
        dump_only=True,
        only=('id', 'name_area')
    )
    doctor = fields.Nested(
        DoctorSchema,
        dump_only=True,
        only=('id', 'full_name')
    )
    user = fields.Nested(
        UserReferenceSchema,
        dump_only=True,
        only=('id', 'name', 'login')
    )