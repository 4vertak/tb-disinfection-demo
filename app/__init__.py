from .domain.services.notification_service import NotificationService

from .domain.services.user_service import UserInitializer
from .utils.filters import localtime_filter, sanitize_and_nl2br
from .api import register_api 
from flask import Flask


from .core.bundles import bundles, register_bundles
from .core.extensions import db, migrate, login_manager, assets, socketio, limiter
from .core.config import config_by_name, Config
from .routes.dadata.routes import bp as dadata_bp

from .routes.notification.routes import notification_bp
from .routes.application.routes import application
from .routes.disinfection.routes import disinfection
from .routes.dashboard.routes import dashboard
from .routes.user.routes import user
from .routes.blog.routes import blog
from .routes.import_export.routes import import_export
from .routes.health.routes import bp as health_bp
from .routes.spa.routes import spa_bp

from .core.signals import register_signals
from .core.errors import register_error_handlers

from .commands import init_app

from .domain.models.user.entities import User
from .domain.models.application.entities import Application, Area, Diagnosis, EpidemicFocus, Disinfection
from .domain.models.notification.entities import Notification


def create_app(config_class=Config):
    app = Flask(__name__)

    app.config.from_object(config_class)

    app.add_template_filter(localtime_filter, name="localtime")
    app.add_template_filter(sanitize_and_nl2br, name="sanitize_and_nl2br")

    app.register_blueprint(dadata_bp)
    app.register_blueprint(application)
    app.register_blueprint(disinfection)
    app.register_blueprint(dashboard)
    app.register_blueprint(user)
    app.register_blueprint(notification_bp)
    app.register_blueprint(blog, url_prefix='/blog')
    app.register_blueprint(import_export, url_prefix='/import-export')
    app.register_blueprint(health_bp)
    app.register_blueprint(spa_bp)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    assets.init_app(app)
    socketio.init_app(
        app,
        cors_allowed_origins=app.config.get('CORS_ALLOWED_ORIGINS') or ['*'] if app.config.get('FLASK_ENV') == 'development' else app.config.get('CORS_ALLOWED_ORIGINS', []),
        async_mode=app.config['SOCKETIO_ASYNC_MODE'],
        ping_timeout=60,
        ping_interval=25,
        # Отключаем WebSocket upgrade — используем long-polling через uwsgi
        transports=['polling'],
    )
    limiter.init_app(app)

    # Настройка обработчиков SocketIO
    with app.app_context():
        NotificationService.setup_socket_handlers()

    # LOGIN MANAGER
    login_manager.login_view = 'user.login'
    login_manager.login_message = 'Вы не можете получить доступ к данной странице. Нужно сначала войти.'
    login_manager.login_message_category = 'info'

    # ASSETS
    register_bundles(assets, bundles)

    # SIGNALS
    register_signals(app)

    # ERROR HANDLERS
    register_error_handlers(app)

    # РЕГИСТРАЦИЯ КОМАНД
    init_app(app)

    with app.app_context():
        
        flask_env = app.config.get('FLASK_ENV', 'production')
        
        if flask_env in ('development', 'testing'):
            try:
                db.create_all()
                app.logger.info("Database tables created successfully")
            except Exception as e:
                app.logger.error(f"Failed to create tables: {e}")
        
        # Создаём админа и справочники
        try:
            UserInitializer.create_admin_account()
            UserInitializer.fill_directories()
        except Exception as e:
            app.logger.warning(f"Failed to initialize data: {e}")
    
    # РЕГИСТРАЦИЯ REST API
    register_api(app)

    return app
