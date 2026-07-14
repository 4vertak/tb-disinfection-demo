import pytest
import uuid

class TestUsersAPI:
    """Integration тесты для Users API"""
    
    def test_get_users_list(self, client, auth_headers, users):
        """Тест получения списка пользователей"""

        response = client.get('/api/v1/users/', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'items' in data['data']
        assert 'meta' in data['data']
        assert len(data['data']['items']) > 0
    
    def test_get_users_list_with_pagination(self, client, auth_headers, users):
        """Тест пагинации списка пользователей"""

        response = client.get('/api/v1/users/?page=1&per_page=5', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['meta']['page'] == 1
        assert data['data']['meta']['per_page'] == 5
    
    def test_get_users_list_filter_by_type(self, client, auth_headers, users):
        """Тест фильтрации по типу пользователя"""

        response = client.get('/api/v1/users/?user_type=doctor', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        for user in data['data']['items']:
            assert user['user_type'] == 'doctor'
    
    def test_get_users_list_search(self, client, auth_headers, users):
        """Тест поиска пользователей"""
        response = client.get('/api/v1/users/?search=doctor', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']['items']) > 0
    
    def test_get_user_by_id(self, client, auth_headers, user):
        """Тест получения пользователя по ID"""

        response = client.get(f'/api/v1/users/{user.id}', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['id'] == user.id
        assert data['data']['login'] == user.login
    
    def test_get_user_not_found(self, client, auth_headers):
        """Тест получения несуществующего пользователя"""

        response = client.get('/api/v1/users/99999', headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_create_user_as_admin(self, client, admin_auth_headers):
        """Тест создания пользователя администратором"""

        unique_login = f'newdoctor_{uuid.uuid4().hex[:8]}'

        response = client.post('/api/v1/users/',
            headers=admin_auth_headers,
            json={
                'login': unique_login,
                'password': 'password123',
                'name': 'New Doctor',
                'user_type': 'doctor'
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['data']['login'] == unique_login
        assert data['data']['user_type'] == 'doctor'
    
    def test_create_user_duplicate_login(self, client, admin_auth_headers, user):
        """Тест создания пользователя с дублирующимся логином"""

        response = client.post('/api/v1/users/',
            headers=admin_auth_headers,
            json={
                'login': user.login,
                'password': 'password123',
                'name': 'Duplicate User',
                'user_type': 'doctor'
            }
        )
        
        assert response.status_code == 422
    
    def test_create_user_as_doctor_forbidden(self, client, doctor_auth_headers):
        """Тест создания пользователя врачом (должно быть запрещено)"""

        response = client.post('/api/v1/users/',
            headers=doctor_auth_headers,
            json={
                'login': 'newuser',
                'password': 'password123',
                'name': 'New User',
                'user_type': 'doctor'
            }
        )
        
        assert response.status_code == 403
    
    def test_update_user(self, client, admin_auth_headers, user):
        """Тест обновления пользователя"""

        response = client.patch(f'/api/v1/users/{user.id}',
            headers=admin_auth_headers,
            json={
                'name': 'Updated Name'
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['name'] == 'Updated Name'
    
    def test_update_user_not_found(self, client, admin_auth_headers):
        """Тест обновления несуществующего пользователя"""

        response = client.patch('/api/v1/users/99999',
            headers=admin_auth_headers,
            json={
                'name': 'Updated Name'
            }
        )
        
        assert response.status_code == 404
    
    def test_delete_user(self, client, admin_auth_headers, user):
        """Тест удаления пользователя"""

        response = client.delete(f'/api/v1/users/{user.id}', headers=admin_auth_headers)
        
        assert response.status_code == 204
        
        # Проверяем, что пользователь удалён
        get_response = client.get(f'/api/v1/users/{user.id}', headers=admin_auth_headers)
        assert get_response.status_code == 404
    
    def test_delete_user_not_found(self, client, admin_auth_headers):
        """Тест удаления несуществующего пользователя"""

        response = client.delete('/api/v1/users/99999', headers=admin_auth_headers)
        
        assert response.status_code == 404
    
    def test_get_doctors_list(self, client, auth_headers, users):
        """Тест получения списка врачей"""

        response = client.get('/api/v1/users/doctors', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        for user in data['data']['items']:
            assert user['user_type'] == 'doctor'
    
    def test_get_disinfectors_list(self, client, auth_headers, users):
        """Тест получения списка дезинфекторов"""
        
        response = client.get('/api/v1/users/disinfectors', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        for user in data['data']['items']:
            assert user['user_type'] == 'disinfector'