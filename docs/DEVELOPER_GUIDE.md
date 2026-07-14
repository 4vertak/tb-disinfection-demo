# Руководство разработчика

## Содержание

- [Настройка окружения](#настройка-окружения)
- [Структура проекта](#структура-проекта)
- [Рабочий процесс](#рабочий-процесс)
- [Создание новых функций](#создание-новых-функций)
- [Работа с базой данных](#работа-с-базой-данных)
- [Тестирование](#тестирование)
- [Стиль кода](#стиль-кода)
- [Добавление новых маршрутов](#добавление-новых-маршрутов)
- [Добавление новых моделей](#добавление-новых-моделей)
- [Работа с WebSocket](#работа-с-websocket)
- [Отладка](#отладка)
- [Полезные команды](#полезные-команды)

## Настройка окружения

### Предварительные требования

- **Python 3.8+**
- **PostgreSQL 15+**
- **Git**
- **Make** (опционально)
- **Docker** (для production тестирования)

### Шаг 1: Клонирование репозитория

```bash
git clone <repository-url>
cd disinfection-requests-system
```

### Шаг 2: Создание виртуального окружения

```bash
# Создание
python -m venv venv

# Активация (Linux/macOS)
source venv/bin/activate

# Активация (Windows)
venv\Scripts\activate
```

### Шаг 3: Установка зависимостей

```bash
# Через Makefile
make dev-install

# Вручную
pip install -r requirements.txt
```

### Шаг 4: Настройка базы данных

**Вариант A: Docker (рекомендуется)**

```bash
make dev-db-up
```

**Вариант B: Локальный PostgreSQL**

```bash
# Создание пользователя и БД
sudo -u postgres psql
CREATE USER disinfection_user WITH PASSWORD 'your_password';
CREATE DATABASE disinfection_db OWNER disinfection_user;
\q

# Настройка .env
cp .env_example .env
nano .env  # укажите ваши параметры
```

### Шаг 5: Инициализация приложения

```bash
# Применение миграций (если есть)
flask db upgrade

# Или создание таблиц (в development режиме)
# Таблицы создаются автоматически при первом запуске
```

### Шаг 6: Запуск

```bash
make dev
# или
FLASK_ENV=development flask run --host=0.0.0.0 --port=8081
```

Приложение доступно: http://localhost:8081

## Структура проекта

```
disinfection-requests-system/
├── app/
│   ├── core/                    # Ядро приложения
│   │   ├── config.py           # Конфигурация
│   │   ├── extensions.py       # Расширения (db, migrate, etc.)
│   │   ├── errors.py           # Обработчики ошибок
│   │   ├── signals.py          # Flask signals
│   │   └── bundles.py          # Assets bundles
│   │
│   ├── domain/                  # Бизнес-логика
│   │   ├── models/             # SQLAlchemy модели
│   │   │   ├── user/          # Пользователи
│   │   │   ├── application/   # Заявки
│   │   │   ├── audit/         # Аудит
│   │   │   ├── blog/          # Блог
│   │   │   └── notification/  # Уведомления
│   │   │
│   │   └── services/           # Бизнес-логика
│   │       ├── user_service.py
│   │       ├── notification_service.py
│   │       └── import_export_service.py
│   │
│   ├── routes/                  # HTTP контроллеры
│   │   ├── user/               # Аутентификация, пользователи
│   │   ├── application/        # Заявки
│   │   ├── dashboard/          # Админка, статистика
│   │   ├── disinfection/       # Дезинфекция
│   │   ├── notification/       # Уведомления
│   │   ├── blog/               # Блог
│   │   ├── import_export/      # Импорт/экспорт
│   │   └── dadata/             # API DaData
│   │
│   ├── templates/               # Jinja2 шаблоны
│   ├── static/                  # Статические файлы
│   └── utils/                   # Утилиты
│       ├── filters.py          # Jinja2 фильтры
│       └── serializers.py      # JSON сериализация
│
├── tests/                       # Тесты
├── migrations/                  # Alembic миграции
├── docs/                        # Документация
├── nginx/                       # Nginx конфиг
├── .env_example                # Пример .env
├── docker-compose.yml          # Docker Compose
├── Dockerfile                  # Docker образ
├── Makefile                    # Make команды
├── requirements.txt            # Зависимости
└── run.py                      # Точка входа
```

## Рабочий процесс

### Git Flow

```bash
# Создание ветки для новой функции
git checkout -b feature/name-of-feature

# Внесение изменений
git add .
git commit -m "feat: описание изменений"

# Push на удалённый репозиторий
git push origin feature/name-of-feature

# Создание Pull Request
# (через GitHub/GitLab интерфейс)
```

### Коммиты

**Соглашение:** Conventional Commits

```
type(scope): описание

types:
  feat     - новая функция
  fix      - исправление бага
  docs     - изменения в документации
  style    - форматирование, пробелы
  refactor - рефакторинг
  test     - добавление/изменение тестов
  chore    - обновление зависимостей, инструментов
```

**Примеры:**

```bash
git commit -m "feat(auth): добавить двухфакторную аутентификацию"
git commit -m "fix(users): исправить ошибку при регистрации"
git commit -m "docs(readme): обновить инструкции по установке"
```

## Создание новых функций

### Пример: Добавление новой страницы

**1. Создание модели (если нужна)**

```python
# app/domain/models/my_new_model/entities.py
from ....core.extensions import db
from datetime import datetime

class MyNewModel(db.Model):
    __tablename__ = 'my_new_model'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MyNewModel {self.title}>'
```

**2. Создание Blueprint**

```python
# app/routes/my_new_route/routes.py
from flask import Blueprint, render_template, request, flash, redirect
from flask_login import login_required, current_user
from ...domain.models.my_new_model.entities import MyNewModel

my_blueprint = Blueprint('my_new_route', __name__)

@my_blueprint.route('/my-page')
@login_required
def my_page():
    items = MyNewModel.query.all()
    return render_template('my_page/index.html', items=items)
```

**3. Регистрация Blueprint**

```python
# app/__init__.py
from .routes.my_new_route.routes import my_blueprint

def create_app(config_class=Config):
    app = Flask(__name__)
    
    # ... существующий код ...
    
    app.register_blueprint(my_blueprint, url_prefix='/my')
    
    # ... остальной код ...
    
    return app
```

**4. Создание шаблона**

```html
<!-- app/templates/my_page/index.html -->
{% extends "base.html" %}

{% block content %}
<h1>Моя новая страница</h1>

<ul>
    {% for item in items %}
    <li>{{ item.title }}</li>
    {% endfor %}
</ul>
{% endblock %}
```

**5. Создание миграции**

```bash
flask db migrate -m "add my_new_model table"
flask db upgrade
```

## Работа с базой данных

### Модели (Entities)

**Базовая модель:**

```python
from ....core.extensions import db
from datetime import datetime

class MyModel(db.Model):
    __tablename__ = 'my_model'
    
    # Поля
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    related_id = db.Column(db.Integer, db.ForeignKey('related_table.id'))
    related = db.relationship('RelatedModel', backref='my_models')
    
    def __repr__(self):
        return f'<MyModel {self.name}>'
```

### Запросы

```python
# Получить все записи
items = MyModel.query.all()

# Фильтрация
items = MyModel.query.filter_by(status='active').all()

# Сортировка
items = MyModel.query.order_by(MyModel.created_at.desc()).all()

# Лимит
items = MyModel.query.limit(10).all()

# Paginate (для списков)
page = request.args.get('page', 1, type=int)
items = MyModel.query.order_by(MyModel.created_at.desc()).paginate(
    page=page, per_page=20, error_out=False
)
```

### Связи

**One-to-Many:**

```python
# Parent model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    applications = db.relationship('Application', backref='author', lazy=True)

# Child model
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
```

**Many-to-Many:**

```python
# Association table
tags = db.Table('tags',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tags = db.relationship('Tag', secondary=tags, backref='posts')
```

### Миграции

```bash
# Создать миграцию
flask db migrate -m "описание изменений"

# Проверить файл миграции
# migrations/versions/xxx_description.py

# Применить миграцию
flask db upgrade

# Откатить миграцию
flask db downgrade

# Текущая версия
flask db current

# История миграций
flask db history
```

## Тестирование

### API Testing
#### Тестирование через Swagger UI

1. Запустите приложение: `make dev`
2. Откройте http://localhost:8081/api/docs
3. Авторизуйтесь через POST `/api/v1/auth/login`
4. Скопируйте `access_token`
5. Нажмите "Authorize" и вставьте токен
6. Тестируйте эндпоинты прямо в браузере

#### Тестирование через curl

```bash
# Аутентификация
curl -X POST http://localhost:8081/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login": "admin", "password": "admin123"}'

# Получить список заявок
curl -X GET "http://localhost:8081/api/v1/applications?page=1&per_page=20" \
  -H "Authorization: Bearer <access_token>"

# Создать заявку
curl -X POST http://localhost:8081/api/v1/applications \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_full_name": "Иванов Иван Иванович",
    "birth_date": "1980-01-15",
    "address": "г. Якутск, ул. Ленина, д. 1",
    "diagnosis_id": 1,
    "focus_id": 1,
    "area_id": 1
  }'
```

### Запуск тестов

```bash
# Все тесты
pytest

# Все API тесты
pytest tests/integration/ -v

# Конкретный namespace
pytest tests/integration/test_applications_api.py -v

# С покрытием
pytest tests/integration/ --cov=app/api --cov-report=html

# С подробным выводом
pytest -v

# С покрытием
pytest --cov=app --cov-report=html

# Один файл
pytest tests/test_user_service.py -v

# С marker
pytest -m unit



```

### Написание тестов

**Пример теста:**

```python
import pytest

class TestMyFeature:
    
    def test_create_item(self, client, test_user, app):
        """Тест создания нового элемента."""
        # Arrange
        with app.app_context():
            # Login
            client.post('/login', data={
                'login': 'testuser',
                'password': 'testpass123'
            }, follow_redirects=True)
            
            # Act
            response = client.post('/my/create', data={
                'title': 'Test Item',
                'description': 'Test Description'
            }, follow_redirects=True)
            
            # Assert
            assert response.status_code == 200
            assert b'Test Item' in response.data
```

### Фикстуры

**Файл:** `tests/conftest.py`

```python
@pytest.fixture
def client(app):
    """Тестовый клиент."""
    return app.test_client()

@pytest.fixture
def test_user(db_session):
    """Тестовый пользователь."""
    user = User(
        login='testuser',
        name='Test User',
        password_hash=generate_password_hash('testpass123'),
        user_type='doctor'
    )
    db_session.add(user)
    db_session.commit()
    return user
```

## Стиль кода

### Именование

- **Классы:** PascalCase → `MyNewModel`
- **Функции:** snake_case → `create_user()`
- **Переменные:** snake_case → `user_id`
- **Константы:** UPPER_SNAKE_CASE → `MAX_ATTEMPTS`
- **Файлы:** snake_case → `user_service.py`

### Структура импортов

```python
# 1. Стандартные библиотеки
import os
from datetime import datetime

# 2. Сторонние библиотеки
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

# 3. Локальные импорты (относительные)
from ...core.extensions import db
from ...domain.models.user.entities import User
from ...domain.services.user_service import UserService
```

### Документирование кода

```python
def create_user(user_data: dict) -> User:
    """
    Создание нового пользователя.
    
    Args:
        user_data: Словарь с данными пользователя
        
    Returns:
        Созданный объект User
        
    Raises:
        ValueError: Если данные невалидны
        IntegrityError: Если login уже существует
    """
    # ... код ...
```

### Линтеры

**Рекомендуемые инструменты:**

```bash
# Flake8 - проверка стиля
pip install flake8
flake8 app/

# Black - автоформатирование
pip install black
black app/

# isort - сортировка импортов
pip install isort
isort app/

# Mypy - проверка типов
pip install mypy
mypy app/
```

## Добавление новых маршрутов

### Blueprint структура

```python
# app/routes/my_feature/routes.py
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.exceptions import abort
from ...core.extensions import db
from ...domain.models.my_feature.entities import MyModel

# Создание Blueprint
my_feature = Blueprint('my_feature', __name__)

# Маршрут: список элементов
@my_feature.route('/my-items')
@login_required
def list_items():
    """Показать все элементы текущего пользователя."""
    items = MyModel.query.filter_by(user_id=current_user.id).all()
    return render_template('my_feature/list.html', items=items)

# Маршрут: создание элемента
@my_feature.route('/my-items/create', methods=['GET', 'POST'])
@login_required
def create_item():
    """Создать новый элемент."""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        
        # Валидация
        if not title:
            flash('Название обязательно', 'danger')
            return render_template('my_feature/create.html')
        
        # Создание
        item = MyModel(
            title=title,
            description=description,
            user_id=current_user.id
        )
        db.session.add(item)
        db.session.commit()
        
        flash('Элемент создан!', 'success')
        return redirect(url_for('my_feature.list_items'))
    
    return render_template('my_feature/create.html')

# Маршрут: редактирование
@my_feature.route('/my-items/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(id):
    """Редактировать элемент."""
    item = MyModel.query.get_or_404(id)
    
    # Проверка прав
    if item.user_id != current_user.id:
        abort(403)
    
    if request.method == 'POST':
        item.title = request.form.get('title')
        item.description = request.form.get('description')
        
        db.session.commit()
        flash('Изменения сохранены!', 'success')
        return redirect(url_for('my_feature.list_items'))
    
    return render_template('my_feature/edit.html', item=item)

# Маршрут: удаление
@my_feature.route('/my-items/<int:id>/delete', methods=['POST'])
@login_required
def delete_item(id):
    """Удалить элемент."""
    item = MyModel.query.get_or_404(id)
    
    # Проверка прав
    if item.user_id != current_user.id:
        abort(403)
    
    db.session.delete(item)
    db.session.commit()
    
    flash('Элемент удален!', 'success')
    return redirect(url_for('my_feature.list_items'))
```

### Регистрация Blueprint

```python
# app/__init__.py
from .routes.my_feature.routes import my_feature

def create_app(config_class=Config):
    app = Flask(__name__)
    
    # ... существующий код ...
    
    app.register_blueprint(my_feature, url_prefix='/my')
    
    return app
```

## Добавление новых моделей

### Пример модели

```python
# app/domain/models/my_feature/entities.py
from ....core.extensions import db
from datetime import datetime

class MyModel(db.Model):
    """Модель для хранения данных о моей функции."""
    
    __tablename__ = 'my_model'
    
    # Поля
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='new')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    comments = db.relationship('Comment', backref='model', lazy=True, cascade='all, delete-orphan')
    
    # Методы
    def to_dict(self):
        """Сериализация в словарь."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<MyModel {self.title}>'
```

### Создание миграции

```bash
# Создать миграцию
flask db migrate -m "add my_model table"

# Проверить сгенерированный файл
# migrations/versions/xxx_add_my_model_table.py

# Применить
flask db upgrade
```

## Работа с WebSocket

### Отправка уведомлений

```python
from flask_socketio import emit
from app.core.extensions import socketio

def send_notification(user_id, message):
    """Отправить уведомление конкретному пользователю."""
    emit('notification', {
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }, room=f'user_{user_id}')
```

### Клиентская часть (JavaScript)

```javascript
// Подключение к SocketIO
const socket = io();

// Обработка уведомлений
socket.on('notification', function(data) {
    showNotification(data.message);
});

// Показ уведомления
function showNotification(message) {
    // Ваш код показа уведомлений
    alert(message);
}
```

## Отладка

### Flask Debug Mode

```bash
# В .env
FLASK_DEBUG=True
FLASK_ENV=development
```

 **Внимание:** Никогда не включайте debug mode в production!

### Python Debugger

```python
import pdb; pdb.set_trace()

# Или (Python 3.7+)
breakpoint()
```

### Логирование

```python
import logging

logger = logging.getLogger(__name__)

# В коде
logger.debug(f"Debug: {variable}")
logger.info(f"Info: {message}")
logger.warning(f"Warning: {message}")
logger.error(f"Error: {error}", exc_info=True)
```

### Просмотр SQL запросов

```python
# В development
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    print(f"SQL: {statement}")
    print(f"Params: {parameters}")
```

## Полезные команды

### Разработка

```bash
# Запуск приложения
make dev

# Установка зависимостей
make dev-install

# Запуск PostgreSQL
make dev-db-up

# Сброс БД
make db-reset

# Подключение к БД
make psql
```

### Тестирование

```bash
# Запуск тестов
pytest

# С покрытием
pytest --cov=app --cov-report=html

# Конкретный тест
pytest tests/test_file.py::TestClass::test_method -v
```

### Миграции

```bash
# Создать миграцию
flask db migrate -m "описание"

# Применить
flask db upgrade

# Откатить
flask db downgrade

# История
flask db history
```

### Docker

```bash
# Production запуск
make prod

# Пересборка
make prod-build

# Логи
make prod-logs

# Остановка
make stop
```

### Git

```bash
# Создание ветки
git checkout -b feature/my-feature

# Коммит
git add .
git commit -m "feat: описание"

# Push
git push origin feature/my-feature
```

### Очистка

```bash
# Удаление кэша
find . -type d -name '__pycache__' -exec rm -rf {} +
find . -type f -name '*.pyc' -delete
rm -rf .pytest_cache/
rm -rf app/static/.webassets-cache/
rm -rf app/static/gen/
```

---

**Дата последнего обновления:** 14 апреля 2026
