"""Минимальные схемы для справочников.
Используются как nested в ApplicationSchema."""
from marshmallow import Schema, fields


class DiagnosisSchema(Schema):
    """Схема диагноза"""
    id = fields.Integer(dump_only=True)
    name = fields.String(metadata={'description': 'Название диагноза'})
    mkb_code = fields.String(
        metadata={'description': 'Код МКБ'},
        allow_none=True
    )


class EpidemicFocusSchema(Schema):
    """Схема эпидемического очага"""
    id = fields.Integer(dump_only=True)
    name = fields.String(metadata={'description': 'Название очага'})


class AreaSchema(Schema):
    """Схема участка"""
    id = fields.Integer(dump_only=True)
    name_area = fields.String(metadata={'description': 'Название участка'})


class DoctorSchema(Schema):
    """Схема врача из справочника"""
    id = fields.Integer(dump_only=True)
    full_name = fields.String(metadata={'description': 'ФИО врача'})
    area_id = fields.Integer(
        metadata={'description': 'ID участка врача'},
        allow_none=True
    )


class DisinfectorSchema(Schema):
    """Схема дезинфектора"""
    id = fields.Integer(dump_only=True)
    full_name = fields.String(metadata={'description': 'ФИО дезинфектора'})


class UserReferenceSchema(Schema):
    """Схема пользователя (упрощенная, для nested)"""
    id = fields.Integer(dump_only=True)
    name = fields.String(metadata={'description': 'Имя пользователя'})
    login = fields.String(
        metadata={'description': 'Логин'},
        dump_only=True
    )
    user_type = fields.String(
        metadata={'description': 'Тип пользователя'},
        dump_only=True
    )