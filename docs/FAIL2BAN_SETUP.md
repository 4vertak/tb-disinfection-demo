# Настройка Fail2Ban для защиты системы

## Что такое Fail2Ban?

Fail2Ban - это система защиты от брутфорс-атак и сканирования портов. Она анализирует логи и банит IP-адреса с подозрительной активностью.

## Установка на хост-машину

### 1. Установка Fail2Ban

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install fail2ban

# CentOS/RHEL
sudo yum install fail2ban
```

### 2. Создание конфигурации

Создайте файл `/etc/fail2ban/jail.local`:

```bash
sudo nano /etc/fail2ban/jail.local
```

Добавьте следующее содержимое:

```ini
[DEFAULT]
# Игнорировать локальные IP
ignoreip = 127.0.0.1/8 ::1 192.168.1.0/24

# Время бана (1 час)
bantime = 3600

# Количество попыток
maxretry = 5

# Окно времени (10 минут)
findtime = 600

# Действие при бане
action = %(action_mwl)s

# Email для уведомлений (опционально)
# destemail = admin@yourdomain.com
# sender = fail2ban@yourdomain.com

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-botsearch]
enabled = true
filter = nginx-botsearch
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 2

[nginx-badbots]
enabled = true
filter = nginx-badbots
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 2

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 5
```

### 3. Создание фильтров

Создайте фильтр для Rate Limiting:

```bash
sudo nano /etc/fail2ban/filter.d/nginx-limit-req.conf
```

Добавьте:

```ini
[Definition]
failregex = ^.*limiting requests, excess:.* by zone ".*", client: <HOST>.*$
ignoreregex =
```

### 4. Настройка логирования Nginx

Убедитесь, что Nginx логирует правильно. В `nginx.conf`:

```nginx
log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                '$status $body_bytes_sent "$http_referer" '
                '"$http_user_agent" "$http_x_forwarded_for"';

access_log /var/log/nginx/access.log main;
error_log /var/log/nginx/error.log warn;
```

### 5. Запуск Fail2Ban

```bash
# Запуск сервиса
sudo systemctl start fail2ban

# Включение автозагрузки
sudo systemctl enable fail2ban

# Проверка статуса
sudo systemctl status fail2ban
```

## Мониторинг

### Проверка забаненных IP

```bash
# Список всех jails
sudo fail2ban-client status

# Статус конкретного jail
sudo fail2ban-client status nginx-http-auth
sudo fail2ban-client status nginx-limit-req

# Разбанить IP
sudo fail2ban-client set nginx-limit-req unbanip <IP_ADDRESS>
```

### Просмотр логов

```bash
# Логи fail2ban
sudo tail -f /var/log/fail2ban.log

# Логи nginx
sudo tail -f /var/log/nginx/error.log
```

## Интеграция с Docker

Если используете Docker, есть два подхода:

### Подход 1: Fail2Ban на хост-машине

Просто направьте логи Docker на хост-машину:

```bash
# Создание директории для логов
mkdir -p /var/log/docker

# Запуск контейнеров с логированием в файл
docker-compose up -d

# Копирование логов
docker logs -f nginx > /var/log/nginx/access.log 2>&1 &
docker logs -f flask > /var/log/flask.log 2>&1 &
```

### Подход 2: Fail2Ban в Docker

Создайте `docker-compose.fail2ban.yml`:

```yaml
version: '3.8'

services:
  fail2ban:
    image: crazymax/fail2ban:latest
    container_name: fail2ban
    cap_add:
      - NET_ADMIN
      - NET_RAW
    volumes:
      - ./fail2ban/data:/data
      - /var/log:/var/log:ro
    env_file:
      - .env
    restart: unless-stopped
    network_mode: "host"
```

Запуск:

```bash
docker-compose -f docker-compose.fail2ban.yml up -d
```

## Тестирование

### Проверка работы

```bash
# Попытайтесь войти несколько раз с неправильными данными
# После maxretry попыток IP будет забанен

# Проверка бана
sudo fail2ban-client status nginx-http-auth
```

### Симуляция атаки

```bash
# С другого сервера или используйте Docker
for i in {1..10}; do
  curl -s http://your-server/login -d "username=admin&password=wrong" > /dev/null
done

# Проверьте логи
sudo tail -f /var/log/fail2ban.log
```

## Настройка уведомлений

### Email уведомления

В `/etc/fail2ban/jail.local`:

```ini
[DEFAULT]
destemail = admin@yourdomain.com
sender = fail2ban@yourdomain.com
action = %(action_mwl)s
```

### Telegram уведомления

Создайте скрипт `/etc/fail2ban/action.d/telegram.conf`:

```ini
[Definition]
actionstart = 
actionstop = 
actioncheck = 
actionban = curl -s -X POST "https://api.telegram.org/bot<BOT_TOKEN>/sendMessage" -d "chat_id=<CHAT_ID>&text=🚫 Ban: <ip> on <hostname> at <time>"
actionunban = curl -s -X POST "https://api.telegram.org/bot<BOT_TOKEN>/sendMessage" -d "chat_id=<CHAT_ID>&text=✅ Unban: <ip> on <hostname>"
```

## Best Practices

1. **Не баните надолго**: 1-24 часа достаточно
2. ** whitelist локальные IP**: 127.0.0.1, ваши офисные IP
3. ** мониторьте логи**: Регулярно проверяйте логи на ложные срабатывания
4. **Тестируйте**: Проверяйте работу бана перед production
5. **Документируйте**: Ведите логику ваших настроек

## Troubleshooting

### Fail2Ban не запускается

```bash
# Проверка конфигурации
sudo fail2ban-client -t

# Проверка логов
sudo tail -f /var/log/fail2ban.log
```

### IP не банится

```bash
# Проверка regex
sudo fail2ban-client get nginx-limit-req failregex
sudo fail2ban-client get nginx-limit-req fail2ban-regex
```

### Ложные срабатывания

```bash
# Разбанить IP
sudo fail2ban-client set nginx-limit-req unbanip <IP>

# Увеличить maxretry
# В /etc/fail2ban/jail.local измените maxretry = 10
```

---

**Важно**: Fail2Ban защищает только на уровне HTTP. Для полной безопасности используйте:
- HTTPS (настроен)
- Health checks (настроены)
- Rate limiting (настроен в приложении)
- Регулярные обновления безопасности
