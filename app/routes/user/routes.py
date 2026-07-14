from asyncio.log import logger

from ...domain.models.application.entities import Application, Disinfection, Area, Doctor
from ...domain.models.audit.entities import UserAuditLog
from ...utils.serializers import json_serializer

from ...domain.models.user.entities import User
from ...domain.services.user_service import UserService
from flask import Blueprint, abort, render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
import json
from datetime import datetime, timezone
from .forms import RegistrationForm, LoginForm, LoginUpdateForm
from werkzeug.security import generate_password_hash, check_password_hash
from ...core.extensions import db, limiter

user = Blueprint('user', __name__)


@user.route('/login', methods=['GET', 'POST'])
@limiter.limit("20 per minute")
def login():
    if current_user.is_authenticated:
        return redirect('/')

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(login=form.login.data).first()

        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('Вы вошли в систему!', 'success')
            if user.user_type == "admin":
                return redirect('/admin')
            return redirect('/all')
        else:
            flash('Неправильное имя пользователя или пароль', 'danger')

    return render_template('user/login.html', form=form)


@user.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if current_user.user_type != "admin":
        abort(403)

    form = RegistrationForm()
    from app.domain.models.application.entities import Area
    form.area_id.choices = [(0, '-- Выберите участок --')] + [(f.id, f.name_area) for f in Area.query.all()]

    if form.validate_on_submit():
        try:
            user_data = {
                'login': form.login.data,
                'name': form.name.data,
                'password': form.password.data,
                'user_type': form.user_type.data,
            }
            if form.user_type.data == 'doctor' and form.area_id.data and form.area_id.data != 0:
                user_data['area_id'] = form.area_id.data

            UserService.create_user(user_data)
            flash('Регистрация прошла успешно!', 'success')
            return redirect('/admin/users')

        except Exception as e:
            flash('Ошибка при регистрации. Попробуйте снова.', 'danger')
            logger.error(f'Ошибка при регистрации: {str(e)}')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Ошибка в поле "{getattr(form, field).label.text}": {error}', 'danger')

    return render_template('user/register.html', form=form)


@user.route('/user/<int:id>/update', methods=['GET', 'POST'])
@user.route('/profile', methods=['GET', 'POST'])
@user.route('/password/change', methods=['GET', 'POST'])
@user.route('/user/password/change', methods=['GET', 'POST'])
@login_required
def update(id=None):
    if id is None:
        id = current_user.id
        
    user_obj = db.session.get(User, id)
    if not user_obj:
        flash('Пользователь не найден.', 'danger')
        return redirect(url_for('application.all'))

    if not (current_user.id == user_obj.id or current_user.user_type == "admin"):
        flash('У вас нет прав для редактирования этого профиля.', 'danger')
        return redirect(url_for('application.all'))

    form = LoginUpdateForm(obj=user_obj)

    if request.method == 'POST' and form.validate_on_submit():
        try:
            update_data = {
                'login': form.login.data,
                'name': form.name.data,
                'user_type': form.user_type.data
            }

            if current_user.user_type != 'admin':
                update_data.pop('user_type', None)

            if form.change_password.data:
                if current_user.user_type != "admin":
                    if not check_password_hash(user_obj.password_hash, form.current_password.data):
                        flash('Текущий пароль введен неверно', 'danger')
                        return render_template('user/update.html', form=form, user=user_obj)

                update_data['password_hash'] = generate_password_hash(form.new_password.data)

                log = UserAuditLog(
                    user_id=current_user.id,
                    action='change_password',
                    details=json.loads(json.dumps({'changed_at': datetime.now(timezone.utc)}, default=json_serializer))
                )
                db.session.add(log)

            UserService.update_user(user_obj.id, update_data)
            flash('Профиль успешно обновлен!', 'success')
            if current_user.user_type == 'admin':
                return redirect('/admin/users')
            else:
                return redirect(url_for('application.all'))

        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении профиля: {str(e)}', 'danger')
            logger.error(f'Ошибка при обновлении профиля {id}: {str(e)}')

    return render_template('user/update.html', form=form, user=user_obj, is_admin=(current_user.user_type == "admin"))


@user.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы!', 'success')
    return redirect('/')


@user.route('/user/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_user(id):
    if current_user.user_type != "admin":
        abort(403)

    user_obj = db.session.get(User, id)
    if not user_obj:
        flash('Пользователь не найден.', 'danger')
        return redirect('/admin/users')

    if current_user.id == id:
        flash('Нельзя удалить свой аккаунт.', 'danger')
        return redirect('/admin/users')

    try:
        with db.session.begin_nested():
            transferred_apps = 0
            transferred_disinfections = 0
            new_owner_id = None

            if user_obj.user_type == 'doctor':
                alternate = User.query.filter(User.user_type == "doctor", User.id != user_obj.id).first()
                if alternate:
                    new_owner_id = alternate.id
                    transferred_apps = Application.query.filter_by(user_id=id).update(
                        {'user_id': alternate.id}, synchronize_session=False
                    )
            elif user_obj.user_type == 'disinfector':
                alternate = User.query.filter(User.user_type == "disinfector", User.id != user_obj.id).first()
                if alternate:
                    new_owner_id = alternate.id
                    transferred_disinfections = Disinfection.query.filter_by(user_id=id).update(
                        {'user_id': alternate.id}, synchronize_session=False
                    )

            log = UserAuditLog(
                user_id=current_user.id,
                action='delete_user',
                details={
                    'deleted_user_id': id,
                    'deleted_login': user_obj.login,
                    'transferred_applications': transferred_apps,
                    'transferred_disinfections': transferred_disinfections,
                    'new_owner_id': new_owner_id
                }
            )
            db.session.add(log)
            db.session.delete(user_obj)

        db.session.commit()
        flash('Пользователь успешно удален!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении пользователя: {str(e)}', 'danger')
        logger.error(f'Ошибка при удалении пользователя {id}: {str(e)}', exc_info=True)

    return redirect('/admin/users')


@user.route('/admin/users', methods=['POST', 'GET'])
@login_required
def users():
    if current_user.user_type != "admin":
        abort(403)

    users = User.query.all()
    total_info = {
        'total_users': len(users),
        'count_admins': sum(1 for u in users if u.user_type == "admin"),
        'count_doctors': sum(1 for u in users if u.user_type == "doctor"),
        'count_disinfectors': sum(1 for u in users if u.user_type == "disinfector"),
    }

    all_users = [
        {'id': u.id, 'login': u.login, 'name': u.name, 'user_type': u.user_type}
        for u in users
    ]

    return render_template('application/users.html', total_info=total_info, users=all_users)