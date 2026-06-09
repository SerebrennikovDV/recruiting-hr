"""
WSGI-конфигурация проекта «Рекрутинговая ИС с HR-аналитикой».

Файл предоставляет вызываемый объект application, который используется
сервером приложений (gunicorn) на хостинге для обработки запросов.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "recruiting.settings")

application = get_wsgi_application()
