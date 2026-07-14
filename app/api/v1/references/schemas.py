"""
Marshmallow схемы для справочников.
"""
from marshmallow import Schema, fields, validate, validates, ValidationError


# ==================== AREA SCHEMAS ====================

class AreaSchema(Schema):
    """Схема для сериализации участка"""
    id = fields.Integer(dump_only=True)
    name_area = fields.String(metadata={'description': 'Название участка'})


class AreaCreateSchema(Schema):
    """Схема для создания участка"""
    name_area = fields.String(
        required=True,
        validate=validate.Length(min=1, max=50, error='Название участка обязательно')
    )
    
    @validates('name_area')
    def validate_name_unique(self, value):
        from app.domain.models.application.entities import Area
        if Area.query.filter_by(name_area=value).first():
            raise ValidationError('Участок с таким названием уже существует')


class AreaUpdateSchema(Schema):
    """Схема для обновления участка"""
    name_area = fields.String(validate=validate.Length(min=1, max=50))


# ==================== DOCTOR SCHEMAS ====================

class DoctorSchema(Schema):
    """Схема для сериализации врача"""
    id = fields.Integer(dump_only=True)
    full_name = fields.String(metadata={'description': 'ФИО врача'})
    area_id = fields.Integer(metadata={'description': 'ID участка'})
    # ✅ ИСПРАВЛЕНО: Используем прямую ссылку на класс вместо строки
    area = fields.Nested(AreaSchema, dump_only=True, only=('id', 'name_area'))


class DoctorCreateSchema(Schema):
    """Схема для создания врача"""
    full_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100, error='ФИО врача обязательно')
    )
    area_id = fields.Integer(required=True)
    
    @validates('full_name')
    def validate_name_unique(self, value):
        from app.domain.models.application.entities import Doctor
        if Doctor.query.filter_by(full_name=value).first():
            raise ValidationError('Врач с таким ФИО уже существует')
    
    @validates('area_id')
    def validate_area_exists(self, value):
        from app.domain.models.application.entities import Area
        from app.core.extensions import db
        if not db.session.get(Area, value):
            raise ValidationError('Участок не найден')


class DoctorUpdateSchema(Schema):
    """Схема для обновления врача"""
    full_name = fields.String(validate=validate.Length(min=1, max=100))
    area_id = fields.Integer()


# ==================== DISINFECTOR SCHEMAS ====================

class DisinfectorSchema(Schema):
    """Схема для сериализации дезинфектора"""
    id = fields.Integer(dump_only=True)
    full_name = fields.String(metadata={'description': 'ФИО дезинфектора'})


class DisinfectorCreateSchema(Schema):
    """Схема для создания дезинфектора"""
    full_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255, error='ФИО дезинфектора обязательно')
    )
    
    @validates('full_name')
    def validate_name_unique(self, value):
        from app.domain.models.application.entities import Disinfector
        if Disinfector.query.filter_by(full_name=value).first():
            raise ValidationError('Дезинфектор с таким ФИО уже существует')


class DisinfectorUpdateSchema(Schema):
    """Схема для обновления дезинфектора"""
    full_name = fields.String(validate=validate.Length(min=1, max=255))


# ==================== DIAGNOSIS SCHEMAS ====================

class DiagnosisSchema(Schema):
    """Схема для сериализации диагноза"""
    id = fields.Integer(dump_only=True)
    mkb_code = fields.String(metadata={'description': 'Код МКБ'})
    name = fields.String(metadata={'description': 'Название диагноза'})


class DiagnosisCreateSchema(Schema):
    """Схема для создания диагноза"""
    mkb_code = fields.String(
        required=True,
        validate=validate.Length(min=1, max=20, error='Код МКБ обязателен')
    )
    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255, error='Название диагноза обязательно')
    )
    
    @validates('mkb_code')
    def validate_code_unique(self, value):
        from app.domain.models.application.entities import Diagnosis
        if Diagnosis.query.filter_by(mkb_code=value).first():
            raise ValidationError('Диагноз с таким кодом уже существует')


class DiagnosisUpdateSchema(Schema):
    """Схема для обновления диагноза"""
    mkb_code = fields.String(validate=validate.Length(min=1, max=20))
    name = fields.String(validate=validate.Length(min=1, max=255))


# ==================== EPIDEMIC FOCUS SCHEMAS ====================

class EpidemicFocusSchema(Schema):
    """Схема для сериализации эпидемического очага"""
    id = fields.Integer(dump_only=True)
    name = fields.String(metadata={'description': 'Название очага'})


class EpidemicFocusCreateSchema(Schema):
    """Схема для создания эпидемического очага"""
    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=20, error='Название очага обязательно')
    )
    
    @validates('name')
    def validate_name_unique(self, value):
        from app.domain.models.application.entities import EpidemicFocus
        if EpidemicFocus.query.filter_by(name=value).first():
            raise ValidationError('Очаг с таким названием уже существует')


class EpidemicFocusUpdateSchema(Schema):
    """Схема для обновления эпидемического очага"""
    name = fields.String(validate=validate.Length(min=1, max=20))