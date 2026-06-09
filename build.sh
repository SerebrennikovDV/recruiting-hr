#!/usr/bin/env bash
# Скрипт сборки для развёртывания на хостинге Render.
# Останавливаемся при первой же ошибке.
set -o errexit

# Установка зависимостей.
pip install -r requirements.txt

# Сбор статических файлов (WhiteNoise отдаёт их в продакшене).
python manage.py collectstatic --no-input

# Применение миграций базы данных.
python manage.py migrate

# Первичное наполнение базы демонстрационными данными (только если пусто).
python manage.py seed_demo
