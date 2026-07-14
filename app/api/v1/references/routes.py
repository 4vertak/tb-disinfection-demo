"""
REST API эндпоинты для справочников.
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from .schemas import (
    AreaSchema, AreaCreateSchema, AreaUpdateSchema,
    DoctorSchema, DoctorCreateSchema, DoctorUpdateSchema,
    DisinfectorSchema, DisinfectorCreateSchema, DisinfectorUpdateSchema,
    DiagnosisSchema, DiagnosisCreateSchema, DiagnosisUpdateSchema,
    EpidemicFocusSchema, EpidemicFocusCreateSchema, EpidemicFocusUpdateSchema
)
from .services import ReferencesService
from ..common.response import (
    success_response, created_response, no_content_response,
    error_response, validation_error_response, list_response
)
from ..common.decorators import admin_required

# Создание namespace
references_ns = Namespace('references', description='Справочники (участки, врачи, диагнозы и т.д.)')


# ==================== SWAGGER МОДЕЛИ ====================

area_model = references_ns.model('Area', {
    'id': fields.Integer(description='ID участка'),
    'name_area': fields.String(description='Название участка')
})

doctor_model = references_ns.model('Doctor', {
    'id': fields.Integer(description='ID врача'),
    'full_name': fields.String(description='ФИО врача'),
    'area_id': fields.Integer(description='ID участка'),
    'area': fields.Nested(area_model, description='Участок')
})

disinfector_model = references_ns.model('Disinfector', {
    'id': fields.Integer(description='ID дезинфектора'),
    'full_name': fields.String(description='ФИО дезинфектора')
})

diagnosis_model = references_ns.model('Diagnosis', {
    'id': fields.Integer(description='ID диагноза'),
    'mkb_code': fields.String(description='Код МКБ'),
    'name': fields.String(description='Название диагноза')
})

epidemic_focus_model = references_ns.model('EpidemicFocus', {
    'id': fields.Integer(description='ID очага'),
    'name': fields.String(description='Название очага')
})


# ==================== AREA ENDPOINTS ====================

@references_ns.route('/areas')
class AreaList(Resource):
    """Список участков"""
    
    @references_ns.doc('list_areas')
    @references_ns.response(200, 'Список участков')
    @jwt_required()
    def get(self):
        """Получить список всех участков"""
        areas = ReferencesService.get_all_areas()
        return list_response(AreaSchema(many=True).dump(areas), meta={'total': len(areas)})
    
    @references_ns.doc('create_area')
    @references_ns.response(201, 'Участок создан', area_model)
    @jwt_required()
    @admin_required
    def post(self):
        """Создать новый участок (только admin)"""
        try:
            data = AreaCreateSchema().load(request.get_json())
        except ValidationError as err:
            return validation_error_response(err.messages)
        
        area = ReferencesService.create_area(data)
        return created_response(AreaSchema().dump(area))


@references_ns.route('/areas/<int:id>')
@references_ns.param('id', 'ID участка')
class AreaResource(Resource):
    """Детали участка"""
    
    @references_ns.doc('get_area')
    @references_ns.response(200, 'Детали участка', area_model)
    @references_ns.response(404, 'Участок не найден')
    @jwt_required()
    def get(self, id):
        """Получить детали участка по ID"""
        area = ReferencesService.get_area_by_id(id)
        if not area:
            return error_response('Area not found', 404)
        
        return success_response(AreaSchema().dump(area))
    
    @references_ns.doc('update_area')
    @references_ns.response(200, 'Участок обновлён', area_model)
    @jwt_required()
    @admin_required
    def patch(self, id):
        """Обновить участок (только admin)"""
        try:
            data = AreaUpdateSchema().load(request.get_json(), partial=True)
        except ValidationError as err:
            return validation_error_response(err.messages)
        
        try:
            area = ReferencesService.update_area(id, data)
        except ValueError as e:
            return error_response(str(e), 404)
        
        return success_response(AreaSchema().dump(area))
    
    @references_ns.doc('delete_area')
    @references_ns.response(204, 'Участок удалён')
    @jwt_required()
    @admin_required
    def delete(self, id):
        """Удалить участок (только admin)"""
        try:
            ReferencesService.delete_area(id)
        except ValueError as e:
            return error_response(str(e), 400)
        
        return no_content_response()


# ==================== DOCTOR ENDPOINTS ====================

@references_ns.route('/doctors')
class DoctorList(Resource):
    """Список врачей"""
    
    @references_ns.doc('list_doctors')
    @references_ns.response(200, 'Список врачей')
    @jwt_required()
    def get(self):
        """Получить список всех врачей"""
        doctors = ReferencesService.get_all_doctors()
        return list_response(DoctorSchema(many=True).dump(doctors), meta={'total': len(doctors)})
    
    @references_ns.doc('create_doctor')
    @references_ns.response(201, 'Врач создан', doctor_model)
    @jwt_required()
    @admin_required
    def post(self):
        """Создать нового врача (только admin)"""
        try:
            data = DoctorCreateSchema().load(request.get_json())
        except ValidationError as err:
            return validation_error_response(err.messages)
        
        doctor = ReferencesService.create_doctor(data)
        return created_response(DoctorSchema().dump(doctor))


@references_ns.route('/doctors/<int:id>')
@references_ns.param('id', 'ID врача')
class DoctorResource(Resource):
    """Детали врача"""
    
    @references_ns.doc('get_doctor')
    @references_ns.response(200, 'Детали врача', doctor_model)
    @references_ns.response(404, 'Врач не найден')
    @jwt_required()
    def get(self, id):
        """Получить детали врача по ID"""
        doctor = ReferencesService.get_doctor_by_id(id)
        if not doctor:
            return error_response('Doctor not found', 404)
        
        return success_response(DoctorSchema().dump(doctor))
    
    @references_ns.doc('update_doctor')
    @references_ns.response(200, 'Врач обновлён', doctor_model)
    @jwt_required()
    @admin_required
    def patch(self, id):
        """Обновить врача (только admin)"""
        try:
            data = DoctorUpdateSchema().load(request.get_json(), partial=True)
        except ValidationError as err:
            return validation_error_response(err.messages)
        
        try:
            doctor = ReferencesService.update_doctor(id, data)
        except ValueError as e:
            return error_response(str(e), 404)
        
        return success_response(DoctorSchema().dump(doctor))
    
    @references_ns.doc('delete_doctor')
    @references_ns.response(204, 'Врач удалён')
    @jwt_required()
    @admin_required
    def delete(self, id):
        """Удалить врача (только admin)"""
        try:
            ReferencesService.delete_doctor(id)
        except ValueError as e:
            return error_response(str(e), 400)
        
        return no_content_response()


# ==================== DISINFECTOR ENDPOINTS ====================

@references_ns.route('/disinfectors')
class DisinfectorList(Resource):
    """Список дезинфекторов"""
    
    @references_ns.doc('list_disinfectors')
    @references_ns.response(200, 'Список дезинфекторов')
    @jwt_required()
    def get(self):
        """Получить список всех дезинфекторов"""
        disinfectors = ReferencesService.get_all_disinfectors()
        return list_response(DisinfectorSchema(many=True).dump(disinfectors), meta={'total': len(disinfectors)})
    
    @references_ns.doc('create_disinfector')
    @references_ns.response(201, 'Дезинфектор создан', disinfector_model)
    @jwt_required()
    @admin_required
    def post(self):
        """Создать нового дезинфектора (только admin)"""
        try:
            data = DisinfectorCreateSchema().load(request.get_json())
        except ValidationError as err:
            return validation_error_response(err.messages)
        
        disinfector = ReferencesService.create_disinfector(data)
        return created_response(DisinfectorSchema().dump(disinfector))


@references_ns.route('/disinfectors/<int:id>')
@references_ns.param('id', 'ID дезинфектора')
class DisinfectorResource(Resource):
    """Детали дезинфектора"""
    
    @references_ns.doc('get_disinfector')
    @references_ns.response(200, 'Детали дезинфектора', disinfector_model)
    @references_ns.response(404, 'Дезинфектор не найден')
    @jwt_required()
    def get(self, id):
        """Получить детали дезинфектора по ID"""
        disinfector = ReferencesService.get_disinfector_by_id(id)
        if not disinfector:
            return error_response('Disinfector not found', 404)
        
        return success_response(DisinfectorSchema().dump(disinfector))
    
    @references_ns.doc('update_disinfector')
    @references_ns.response(200, 'Дезинфектор обновлён', disinfector_model)
    @jwt_required()
    @admin_required
    def patch(self, id):
        """Обновить дезинфектора (только admin)"""
        try:
            data = DisinfectorUpdateSchema().load(request.get_json(), partial=True)
        except ValidationError as err:
            return validation_error_response(err.messages)
        
        try:
            disinfector = ReferencesService.update_disinfector(id, data)
        except ValueError as e:
            return error_response(str(e), 404)
        
        return success_response(DisinfectorSchema().dump(disinfector))
    
    @references_ns.doc('delete_disinfector')
    @references_ns.response(204, 'Дезинфектор удалён')
    @jwt_required()
    @admin_required
    def delete(self, id):
        """Удалить дезинфектора (только admin)"""
        try:
            ReferencesService.delete_disinfector(id)
        except ValueError as e:
            return error_response(str(e), 400)
        
        return no_content_response()


# ==================== DIAGNOSIS ENDPOINTS ====================

@references_ns.route('/diagnoses')
class DiagnosisList(Resource):
    """Список диагнозов"""
    
    @references_ns.doc('list_diagnoses')
    @references_ns.response(200, 'Список диагнозов')
    @jwt_required()
    def get(self):
        """Получить список всех диагнозов"""
        diagnoses = ReferencesService.get_all_diagnoses()
        return list_response(DiagnosisSchema(many=True).dump(diagnoses), meta={'total': len(diagnoses)})
    
    @references_ns.doc('create_diagnosis')
    @references_ns.response(201, 'Диагноз создан', diagnosis_model)
    @jwt_required()
    @admin_required
    def post(self):
        """Создать новый диагноз (только admin)"""
        try:
            data = DiagnosisCreateSchema().load(request.get_json())
        except ValidationError as err:
            return validation_error_response(err.messages)
        
        diagnosis = ReferencesService.create_diagnosis(data)
        return created_response(DiagnosisSchema().dump(diagnosis))


@references_ns.route('/diagnoses/<int:id>')
@references_ns.param('id', 'ID диагноза')
class DiagnosisResource(Resource):
    """Детали диагноза"""
    
    @references_ns.doc('get_diagnosis')
    @references_ns.response(200, 'Детали диагноза', diagnosis_model)
    @references_ns.response(404, 'Диагноз не найден')
    @jwt_required()
    def get(self, id):
        """Получить детали диагноза по ID"""
        diagnosis = ReferencesService.get_diagnosis_by_id(id)
        if not diagnosis:
            return error_response('Diagnosis not found', 404)
        
        return success_response(DiagnosisSchema().dump(diagnosis))
    
    @references_ns.doc('update_diagnosis')
    @references_ns.response(200, 'Диагноз обновлён', diagnosis_model)
    @jwt_required()
    @admin_required
    def patch(self, id):
        """Обновить диагноз (только admin)"""
        try:
            data = DiagnosisUpdateSchema().load(request.get_json(), partial=True)
        except ValidationError as err:
            return validation_error_response(err.messages)
        
        try:
            diagnosis = ReferencesService.update_diagnosis(id, data)
        except ValueError as e:
            return error_response(str(e), 404)
        
        return success_response(DiagnosisSchema().dump(diagnosis))
    
    @references_ns.doc('delete_diagnosis')
    @references_ns.response(204, 'Диагноз удалён')
    @jwt_required()
    @admin_required
    def delete(self, id):
        """Удалить диагноз (только admin)"""
        try:
            ReferencesService.delete_diagnosis(id)
        except ValueError as e:
            return error_response(str(e), 400)
        
        return no_content_response()


# ==================== EPIDEMIC FOCUS ENDPOINTS ====================

@references_ns.route('/epidemic-focuses')
class EpidemicFocusList(Resource):
    """Список эпидемических очагов"""
    
    @references_ns.doc('list_epidemic_focuses')
    @references_ns.response(200, 'Список эпидемических очагов')
    @jwt_required()
    def get(self):
        """Получить список всех эпидемических очагов"""
        focuses = ReferencesService.get_all_epidemic_focuses()
        return list_response(EpidemicFocusSchema(many=True).dump(focuses), meta={'total': len(focuses)})
    
    @references_ns.doc('create_epidemic_focus')
    @references_ns.response(201, 'Эпидемический очаг создан', epidemic_focus_model)
    @jwt_required()
    @admin_required
    def post(self):
        """Создать новый эпидемический очаг (только admin)"""
        try:
            data = EpidemicFocusCreateSchema().load(request.get_json())
        except ValidationError as err:
            return validation_error_response(err.messages)
        
        focus = ReferencesService.create_epidemic_focus(data)
        return created_response(EpidemicFocusSchema().dump(focus))


@references_ns.route('/epidemic-focuses/<int:id>')
@references_ns.param('id', 'ID эпидемического очага')
class EpidemicFocusResource(Resource):
    """Детали эпидемического очага"""
    
    @references_ns.doc('get_epidemic_focus')
    @references_ns.response(200, 'Детали эпидемического очага', epidemic_focus_model)
    @references_ns.response(404, 'Эпидемический очаг не найден')
    @jwt_required()
    def get(self, id):
        """Получить детали эпидемического очага по ID"""
        focus = ReferencesService.get_epidemic_focus_by_id(id)
        if not focus:
            return error_response('EpidemicFocus not found', 404)
        
        return success_response(EpidemicFocusSchema().dump(focus))
    
    @references_ns.doc('update_epidemic_focus')
    @references_ns.response(200, 'Эпидемический очаг обновлён', epidemic_focus_model)
    @jwt_required()
    @admin_required
    def patch(self, id):
        """Обновить эпидемический очаг (только admin)"""
        try:
            data = EpidemicFocusUpdateSchema().load(request.get_json(), partial=True)
        except ValidationError as err:
            return validation_error_response(err.messages)
        
        try:
            focus = ReferencesService.update_epidemic_focus(id, data)
        except ValueError as e:
            return error_response(str(e), 404)
        
        return success_response(EpidemicFocusSchema().dump(focus))
    
    @references_ns.doc('delete_epidemic_focus')
    @references_ns.response(204, 'Эпидемический очаг удалён')
    @jwt_required()
    @admin_required
    def delete(self, id):
        """Удалить эпидемический очаг (только admin)"""
        try:
            ReferencesService.delete_epidemic_focus(id)
        except ValueError as e:
            return error_response(str(e), 400)
        
        return no_content_response()


# ==================== GDU GROUPS ENDPOINTS ====================

@references_ns.route('/gdu-groups')
class GduGroupsList(Resource):
    """Список ГДУ групп (Группа диспансерного учёта)"""
    
    @references_ns.doc('list_gdu_groups')
    @references_ns.response(200, 'Список ГДУ групп')
    @jwt_required()
    def get(self):
        """
        Получить список уникальных ГДУ групп из существующих заявок.
        
        Возвращает список всех уникальных значений ГДУ, 
        которые используются в созданных заявках.
        """
        from app.domain.services.application_api_service import ApplicationApiService
        
        # Получаем список ГДУ
        # Возвращает JSON response, нужно извлечь данные
        response = ApplicationApiService.get_gdu_list()
        
        # Извлекаем данные из JSON response
        if hasattr(response, 'get_json'):
            gdu_list = response.get_json()
        else:
            gdu_list = []
        
        return success_response(gdu_list)