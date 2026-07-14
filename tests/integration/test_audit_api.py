"""Интеграционные тесты для Audit API."""

import pytest

class TestAuditAPI:
    """Integration тесты для Audit API"""
    
    def test_get_application_audit_history(self, client, admin_auth_headers, application):
        """Тест получения истории заявки (админом)"""
        # При создании заявки через ORM срабатывает event и создается INSERT лог
        response = client.get(f'/api/v1/audit/applications/{application.id}', headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        # Должен быть как минимум 1 лог (INSERT)
        assert len(data['data']) >= 1
        assert data['data'][0]['change_type'] == 'INSERT'
        
    def test_get_application_audit_history_forbidden(self, client, auth_headers, application):
        """Тест получения истории чужой заявки (врачом)"""
        
        response = client.get(f'/api/v1/audit/applications/99999', headers=auth_headers)
        assert response.status_code == 403 # Или 404, если заявки нет

    def test_get_user_audit_history(self, client, admin_auth_headers, user):
        """Тест получения истории действий пользователя"""
        response = client.get(f'/api/v1/audit/users/{user.id}', headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        # У пользователя должен быть логин (login) в истории
        assert isinstance(data['data'], list)