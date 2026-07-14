import pytest
import uuid


class TestReferencesAPI:
    """Integration тесты для References API"""
    
    # ==================== AREA TESTS ====================
    
    def test_get_areas_list(self, client, auth_headers):
        """Тест получения списка участков"""
        response = client.get('/api/v1/references/areas', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'items' in data['data']
        assert len(data['data']['items']) > 0
    
    def test_create_area_as_admin(self, client, admin_auth_headers):
        """Тест создания участка администратором"""
        unique_name = f'Участок_{uuid.uuid4().hex[:8]}'
        
        response = client.post('/api/v1/references/areas',
            headers=admin_auth_headers,
            json={'name_area': unique_name}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['data']['name_area'] == unique_name
    
    def test_create_area_as_doctor_forbidden(self, client, doctor_auth_headers):
        """Тест создания участка врачом (должно быть запрещено)"""
        response = client.post('/api/v1/references/areas',
            headers=doctor_auth_headers,
            json={'name_area': 'Новый участок'}
        )
        
        assert response.status_code == 403
    
    def test_update_area(self, client, admin_auth_headers):
        """Тест обновления участка"""
        # Создаём участок
        unique_name = f'Участок_{uuid.uuid4().hex[:8]}'
        create_response = client.post('/api/v1/references/areas',
            headers=admin_auth_headers,
            json={'name_area': unique_name}
        )
        area_id = create_response.get_json()['data']['id']
        
        # Обновляем
        new_name = f'Обновлённый_{uuid.uuid4().hex[:8]}'
        response = client.patch(f'/api/v1/references/areas/{area_id}',
            headers=admin_auth_headers,
            json={'name_area': new_name}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['name_area'] == new_name
    
    def test_delete_area(self, client, admin_auth_headers):
        """Тест удаления участка"""
        # Создаём участок
        unique_name = f'Участок_{uuid.uuid4().hex[:8]}'
        create_response = client.post('/api/v1/references/areas',
            headers=admin_auth_headers,
            json={'name_area': unique_name}
        )
        area_id = create_response.get_json()['data']['id']
        
        # Удаляем
        response = client.delete(f'/api/v1/references/areas/{area_id}',
            headers=admin_auth_headers
        )
        
        assert response.status_code == 204
        
        # Проверяем, что участок удалён
        get_response = client.get(f'/api/v1/references/areas/{area_id}',
            headers=admin_auth_headers
        )
        assert get_response.status_code == 404
    
    # ==================== DOCTOR TESTS ====================
    
    def test_get_doctors_list(self, client, auth_headers):
        """Тест получения списка врачей"""
        response = client.get('/api/v1/references/doctors', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'items' in data['data']
    
    def test_create_doctor_as_admin(self, client, admin_auth_headers):
        """Тест создания врача администратором"""
        unique_name = f'Доктор {uuid.uuid4().hex[:8]}'
        
        # Получаем первый участок
        areas_response = client.get('/api/v1/references/areas', headers=admin_auth_headers)
        area_id = areas_response.get_json()['data']['items'][0]['id']
        
        response = client.post('/api/v1/references/doctors',
            headers=admin_auth_headers,
            json={
                'full_name': unique_name,
                'area_id': area_id
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['data']['full_name'] == unique_name
        assert data['data']['area_id'] == area_id
    
    # ==================== DIAGNOSIS TESTS ====================
    
    def test_get_diagnoses_list(self, client, auth_headers):
        """Тест получения списка диагнозов"""
        response = client.get('/api/v1/references/diagnoses', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'items' in data['data']
        assert len(data['data']['items']) > 0
    
    def test_create_diagnosis_as_admin(self, client, admin_auth_headers):
        """Тест создания диагноза администратором"""
        unique_code = f'X{uuid.uuid4().hex[:4]}'
        
        response = client.post('/api/v1/references/diagnoses',
            headers=admin_auth_headers,
            json={
                'mkb_code': unique_code,
                'name': f'Тестовый диагноз {unique_code}'
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['data']['mkb_code'] == unique_code
    
    # ==================== EPIDEMIC FOCUS TESTS ====================
    
    def test_get_epidemic_focuses_list(self, client, auth_headers):
        """Тест получения списка эпидемических очагов"""
        response = client.get('/api/v1/references/epidemic-focuses', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'items' in data['data']
        assert len(data['data']['items']) > 0
    
    def test_create_epidemic_focus_as_admin(self, client, admin_auth_headers):
        """Тест создания эпидемического очага администратором"""
        unique_name = f'Очаг_{uuid.uuid4().hex[:8]}'
        
        response = client.post('/api/v1/references/epidemic-focuses',
            headers=admin_auth_headers,
            json={'name': unique_name}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['data']['name'] == unique_name


class TestGduGroupsAPI:
    """Integration тесты для GDU Groups API"""
    
    def test_get_gdu_groups_empty(self, client, auth_headers):
        """Тест получения списка ГДУ групп (пустой список, если нет заявок)"""
        response = client.get('/api/v1/references/gdu-groups', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert isinstance(data['data'], list)
    
    def test_get_gdu_groups_with_data(self, client, auth_headers, db_session, test_user):
        """Тест получения списка ГДУ групп с данными"""
        from app.domain.models.application.entities import Application, Diagnosis, EpidemicFocus, Area
        from datetime import datetime, date
        
        # 1. Создаем необходимые справочники
        area = Area(name_area='Тестовый участок для ГДУ')
        db_session.add(area)
        
        # Используем уникальные значения, чтобы не конфликтовать с fill_directories
        diagnosis = Diagnosis(mkb_code='T99.9', name='Тестовый диагноз для ГДУ')
        db_session.add(diagnosis)
        
        focus = EpidemicFocus(name='Тестовый очаг ГДУ')
        db_session.add(focus)
        
        db_session.commit()
        
        # 2. Создаем заявки с разными ГДУ
        app1 = Application(
            user_id=test_user.id,
            submission_date=datetime.now(),
            patient_full_name='Пациент 1',
            birth_date=date(1990, 1, 1),
            address='Адрес 1',
            diagnosis_id=diagnosis.id,
            gdu='IА',
            focus_id=focus.id,
            area_id=area.id,
            reason_application='hospitalization',
            status='incompleted'
        )
        app2 = Application(
            user_id=test_user.id,
            submission_date=datetime.now(),
            patient_full_name='Пациент 2',
            birth_date=date(1985, 1, 1),
            address='Адрес 2',
            diagnosis_id=diagnosis.id,
            gdu='IIБ',
            focus_id=focus.id,
            area_id=area.id,
            reason_application='hospitalization',
            status='incompleted'
        )
        
        db_session.add_all([app1, app2])
        db_session.commit()
        
        # 3. Выполняем запрос к API
        response = client.get('/api/v1/references/gdu-groups', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        
        # 4. Проверяем, что наши ГДУ есть в списке
        gdu_values = [item['text'] for item in data['data'] if 'text' in item]
        assert 'IА' in gdu_values
        assert 'IIБ' in gdu_values
    
    def test_get_gdu_groups_unauthorized(self, client):
        """Тест получения списка ГДУ групп без авторизации"""
        response = client.get('/api/v1/references/gdu-groups')
        
        # Должен вернуть 401 Unauthorized
        assert response.status_code == 401