"""
Бизнес-логика для справочников.
"""
from app.domain.models.application.entities import (
    Area, Doctor, Disinfector, Diagnosis, EpidemicFocus
)
from app.core.extensions import db


class ReferencesService:
    """Сервис для работы со справочниками"""
    
    # ==================== AREA METHODS ====================
    
    @staticmethod
    def get_all_areas():
        """Получить все участки"""
        return Area.query.order_by(Area.name_area).all()
    
    @staticmethod
    def get_area_by_id(area_id: int):
        """Получить участок по ID"""
        return db.session.get(Area, area_id)
    
    @staticmethod
    def create_area(data: dict):
        """Создать новый участок"""
        area = Area(name_area=data['name_area'])
        db.session.add(area)
        db.session.commit()
        return area
    
    @staticmethod
    def update_area(area_id: int, data: dict):
        """Обновить участок"""
        area = db.session.get(Area, area_id)
        if not area:
            raise ValueError('Area not found')
        
        if 'name_area' in data:
            area.name_area = data['name_area']
        
        db.session.commit()
        return area
    
    @staticmethod
    def delete_area(area_id: int):
        """Удалить участок"""
        area = db.session.get(Area, area_id)
        if not area:
            raise ValueError('Area not found')
        
        # Проверяем, что участок не используется
        if area.doctors or area.applications:
            raise ValueError('Cannot delete area: it is being used by doctors or applications')
        
        db.session.delete(area)
        db.session.commit()
        return True
    
    # ==================== DOCTOR METHODS ====================
    
    @staticmethod
    def get_all_doctors():
        """Получить всех врачей"""
        return Doctor.query.order_by(Doctor.full_name).all()
    
    @staticmethod
    def get_doctor_by_id(doctor_id: int):
        """Получить врача по ID"""
        return db.session.get(Doctor, doctor_id)
    
    @staticmethod
    def create_doctor(data: dict):
        """Создать нового врача"""
        doctor = Doctor(
            full_name=data['full_name'],
            area_id=data['area_id']
        )
        db.session.add(doctor)
        db.session.commit()
        return doctor
    
    @staticmethod
    def update_doctor(doctor_id: int, data: dict):
        """Обновить врача"""
        doctor = db.session.get(Doctor, doctor_id)
        if not doctor:
            raise ValueError('Doctor not found')
        
        if 'full_name' in data:
            doctor.full_name = data['full_name']
        if 'area_id' in data:
            doctor.area_id = data['area_id']
        
        db.session.commit()
        return doctor
    
    @staticmethod
    def delete_doctor(doctor_id: int):
        """Удалить врача"""
        doctor = db.session.get(Doctor, doctor_id)
        if not doctor:
            raise ValueError('Doctor not found')
        
        # Проверяем, что врач не используется
        if doctor.applications:
            raise ValueError('Cannot delete doctor: it is being used by applications')
        
        db.session.delete(doctor)
        db.session.commit()
        return True
    
    # ==================== DISINFECTOR METHODS ====================
    
    @staticmethod
    def get_all_disinfectors():
        """Получить всех дезинфекторов"""
        return Disinfector.query.order_by(Disinfector.full_name).all()
    
    @staticmethod
    def get_disinfector_by_id(disinfector_id: int):
        """Получить дезинфектора по ID"""
        return db.session.get(Disinfector, disinfector_id)
    
    @staticmethod
    def create_disinfector(data: dict):
        """Создать нового дезинфектора"""
        disinfector = Disinfector(full_name=data['full_name'])
        db.session.add(disinfector)
        db.session.commit()
        return disinfector
    
    @staticmethod
    def update_disinfector(disinfector_id: int, data: dict):
        """Обновить дезинфектора"""
        disinfector = db.session.get(Disinfector, disinfector_id)
        if not disinfector:
            raise ValueError('Disinfector not found')
        
        if 'full_name' in data:
            disinfector.full_name = data['full_name']
        
        db.session.commit()
        return disinfector
    
    @staticmethod
    def delete_disinfector(disinfector_id: int):
        """Удалить дезинфектора"""
        disinfector = db.session.get(Disinfector, disinfector_id)
        if not disinfector:
            raise ValueError('Disinfector not found')
        
        # Проверяем, что дезинфектор не используется
        if disinfector.disinfections:
            raise ValueError('Cannot delete disinfector: it is being used by disinfections')
        
        db.session.delete(disinfector)
        db.session.commit()
        return True
    
    # ==================== DIAGNOSIS METHODS ====================
    
    @staticmethod
    def get_all_diagnoses():
        """Получить все диагнозы"""
        return Diagnosis.query.order_by(Diagnosis.mkb_code).all()
    
    @staticmethod
    def get_diagnosis_by_id(diagnosis_id: int):
        """Получить диагноз по ID"""
        return db.session.get(Diagnosis, diagnosis_id)
    
    @staticmethod
    def create_diagnosis(data: dict):
        """Создать новый диагноз"""
        diagnosis = Diagnosis(
            mkb_code=data['mkb_code'],
            name=data['name']
        )
        db.session.add(diagnosis)
        db.session.commit()
        return diagnosis
    
    @staticmethod
    def update_diagnosis(diagnosis_id: int, data: dict):
        """Обновить диагноз"""
        diagnosis = db.session.get(Diagnosis, diagnosis_id)
        if not diagnosis:
            raise ValueError('Diagnosis not found')
        
        if 'mkb_code' in data:
            diagnosis.mkb_code = data['mkb_code']
        if 'name' in data:
            diagnosis.name = data['name']
        
        db.session.commit()
        return diagnosis
    
    @staticmethod
    def delete_diagnosis(diagnosis_id: int):
        """Удалить диагноз"""
        diagnosis = db.session.get(Diagnosis, diagnosis_id)
        if not diagnosis:
            raise ValueError('Diagnosis not found')
        
        # Проверяем, что диагноз не используется
        if diagnosis.applications:
            raise ValueError('Cannot delete diagnosis: it is being used by applications')
        
        db.session.delete(diagnosis)
        db.session.commit()
        return True
    
    # ==================== EPIDEMIC FOCUS METHODS ====================
    
    @staticmethod
    def get_all_epidemic_focuses():
        """Получить все эпидемические очаги"""
        return EpidemicFocus.query.order_by(EpidemicFocus.name).all()
    
    @staticmethod
    def get_epidemic_focus_by_id(focus_id: int):
        """Получить эпидемический очаг по ID"""
        return db.session.get(EpidemicFocus, focus_id)
    
    @staticmethod
    def create_epidemic_focus(data: dict):
        """Создать новый эпидемический очаг"""
        focus = EpidemicFocus(name=data['name'])
        db.session.add(focus)
        db.session.commit()
        return focus
    
    @staticmethod
    def update_epidemic_focus(focus_id: int, data: dict):
        """Обновить эпидемический очаг"""
        focus = db.session.get(EpidemicFocus, focus_id)
        if not focus:
            raise ValueError('EpidemicFocus not found')
        
        if 'name' in data:
            focus.name = data['name']
        
        db.session.commit()
        return focus
    
    @staticmethod
    def delete_epidemic_focus(focus_id: int):
        """Удалить эпидемический очаг"""
        focus = db.session.get(EpidemicFocus, focus_id)
        if not focus:
            raise ValueError('EpidemicFocus not found')
        
        # Проверяем, что очаг не используется
        if focus.applications:
            raise ValueError('Cannot delete epidemic focus: it is being used by applications')
        
        db.session.delete(focus)
        db.session.commit()
        return True