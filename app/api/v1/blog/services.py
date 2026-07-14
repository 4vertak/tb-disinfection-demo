"""Бизнес-логика для постов блога через API"""

from app.domain.models.blog.entities import BlogPost
from app.domain.services.blog_service import BlogService
from app.core.extensions import db
from werkzeug.datastructures import FileStorage


class BlogApiService:
    """Сервис для работы с постами блога через API"""
    
    @staticmethod
    def get_all_posts(published_only: bool = True, search: str = None, page: int = 1, per_page: int = 10):
        """
        Получить список постов с пагинацией и поиском
        
        Args:
            published_only: Показывать только опубликованные
            search: Поисковый запрос
            page: Номер страницы
            per_page: Количество постов на странице
        
        Returns:
            dict: Словарь с posts, total, pages, has_next, has_prev
        """
        if search:
            pagination = BlogService.search_posts(search, page=page, per_page=per_page)
        else:
            pagination = BlogService.get_paginated_posts(
                page=page, 
                per_page=per_page, 
                published_only=published_only
            )
        
        return {
            'posts': pagination.items,
            'total': pagination.total,
            'pages': pagination.pages,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    
    @staticmethod
    def get_post_by_id(post_id: int):
        """
        Получить пост по ID
        
        Args:
            post_id: ID поста
        
        Returns:
            BlogPost or None: Пост или None
        """
        return BlogService.get_post_by_id(post_id)
    
    @staticmethod
    def get_recent_posts(limit: int = 3):
        """
        Получить последние опубликованные посты
        
        Args:
            limit: Количество постов
        
        Returns:
            list: Список постов
        """
        return BlogService.get_recent_posts(limit=limit)
    
    @staticmethod
    def create_post(data: dict):
        """
        Создать новый пост
        
        Args:
            data: Данные поста (title, content, excerpt, is_published)
        
        Returns:
            BlogPost: Созданный пост
        """
        return BlogService.create_blog_post(
            title=data['title'],
            content=data['content'],
            excerpt=data.get('excerpt'),
            image_file=None
        )
    
    @staticmethod
    def update_post(post_id: int, data: dict):
        """
        Обновить пост
        
        Args:
            post_id: ID поста
            data: Данные для обновления
        
        Returns:
            BlogPost: Обновленный пост
        
        Raises:
            ValueError: Если пост не найден
        """
        post = BlogService.get_post_by_id(post_id)
        if not post:
            raise ValueError('Post not found')
        
        # Логируем входные данные
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Updating blog post {post_id} with data: {data}")
        logger.info(f"Current post excerpt: {post.excerpt}")
        
        # Используем существующие значения если новые не переданы
        title = data.get('title', post.title)
        content = data.get('content', post.content)
        
        # Для excerpt: если передан в data, используем его (даже если None)
        # Иначе сохраняем существующее значение
        if 'excerpt' in data:
            excerpt = data.get('excerpt')
        else:
            excerpt = post.excerpt
        
        logger.info(f"Resolved values - title: {title}, content length: {len(content)}, excerpt: {excerpt}")
        
        try:
            result = BlogService.update_blog_post(
                post_id=post_id,
                title=title,
                content=content,
                excerpt=excerpt,
                image_file=None
            )
            logger.info(f"Successfully updated blog post {post_id}")
            return result
        except Exception as e:
            logger.error(f"Error updating blog post {post_id}: {type(e).__name__}: {str(e)}", exc_info=True)
            raise ValueError(f'Failed to update post: {str(e)}')

    
    @staticmethod
    def delete_post(post_id: int):
        """
        Удалить пост
        
        Args:
            post_id: ID поста
        
        Returns:
            bool: True если удален
        
        Raises:
            ValueError: Если пост не найден
        """
        return BlogService.delete_blog_post(post_id)
    
    @staticmethod
    def upload_image(post_id: int, file: FileStorage):
        """
        Загрузить изображение для поста
        
        Args:
            post_id: ID поста
            file: Загруженный файл
        
        Returns:
            BlogPost: Пост с обновленным изображением
        
        Raises:
            ValueError: Если пост не найден или файл невалидный
        """
        post = BlogService.get_post_by_id(post_id)
        if not post:
            raise ValueError('Post not found')
        
        # Проверяем файл
        if not file or not BlogService.allowed_file(file.filename):
            raise ValueError('Invalid file type. Allowed: png, jpg, jpeg, gif, webp')
        
        # Сохраняем изображение
        image_path = BlogService.save_image(file)
        if not image_path:
            raise ValueError('Failed to save image')
        
        # Обновляем пост
        if post.image:
            BlogService.delete_image(post.image)
        
        post.image = image_path
        db.session.commit()
        
        return post