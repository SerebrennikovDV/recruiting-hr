"""
Файл конфигурации Django-проекта «Рекрутинговая информационная система
с HR-аналитикой» (ООО «ЮНИТКОД»).

Автор: Серебренников Д. В.
Тема ВКР: «Проектирование рекрутинговой информационной системы на основе
HR-аналитики».

Настройки рассчитаны на два режима работы:
1. Локальная разработка/проверка — СУБД SQLite (не требует установки сервера БД).
2. Промышленная эксплуатация в Yandex Cloud (Compute Cloud VM + PostgreSQL 15
   в Docker-контейнере либо Managed Service for PostgreSQL) — адрес БД
   передаётся через переменную окружения DATABASE_URL.
Выбор СУБД выполняется автоматически по наличию переменной DATABASE_URL,
поэтому один и тот же код работает и локально, и в облаке.
"""

from pathlib import Path
import os

import dj_database_url
from dotenv import load_dotenv

# Корневой каталог проекта (на один уровень выше пакета recruiting/).
BASE_DIR = Path(__file__).resolve().parent.parent

# Загружаем переменные окружения из файла .env (если он присутствует рядом).
# Секреты (ключ приложения, пароль БД) не хранятся в репозитории — только в .env.
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    """Прочитать булеву переменную окружения ('1', 'true', 'yes' -> True)."""
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


# --- Безопасность -----------------------------------------------------------
# Секретный ключ берётся из окружения; значение по умолчанию пригодно только
# для локальной разработки и НЕ должно использоваться в продакшене.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-insecure-key-only-for-local-use-change-me-in-production",
)

# Режим отладки по умолчанию выключен; включается переменной окружения.
DEBUG = env_bool("DJANGO_DEBUG", True)

# Список разрешённых хостов. Локально — стандартные адреса, в продакшене на
# Yandex Cloud — публичный IP или домен ВМ через DJANGO_ALLOWED_HOSTS.
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]", "testserver"]
_extra_hosts = os.environ.get("DJANGO_ALLOWED_HOSTS", "")
if _extra_hosts:
    ALLOWED_HOSTS += [h.strip() for h in _extra_hosts.split(",") if h.strip()]

# Доверенные источники CSRF: указываются полной строкой включая схему,
# например "http://111.88.244.202" или "https://unithire.example.ru".
CSRF_TRUSTED_ORIGINS = []
for _origin in os.environ.get("DJANGO_CSRF_TRUSTED", "").split(","):
    if _origin.strip():
        CSRF_TRUSTED_ORIGINS.append(_origin.strip())

# --- Приложения -------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",          # встроенная панель администратора
    "django.contrib.auth",           # подсистема аутентификации и прав
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",       # всплывающие уведомления (flash)
    "django.contrib.humanize",       # человекочитаемое форматирование чисел/дат
    "django.contrib.staticfiles",
    "django_filters",                # поиск и фильтрация в списках
    "core",                          # основное приложение проекта
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise отдаёт статические файлы в продакшене без отдельного веб-сервера.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "recruiting.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Собственный процессор контекста: пункты меню, ФИО автора,
                # год и счётчики для шапки/подвала на всех страницах сайта.
                "core.context_processors.site_globals",
            ],
        },
    },
]

WSGI_APPLICATION = "recruiting.wsgi.application"

# --- База данных ------------------------------------------------------------
# По умолчанию — локальный файл SQLite. Если задана переменная DATABASE_URL
# (Yandex Cloud — Managed PG или PostgreSQL в Docker-контейнере), используется именно она.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        ssl_require=env_bool("DB_SSL_REQUIRE", False),
    )
}

# --- Проверка паролей -------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 6}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Собственная модель пользователя с полем «роль» (см. core/models.py).
AUTH_USER_MODEL = "core.User"

# --- Локализация ------------------------------------------------------------
LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

# --- Статика и медиа --------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"           # куда collectstatic собирает файлы
STATICFILES_DIRS = [BASE_DIR / "static"]          # исходные статические файлы проекта
# Сжатие и кеширование статики средствами WhiteNoise в продакшене.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"
        if not DEBUG
        else "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"                   # загруженные пользователями файлы (резюме)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Аутентификация: маршруты входа/выхода ---------------------------------
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"                  # после входа — общий диспетчер кабинетов
LOGOUT_REDIRECT_URL = "home"

# --- Сопоставление уровней сообщений с CSS-классами Bootstrap ---------------
from django.contrib.messages import constants as message_constants  # noqa: E402

MESSAGE_TAGS = {
    message_constants.DEBUG: "secondary",
    message_constants.INFO: "info",
    message_constants.SUCCESS: "success",
    message_constants.WARNING: "warning",
    message_constants.ERROR: "danger",
}

# --- Прикладные константы проекта ------------------------------------------
# ФИО автора выводится в подвале каждой страницы и в разделе «Справка».
SITE_AUTHOR = "Серебренников Д. В."
SITE_AUTHOR_FULL = "Серебренников Дмитрий Валерьевич"
SITE_ORG = 'ООО «ЮНИТКОД»'
SITE_NAME = "UnitHire"
SITE_TAGLINE = "Рекрутинговая платформа с HR-аналитикой"

# Размер страницы для пагинации списков (вакансии, кандидаты, заявки).
PAGE_SIZE = 8

# Ограничение на загружаемые резюме: 5 МБ, допустимые расширения.
RESUME_MAX_SIZE_MB = 5
RESUME_ALLOWED_EXT = [".pdf", ".doc", ".docx", ".rtf", ".odt"]

# В продакшене (DEBUG=False) включаем безопасные заголовки.
# Cookie помечаем атрибутом Secure только если приложение реально работает
# по HTTPS — иначе авторизация и CSRF по HTTP перестанут работать (cookie
# не отправится). Управляется переменной окружения DJANGO_USE_HTTPS.
# Для развёртывания UnitHire на Yandex Cloud по публичному IP без домена
# используется HTTP, поэтому DJANGO_USE_HTTPS=False (см. .env.example).
if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = "DENY"
    if env_bool("DJANGO_USE_HTTPS", False):
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
        SESSION_COOKIE_SECURE = True
        CSRF_COOKIE_SECURE = True
        SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # 30 дней
        SECURE_HSTS_INCLUDE_SUBDOMAINS = True
