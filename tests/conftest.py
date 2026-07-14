"""Pytest fixtures for the disinfection-requests-system tests."""

import os
import pytest

os.environ['POSTGRES_USER'] = 'testuser'
os.environ['POSTGRES_PASSWORD'] = 'testpass'
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5432'
os.environ['POSTGRES_DB'] = 'testdb'
os.environ['SECRET_KEY'] = 'test-secret-key-that-is-at-least-32-bytes-long-for-testing-purposes-only'
os.environ['FLASK_ENV'] = 'testing'
os.environ['SOCKETIO_ASYNC_MODE'] = 'threading'
os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret-key-that-is-at-least-32-bytes-long-for-testing'

from app import create_app
from app.core.extensions import db
from app.core.config import TestingConfig 
from app.domain.models.user.entities import User
from app.domain.models.application.entities import Area, Diagnosis, EpidemicFocus
from werkzeug.security import generate_password_hash


class TestConfig(TestingConfig):
    """Тестовая конфигурация с SQLite."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

    SECRET_KEY = 'test-secret-key-that-is-at-least-32-bytes-long-for-testing-purposes-only'
    JWT_SECRET_KEY = 'test-jwt-secret-key-that-is-at-least-32-bytes-long-for-testing-purposes'


    FLASK_ENV = 'testing'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    SOCKETIO_ASYNC_MODE = 'threading'
    CORS_ALLOWED_ORIGINS = []
    RATELIMIT_STORAGE_URL = 'memory://'
    
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    JWT_ACCESS_TOKEN_EXPIRES = 300  # 5 минут в секундах

    CACHE_TYPE = 'SimpleCache'
    CACHE_REDIS_URL = None

    RATELIMIT_ENABLED = False
    RATELIMIT_DEFAULT = ''
    RATELIMIT_STORAGE_URL = 'memory://'

    FEATURE_FLAG_API_V1_ENABLED = True
    FEATURE_FLAG_JWT_AUTH_ENABLED = True
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True


@pytest.fixture(scope="function")  #ВАЖНО: scope="function"
def app():
    """Creates a test Flask application with in-memory SQLite database."""
    
    app = create_app(config_class=TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Returns a test Flask client."""

    return app.test_client()


@pytest.fixture
def db_session(app):
    """Provides a DB session that is cleaned after each test."""

    with app.app_context():
        db.create_all()
        yield db.session
        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_user(db_session):
    """Creates a test user (doctor)."""

    user = User(
        login='testuser',
        name='Test User',
        password_hash=generate_password_hash('testpass123'),
        user_type='doctor'
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def admin_user(db_session):
    """Creates an admin user."""

    user = User(
        login='testadmin',
        name='Test Admin',
        password_hash=generate_password_hash('adminpass123'),
        user_type='admin'
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def area(db_session):
    """Returns the first test area."""

    area = db_session.query(Area).first()
    if not area:
        area = Area(name_area='Тестовый участок №1')
        db_session.add(area)
        db_session.commit()
    return area


@pytest.fixture
def diagnosis(db_session):
    """Returns the first test diagnosis."""

    diagnosis = db_session.query(Diagnosis).first()
    if not diagnosis:
        diagnosis = Diagnosis(mkb_code='A15.0', name='Туберкулёз лёгких')
        db_session.add(diagnosis)
        db_session.commit()
    return diagnosis


@pytest.fixture
def focus(db_session):
    """Returns the first test epidemic focus."""

    focus = db_session.query(EpidemicFocus).first()
    if not focus:
        focus = EpidemicFocus(name='II очаг')
        db_session.add(focus)
        db_session.commit()
    return focus


@pytest.fixture
def auth_headers(client, test_user):
    response = client.post('/api/v1/auth/login', json={
        'login': 'testuser',
        'password': 'testpass123'
    })
    print(f"\n[DEBUG] Login response status: {response.status_code}")
    print(f"[DEBUG] Login response body: {response.get_json()}")
    
    data = response.get_json()
    token = data['data']['access_token']
    print(f"[DEBUG] Token (first 50 chars): {token[:50]}...")
    
    headers = {'Authorization': f'Bearer {token}'}
    print(f"[DEBUG] Headers: {headers}")
    
    # Пробный запрос для проверки
    test_response = client.get('/api/v1/auth/me', headers=headers)
    print(f"[DEBUG] Test /me response: {test_response.status_code} {test_response.get_json()}")
    
    return headers


@pytest.fixture
def admin_auth_headers(client, admin_user):
    """Returns authorization headers for admin user."""

    response = client.post('/api/v1/auth/login', json={
        'login': 'testadmin',
        'password': 'adminpass123'
    })
    data = response.get_json()
    token = data['data']['access_token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def db_extension(app):
    """
    Фикстура для прямого доступа к SQLAlchemy (используется в unit-тестах).
    Переименована с `db` на `db_extension`, чтобы не конфликтовать 
    с импортом `from app.core.extensions import db`.
    """

    with app.app_context():
        from app.core.extensions import db as _db
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def user(test_user):
    """Алиас для test_user (для совместимости с тестами)."""

    return test_user


@pytest.fixture
def users(db_session):
    """Создаёт нескольких тестовых пользователей."""

    from werkzeug.security import generate_password_hash
    
    users_data = [
        {'login': 'doctor1', 'name': 'Doctor One', 'user_type': 'doctor', 'password': 'pass123'},
        {'login': 'doctor2', 'name': 'Doctor Two', 'user_type': 'doctor', 'password': 'pass123'},
        {'login': 'disinfector1', 'name': 'Disinfector One', 'user_type': 'disinfector', 'password': 'pass123'},
    ]
    
    created_users = []
    for u_data in users_data:
        user = User(
            login=u_data['login'],
            name=u_data['name'],
            password_hash=generate_password_hash(u_data['password']),
            user_type=u_data['user_type']
        )
        db_session.add(user)
        created_users.append(user)
    
    db_session.commit()
    return created_users


@pytest.fixture
def applications(db_session, test_user, area, diagnosis, focus):
    """Создаёт несколько тестовых заявок."""

    from app.domain.models.application.entities import Application
    from datetime import datetime, date
    
    apps_data = [
        {
            'patient_full_name': 'Иванов Иван',
            'status': 'incompleted',
            'contact_phone': '+79141111111',
            'workplace': 'Завод №1',
            'reason_application': 'hospitalization'
        },
        {
            'patient_full_name': 'Петров Пётр',
            'status': 'completed',
            'contact_phone': '+79142222222',
            'workplace': 'Офис',
            'reason_application': 'sheduled'
        },
        {
            'patient_full_name': 'Сидоров Сидор',
            'status': 'refusal',
            'contact_phone': '+79143333333',
            'workplace': 'Школа',
            'reason_application': 'posthumously'
        },
    ]
    
    created_apps = []
    for i, a_data in enumerate(apps_data):
        app = Application(
            user_id=test_user.id,
            submission_date=datetime.now(),
            patient_full_name=a_data['patient_full_name'],
            birth_date=date(1990, 1, 1),
            address=f'Адрес {i}',
            contact_phone=a_data['contact_phone'],
            workplace=a_data['workplace'],
            diagnosis_id=diagnosis.id,
            gdu=f'{100 + i}',
            focus_id=focus.id,
            area_id=area.id,
            status=a_data['status'],
            reason_application=a_data['reason_application']
        )
        db_session.add(app)
        created_apps.append(app)
    
    db_session.commit()
    return created_apps


@pytest.fixture
def application(db_session, test_user, area, diagnosis, focus):
    """Создаёт одну тестовую заявку."""

    from app.domain.models.application.entities import Application
    from datetime import datetime, date
    
    app = Application(
        user_id=test_user.id,
        submission_date=datetime.now(),
        patient_full_name='Тестовый Пациент',
        birth_date=date(1990, 1, 1),
        address='Тестовый адрес',
        diagnosis_id=diagnosis.id,
        focus_id=focus.id,
        area_id=area.id,
        status='incompleted'
    )
    db_session.add(app)
    db_session.commit()
    return app


@pytest.fixture
def disinfection_data(db_session, application, disinfector):
    """Создаёт тестовые данные дезинфекции"""

    from app.domain.models.application.entities import Disinfection
    from datetime import datetime
    
    disinfection = Disinfection(
        application_id=application.id,
        disinfection_date=datetime.now(),
        area_size=50.5,
        volume_size=150.0,
        spraying_time='30 мин',
        swab_testing=5,
        rejection_reason=None
    )
    
    disinfector.disinfections.append(disinfection)
    
    db_session.add(disinfection)
    db_session.commit()
    return disinfection


@pytest.fixture
def disinfector(db_session):
    """Создаёт тестового дезинфектора (справочная запись)."""

    from app.domain.models.application.entities import Disinfector
    
    disinfector_obj = Disinfector(full_name='Test Disinfector')
    db_session.add(disinfector_obj)
    db_session.commit()
    return disinfector_obj


@pytest.fixture
def doctor_auth_headers(client, test_user):
    """Алиас для auth_headers (для совместимости с тестами)."""

    response = client.post('/api/v1/auth/login', json={
        'login': 'testuser',
        'password': 'testpass123'
    })
    data = response.get_json()
    token = data['data']['access_token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def disinfector_user(db_session):
    """Создаёт пользователя-дезинфектора (для логина)."""

    user = User(
        login='disinfector_user',
        name='Disinfector User',
        password_hash=generate_password_hash('pass123'),
        user_type='disinfector'
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def disinfector_auth_headers(client, disinfector_user):
    """Заголовки авторизации для пользователя-дезинфектора."""

    response = client.post('/api/v1/auth/login', json={
        'login': 'disinfector_user',
        'password': 'pass123'
    })
    data = response.get_json()
    token = data['data']['access_token']
    return {'Authorization': f'Bearer {token}'}