"""
REST API эндпоинты для управления заявками.
"""
from datetime import datetime, date
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from marshmallow import ValidationError

from .schemas import (
    ApplicationSchema, ApplicationCreateSchema, ApplicationUpdateSchema,
    DisinfectionSchema, DisinfectionCreateSchema
)
from .services import ApplicationService, DisinfectionService
from ..common.response import (
    success_response, created_response, no_content_response,
    error_response, validation_error_response, list_response
)
from ..common.decorators import admin_required, doctor_required, disinfector_required
from ..common.pagination import paginate_query

applications_ns = Namespace('applications', description='Управление заявками')

# ==================== SWAGGER МОДЕЛИ ====================
application_model = applications_ns.model('Application', {
    'id': fields.Integer(description='ID заявки'),
    'application_number': fields.Integer(description='Номер заявки'),
    'user_id': fields.Integer(description='ID пользователя (врача)'),
    'submission_date': fields.DateTime(description='Дата подачи (UTC)'),
    'patient_full_name': fields.String(description='ФИО пациента'),
    'birth_date': fields.Date(description='Дата рождения'),
    'address': fields.String(description='Адрес'),
    'contact_phone': fields.String(description='Телефон пациента'),
    'relative_contact_phone': fields.String(description='Телефон родственника'),
    'workplace': fields.String(description='Место работы'),
    'position': fields.String(description='Должность'),
    'registration_date': fields.Date(description='Дата взятия на учет'),
    'diagnosis_id': fields.Integer(description='ID диагноза'),
    'gdu': fields.String(description='ГДУ'),
    'focus_id': fields.Integer(description='ID эпид. очага'),
    'area_id': fields.Integer(description='ID участка'),
    'reason_application': fields.String(description='Причина обращения', enum=['hospitalization', 'sheduled', 'posthumously']),
    'doctor_id': fields.Integer(description='ID врача из справочника'),
    'doctor_full_name': fields.String(description='ФИО врача'),
    'hospitalization_date': fields.Date(description='Дата госпитализации'),
    'place_of_hospitalization': fields.String(description='Место госпитализации'),
    'status': fields.String(description='Статус', enum=['incompleted', 'completed', 'refusal'])
})

application_create_model = applications_ns.model('ApplicationCreate', {
    'patient_full_name': fields.String(required=True, description='ФИО пациента'),
    'birth_date': fields.Date(required=True, description='Дата рождения'),
    'address': fields.String(required=True, description='Адрес'),
    'contact_phone': fields.String(description='Телефон пациента'),
    'relative_contact_phone': fields.String(description='Телефон родственника'),
    'workplace': fields.String(description='Место работы'),
    'position': fields.String(description='Должность'),
    'diagnosis_id': fields.Integer(required=True, description='ID диагноза'),
    'gdu': fields.String(description='ГДУ'),
    'focus_id': fields.Integer(required=True, description='ID эпид. очага'),
    'area_id': fields.Integer(required=True, description='ID участка'),
    'reason_application': fields.String(description='Причина обращения', enum=['hospitalization', 'sheduled', 'posthumously']),
    'doctor_id': fields.Integer(description='ID врача из справочника'),
    'doctor_full_name': fields.String(description='ФИО врача (если нет в справочнике)'),
    'hospitalization_date': fields.Date(description='Дата госпитализации'),
    'place_of_hospitalization': fields.String(description='Место госпитализации')
})

disinfection_model = applications_ns.model('Disinfection', {
    'id': fields.Integer(description='ID'),
    'application_id': fields.Integer(description='ID заявки'),
    'rejection_reason': fields.String(description='Причина отказа'),
    'disinfection_date': fields.DateTime(description='Дата дезинфекции (UTC)'),
    'area_size': fields.Float(description='Площадь помещения (кв.м)'),
    'volume_size': fields.Float(description='Объем помещения (куб.м)'),
    'spraying_time': fields.String(description='Время распыления'),
    'swab_testing': fields.Integer(description='Количество смывов'),
    'user_id': fields.Integer(
        description='ID пользователя, заполнившего данные',
        readonly=True
    ),
    'disinfectors': fields.List(fields.Nested(
        applications_ns.model('DisinfectorRef', {
            'id': fields.Integer(),
            'full_name': fields.String()
        })
    ), description='Список дезинфекторов')
})


# ==================== ЭНДПОИНТЫ ====================

@applications_ns.route('/')
class ApplicationList(Resource):
    @applications_ns.doc('list_applications')
    @applications_ns.response(200, 'Список заявок')
    @jwt_required()
    def get(self):
        """Получение списка заявок с пагинацией и фильтрацией"""
        filters = {
            'status': request.args.get('status'),
            'doctor_id': request.args.get('doctor_id', type=int),
            'area_id': request.args.get('area_id', type=int),
            'focus_id': request.args.get('focus_id', type=int),
            'diagnosis_id': request.args.get('diagnosis_id', type=int),
            'search': request.args.get('search')
        }
        
        # Парсинг дат (формат YYYY-MM-DD)
        date_from = request.args.get('date_from')
        if date_from:
            try: filters['date_from'] = date.fromisoformat(date_from)
            except ValueError: pass
            
        date_to = request.args.get('date_to')
        if date_to:
            try: filters['date_to'] = date.fromisoformat(date_to)
            except ValueError: pass

        # Проверка прав доступа
        claims = get_jwt()
        user_id = int(get_jwt_identity())
        
        if claims.get('user_type') == 'doctor':
            filters['doctor_id'] = user_id
        
        query = ApplicationService.get_all_applications(filters)
        result = paginate_query(query, ApplicationSchema())
        
        return list_response(result['items'], result['meta'])
    
    @applications_ns.expect(application_create_model, validate=True)
    @applications_ns.doc('create_application')
    @applications_ns.response(201, 'Заявка создана', application_model)
    @jwt_required()
    @doctor_required
    def post(self):
        """Создание новой заявки"""
        try:
            data = ApplicationCreateSchema().load(request.get_json())
        except ValidationError as err:
            return validation_error_response(err.messages)
        
        user_id = int(get_jwt_identity())
        application = ApplicationService.create_application(data, user_id)
        
        return created_response(ApplicationSchema().dump(application))


@applications_ns.route('/my')
class MyApplications(Resource):
    @applications_ns.doc('my_applications')
    @jwt_required()
    def get(self):
        """Получение списка заявок текущего врача"""
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        
        if claims.get('user_type') != 'doctor':
            return error_response('Only doctors can access their applications', 403)
        
        filters = {'status': request.args.get('status')}
        query = ApplicationService.get_applications_by_doctor(user_id, filters)
        result = paginate_query(query, ApplicationSchema())
        
        return list_response(result['items'], result['meta'])


@applications_ns.route('/<int:id>')
@applications_ns.param('id', 'ID заявки')
class ApplicationResource(Resource):
    @applications_ns.doc('get_application')
    @jwt_required()
    def get(self, id):
        """Получение деталей заявки"""
        application = ApplicationService.get_application_by_id(id)
        if not application:
            return error_response('Application not found', 404)
        
        return success_response(ApplicationSchema().dump(application))
    
    @applications_ns.doc('update_application')
    @jwt_required()
    def patch(self, id):
        """Частичное обновление заявки"""
        try:
            data = ApplicationUpdateSchema().load(request.get_json(), partial=True)
        except ValidationError as err:
            return validation_error_response(err.messages)
        
        # Проверка прав (врач может менять только свои заявки)
        claims = get_jwt()
        user_id = int(get_jwt_identity())
        application = ApplicationService.get_application_by_id(id)
        
        if not application:
            return error_response('Application not found', 404)
            
        if claims.get('user_type') != 'admin' and application.user_id != user_id:
            return error_response('Access denied', 403)
        
        try:
            application = ApplicationService.update_application(id, data)
        except ValueError as e:
            return error_response(str(e), 404)
        
        return success_response(ApplicationSchema().dump(application))
    
    @applications_ns.doc('delete_application')
    @jwt_required()
    @admin_required
    def delete(self, id):
        """Удаление заявки (только admin)"""
        try:
            ApplicationService.delete_application(id)
        except ValueError as e:
            return error_response(str(e), 404)
        return no_content_response()


@applications_ns.route('/<int:id>/disinfection')
@applications_ns.param('id', 'ID заявки')
class ApplicationDisinfection(Resource):
    @applications_ns.doc('get_disinfection_data')
    @jwt_required()
    def get(self, id):
        """Получение данных дезинфекции"""
        disinfection = DisinfectionService.get_disinfection_data(id)
        if not disinfection:
            return error_response('Disinfection data not found', 404)
        return success_response(DisinfectionSchema().dump(disinfection))
    
    @applications_ns.doc('update_disinfection_data')
    @jwt_required()
    @disinfector_required
    def put(self, id):
        """Обновление данных дезинфекции"""
        try:
            data = DisinfectionCreateSchema().load(request.get_json())
        except ValidationError as err:
            return validation_error_response(err.messages)
        
        user_id = int(get_jwt_identity())
        
        try:
            disinfection = DisinfectionService.create_or_update_disinfection_data(id, data, user_id)
            return success_response(DisinfectionSchema().dump(disinfection))
        except ValueError as e:
            return error_response(str(e), 404)