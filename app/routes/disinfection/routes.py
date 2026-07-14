from flask import Blueprint, abort, render_template, redirect, url_for, flash, jsonify, request
from ...domain.services.notification_service import NotificationService
from ...domain.services.disinfector_service import DisinfectorService
from ...domain.models.user.entities import User
from .forms import DisinfectionForm
from ...domain.models.application.entities import Application, Disinfection, Disinfector
from ...core.extensions import db
from flask_login import current_user, login_required
import logging
from datetime import datetime, time
from ...utils.date_utils import LOCAL_TZ, to_local, to_utc

logger = logging.getLogger(__name__)

disinfection = Blueprint('disinfection', __name__)

@disinfection.route('/<int:id>/add/disinfection/data/', methods=['GET', 'POST'])
@login_required
def add_data(id):
    application = Application.query.get(id)

    if application is None:
        flash('Заявка не найдена.', 'error')
        return redirect(url_for('application.all'))

    disinfection = db.session.query(Disinfection).filter(
        Disinfection.application_id == id
    ).one_or_none()

    form = None   

    if current_user.user_type == "disinfector":
        if disinfection is None:
            disinfection = Disinfection(application_id=id)
            db.session.add(disinfection)

        disinfection.rejection_reason = None

        # Для GET-запроса создаем форму с данными
        if request.method == 'GET':
            # Создаем словарь данных для формы
            form_data = {
                'disinfection_date': disinfection.disinfection_date,
                'area_size': disinfection.area_size,
                'swab_testing': disinfection.swab_testing,
                'volume_size': disinfection.volume_size,
                'spraying_time': disinfection.spraying_time,
                'rejection_reason': disinfection.rejection_reason if disinfection.rejection_reason != 'completed' else '',
            }
            
            # Добавляем дезинфекторов в виде строки
            if disinfection.disinfectors:
                disinfectors_names = [d.full_name for d in disinfection.disinfectors]
                form_data['disinfectors_input'] = ', '.join(disinfectors_names)
            
            form = DisinfectionForm(data=form_data)
            
        # Для POST-запроса создаем форму из request.form
        else:
            form = DisinfectionForm()

        if form.validate_on_submit():
            logger.debug(f"Request form data: {request.form.to_dict()}")
            logger.debug(f"disinfectors_input from request: {request.form.get('disinfectors_input')}")
            logger.debug(f"disinfectors_input from form: {form.disinfectors_input.data}")
            selected_date = form.disinfection_date.data
            now_local = datetime.now(LOCAL_TZ)
            local_datetime = datetime.combine(selected_date, now_local.time(), tzinfo=LOCAL_TZ)
            disinfection.disinfection_date = to_utc(local_datetime)
            disinfection.area_size = form.area_size.data
            disinfection.swab_testing = form.swab_testing.data
            disinfection.volume_size = form.volume_size.data
            disinfection.spraying_time = form.spraying_time.data
            disinfection.user_id = current_user.id

            if form.rejection_reason.data and form.rejection_reason.data != 'completed':
                disinfection.rejection_reason = form.rejection_reason.data
                application.status = 'refusal'
            else:
                disinfection.rejection_reason = 'completed'
                application.status = 'completed'

            
            # Обрабатываем дезинфекторов
            DisinfectorService.update_disinfection_disinfectors(
                disinfection, 
                form.disinfectors_input.data
            )

            try:
                db.session.commit()

                # Отправка уведомления участкам об изменении статуса
                NotificationService.notify_application_updated(application, current_user)
                
                # Отправляем событие для обновления таблицы заявок в реальном времени
                from flask_socketio import emit
                from ...core.extensions import socketio
                socketio.emit('application_status_updated', {
                    'application_id': application.id,
                    'new_status': application.status,
                    'message': f'Заявка №{application.application_number} обновлена'
                }, room='notifications_all')

                flash('Данные о дезинфекции успешно добавлены!', 'success')
                return redirect(url_for('application.all'))
            except Exception as e:
                db.session.rollback()
                flash(f'Произошла ошибка: {str(e)}', 'error')
    else:
        abort(403)

    return render_template('application/add_data.html', application=application, form=form)

@disinfection.route('/api/search/disinfectors')
@login_required
def search_disinfectors():
    """API для поиска дезинфекторов"""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 10, type=int)
    
    results = DisinfectorService.search_disinfectors(query, limit)
    return jsonify(results)

