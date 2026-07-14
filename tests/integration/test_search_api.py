"""
Интеграционные тесты для Search API (autocomplete).
"""
import pytest


class TestSearchAPI:
    """Integration тесты для Search API"""
    
    def test_search_doctors_empty_query(self, client, auth_headers):
        """Тест поиска врачей с коротким запросом (возвращает пустой список)"""
        response = client.get('/api/v1/search/doctors?q=А', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['data'] == []

    def test_search_doctors_success(self, client, auth_headers, db_session):
        """Тест успешного поиска врачей"""
        from app.domain.models.application.entities import Doctor, Area
        
        # Создаем участок и врача
        area = Area(name_area='Тестовый участок')
        db_session.add(area)
        db_session.commit()
        
        doctor = Doctor(full_name='Иванов Иван Иванович', area_id=area.id)
        db_session.add(doctor)
        db_session.commit()
        
        response = client.get('/api/v1/search/doctors?q=Иванов', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) == 1
        assert data['data'][0]['value'] == 'Иванов Иван Иванович'
        assert data['data'][0]['area_name'] == 'Тестовый участок'

    def test_search_disinfectors_empty_query(self, client, auth_headers):
        """Тест поиска дезинфекторов с коротким запросом"""
        response = client.get('/api/v1/search/disinfectors?q=А', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['data'] == []

    def test_search_disinfectors_success(self, client, auth_headers, db_session):
        """Тест успешного поиска дезинфекторов"""
        from app.domain.models.application.entities import Disinfector
        
        disinfector = Disinfector(full_name='Петров Петр Петрович')
        db_session.add(disinfector)
        db_session.commit()
        
        response = client.get('/api/v1/search/disinfectors?q=Петров', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) == 1
        assert data['data'][0]['full_name'] == 'Петров Петр Петрович'
        assert data['data'][0]['value'] == 'Петров Петр Петрович'
        assert data['data'][0]['id'] == disinfector.id