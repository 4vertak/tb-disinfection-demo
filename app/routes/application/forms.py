
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, DateField, FloatField, TextAreaField
from wtforms.validators import DataRequired, Optional


class ApplicationForm(FlaskForm):
    patient_full_name = StringField("Ф.И.О. пациента", validators=[DataRequired()])
    birth_date = DateField("Дата рождения", format="%Y-%m-%d", validators=[DataRequired()])
    address = StringField("Адрес", validators=[DataRequired()])
    contact_phone = StringField("Контактный телефон", validators=[Optional()])
    relative_contact_phone = StringField("Контактный телефон родственника", validators=[Optional()])
    workplace = StringField("Место работы", validators=[Optional()])
    position = StringField("Должность", default="не работает", validators=[Optional()])
    diagnosis_id = SelectField("Диагноз", coerce=int, validators=[Optional()])
    focus_id = SelectField("Очаг", coerce=int, validators=[DataRequired()])
    reason_application = SelectField("Причина дезинфекции", choices=[("hospitalization", "Госпитализация"), ("sheduled", "Плановая"), ("posthumously", "Посмертно")], default="hospitalization", validators=[Optional()],)
    hospitalization_date = DateField("Дата госпитализации", format="%Y-%m-%d", validators=[Optional()])
    gdu = SelectField("Группа диспансерного наблюдения", choices=[("0", "0"),("IА", "IА"), ("IБ", "IБ"), ("IК", "IК"), ("IIА", "IIА"), ("IIБ", "IIБ"), ("III", "III"), ("IV", "IV"), ("V", "V"), ("VI", "VI"), ], validators=[Optional()], )
    mbt = SelectField("МБТ статус:", choices=[("МБТ+", "МБТ+"), ("МБТ-", "МБТ-"), ("", "нет"),], validators=[Optional()],)
    registration_date = DateField("Дата взятия на учет", format="%Y-%m-%d", validators=[DataRequired()])
    place_of_hospitalization = StringField("Место госпитализации", validators=[Optional()])

    # doctor_id = SelectField("Выбрать врача", coerce=int, validators=[Optional()])
    # doctor_full_name = StringField("Ф.И.О. врача (если новый)", validators=[Optional()])
    doctor_name = StringField("Ф.И.О. врача", validators=[DataRequired()])
    area_id = SelectField("Диспансерный участок", coerce=int, validators=[DataRequired()])




class DisinfectionForm(FlaskForm):
    area_size = FloatField('Площадь помещения (кв.м.)',
                           validators=[Optional()], default=0)
    rejection_reason = TextAreaField('Причина отказа', validators=[
                                     Optional()], default='completed')
    disinfection_date = DateField(
        'Дата проведения дезинфекции', format='%Y-%m-%d', validators=[DataRequired()], default=datetime.now)

    volume_size = FloatField('Объем помещения (куб.м.)',
                             validators=[Optional()])
    spraying_time = TextAreaField('Время раcпыления', validators=[
                                  Optional()])
    submit = SubmitField('Добавить')
