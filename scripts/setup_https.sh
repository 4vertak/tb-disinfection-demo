#!/bin/bash

# Скрипт для настройки HTTPS с помощью Let's Encrypt
# Использование: bash scripts/setup_https.sh your_domain.com

set -e

DOMAIN=${1:-}

if [ -z "$DOMAIN" ]; then
    echo "Укажите домен: bash scripts/setup_https.sh your_domain.com"
    exit 1
fi

echo "Настройка HTTPS для домена: $DOMAIN"
echo ""

# Создание директории для certbot
echo "Создание директорий..."
mkdir -p ./nginx/certbot
mkdir -p ./nginx/certbot/www

# Проверка наличия docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "docker-compose не установлен"
    exit 1
fi

# Запуск certbot для получения сертификатов
echo "Запуск certbot..."
docker-compose run --rm certbot certonly --webroot \
    --webroot-path=/var/www/certbot \
    -d $DOMAIN \
    --email admin@$DOMAIN \
    --agree-tos \
    --no-eff-email \
    --force-renewal

if [ $? -eq 0 ]; then
    echo ""
    echo "Сертификаты успешно получены!"
    echo ""
    echo "Следующие шаги:"
    echo "1. Раскомментируйте HTTPS секцию в nginx/nginx.conf"
    echo "2. Замените 'your_domain.com' на '$DOMAIN' в nginx/nginx.conf"
    echo "3. Перезапустите nginx: docker-compose restart nginx"
    echo ""
    echo "Для автоматического обновления сертификатов:"
    echo "   docker-compose run --rm certbot renew"
    echo ""
else
    echo "Ошибка при получении сертификатов"
    exit 1
fi
