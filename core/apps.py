from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Конфигурация основного приложения «core» рекрутинговой ИС."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Рекрутинговая ИС"
