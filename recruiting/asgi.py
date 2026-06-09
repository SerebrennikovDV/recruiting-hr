"""ASGI-конфигурация проекта (для асинхронных серверов, при необходимости)."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "recruiting.settings")

application = get_asgi_application()
