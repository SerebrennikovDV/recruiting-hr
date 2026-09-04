"""Подсистема интеграции с внешними площадками подбора.

Реестр коннекторов позволяет обращаться к площадке по короткому имени,
не зная класса реализации. Подключение новой площадки сводится
к написанию наследника BaseVacancyConnector и одной строке в реестре.
"""
from __future__ import annotations

from .avito import AvitoConnector
from .base import BaseVacancyConnector
from .hh import HHConnector
from .superjob import SuperJobConnector

REGISTRY: dict[str, type[BaseVacancyConnector]] = {
    HHConnector.source: HHConnector,
    SuperJobConnector.source: SuperJobConnector,
    AvitoConnector.source: AvitoConnector,
}


def get_connector(name: str) -> BaseVacancyConnector:
    """Возвращает коннектор по краткому имени площадки."""
    try:
        return REGISTRY[name]()
    except KeyError:
        raise ValueError(
            f"Неизвестная площадка: {name}. "
            f"Доступны: {', '.join(sorted(REGISTRY))}"
        ) from None


def available_sources() -> list[tuple[str, str]]:
    """Пары «краткое имя - название» для выпадающего списка на форме."""
    return [(name, cls.display_name) for name, cls in sorted(REGISTRY.items())]


__all__ = [
    "BaseVacancyConnector",
    "HHConnector",
    "SuperJobConnector",
    "AvitoConnector",
    "REGISTRY",
    "get_connector",
    "available_sources",
]
