from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, StringField, PasswordField, SubmitField, SelectFieldBase
from wtforms.validators import DataRequired, Length, EqualTo, Optional

class RegistrationForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired(
        message='Имя обязательно'), Length(min=1, max=100)])
    login = StringField('Логин', validators=[DataRequired(message='Логин обязателен'), Length(
        min=2, max=20, message='Логин  должен содержать минимум 2 символа')])
    password = PasswordField('Пароль', validators=[DataRequired(message='Пароль обязателен'), Length(
        min=8, message='Пароль должен содержать минимум 8 символов.')])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(
        message='Подтверждение пароля обязательно'), EqualTo('password', message='Пароли не совпадают')])
    user_type = SelectField('Тип пользователя', choices=[('doctor', 'Врач'), ('disinfector', 'Дезинфектор'), ('admin', 'Администратор')], default='disinfector')
    area_id = SelectField('Диспансерный участок', choices=[], coerce=int)
    submit = SubmitField('Зарегистрироваться')

class LoginUpdateForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired(message='Имя обязательно'), 
                                         Length(min=1, max=100)])
    login = StringField('Логин', validators=[DataRequired(message='Логин обязателен'), 
                                           Length(min=2, max=20)])
    
    
    change_password = BooleanField('Изменить пароль')
    current_password = PasswordField('Текущий пароль', validators=[Optional()])
    
    new_password = PasswordField('Новый пароль', validators=[
        Optional(),
        Length(min=8, message='Пароль должен содержать минимум 8 символов.')
    ])
    confirm_new_password = PasswordField('Подтвердите новый пароль', validators=[
        Optional(),
        EqualTo('new_password', message='Пароли не совпадают')
    ])
    
    user_type = SelectField('Тип пользователя', choices=[
        ('doctor', 'Врач'), 
        ('disinfector', 'Дезинфектор'), 
        ('admin', 'Администратор')
    ], default='disinfector')
    
    submit = SubmitField('Обновить')


class LoginForm(FlaskForm):
    login = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')
