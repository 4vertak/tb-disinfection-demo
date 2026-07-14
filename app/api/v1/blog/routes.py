"""REST API эндпоинты для постов блога"""

from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from .schemas import BlogPostSchema, BlogPostCreateSchema, BlogPostUpdateSchema
from .services import BlogApiService
from ..common.response import (
    success_response, created_response, no_content_response,
    error_response, validation_error_response, list_response
)
from ..common.decorators import admin_required

blog_ns = Namespace('blog', description='Управление постами блога')


# ==================== SWAGGER МОДЕЛИ ====================

blog_post_model = blog_ns.model('BlogPost', {
    'id': fields.Integer(description='ID поста'),
    'title': fields.String(description='Заголовок'),
    'content': fields.String(description='Содержимое'),
    'excerpt': fields.String(description='Краткое описание'),
    'image': fields.String(description='URL изображения'),
    'is_published': fields.Boolean(description='Опубликован'),
    'created_at': fields.DateTime(description='Дата создания'),
    'updated_at': fields.DateTime(description='Дата обновления')
})

blog_post_create_model = blog_ns.model('BlogPostCreate', {
    'title': fields.String(required=True, description='Заголовок'),
    'content': fields.String(required=True, description='Содержимое'),
    'excerpt': fields.String(description='Краткое описание'),
    'is_published': fields.Boolean(description='Опубликовать', default=True)
})

blog_post_update_model = blog_ns.model('BlogPostUpdate', {
    'title': fields.String(description='Заголовок'),
    'content': fields.String(description='Содержимое'),
    'excerpt': fields.String(description='Краткое описание'),
    'is_published': fields.Boolean(description='Опубликовать')
})


# ==================== ENDPOINTS ====================

@blog_ns.route('/posts')
class BlogPostList(Resource):
    """Список постов блога"""
    
    @blog_ns.doc('list_blog_posts')
    @blog_ns.response(200, 'Список постов')
    def get(self):
        """
        Получить список постов блога с пагинацией и поиском
        
        Query параметры:
        - page: Номер страницы (по умолчанию 1)
        - per_page: Постов на странице (по умолчанию 10, макс 100)
        - published_only: Только опубликованные (true/false, по умолчанию true)
        - search: Поисковый запрос
        """
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        published_only = request.args.get('published_only', 'true').lower() == 'true'
        search = request.args.get('search')
        
        result = BlogApiService.get_all_posts(
            published_only=published_only,
            search=search,
            page=page,
            per_page=per_page
        )
        
        return list_response(
            BlogPostSchema(many=True).dump(result['posts']),
            meta={
                'total': result['total'],
                'pages': result['pages'],
                'page': result['page'],
                'per_page': result['per_page'],
                'has_next': result['has_next'],
                'has_prev': result['has_prev']
            }
        )
    
    @blog_ns.expect(blog_post_create_model, validate=True)
    @blog_ns.doc('create_blog_post')
    @blog_ns.response(201, 'Пост создан', blog_post_model)
    @blog_ns.response(403, 'Доступ запрещён (только admin)')
    @blog_ns.response(422, 'Ошибка валидации')
    @jwt_required()
    @admin_required
    def post(self):
        """Создать новый пост блога (только admin)"""
        try:
            data = BlogPostCreateSchema().load(request.get_json())
        except ValidationError as err:
            return validation_error_response(err.messages)
        
        try:
            post = BlogApiService.create_post(data)
        except Exception as e:
            return error_response(str(e), 500)
        
        return created_response(BlogPostSchema().dump(post))


@blog_ns.route('/posts/<int:id>')
@blog_ns.param('id', 'ID поста')
class BlogPostResource(Resource):
    """Детали поста блога"""
    
    @blog_ns.doc('get_blog_post')
    @blog_ns.response(200, 'Детали поста', blog_post_model)
    @blog_ns.response(404, 'Пост не найден')
    def get(self, id):
        """Получить детали поста по ID"""
        post = BlogApiService.get_post_by_id(id)
        
        if not post:
            return error_response('Post not found', 404)
        
        return success_response(BlogPostSchema().dump(post))
    
    @blog_ns.expect(blog_post_update_model)
    @blog_ns.doc('update_blog_post')
    @blog_ns.response(200, 'Пост обновлён', blog_post_model)
    @blog_ns.response(400, 'Ошибка запроса')
    @blog_ns.response(403, 'Доступ запрещён (только admin)')
    @blog_ns.response(404, 'Пост не найден')
    @blog_ns.response(422, 'Ошибка валидации')
    @jwt_required()
    @admin_required
    def patch(self, id):
        """Обновить пост блога (только admin)"""
        try:
            data = BlogPostUpdateSchema().load(request.get_json(), partial=True)
        except ValidationError as err:
            return validation_error_response(err.messages)
        
        try:
            post = BlogApiService.update_post(id, data)
        except ValueError as e:
            error_msg = str(e)
            if 'not found' in error_msg.lower():
                return error_response(error_msg, 404)
            return error_response(error_msg, 400)
        except Exception as e:
            return error_response(f'Failed to update post: {str(e)}', 500)
        
        return success_response(BlogPostSchema().dump(post))
    
    @blog_ns.doc('delete_blog_post')
    @blog_ns.response(204, 'Пост удалён')
    @blog_ns.response(403, 'Доступ запрещён (только admin)')
    @blog_ns.response(404, 'Пост не найден')
    @jwt_required()
    @admin_required
    def delete(self, id):
        """Удалить пост блога (только admin)"""
        try:
            BlogApiService.delete_post(id)
        except ValueError as e:
            return error_response(str(e), 404)
        except Exception as e:
            return error_response(str(e), 500)
        
        return no_content_response()


@blog_ns.route('/posts/<int:id>/upload-image')
@blog_ns.param('id', 'ID поста')
class BlogPostImageUpload(Resource):
    """Загрузка изображения для поста"""
    
    @blog_ns.doc('upload_blog_image')
    @blog_ns.response(200, 'Изображение загружено', blog_post_model)
    @blog_ns.response(400, 'Невалидный файл')
    @blog_ns.response(403, 'Доступ запрещён (только admin)')
    @blog_ns.response(404, 'Пост не найден')
    @jwt_required()
    @admin_required
    def post(self, id):
        """
        Загрузить изображение для поста (только admin)
        
        Требует multipart/form-data с полем 'image'
        """
        if 'image' not in request.files:
            return error_response('No image file provided', 400)
        
        file = request.files['image']
        
        try:
            post = BlogApiService.upload_image(id, file)
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
        
        return success_response(BlogPostSchema().dump(post))


@blog_ns.route('/recent')
class BlogRecentPosts(Resource):
    """Последние посты блога"""
    
    @blog_ns.doc('get_recent_posts')
    @blog_ns.response(200, 'Последние посты')
    def get(self):
        """
        Получить последние опубликованные посты
        
        Query параметры:
        - limit: Количество постов (по умолчанию 3, макс 10)
        """
        limit = min(request.args.get('limit', 3, type=int), 10)
        
        posts = BlogApiService.get_recent_posts(limit=limit)
        
        return success_response(BlogPostSchema(many=True).dump(posts))