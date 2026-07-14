from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Optional

class BlogPostForm(FlaskForm):
    title = StringField('Заголовок', validators=[
        DataRequired(message='Заголовок обязателен'),
        Length(min=5, max=255, message='Заголовок должен быть от 5 до 255 символов')
    ])
    content = TextAreaField('Содержание', validators=[
        DataRequired(message='Содержание обязательно'),
        Length(min=10, message='Содержание должно быть не менее 10 символов')
    ])
    excerpt = TextAreaField('Краткое описание (опционально)', validators=[
        Optional(),
        Length(max=300, message='Краткое описание не должно превышать 300 символов')
    ])
    image = FileField('Изображение', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Только изображения!')
    ])
    is_published = BooleanField('Опубликовать', default=True)
    submit = SubmitField('Сохранить')