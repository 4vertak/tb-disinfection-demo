"""Tests for health check endpoint."""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import OperationalError


class TestHealthCheck:
    """Tests for health check endpoints."""

    def test_basic_health_check(self, client):
        """Test basic health check endpoint."""
        response = client.get('/api/health/')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'disinfection-requests-system'

    def test_detailed_health_check_healthy(self, client):
        """Test detailed health check when everything is healthy."""
        response = client.get('/api/health/detailed')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'disinfection-requests-system'
        assert 'database' in data['checks']
        assert data['checks']['database'] == 'healthy'
        assert 'configuration' in data['checks']

    def test_detailed_health_check_database_failure(self, client, app):
        """Test detailed health check when database is down."""
        # Mock database to raise exception
        with patch('app.routes.health.routes.db') as mock_db:
            mock_session = MagicMock()
            mock_session.execute.side_effect = OperationalError(
                statement=None,
                params=None,
                orig=Exception("Connection refused")
            )
            mock_db.session = mock_session
            
            response = client.get('/api/health/detailed')
            
            data = response.get_json()
            assert data['status'] == 'unhealthy'
            assert data['checks']['database'] == 'unhealthy'
            assert 'database_error' in data['checks']

    def test_detailed_health_check_missing_config(self, client, app):
        """Test health check when some configs are missing."""
        with app.test_request_context():
            # Remove SECRET_KEY temporarily
            original_secret = app.config.get('SECRET_KEY')
            app.config['SECRET_KEY'] = None
            
            try:
                response = client.get('/api/health/detailed')
                
                data = response.get_json()
                # Status should be degraded, not unhealthy
                assert data['status'] in ['degraded', 'healthy']
                if 'configuration' in data['checks']:
                    assert data['checks']['configuration'] in ['healthy', 'incomplete']
            finally:
                app.config['SECRET_KEY'] = original_secret


class TestHealthCheckPerformance:
    """Performance tests for health check endpoints."""

    def test_health_check_response_time(self, client):
        """Test that health check responds quickly (< 100ms)."""
        import time
        
        start = time.time()
        response = client.get('/api/health/')
        end = time.time()
        
        response_time_ms = (end - start) * 1000
        assert response.status_code == 200
        assert response_time_ms < 100, f"Health check too slow: {response_time_ms}ms"

    def test_detailed_health_check_response_time(self, client):
        """Test that detailed health check responds reasonably fast."""
        import time
        
        start = time.time()
        response = client.get('/api/health/detailed')
        end = time.time()
        
        response_time_ms = (end - start) * 1000
        assert response.status_code == 200
        assert response_time_ms < 500, f"Detailed health check too slow: {response_time_ms}ms"
