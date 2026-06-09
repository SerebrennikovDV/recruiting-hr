#!/usr/bin/env python
"""Стандартная утилита командной строки Django для административных задач."""
import os
import sys


def main():
    """Точка входа: настраивает модуль настроек и передаёт управление Django."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "recruiting.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Не удалось импортировать Django. Убедитесь, что он установлен и "
            "доступно виртуальное окружение (см. README.md)."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
