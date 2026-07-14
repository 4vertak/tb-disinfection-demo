from ...domain.services.blog_service import BlogService
from ...domain.models.application.entities import Application, Diagnosis, EpidemicFocus, Doctor, Area
from ...utils.get_total_info import get_total_info, get_carry_over_count
from ...utils.date_utils import get_period_dates, to_local, LOCAL_TZ
from flask import Blueprint, render_template, redirect, request, url_for, flash, abort, send_file, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, time, timezone
import logging

logger = logging.getLogger(__name__)

from ...domain.models.user.entities import User
from ...domain.services.application_service import ApplicationService
from ...domain.services.application_api_service import ApplicationApiService
from .forms import ApplicationForm
from ...core.extensions import db

application = Blueprint("application", __name__)


@application.route("/")
def index():
    if current_user.is_authenticated:
        return redirect("/all")

    recent_posts = BlogService.get_recent_posts(limit=3)
    return render_template("application/index.html", recent_posts=recent_posts)


@application.route("/all", methods=["GET"])
@application.route("/applications", methods=["GET"])
@login_required
def all():
    selected_year = request.args.get('year', default=to_local(datetime.now(timezone.utc)).year, type=int)
    start_date, end_date = get_period_dates("год", selected_year)
    total_info = get_total_info(start_date, end_date)

    if start_date < datetime.combine(date(selected_year, 2, 1), time.min, tzinfo=LOCAL_TZ):
        carry_over = get_carry_over_count(start_date, end_date)
        total_info['total'] += carry_over

    applications = ApplicationService.get_applications(current_user.id)
    
    if not isinstance(applications, list):
        applications = list(applications)

    return render_template(
        "application/all.html", applications=applications, total_info=total_info,
        selected_year=selected_year
    )


@application.route("/create", methods=["GET", "POST"])
@application.route("/application/create", methods=["GET", "POST"])
@application.route("/applications/create", methods=["GET", "POST"])
@login_required
def create():
    if current_user.user_type not in ("doctor", "admin"):
        abort(403)

    form = ApplicationForm()
    form.diagnosis_id.choices = [(d.id, d.name) for d in Diagnosis.query.order_by(Diagnosis.id).all()]
    form.focus_id.choices = [(f.id, f.name) for f in EpidemicFocus.query.all()]
    form.area_id.choices = [(f.id, f.name_area) for f in Area.query.all()]

    if form.validate_on_submit():
        try:
            ApplicationService.create_application(form, current_user)
            flash("Заявка успешно создана!", "success")
            return redirect(url_for("application.all"))
        except Exception as e:
            db.session.rollback()
            flash(f"Ошибка при создании заявки: {str(e)}", "danger")
            logger.error(f"Ошибка при создании заявки: {str(e)}")

    return render_template("application/create.html", form=form)


@application.route("/application/<int:id>/update", methods=["GET", "POST"])
@application.route("/application/<int:id>", methods=["GET"])
@application.route("/application/<int:id>/edit", methods=["GET", "POST"])
@application.route("/applications/<int:id>/edit", methods=["GET", "POST"])
@login_required
def update(id):
    if current_user.user_type not in ("doctor", "admin"):
        abort(403)

    application = db.session.get(Application, id)

    if not application:
        flash("Заявка не найдена.", "danger")
        return redirect(url_for("application.all"))

    if current_user.user_type == "doctor" and application.user_id != current_user.id:
        flash("У вас нет прав для редактирования этой заявки.", "danger")
        return redirect(url_for("application.all"))

    form = ApplicationForm(obj=application)
    form.diagnosis_id.choices = [(d.id, d.name) for d in Diagnosis.query.all()]
    form.focus_id.choices = [(f.id, f.name) for f in EpidemicFocus.query.all()]
    form.area_id.choices = [(f.id, f.name_area) for f in Area.query.all()]

    if request.method == "GET":
        if application.doctor:
            form.doctor_name.data = application.doctor.full_name
        else:
            form.doctor_name.data = application.doctor_full_name

        form.patient_full_name.data = application.patient_full_name
        form.birth_date.data = application.birth_date
        form.address.data = application.address
        form.contact_phone.data = application.contact_phone
        form.relative_contact_phone.data = application.relative_contact_phone
        form.workplace.data = application.workplace
        form.position.data = application.position
        form.diagnosis_id.data = application.diagnosis_id
        form.registration_date.data = application.registration_date
        form.focus_id.data = application.focus_id
        form.reason_application.data = application.reason_application
        form.place_of_hospitalization.data = application.place_of_hospitalization
        form.hospitalization_date.data = application.hospitalization_date
        form.area_id.data = application.area_id

        if application.gdu:
            if '-' in application.gdu:
                gdu_part, mbt_part = application.gdu.split('-', 1)
                form.gdu.data = gdu_part
                form.mbt.data = mbt_part
            else:
                form.gdu.data = application.gdu
                form.mbt.data = ""
        else:
            form.gdu.data = ""
            form.mbt.data = ""

        logger.debug(f"relative_contact_phone: {form.relative_contact_phone.data}")

    if request.method == "POST" and form.validate_on_submit():
        try:
            ApplicationService.update_application(id, form, current_user)
            flash("Заявка успешно обновлена!", "success")
            return redirect(url_for("application.all"))
        except Exception as e:
            db.session.rollback()
            flash(f"Произошла ошибка при обновлении заявки: {str(e)}", "danger")
            logger.error(f"Ошибка при обновлении заявки {id}: {str(e)}")

    return render_template("application/update.html", form=form, application=application)


@application.route("/application/<int:id>/delete", methods=["GET", "POST"])
@application.route("/applications/<int:id>/delete", methods=["GET", "POST"])
@login_required
def delete_application(id):
    if current_user.user_type not in ("doctor", "admin"):
        abort(403)
    try:
        ApplicationService.delete_application(id, current_user)
        flash("Заявка успешно удалена!", "success")
    except ValueError as e:
        flash(f"Заявка не найдена: {str(e)}", "danger")
    except PermissionError as e:
        flash(f"Ошибка прав доступа: {str(e)}", "danger")
    except Exception as e:
        flash(f"Произошла ошибка при удалении заявки: {str(e)}", "danger")

    return redirect(url_for("application.all"))


@application.route("/api/search/doctors")
@login_required
def search_doctors():
    query = request.args.get('q', '')
    limit = request.args.get('limit', 10, type=int)

    if len(query) < 2:
        return jsonify([])

    doctors = ApplicationService.search_doctors(query, limit)
    return jsonify(doctors)


@application.route("/application/<int:id>/download", methods=["GET"])
@login_required
def download_application(id):
    doc_stream = ApplicationService.generate_application_doc(id)
    current_date = to_local(datetime.now(timezone.utc)).strftime("%Y-%m-%d")
    filename = f"{id}_{current_date}.docx"

    return send_file(
        doc_stream,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@application.route("/api/diagnoses")
@login_required
def api_diagnoses():
    return ApplicationApiService.get_diagnoses()


@application.route("/api/gdu")
@login_required
def api_gdu():
    return ApplicationApiService.get_gdu_list()


@application.route("/test-notification")
@login_required
def test_notification():
    from ...domain.services.notification_service import NotificationService

    class MockApplication:
        def __init__(self):
            self.id = 999
            self.application_number = 999
            self.patient_full_name = "Тестовый Пациент"
            self.address = "Тестовый адрес"
            self.status = "completed"

    mock_app = MockApplication()

    if current_user.user_type == "doctor":
        NotificationService.notify_application_updated(mock_app, current_user)
        flash("Тестовое уведомление для врачей отправлено!", "success")
    elif current_user.user_type == "disinfector":
        NotificationService.notify_new_application(mock_app)
        flash("Тестовое уведомление для дезинфекторов отправлено!", "success")
    else:
        flash("Тестовые уведомления доступны только врачам и дезинфекторам", "warning")

    return redirect(url_for("application.all"))
