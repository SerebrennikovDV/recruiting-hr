"""
Контекст-процессор: добавляет в каждый шаблон общие данные сайта — пункты
главного меню, ФИО автора, название и слоган сервиса, текущий год. Благодаря
этому шапка, навигация и подвал единообразны на всех страницах.
"""
from django.conf import settings
from django.utils import timezone


# Пункты верхнего меню навигации (≥10 пунктов согласно требованиям).
# Каждый элемент: (имя URL-маршрута, подпись, иконка bootstrap-icons).
MAIN_MENU = [
    ("home", "Главная", "house"),
    ("vacancies", "Вакансии", "briefcase"),
    ("how_it_works", "Как это работает", "diagram-3"),
    ("employers", "Работодателям", "building"),
    ("candidates_info", "Соискателям", "person-badge"),
    ("analytics_demo", "HR-аналитика", "bar-chart-line"),
    ("news", "Новости", "newspaper"),
    ("about", "О компании", "info-circle"),
    ("contacts", "Контакты", "envelope"),
    ("help", "Справка", "question-circle"),
]


def site_globals(request):
    """Вернуть словарь переменных, доступных во всех шаблонах проекта."""
    return {
        "MAIN_MENU": MAIN_MENU,
        "SITE_AUTHOR": settings.SITE_AUTHOR,
        "SITE_AUTHOR_FULL": settings.SITE_AUTHOR_FULL,
        "SITE_ORG": settings.SITE_ORG,
        "SITE_NAME": settings.SITE_NAME,
        "SITE_TAGLINE": settings.SITE_TAGLINE,
        "CURRENT_YEAR": timezone.localdate().year,
    }
