#!/usr/bin/env python
"""
Скрипт для проверки production конфигурации перед деплоем.
"""
import os
import sys

def validate_production_config():
    """Проверяет что все необходимые переменные окружения установлены."""
    
    required_vars = [
        'FLASK_ENV',
        'DATABASE_URL',
        'JWT_SECRET_KEY',
        'SECRET_KEY',
        'REDIS_URL',
        'ADMIN_PASSWORD',
        'CORS_ALLOWED_ORIGINS',
    ]
    
    missing = []
    warnings = []
    
    print("Проверка production конфигурации...\n")
    
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            missing.append(var)
        else:
            # Проверяем длину секретов
            if var in ['JWT_SECRET_KEY', 'SECRET_KEY'] and len(value) < 32:
                warnings.append(f"{var} слишком короткий (минимум 32 символа)")
            
            # Проверяем что используем дефолтные значения
            if var == 'JWT_SECRET_KEY' and value == 'dev-secret-key-change-in-production':
                warnings.append(f"{var} использует дефолтное значение!")
            
            if var == 'ADMIN_PASSWORD' and len(value) < 12:
                warnings.append(f"{var} слишком короткий (минимум 12 символов)")
    
    # Проверяем окружение
    flask_env = os.environ.get('FLASK_ENV')
    if flask_env != 'production':
        warnings.append(f"FLASK_ENV={flask_env}, ожидалось 'production'")
    
    # Проверяем DEBUG
    debug = os.environ.get('DEBUG', 'False').lower()
    if debug == 'true' and flask_env == 'production':
        warnings.append("DEBUG=True в production - это опасно!")
    
    # Выводим результаты
    if missing:
        print("ОТСУТСТВУЮЩИЕ ПЕРЕМЕННЫЕ:")
        for var in missing:
            print(f"   - {var}")
        print()
    
    if warnings:
        print("ПРЕДУПРЕЖДЕНИЯ:")
        for warning in warnings:
            print(f"   - {warning}")
        print()
    
    if not missing and not warnings:
        print("Все проверки пройдены успешно!")
        return True
    elif missing:
        print("Конфигурация не готова к production!")
        return False
    else:
        print("Конфигурация готова, но есть предупреждения")
        return True


if __name__ == '__main__':
    success = validate_production_config()
    sys.exit(0 if success else 1)