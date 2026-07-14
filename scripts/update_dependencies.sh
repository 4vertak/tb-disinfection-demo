#!/bin/bash

# Скрипт для безопасного обновления зависимостей
# Использование: bash scripts/update_dependencies.sh [--dry-run]

set -e

DRY_RUN=false
if [ "$1" == "--dry-run" ]; then
    DRY_RUN=true
    echo "🔍 DRY RUN MODE - только показ обновлений"
    echo ""
fi

echo "Обновление зависимостей Python"
echo ""

# Проверка виртуального окружения
if [ ! -d "venv" ]; then
    echo "Виртуальное окружение 'venv' не найдено"
    echo "Создайте: python -m venv venv && source venv/bin/activate"
    exit 1
fi

# Активация venv
source venv/bin/activate

# Проверка pip
echo "🔧 Проверка pip..."
pip install --upgrade pip

if [ "$DRY_RUN" = true ]; then
    echo ""
    echo "Список доступных обновлений:"
    pip list --outdated
    echo ""
    echo "Для реального обновления запустите без --dry-run"
    exit 0
fi

# Backup текущего requirements.txt
echo "Создание backup requirements.txt..."
cp requirements.txt requirements.txt.backup.$(date +%Y%m%d_%H%M%S)

# Обновление зависимостей
echo ""
echo "Обновление зависимостей..."
pip list --outdated --format=columns | tail -n +3 | awk '{print $1}' | while read package; do
    echo "Обновление $package..."
    pip install --upgrade "$package"
done

# Генерация нового requirements.txt
echo ""
echo "Генерация requirements.txt..."
pip freeze > requirements.txt

# Удаление дубликатов и сортировка
echo "Сортировка requirements.txt..."
sort -u -o requirements.txt requirements.txt

echo ""
echo "Зависимости обновлены!"
echo ""
echo "Следующие шаги:"
echo "1. Проверьте изменения: diff requirements.txt.backup.* requirements.txt"
echo "2. Запустите тесты: make test (если есть)"
echo "3. Проверьте приложение локально"
echo "4. Закоммитьте изменения: git add requirements.txt && git commit -m 'chore: update dependencies'"
