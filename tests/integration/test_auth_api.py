import pytest
import json


class TestAuthAPI:
    """Integration тесты для Auth API"""
    
    def test_login_success(self, client, user):
        """Тест успешного входа"""

        response = client.post('/api/v1/auth/login', json={
            'login': user.login,
            'password': 'testpass123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data['data']
        assert 'refresh_token' in data['data']
        assert data['data']['token_type'] == 'Bearer'
    
    def test_login_invalid_credentials(self, client, user):
        """Тест входа с неверными учетными данными"""

        response = client.post('/api/v1/auth/login', json={
            'login': user.login,
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['errors'][0]['message'] == 'Invalid credentials'
    
    def test_login_missing_fields(self, client):
        response = client.post('/api/v1/auth/login', json={
            'login': 'testuser'
        })
        # Flask-RESTX возвращает 400 при валидации через @expect
        assert response.status_code in [400, 422]
        
    def test_refresh_token(self, client, user):
        """Тест обновления access token"""

        # Сначала логинимся
        login_response = client.post('/api/v1/auth/login', json={
            'login': user.login,
            'password': 'testpass123'
        })
        refresh_token = login_response.get_json()['data']['refresh_token']
        
        # Обновляем токен
        response = client.post('/api/v1/auth/refresh', headers={
            'Authorization': f'Bearer {refresh_token}'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data['data']
    
    def test_get_current_user(self, client, user, auth_headers):
        """Тест получения информации о текущем пользователе"""

        response = client.get('/api/v1/auth/me', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['id'] == user.id
        assert data['data']['login'] == user.login
        assert data['data']['name'] == user.name
        assert data['data']['user_type'] == user.user_type
        assert 'area_id' not in data['data']
    
    def test_get_current_user_unauthorized(self, client):
        """Тест получения информации без авторизации"""

        response = client.get('/api/v1/auth/me')
        
        assert response.status_code == 401
    
    def test_change_password(self, client, user, auth_headers):
        """Тест смены пароля"""

        response = client.post('/api/v1/auth/change-password', 
            headers=auth_headers,
            json={
                'old_password': 'testpass123',
                'new_password': 'newpassword456'
            }
        )
        
        assert response.status_code == 200
        
        # Проверяем, что можно войти с новым паролем
        login_response = client.post('/api/v1/auth/login', json={
            'login': user.login,
            'password': 'newpassword456'
        })
        assert login_response.status_code == 200
    
    def test_change_password_invalid_old(self, client, user, auth_headers):
        """Тест смены пароля с неверным старым паролем"""

        response = client.post('/api/v1/auth/change-password',
            headers=auth_headers,
            json={
                'old_password': 'wrongpassword',
                'new_password': 'newpassword456'
            }
        )
        
        assert response.status_code == 400
    
    def test_register_user_as_admin(self, client, admin_auth_headers):
        """Тест регистрации пользователя администратором"""

        response = client.post('/api/v1/auth/register',
            headers=admin_auth_headers,
            json={
                'login': 'newdoctor',
                'password': 'testpass123',
                'name': 'New Doctor',
                'user_type': 'doctor'
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['data']['login'] == 'newdoctor'
        assert data['data']['user_type'] == 'doctor'
        assert 'area_id' not in data['data']
    
    def test_register_user_as_doctor_forbidden(self, client, doctor_auth_headers):
        """Тест регистрации пользователя врачом (должно быть запрещено)"""

        response = client.post('/api/v1/auth/register',
            headers=doctor_auth_headers,
            json={
                'login': 'newuser',
                'password': 'testpass123',
                'name': 'New User',
                'user_type': 'doctor'
            }
        )
        
        assert response.status_code == 403
    
    def test_logout(self, client, auth_headers):
        """Тест выхода из системы"""
        
        response = client.post('/api/v1/auth/logout', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['message'] == 'Successfully logged out'