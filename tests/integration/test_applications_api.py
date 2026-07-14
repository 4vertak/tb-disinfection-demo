import pytest
from datetime import datetime, timedelta


class TestApplicationsAPI:
    """Integration тесты для Applications API"""
    
    def test_get_applications_list(self, client, auth_headers, applications):
        """Тест получения списка заявок"""
        
        response = client.get('/api/v1/applications/', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'items' in data['data']
        assert 'meta' in data['data']
        assert len(data['data']['items']) > 0
    
    def test_get_applications_filter_by_status(self, client, auth_headers, applications):
        """Тест фильтрации по статусу (используем реальные статусы из БД)"""

        response = client.get('/api/v1/applications/?status=incompleted', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        for app in data['data']['items']:
            assert app['status'] == 'incompleted'
    
    def test_get_applications_search(self, client, auth_headers, applications):
        """Тест поиска заявок"""

        response = client.get('/api/v1/applications/?search=Иванов', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']['items']) > 0
    
    def test_get_application_by_id(self, client, auth_headers, application):
        """Тест получения заявки по ID"""
        response = client.get(f'/api/v1/applications/{application.id}', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['id'] == application.id
    
    def test_get_application_not_found(self, client, auth_headers):
        """Тест получения несуществующей заявки"""
        response = client.get('/api/v1/applications/99999', headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_create_application_as_doctor(self, client, doctor_auth_headers, diagnosis, area, focus):
        """Тест создания заявки врачом"""

        response = client.post('/api/v1/applications/',
            headers=doctor_auth_headers,
            json={
                'patient_full_name': 'Иванов Иван Иванович',
                'birth_date': '1990-01-15',
                'address': 'г. Якутск, ул. Ленина, д. 1',
                'contact_phone': '+79141234567',
                'relative_contact_phone': '+79147654321',
                'workplace': 'ООО "Тест"',
                'position': 'Инженер',
                'diagnosis_id': diagnosis.id,
                'gdu': '123',
                'focus_id': focus.id,
                'area_id': area.id,
                'reason_application': 'hospitalization',
                'doctor_full_name': 'Доктор Тестов Т.Т.'
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['data']['patient_full_name'] == 'Иванов Иван Иванович'
        assert data['data']['contact_phone'] == '+79141234567'
        assert data['data']['workplace'] == 'ООО "Тест"'
        assert data['data']['status'] == 'incompleted'  # ← Legacy статус
        assert data['data']['reason_application'] == 'hospitalization'
    
    def test_create_application_validation_error(self, client, doctor_auth_headers):
        """Тест создания заявки с ошибкой валидации"""

        response = client.post('/api/v1/applications/',
            headers=doctor_auth_headers,
            json={
                'patient_full_name': '',
                'contact_phone': '+79001234567',
                'address': 'г. Москва'
            }
        )
        assert response.status_code in [400, 422]
    
    def test_update_application(self, client, doctor_auth_headers, application):
        """Тест обновления заявки"""

        response = client.patch(f'/api/v1/applications/{application.id}', headers=doctor_auth_headers, json={
            'status': 'completed',
            'gdu': '456'
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['status'] == 'completed'
    
    def test_complete_application_via_disinfection(self, client, disinfector_auth_headers, application, disinfector):
        """Завершение заявки через добавление данных дезинфекции """

        response = client.put(f'/api/v1/applications/{application.id}/disinfection',
            headers=disinfector_auth_headers,
            json={
                'disinfection_date': datetime.utcnow().isoformat(),
                'area_size': 45.5,
                'volume_size': 120.0,
                'spraying_time': '45 мин',
                'swab_testing': 3,
                'disinfector_ids': [disinfector.id]
            }
        )
        assert response.status_code in [200, 201]
        
        get_response = client.get(f'/api/v1/applications/{application.id}', 
                                headers=disinfector_auth_headers)
        assert get_response.get_json()['data']['status'] == 'completed'
    
    def test_delete_application_as_admin(self, client, admin_auth_headers, application):
        """Тест удаления заявки администратором"""

        response = client.delete(f'/api/v1/applications/{application.id}', headers=admin_auth_headers)
        
        assert response.status_code == 204
    
    def test_delete_application_as_doctor_forbidden(self, client, doctor_auth_headers, application):
        """Тест удаления заявки врачом (должно быть запрещено)"""

        response = client.delete(f'/api/v1/applications/{application.id}', headers=doctor_auth_headers)
        
        assert response.status_code == 403
    
    def test_get_my_applications(self, client, doctor_auth_headers, applications):
        """Тест получения своих заявок"""
        response = client.get('/api/v1/applications/my', headers=doctor_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']['items']) > 0
    
    def test_create_disinfection_data(self, client, disinfector_auth_headers, application, disinfector):
        """Тест создания данных дезинфекции"""

        response = client.put(f'/api/v1/applications/{application.id}/disinfection',
            headers=disinfector_auth_headers,
            json={
                'disinfection_date': datetime.utcnow().isoformat(),
                'area_size': 50.0,
                'volume_size': 150.0,
                'spraying_time': '30 мин',
                'swab_testing': 5,
                'disinfector_ids': [disinfector.id]
            }
        )
        assert response.status_code in [200, 201]
        data = response.get_json()
        assert data['data']['area_size'] == 50.0
    
    def test_get_disinfection_data(self, client, auth_headers, application, disinfection_data):
        """Тест получения данных дезинфекции"""

        response = client.get(f'/api/v1/applications/{application.id}/disinfection', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['application_id'] == application.id