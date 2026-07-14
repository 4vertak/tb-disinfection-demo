from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app, jsonify
from flask_login import login_required, current_user
import os

from ...domain.services.blog_service import BlogService
from ...domain.models.blog.entities import BlogPost
from .forms import BlogPostForm

blog = Blueprint('blog', __name__)

@blog.route('/')
def index():
    """Страница со списком всех постов блога с пагинацией"""
    page = request.args.get('page', 1, type=int)
    posts_pagination = BlogService.get_paginated_posts(page=page, per_page=5)

    recent_posts = BlogService.get_recent_posts(limit=5)

    return render_template('blog/blog.html', posts_pagination=posts_pagination, recent_posts=recent_posts)

@blog.route('/<int:post_id>/')
def post_detail(post_id):
    """Детальная страница поста"""
    post = BlogService.get_post_by_id(post_id)
    if not post or (not post.is_published and (not current_user.is_authenticated or current_user.user_type != 'admin')):
        abort(404)
    return render_template('blog/blog_detail.html', post=post)

@blog.route('/add/', methods=['GET', 'POST'])
@login_required
def add_post():
    """Добавление нового поста (только для администратора)"""
    if current_user.user_type != 'admin':
        abort(403)

    form = BlogPostForm()
    if form.validate_on_submit():
        try:
            blog_post = BlogService.create_blog_post(
                title=form.title.data,
                content=form.content.data,
                image_file=form.image.data,
                excerpt=form.excerpt.data
            )
            flash('Пост успешно создан!', 'success')
            return redirect(url_for('blog.post_detail', post_id=blog_post.id))
        except Exception as e:
            flash(f'Ошибка при создании поста: {str(e)}', 'danger')

    return render_template('blog/blog_form.html', form=form, title='Добавить пост')

@blog.route('/<int:post_id>/edit/', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    """Редактирование поста (только для администратора)"""
    if current_user.user_type != 'admin':
        abort(403)

    post = BlogService.get_post_by_id(post_id)
    if not post:
        abort(404)

    form = BlogPostForm(obj=post)

    if form.validate_on_submit():
        try:
            BlogService.update_blog_post(
                post_id=post_id,
                title=form.title.data,
                content=form.content.data,
                image_file=form.image.data,
                excerpt=form.excerpt.data
            )
            flash('Пост успешно обновлен!', 'success')
            return redirect(url_for('blog.post_detail', post_id=post_id))
        except Exception as e:
            flash(f'Ошибка при обновлении поста: {str(e)}', 'danger')

    return render_template('blog/blog_form.html', form=form, title='Редактировать пост', post=post)

@blog.route('/<int:post_id>/delete/', methods=['POST'])
@login_required
def delete_post(post_id):
    """Удаление поста (только для администратора)"""
    if current_user.user_type != 'admin':
        abort(403)

    try:
        BlogService.delete_blog_post(post_id)
        flash('Пост успешно удален!', 'success')
    except Exception as e:
        flash(f'Ошибка при удалении поста: {str(e)}', 'danger')

    return redirect(url_for('blog.index'))

@blog.route('/search')
def search():
    """Поиск постов"""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    if query:
        posts_pagination = BlogService.search_posts(query, page=page, per_page=6)
    else:
        posts_pagination = BlogService.get_paginated_posts(page=page, per_page=6)

    return render_template('blog/blog.html',
                         posts_pagination=posts_pagination,
                         search_query=query)

@blog.route('/api/post/<int:post_id>')
def api_post_detail(post_id):
    post = BlogPost.query.get_or_404(post_id)

    # Форматируем контент для безопасного отображения
    formatted_content = post.content.replace('\n', '<br>')

    return jsonify({
        'title': post.title,
        'content': formatted_content,
        'image': url_for('static', filename=post.image) if post.image else None,
        'excerpt': post.excerpt,
        'created_at': post.created_at.strftime('%d.%m.%Y в %H:%M')
    })
