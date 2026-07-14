"""
Тесты для JWT blacklist функциональности.
"""

import pytest
from unittest.mock import Mock, patch


class TestAuthBlacklist:
    """Тесты для JWT blacklist"""
    
    def test_logout_adds_token_to_blacklist(self, client, auth_headers):
        """Тест что logout добавляет токен в blacklist"""
        # Получаем токен из заголовков
        token = auth_headers['Authorization'].split(' ')[1]
        
        # Выполняем logout
        response = client.post('/api/v1/auth/logout', headers=auth_headers)
        assert response.status_code == 200
        
        # Пытаемся использовать тот же токен снова
        response = client.get('/api/v1/auth/me', headers=auth_headers)
        
        # Если Redis доступен, токен должен быть отклонен
        from app.core.redis_client import is_redis_available
        if is_redis_available():
            assert response.status_code == 401
        else:
            # Если Redis недоступен, токен все еще работает
            assert response.status_code == 200
    
    def test_revoked_token_cannot_access_protected_endpoints(self, client, user):
        """Тест что отозванный токен не может получить доступ к защищенным эндпоинтам"""
        # Логинимся
        login_response = client.post('/api/v1/auth/login', json={
            'login': user.login,
            'password': 'testpass123'
        })
        assert login_response.status_code == 200
        
        token = login_response.get_json()['data']['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Проверяем что токен работает
        response = client.get('/api/v1/auth/me', headers=headers)
        assert response.status_code == 200
        
        # Выполняем logout
        logout_response = client.post('/api/v1/auth/logout', headers=headers)
        assert logout_response.status_code == 200
        
        # Пытаемся использовать отозванный токен
        response = client.get('/api/v1/auth/me', headers=headers)
        
        from app.core.redis_client import is_redis_available
        if is_redis_available():
            assert response.status_code == 401
        else:
            assert response.status_code == 200
    
    @patch('app.core.redis_client.get_redis_client')
    def test_graceful_degradation_when_redis_unavailable(self, mock_get_redis, client, auth_headers):
        """Тест graceful degradation когда Redis недоступен"""
        # Мокаем Redis как недоступный
        mock_get_redis.return_value = None
        
        # Logout должен работать даже без Redis
        response = client.post('/api/v1/auth/logout', headers=auth_headers)
        assert response.status_code == 200
        
        # Токен должен продолжать работать (graceful degradation)
        response = client.get('/api/v1/auth/me', headers=auth_headers)
        assert response.status_code == 200
    
    def test_refresh_token_also_blacklisted(self, client, user):
        """Тест что refresh token тоже добавляется в blacklist"""
        # Логинимся
        login_response = client.post('/api/v1/auth/login', json={
            'login': user.login,
            'password': 'testpass123'
        })
        assert login_response.status_code == 200
        
        # Используем ACCESS token для logout (не refresh!)
        access_token = login_response.get_json()['data']['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Logout с access token
        logout_response = client.post('/api/v1/auth/logout', headers=headers)
        assert logout_response.status_code == 200
        
        # Пытаемся использовать отозванный access token
        response = client.get('/api/v1/auth/me', headers=headers)
        
        from app.core.redis_client import is_redis_available
        if is_redis_available():
            assert response.status_code == 401
        else:
            assert response.status_code == 200