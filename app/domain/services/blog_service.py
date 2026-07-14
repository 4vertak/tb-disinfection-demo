from datetime import datetime, timezone
import os
from sqlalchemy import desc
from ...core.extensions import db 
from ..models.blog.entities import BlogPost
from werkzeug.utils import secure_filename

class BlogService:
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    UPLOAD_FOLDER = 'app/static/uploads/blog'
    
    @staticmethod
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in BlogService.ALLOWED_EXTENSIONS
    
    @staticmethod
    def save_image(file):
        if file and BlogService.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Добавляем timestamp для уникальности
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
            filename = timestamp + filename
            
            # Создаем папку если не существует
            os.makedirs(BlogService.UPLOAD_FOLDER, exist_ok=True)
            
            file_path = os.path.join(BlogService.UPLOAD_FOLDER, filename)
            file.save(file_path)
            return f"uploads/blog/{filename}"
        return None
    
    @staticmethod
    def delete_image(image_path):
        if image_path:
            full_path = os.path.join('app/static', image_path)
            if os.path.exists(full_path):
                os.remove(full_path)
    
    @staticmethod
    def create_blog_post(title, content, image_file=None, excerpt=None):
        try:
            image_path = None
            if image_file:
                image_path = BlogService.save_image(image_file)
            
            if not excerpt and content:
                # Автоматически генерируем краткое описание из первых 150 символов
                excerpt = content[:150] + '...' if len(content) > 150 else content
            
            blog_post = BlogPost(
                title=title,
                content=content,
                excerpt=excerpt,
                image=image_path
            )
            
            db.session.add(blog_post)
            db.session.commit()
            return blog_post
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def update_blog_post(post_id, title, content, image_file=None, excerpt=None):
        try:
            blog_post = db.session.get(BlogPost, post_id)
            if not blog_post:
                raise ValueError("Blog post not found")
            
            blog_post.title = title
            blog_post.content = content
            
            if excerpt is not None:
                blog_post.excerpt = excerpt
            elif content and not blog_post.excerpt:
                if len(content) > 150:
                    blog_post.excerpt = content[:150] + '...'
                else:
                    blog_post.excerpt = content
            
            if image_file:
                if blog_post.image:
                    BlogService.delete_image(blog_post.image)
                # Сохраняем новое
                blog_post.image = BlogService.save_image(image_file)
            
            from datetime import datetime
            blog_post.updated_at = datetime.utcnow()
            
            db.session.commit()
            return blog_post
        except Exception as e:
            db.session.rollback()
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in update_blog_post: {type(e).__name__}: {str(e)}", exc_info=True)
            raise e
    
    @staticmethod
    def delete_blog_post(post_id):
        try:
            blog_post = db.session.get(BlogPost, post_id)
            if not blog_post:
                raise ValueError("Blog post not found")
            
            # Удаляем изображение
            if blog_post.image:
                BlogService.delete_image(blog_post.image)
            
            db.session.delete(blog_post)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_all_posts(limit=None, published_only=True):
        query = BlogPost.query
        if published_only:
            query = query.filter_by(is_published=True)
        query = query.order_by(BlogPost.created_at.desc())
        
        if limit:
            return query.limit(limit).all()
        return query.all()
    
    @staticmethod
    def get_post_by_id(post_id):
        return db.session.get(BlogPost, post_id)
    
    @staticmethod
    def get_recent_posts(limit=3):
        return BlogPost.query.filter_by(is_published=True)\
                            .order_by(BlogPost.created_at.desc())\
                            .limit(limit).all()
    
    @staticmethod
    def get_paginated_posts(page=1, per_page=6, published_only=True):
        """
        Получить посты с пагинацией
        """
        query = BlogPost.query
        if published_only:
            query = query.filter_by(is_published=True)
        
        posts = query.order_by(db.desc(BlogPost.created_at)).paginate(page=page, per_page=per_page, error_out=False)
        
        return posts
    
    @staticmethod
    def search_posts(query, page=1, per_page=6):
        """
        Поиск постов по заголовку и содержанию
        """
        search = f"%{query}%"
        posts = BlogPost.query.filter(
            BlogPost.is_published == True,
            BlogPost.title.ilike(search) | BlogPost.content.ilike(search)
        ).order_by(desc(BlogPost.created_at))\
        .paginate(page=page, per_page=per_page, error_out=False)
        
        return posts