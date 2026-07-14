# Руководство по деплою

## Содержание

- [Архитектура развертывания](#архитектура-развертывания)
- [Docker Compose](#docker-compose)
- [Production конфигурация](#production-конфигурация)
- [Пошаговый деплой](#пошаговый-деплой)
- [Настройка HTTPS](#настройка-https)
- [Backup базы данных](#backup-базы-данных)
- [Мониторинг](#мониторинг)
  - [Health Checks](#health-checks)
  - [Docker Stats](#docker-stats)
  - [Логирование](#логирование)
- [Troubleshooting](#troubleshooting)
- [Production checklist](#production-checklist)

## Архитектура развертывания

### Компоненты

```
┌─────────────────────────────────────────────────┐
│                 Internet                        │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
            ┌──────────────┐
            │   Nginx      │  Порт 8081 (host)
            │  (reverse    │  -> Порт 80 (container)
            │   proxy)     │
            └──────┬───────┘
                   │ uwsgi_pass
                   ▼
            ┌──────────────┐
            │    Flask     │  Порт 8081 (container)
            │  (uWSGI)     │  async_mode: gevent
            │ + SocketIO   │  transports: polling
            └──────┬───────┘
                   │ SQLAlchemy
                   ▼
            ┌──────────────┐
            │  PostgreSQL  │  Порт 54321 (host)
            │   Database   │  -> Порт 5432 (container)
            └──────────────┘
```

### Тома (Volumes)

| Том | Хост | Контейнер | Описание |
|-----|------|-----------|----------|
| PostgreSQL | `~/.pg/pg_data/flask-yt` | `/var/lib/postgresql/data` | Данные БД |
| Uploads | `~/.uploads/images/flask-yt` | `/app/app/static/upload` | Загруженные файлы |

## Docker Compose

### Файл: `docker-compose.yml`

```yaml
services:
  postgres:
    image: postgres:15.5
    container_name: postgres
    volumes:
      - ~/.pg/pg_data/flask-yt:/var/lib/postgresql/data
    env_file:
      - .env
    ports:
      - "54321:5432"
  
  flask:
    build:
      dockerfile: Dockerfile
      context: .
    container_name: flask
    volumes:
      - ~/.uploads/images/flask-yt:/app/app/static/upload
    env_file:
      - .env
    environment:
      - POSTGRES_HOST=${POSTGRES_HOST}
      - POSTGRES_PORT=${POSTGRES_PORT}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    depends_on:
      - postgres
    expose:
      - 8081
  
  nginx:
    build:
      dockerfile: Dockerfile
      context: ./nginx/
    container_name: nginx
    env_file:
      - .env
    depends_on:
      - flask
    ports:
      - "8081:80"
```

### Nginx конфигурация

**Файл:** `nginx/nginx.conf`

```nginx
upstream flask_backend {
    server flask:8081;
}

server {
    listen 80;
    server_name _;

    client_max_body_size 1G;

    # Основной трафик через uwsgi
    location / {
        include uwsgi_params;
        uwsgi_pass flask:8081;
        uwsgi_read_timeout 300;
        uwsgi_send_timeout 300;
    }

    # Socket.IO через uwsgi (long-polling)
    location /socket.io {
        include uwsgi_params;
        uwsgi_pass flask:8081;

        uwsgi_buffering off;
        uwsgi_read_timeout 300;
        uwsgi_send_timeout 300;

        uwsgi_param HTTP_X_REAL_IP $remote_addr;
        uwsgi_param HTTP_X_FORWARDED_FOR $proxy_add_x_forwarded_for;
        uwsgi_param HTTP_X_FORWARDED_PROTO $scheme;
    }
}
```

## Production конфигурация

### Переменные окружения (.env)

```bash
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<СЛОЖНЫЙ_ПАРОЛЬ>
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=disinfection_db

# Flask
FLASK_APP=app
SECRET_KEY=<СГЕНЕРИРУЙТЕ_СЛОЖНЫЙ_КЛЮЧ>
FLASK_ENV=production

# CORS - УКАЖИТЕ ВАШ ДОМЕН
CORS_ALLOWED_ORIGINS=https://yourdomain.com

# Администратор
ADMIN_PASSWORD=<СЛОЖНЫЙ_ПАРОЛЬ>

# DaData (опционально)
DADATA_API_KEY=your_api_key
```

### Генерация секретных ключей

```bash
# Python
python -c "import secrets; print(secrets.token_hex(32))"

# Linux
openssl rand -hex 32
```

## Пошаговый деплой

### Шаг 1: Подготовка сервера

**Требования:**
- Ubuntu 20.04+ / Debian 11+
- Docker 20+
- Docker Compose 2+
- Минимум 2 GB RAM
- Минимум 10 GB диска

**Установка Docker:**

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

**Установка Docker Compose:**

```bash
sudo apt install docker-compose-plugin
```

### Шаг 2: Клонирование репозитория

```bash
git clone <repository-url>
cd disinfection-requests-system
```

### Шаг 3: Настройка конфигурации

```bash
# Копирование примера
cp .env_example .env

# Редактирование
nano .env
```

**Обязательно измените:**
- `POSTGRES_PASSWORD`
- `SECRET_KEY`
- `ADMIN_PASSWORD`
- `CORS_ALLOWED_ORIGINS` (укажите ваш домен)

### Шаг 4: Build и запуск

```bash
# Пересборка и запуск
make prod-build

# или
docker-compose up -d --build
```

### Шаг 5: Проверка статуса

```bash
# Проверка контейнеров
docker-compose ps

# Должны быть запущены:
# - postgres (healthy)
# - flask
# - nginx
```

### Шаг 6: Миграции базы данных

```bash
# Применение миграций
docker-compose exec flask flask db upgrade
```

### Шаг 7: Проверка логов

```bash
# Логи Flask
make prod-logs

# Логи Nginx
docker-compose logs -f nginx

# Логи PostgreSQL
docker-compose logs -f postgres
```

### Шаг 8: Тестирование

Откройте в браузере: `http://your-server-ip:8081`

Войдите под администратором:
- Логин: `admin`
- Пароль: значение из `ADMIN_PASSWORD`

## Настройка HTTPS

### Вариант 1: Let's Encrypt (Certbot)

**1. Установка Certbot:**

```bash
sudo apt install certbot python3-certbot-nginx
```

**2. Получение сертификата:**

```bash
sudo certbot --nginx -d yourdomain.com
```

**3. Автоматическое обновление:**

```bash
sudo systemctl enable certbot.timer
```

### Вариант 2: Самоподписанный сертификат (для тестирования)

```bash
# Создание сертификата
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout server.key \
  -out server.crt \
  -subj "/C=RU/ST=Moscow/L=Moscow/O=MyOrg/CN=yourdomain.com"
```

**Обновите nginx.conf:**

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/server.crt;
    ssl_certificate_key /etc/nginx/ssl/server.key;

    # ... rest of configuration
}
```

## Backup базы данных

### Ручной backup

```bash
# Создание дампа
docker-compose exec postgres pg_dump \
  -U postgres \
  -d disinfection_db \
  > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановление из дампа
docker-compose exec -T postgres psql \
  -U postgres \
  -d disinfection_db \
  < backup_20260414_120000.sql
```

### Автоматический backup (cron)

**Скрипт backup.sh:**

```bash
#!/bin/bash
BACKUP_DIR="/backup/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql"

# Создание директории
mkdir -p $BACKUP_DIR

# Создание дампа
docker-compose exec postgres pg_dump \
  -U postgres \
  -d disinfection_db \
  > $BACKUP_FILE

# Удаление старых бэкапов (>7 дней)
find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete

echo "Backup created: $BACKUP_FILE"
```

**Добавить в cron:**

```bash
# Открыть crontab
crontab -e

# Добавить задачу (каждый день в 2:00)
0 2 * * * /path/to/backup.sh >> /var/log/backup.log 2>&1
```

### Backup через Docker volume

```bash
# Остановка приложения
docker-compose down

# Backup volume
tar czf postgres_backup.tar.gz ~/.pg/pg_data/flask-yt/

# Восстановление
tar xzf postgres_backup.tar.gz -C /
```

## Мониторинг

### Docker stats

```bash
# Мониторинг ресурсов
docker stats
```

### Health Checks

В систему встроена поддержка health checks через API endpoints:

**Доступные endpoints:**

1. **Базовый health check:**
   ```bash
   curl http://localhost:8081/api/health/
   ```
   
   Ответ:
   ```json
   {
     "status": "healthy",
     "service": "disinfection-requests-system"
   }
   ```

2. **Расширенный health check (с проверкой БД):**
   ```bash
   curl http://localhost:8081/api/health/detailed
   ```
   
   Ответ:
   ```json
   {
     "status": "healthy",
     "service": "disinfection-requests-system",
     "checks": {
       "database": "healthy",
       "configuration": "healthy"
     }
   }
   ```

**Возможные статусы:**
- `healthy` - все системы работают (HTTP 200)
- `degraded` - частичная работоспособность, например, отсутствуют некоторые конфигурации (HTTP 200)
- `unhealthy` - критические проблемы, например, нет подключения к БД (HTTP 503)

**Health checks в Docker Compose:**

Все сервисы в docker-compose.yml настроены с health checks:

```yaml
services:
  postgres:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-mydb}"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s

  flask:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8081/api/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s
```

**Параметры health check:**
- `interval` - интервал между проверками (30 секунд)
- `timeout` - максимальное время ожидания ответа (10 секунд)
- `retries` - количество повторных попыток перед пометкой сервиса как unhealthy
- `start_period` - время на запуск сервиса перед началом проверок

**Проверка статуса health checks:**

```bash
# Статус всех health checks
docker inspect --format='{{.Name}}: {{.State.Health.Status}}' $(docker ps -q)

# Детальная информация
docker inspect --format='{{json .State.Health}}' flask

# Через Docker Compose
docker-compose ps
```

**Автоматический restart при проблемах:**

Все сервисы настроены с `restart: unless-stopped`, что обеспечивает автоматический перезапуск при падении или проблемах со здоровьем.

### Логирование

**Просмотр логов:**

```bash
# Все логи
docker-compose logs -f

# Только Flask
docker-compose logs -f flask

# Последние 100 строк
docker-compose logs --tail=100 flask
```

### Uptime мониторинг

Рекомендуемые сервисы:
- **UptimeRobot** (бесплатно, 50 проверок)
- **StatusCake** (бесплатно, 10 проверок)
- **Pingdom** (платно, расширенные функции)

## Troubleshooting

### Контейнер не запускается

```bash
# Проверка логов
docker-compose logs flask

# Проверка статуса
docker-compose ps

# Перезапуск одного контейнера
docker-compose restart flask
```

### Ошибка подключения к БД

**Причина:** PostgreSQL ещё не готов

**Решение:**

```bash
# Проверка PostgreSQL
docker-compose logs postgres

# Перезапуск
docker-compose down
docker-compose up -d

# Подождите 10-15 секунд
sleep 15

# Применение миграций
docker-compose exec flask flask db upgrade
```

### Медленная работа

**Причины:**
- Мало RAM
- Медленный диск
- Много запросов

**Решение:**

```bash
# Проверка ресурсов
docker stats

# Оптимизация PostgreSQL
docker-compose exec postgres psql -U postgres -c "SELECT * FROM pg_stat_activity;"

# Очистка кэша
docker-compose exec flask rm -rf /app/app/static/.webassets-cache/*
```

### Ошибка 502 Bad Gateway

**Причина:** Flask не отвечает

**Решение:**

```bash
# Проверка Flask
docker-compose logs flask

# Перезапуск
docker-compose restart flask

# Проверка Nginx
docker-compose logs nginx
```

### SocketIO не работает

**Причина:** Неправильная конфигурация CORS

**Решение:**

1. Проверьте `CORS_ALLOWED_ORIGINS` в `.env`
2. Перезапустите Flask: `docker-compose restart flask`
3. Проверьте логи на ошибки

### Проблемы с правами на volume

```bash
# Исправление прав
sudo chown -R 999:999 ~/.pg/pg_data/flask-yt
sudo chown -R www-data:www-data ~/.uploads/images/flask-yt
```

## Автоматические обновления безопасности

### Обновление системы (Ubuntu/Debian)

Настройте unattended-upgrades для автоматической установки security patches:

```bash
# Установка
sudo apt update
sudo apt install unattended-upgrades apt-listchanges

# Включение
sudo dpkg-reconfigure -plow unattended-upgrades
```

### Конфигурация

Отредактируйте `/etc/apt/apt.conf.d/50unattended-upgrades`:

```ini
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};

// Автоматическая перезагрузка если требуется
Unattended-Upgrade::Automatic-Reboot "false";

// Отправка email уведомлений
Unattended-Upgrade::Mail "admin@yourdomain.com";
```

### Настройка автообновления Docker образов

Создайте скрипт `scripts/auto_update.sh`:

```bash
#!/bin/bash
# Автоматическое обновление Docker контейнеров

LOG_FILE="/var/log/docker-auto-update.log"

echo "$(date): Начало обновления" >> $LOG_FILE

cd /path/to/project

# Pull новых образов
docker-compose pull >> $LOG_FILE 2>&1

# Перезапуск контейнеров
docker-compose up -d >> $LOG_FILE 2>&1

# Удаление старых образов
docker image prune -f >> $LOG_FILE 2>&1

echo "$(date): Обновление завершено" >> $LOG_FILE
echo "---" >> $LOG_FILE
```

Настройте cron для ежедневного запуска:

```bash
# crontab -e
# Ежедневное обновление в 3:00 AM
0 3 * * * /path/to/project/scripts/auto_update.sh
```

### Обновление Python зависимостей

Используйте скрипт обновления (см. [scripts/update_dependencies.sh](../scripts/update_dependencies.sh)):

```bash
# Проверка доступных обновлений (без установки)
bash scripts/update_dependencies.sh --dry-run

# Обновление зависимостей
bash scripts/update_dependencies.sh
```

**Рекомендуемый процесс:**
1. Запустите `--dry-run` для проверки доступных обновлений
2. Создайте ветку: `git checkout -b feature/update-dependencies`
3. Обновите зависимости
4. Запустите тесты и проверьте приложение
5. Закоммитьте изменения
6. Создайте pull request

### Мониторинг уязвимостей

Используйте инструменты для сканирования уязвимостей:

```bash
# Проверка уязвимостей в Python пакетах
pip install safety
safety check -r requirements.txt

# Проверка Docker образов
docker pull aquasec/trivy
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image your-image:tag
```

## Production checklist

### Безопасность

- [x] **HTTPS**: Настроен (см. [Настройка HTTPS](#настройка-https))
- [x] **Fail2Ban**: См. [FAIL2BAN_SETUP.md](FAIL2BAN_SETUP.md)
- [ ] **Автоматические обновления**: См. ниже
- [x] **Обновление зависимостей**: См. [scripts/update_dependencies.sh](../scripts/update_dependencies.sh)

Перед запуском в production убедитесь, что:

- [ ] **Безопасность**
  - [ ] Установлен сложный `SECRET_KEY` (32+ символа)
  - [ ] Установлен сложный `POSTGRES_PASSWORD`
  - [ ] Установлен сложный `ADMIN_PASSWORD`
  - [ ] `CORS_ALLOWED_ORIGINS` ограничен конкретными доменами
  - [ ] Настроен HTTPS (Let's Encrypt)
  - [ ] Файл `.env` не доступен из интернета

- [ ] **База данных**
  - [ ] Настроен автоматический backup
  - [ ] Проверена работа миграций
  - [ ] Создан индексы для часто используемых полей

- [ ] **Мониторинг**
  - [ ] Настроен логирование
  - [ ] Добавлен health check
  - [ ] Настроен uptime мониторинг
  - [ ] Настроены алерты (email/Telegram)

- [ ] **Инфраструктура**
  - [ ] Настроен firewall (только 80, 443, 22)
  - [ ] Настроен fail2ban
  - [ ] Включен автоматический update безопасности
  - [ ] Настроен NTP (синхронизация времени)

- [ ] **Документация**
  - [ ] Задокументированы все параметры `.env`
  - [ ] Создана инструкция по восстановлению из backup
  - [ ] Задокументирован процесс деплоя

- [ ] **Тестирование**
  - [ ] Пройдены все тесты (`pytest`)
  - [ ] Проведено нагрузочное тестирование
  - [ ] Проверено восстановление из backup

---

**Дата последнего обновления:** 14 апреля 2026
