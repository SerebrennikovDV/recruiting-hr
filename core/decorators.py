"""
Декораторы и примеси (mixins) для разграничения прав доступа по ролям.

Используются для защиты представлений личных кабинетов рекрутёра и кандидата:
пользователь, не обладающий нужной ролью, перенаправляется на страницу входа
или получает понятное сообщение об отсутствии прав (а не пустое окно).
"""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from .models import Role


def role_required(*roles):
    """
    Фабрика декораторов: пропускает только пользователей с одной из указанных
    ролей. Суперпользователь имеет доступ ко всему.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                # Неавторизованного отправляем на форму входа с возвратом назад.
                return redirect_to_login(request.get_full_path())
            if user.is_superuser or user.role in roles:
                return view_func(request, *args, **kwargs)
            messages.error(
                request,
                "Недостаточно прав для доступа к этому разделу. "
                "Войдите под подходящей учётной записью.",
            )
            raise PermissionDenied("Доступ запрещён для данной роли")

        return _wrapped

    return decorator


# Готовые декораторы для конкретных ролей — удобные сокращения.
recruiter_required = role_required(Role.RECRUITER)
candidate_required = role_required(Role.CANDIDATE)
admin_required = role_required(Role.ADMIN)
