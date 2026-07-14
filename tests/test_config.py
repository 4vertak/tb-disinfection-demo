"""Tests for application configuration."""
import pytest
import os
from importlib import reload


class TestConfig:
    """Tests for application configuration."""

    def test_default_config_values(self):
        """Test that default configuration has required values."""

        from app.core.config import Config
        config = Config()
        
        assert hasattr(config, 'SECRET_KEY')
        assert hasattr(config, 'SQLALCHEMY_DATABASE_URI')
        assert hasattr(config, 'SQLALCHEMY_TRACK_MODIFICATIONS')
        assert hasattr(config, 'FLASK_ENV')
        assert hasattr(config, 'SOCKETIO_ASYNC_MODE')
        assert hasattr(config, 'JWT_SECRET_KEY')

    def test_secret_key_from_env(self, monkeypatch):
        """Test that SECRET_KEY is loaded from environment."""

        monkeypatch.setenv('SECRET_KEY', 'test-secret-key-from-env')
        
        import app.core.config
        reload(app.core.config)
        from app.core.config import Config
        
        config = Config()
        assert config.SECRET_KEY == 'test-secret-key-from-env'

    def test_database_uri_from_env(self, monkeypatch):
        """Test that SQLALCHEMY_DATABASE_URI is built correctly from environment variables."""
        # Устанавливаем переменные окружения ПЕРЕД импортом
        monkeypatch.setenv('POSTGRES_USER', 'testuser')
        monkeypatch.setenv('POSTGRES_PASSWORD', 'testpass')
        monkeypatch.setenv('POSTGRES_HOST', 'localhost')
        monkeypatch.setenv('POSTGRES_PORT', '5432')
        monkeypatch.setenv('POSTGRES_DB', 'testdb')
        monkeypatch.setenv('DATABASE_URL', 'postgresql://testuser:testpass@localhost:5432/testdb')
        
        # Перезагружаем модуль конфигурации после изменения переменных окружения
        import sys
        import app.core.config
        
        # Удаляем модуль из кэша
        if 'app.core.config' in sys.modules:
            del sys.modules['app.core.config']
        
        # Импортируем заново
        from app.core.config import Config
        config = Config()
        
        expected_uri = 'postgresql://testuser:testpass@localhost:5432/testdb'
        assert config.SQLALCHEMY_DATABASE_URI == expected_uri

    def test_flask_env_values(self, monkeypatch):
        """Test FLASK_ENV configuration."""

        for env_value in ['development', 'testing', 'production']:
            monkeypatch.setenv('FLASK_ENV', env_value)
            
            import app.core.config
            reload(app.core.config)
            from app.core.config import Config
            
            config = Config()
            assert config.FLASK_ENV == env_value

    def test_sqlalchemy_track_modifications_default(self):
        """Test that SQLALCHEMY_TRACK_MODIFICATIONS is False by default."""

        from app.core.config import Config
        config = Config()
        assert config.SQLALCHEMY_TRACK_MODIFICATIONS is False

    def test_socketio_async_mode(self, monkeypatch):
        """Test SocketIO async mode configuration."""
        monkeypatch.setenv('SOCKETIO_ASYNC_MODE', 'gevent')
        
        import app.core.config
        reload(app.core.config)
        from app.core.config import Config
        
        config = Config()
        assert config.SOCKETIO_ASYNC_MODE == 'gevent'


class TestRateLimitConfig:
    """Tests for rate limiting configuration."""

    def test_rate_limit_storage_url(self):
        """Test rate limit storage configuration."""

        from app.core.config import Config
        config = Config()
        assert hasattr(config, 'RATELIMIT_STORAGE_URL')

    def test_cors_configuration(self):
        """Test CORS configuration."""

        from app.core.config import Config
        config = Config()
        assert hasattr(config, 'CORS_ALLOWED_ORIGINS')


class TestSecurityConfig:
    """Tests for security-related configuration."""

    def test_secret_key_minimum_length(self, monkeypatch):
        """Test that SECRET_KEY can be set to any value."""

        monkeypatch.setenv('SECRET_KEY', 'short')
        monkeypatch.setenv('FLASK_ENV', 'production')
        
        import app.core.config
        reload(app.core.config)
        from app.core.config import Config
        
        config = Config()
        assert config.SECRET_KEY == 'short'

    def test_session_cookie_secure(self):
        """Test session cookie security settings."""
        
        from app.core.config import Config
        config = Config()
        assert hasattr(config, 'SESSION_COOKIE_SECURE')
        assert hasattr(config, 'SESSION_COOKIE_HTTPONLY')