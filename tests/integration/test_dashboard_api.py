import pytest

@pytest.mark.skip(
    reason="Dashboard API использует PostgreSQL-специфичные функции (timezone), "
           "которые не поддерживаются в SQLite. Тесты пропускаются на SQLite, "
           "но будут работать в production на PostgreSQL."
)

class TestDashboardAPI:
    """Integration тесты для Dashboard API"""
    
    def test_get_dashboard_data(self, client, auth_headers):
        """Тест получения данных dashboard"""
        response = client.get('/api/v1/dashboard/', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'total_info' in data['data']
        assert 'monthly_data' in data['data']
    
    def test_get_dashboard_data_with_period(self, client, auth_headers):
        """Тест получения данных за конкретный период"""
        response = client.get('/api/v1/dashboard/?period=year&year=2026', headers=auth_headers)
        
        assert response.status_code == 200