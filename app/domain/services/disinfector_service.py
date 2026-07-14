from typing import List, Optional
from ...core.extensions import db
from ..models.application.entities import Disinfector, Disinfection

class DisinfectorService:
    
    @staticmethod
    def get_or_create_disinfector(full_name: str) -> Disinfector:
        """Находит дезинфектора в справочнике или создаёт нового."""
        if not full_name or not full_name.strip():
            return None
        
        # Ищем дезинфектора с таким ФИО
        disinfector = Disinfector.query.filter_by(
            full_name=full_name.strip()
        ).first()
        
        if disinfector:
            return disinfector
        
        # Создаём нового дезинфектора
        disinfector = Disinfector(full_name=full_name.strip())
        db.session.add(disinfector)
        db.session.flush()
        return disinfector
    
    @staticmethod
    def parse_disinfectors_input(input_str: str) -> List[Disinfector]:
        """Парсит строку с дезинфекторами и возвращает список объектов."""
        if not input_str or not input_str.strip():
            return []
        
        disinfectors = []
        # Разделяем по запятой или точке с запятой
        names = [name.strip() for name in input_str.replace(';', ',').split(',') if name.strip()]
        
        for name in names:
            disinfector = DisinfectorService.get_or_create_disinfector(name)
            if disinfector:
                disinfectors.append(disinfector)
        
        return disinfectors
    
    @staticmethod
    def search_disinfectors(query: str, limit: int = 10):
        """Поиск дезинфекторов по ФИО"""
        if not query or len(query.strip()) < 2:
            return []
        
        search_term = f"%{query.strip()}%"
        disinfectors = Disinfector.query.filter(
            Disinfector.full_name.ilike(search_term)
        ).limit(limit).all()
        
        return [{
            'id': d.id,
            'full_name': d.full_name,
            'value': d.full_name
        } for d in disinfectors]
    
    @staticmethod
    def get_all_disinfectors():
        """Получить всех дезинфекторов"""
        return Disinfector.query.order_by(Disinfector.full_name).all()
    
    @staticmethod
    def update_disinfection_disinfectors(disinfection: Disinfection, disinfectors_input: str):
        """Обновляет связь дезинфекции с дезинфекторами"""
        
        input_str = disinfectors_input.strip() if disinfectors_input else ""
        # Очищаем текущие связи
        disinfection.disinfectors.clear()
        
        # Парсим и добавляем новых дезинфекторов
        disinfectors = DisinfectorService.parse_disinfectors_input(input_str)
        disinfection.disinfectors.extend(disinfectors)