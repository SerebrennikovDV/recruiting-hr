#!/usr/bin/env python
"""
main.py — единая точка запуска веб-сервиса «UnitHire» (рекрутинговая ИС
с HR-аналитикой).

Согласно требованиям к сетевому ресурсу, в корне репозитория размещён файл,
запускающий приложение. Скрипт выполняет полный цикл подготовки и старта:

    1) применяет миграции базы данных (создаёт таблицы при первом запуске);
    2) при пустой базе загружает демонстрационные данные (фикстуры);
    3) запускает встроенный веб-сервер разработки Django.

Запуск:  python main.py            (сервер на http://127.0.0.1:8000/)
         python main.py 0.0.0.0:8080

Автор: Серебренников Д. В.
"""
import os
import sys

import django
from django.core.management import call_command


def _setup():
    """Инициализация Django до обращения к моделям и командам."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "recruiting.settings")
    django.setup()


def _ensure_data():
    """Применить миграции и при необходимости наполнить базу демо-данными."""
    print("[main] Применяю миграции базы данных…")
    call_command("migrate", interactive=False, verbosity=1)

    # Если в базе ещё нет ни одной вакансии — считаем её пустой и наполняем.
    from core.models import Vacancy
    if not Vacancy.objects.exists():
        print("[main] База пуста — загружаю демонстрационные данные…")
        call_command("seed_demo", verbosity=1)
    else:
        print("[main] Демонстрационные данные уже загружены, пропускаю наполнение.")


def main():
    _setup()
    _ensure_data()
    addr = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1:8000"
    print(f"[main] Запускаю веб-сервер на http://{addr}/  (Ctrl+C — остановка)")
    # noreload — чтобы скрипт не перезапускал сам себя и не дублировал подготовку.
    call_command("runserver", addr, use_reloader=False)


if __name__ == "__main__":
    main()
