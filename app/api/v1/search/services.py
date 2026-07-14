"""
Бизнес-логика для поиска (обертка))).
"""
from app.domain.services.application_service import ApplicationService
from app.domain.services.disinfector_service import DisinfectorService


class SearchApiService:
    """Сервис для поиска через API"""
    
    @staticmethod
    def search_doctors(query: str, limit: int = 10):
        """
        Поиск врачей по ФИО.
        Возвращает список словарей для select2.
        """
        return ApplicationService.search_doctors(query, limit)
        
    @staticmethod
    def search_disinfectors(query: str, limit: int = 10):
        """
        Поиск дезинфекторов по ФИО.
        Возвращает список словарей для select2.
        """
        return DisinfectorService.search_disinfectors(query, limit)