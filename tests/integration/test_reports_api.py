import pytest


class TestReportsAPI:
    """Integration тесты для Reports API"""
    
    def test_export_applications_excel(self, client, auth_headers):
        """Тест экспорта заявок в Excel"""
        response = client.get('/api/v1/reports/applications/excel', headers=auth_headers)
        
        assert response.status_code == 200
        assert response.content_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    def test_generate_application_word(self, client, auth_headers, application):
        """Тест генерации Word документа заявки"""
        response = client.get(
            f'/api/v1/reports/applications/{application.id}/word',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'