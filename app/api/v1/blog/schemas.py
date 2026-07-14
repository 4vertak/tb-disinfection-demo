"""Marshmallow схемы для постов блога"""

from marshmallow import Schema, fields, validate, validates, ValidationError


class BlogPostSchema(Schema):
    """Схема для сериализации поста блога"""
    id = fields.Integer(dump_only=True)
    title = fields.String(metadata={'description': 'Заголовок поста'})
    content = fields.String(metadata={'description': 'Содержимое поста'})
    excerpt = fields.String(metadata={'description': 'Краткое описание'})
    image = fields.String(metadata={'description': 'URL изображения'}, allow_none=True)
    is_published = fields.Boolean(metadata={'description': 'Опубликован ли пост'})
    created_at = fields.DateTime(dump_only=True, metadata={'description': 'Дата создания'})
    updated_at = fields.DateTime(dump_only=True, metadata={'description': 'Дата обновления'})


class BlogPostCreateSchema(Schema):
    """Схема для создания поста блога"""
    title = fields.String(
        required=True,
        validate=validate.Length(min=5, max=255, error='Заголовок должен быть от 5 до 255 символов')
    )
    content = fields.String(
        required=True,
        validate=validate.Length(min=10, error='Содержимое должно быть не менее 10 символов')
    )
    excerpt = fields.String(
        validate=validate.Length(max=300, error='Краткое описание не должно превышать 300 символов'),
        allow_none=True
    )
    is_published = fields.Boolean(load_default=True)


class BlogPostUpdateSchema(Schema):
    """Схема для обновления поста блога"""
    title = fields.String(validate=validate.Length(min=5, max=255))
    content = fields.String(validate=validate.Length(min=10))
    excerpt = fields.String(validate=validate.Length(max=300), allow_none=True)
    is_published = fields.Boolean()


class BlogPostFilterSchema(Schema):
    """Схема для фильтрации постов блога"""
    is_published = fields.Boolean()
    search = fields.String()