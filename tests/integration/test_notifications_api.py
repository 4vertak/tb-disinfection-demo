import pytest


class TestNotificationsAPI:
    """Integration тесты для Notifications API"""
    
    def test_get_notifications_list(self, client, auth_headers):
        """Тест получения списка уведомлений"""
        response = client.get('/api/v1/notifications/', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'items' in data['data']
    
    def test_get_unread_count(self, client, auth_headers):
        """Тест получения количества непрочитанных"""
        response = client.get('/api/v1/notifications/unread-count', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'unread_count' in data['data']
    
    def test_mark_all_as_read(self, client, auth_headers):
        """Тест отметки всех как прочитанные"""
        response = client.post('/api/v1/notifications/mark-all-read', headers=auth_headers)
        
        assert response.status_code == 200