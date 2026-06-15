FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=recruiting.settings

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Сбор статики выполняется на старте контейнера, чтобы переменные
# окружения уже были доступны.
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

# Gunicorn в режиме gthread: 4 процесса × 8 потоков = до 32 одновременных
# обработчиков. Подобрано под VM 2 vCPU / 2 ГБ RAM с расчётом на нагрузку
# до 50 параллельных пользователей (см. tools/load_test.py и раздел 3.4.2
# отчёта). При gthread потоки разделяют память процесса, что снижает
# суммарный расход RAM по сравнению с такой же конфигурацией на sync.
CMD ["gunicorn", "recruiting.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "gthread", \
     "--threads", "8", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
