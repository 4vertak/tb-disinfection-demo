# Тестирование disinfection-requests-system

## Запуск тестов

### Быстрый запуск

```bash
# Все тесты
make test

# С отчетом о покрытии
make test-coverage

# С HTML отчетом
make test-html
```

### Ручной запуск

```bash
# Все тесты
pytest tests/ -v

# Конкретный файл тестов
pytest tests/test_user_service.py -v

# Конкретный тест
pytest tests/test_user_service.py::TestUserService::test_get_user_by_id -v

# С покрытием
pytest tests/ --cov=app --cov-report=html

# Только unit-тесты
pytest tests/ -m "not integration"

# С подробным выводом
pytest tests/ -v -s
```

## Структура тестов

```
tests/
├── conftest.py                  # Фикстуры и конфигурация
├── test_user_service.py         # Тесты сервиса пользователей
├── test_user_routes.py          # Тесты маршрутов пользователей
├── test_application_service.py  # Тесты сервиса заявок
├── test_application_routes.py   # Тесты маршрутов заявок
├── test_health_check.py         # Тесты health check
├── test_config.py               # Тесты конфигурации
└── ...
```

## Фикстуры

### Доступные фикстуры

- `app` - тестовое Flask приложение (SQLite in-memory)
- `client` - тестовый клиент Flask
- `db_session` - сессия базы данных (очищается после каждого теста)
- `test_user` - тестовый пользователь (doctor)
- `admin_user` - тестовый пользователь (admin)
- `area` - тестовый участок
- `diagnosis` - тестовый диагноз
- `focus` - тестовый эпидемический очаг

### Использование фикстур

```python
def test_example(db_session, test_user, client):
    # db_session - очищенная сессия БД
    # test_user - готовый тестовый пользователь
    # client - тестовый клиент с настроенным приложением
    pass
```

## Покрытие кода

### Текущее покрытие

Запустите `make test-coverage` для просмотра покрытия.

Целевое покрытие: **>80%**

### Генерация HTML отчета

```bash
make test-html
# Откройте htmlcov/index.html в браузере
```

## Написание тестов

### Структура теста

```python
class TestMyFeature:
    """Tests for my feature."""

    def test_success_case(self, client, test_user):
        """Test successful case."""
        response = client.get('/my-endpoint')
        assert response.status_code == 200
        assert 'expected_data' in response.get_json()

    def test_error_case(self, client):
        """Test error case."""
        response = client.post('/my-endpoint', data={})
        assert response.status_code == 400
```

### Best Practices

1. **Один тест - одна проверка**
   ```python
   # Хорошо
   def test_login_success(self): ...
   def test_login_failure(self): ...

   # Плохо
   def test_login_all_cases(self): ...
   ```

2. **Используйте параметризацию**
   ```python
   @pytest.mark.parametrize('status', ['new', 'in_progress', 'completed'])
   def test_different_statuses(self, status):
       ...
   ```

3. **Мокайте внешние зависимости**
   ```python
   @patch('app.services.external_api.get')
   def test_with_mocked_api(self, mock_get):
       mock_get.return_value = {'data': 'mocked'}
       ...
   ```

4. **Тесты должны быть независимыми**
   - Не полагайтесь на порядок запуска
   - Каждая тестовая функция должна быть самодостаточной

5. **Используйте описательные имена**
   ```python
   # Хорошо
   def test_login_with_invalid_password_returns_401(self): ...

   # Плохо
   def test_login2(self): ...
   ```

## CI/CD интеграция

### GitHub Actions пример

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: testuser
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run tests
        run: pytest tests/ --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Troubleshooting

### Тесты не запускаются

```bash
# Проверьте установку зависимостей
pip install -r requirements.txt

# Проверьте, что pytest установлен
pytest --version

# Если нет, установите
pip install pytest pytest-cov
```

### Ошибки базы данных

```bash
# Очистите кэш тестов
rm -rf .pytest_cache/
find . -type d -name "__pycache__" -exec rm -rf {} +

# Перезапустите тесты с verbose
pytest tests/ -v -s
```

### Медленные тесты

```bash
# Запуск только быстрых тестов (< 1s)
pytest tests/ -m "not slow"

# Показать самые медлые тесты
pytest tests/ --durations=10
```

## Полезные команды

```bash
# Запуск тестов в режиме watch (автоматический перезапуск при изменениях)
make test-watch

# Запуск с отладчиком
pytest tests/ --pdb

# Запуск с xdist (параллельный запуск)
pytest tests/ -n auto

# Проверка линтером
pytest tests/ --flake8
pytest tests/ --pylint
```
