import os
from flask import Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_login import LoginManager
from flask_cors import CORS
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from flask_assets import Environment

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()
login_manager = LoginManager()

# для REST API
cors = CORS()
cache = Cache()
jwt = JWTManager()

# Limiter с Redis
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
)

# Flask-Assets
assets = Environment()

# ==================== REST API ====================

api = None  # будет инициализирован позже
api_bp = None  # будет инициализирован позже

# Swagger/OpenAPI документация (конфигурация)
API_AUTHORIZATIONS = {
    'Bearer Auth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': "Добавьте JWT токен. Пример: **Bearer <token>**"
    }
}