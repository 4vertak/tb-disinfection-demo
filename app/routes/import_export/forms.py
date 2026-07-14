from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField, SelectField
from wtforms.validators import DataRequired, Optional


class ExportExcelForm(FlaskForm):
    period = SelectField('Период', choices=[
        ('январь', 'январь'),
        ('февраль', 'февраль'),
        ('март', 'март'),
        ('апрель', 'апрель'),
        ('май', 'май'),
        ('июнь', 'июнь'),
        ('июль', 'июль'),
        ('август', 'август'),
        ('сентябрь', 'сентябрь'),
        ('октябрь', 'октябрь'),
        ('ноябрь', 'ноябрь'),
        ('декабрь', 'декабрь'),
        ('1-й квартал', '1-й квартал'),
        ('2-й квартал', '2-й квартал'),
        ('3-й квартал', '3-й квартал'),
        ('4-й квартал', '4-й квартал'),
        ('1-е полугодие', '1-е полугодие'),
        ('2-е полугодие', '2-е полугодие'),
        ('год', 'год')
    ], default='год', validators=[Optional()])
    year = SelectField('Год', coerce=int, validators=[Optional()])
    submit = SubmitField('Экспортировать')