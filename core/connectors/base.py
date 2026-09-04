"""Базовый коннектор к внешним площадкам подбора.

Реализации (hh.ru, SuperJob, Avito) наследуют этот класс и определяют
только метод _real_search - обращение к программному интерфейсу
конкретной площадки. Выбор режима работы, приведение ответа к единому
формату и сохранение выборки в базу общие для всех коннекторов,
поэтому добавление новой площадки не затрагивает остальной код.
"""
from __future__ import annotations

import abc
import json
import logging
from typing import Iterable

from django.conf import settings

logger = logging.getLogger(__name__)


class BaseVacancyConnector(abc.ABC):
    """Общий интерфейс коннектора к площадке поиска работы."""

    #: Краткое имя источника: hh, superjob, avito.
    source: str = ""
    #: Человекочитаемое название площадки.
    display_name: str = ""
    #: Имя файла с сохранённым ответом в core/connectors/fixtures/.
    mock_filename: str = ""

    def __init__(self) -> None:
        self.fixtures_path = settings.CONNECTORS["FIXTURES_PATH"]
        self.mock_mode = settings.CONNECTORS["MOCK_MODE"]
        self.timeout = settings.CONNECTORS["REQUEST_TIMEOUT"]

    # -- публичный интерфейс ----------------------------------------------

    def search(self, query: str, limit: int = 20) -> list[dict]:
        """Возвращает вакансии площадки в едином формате.

        Каждый элемент содержит ключи external_id, title, description,
        keywords, url, salary_from, salary_to. Единый формат позволяет
        обрабатывать выборку одинаково независимо от площадки.
        """
        if self.mock_mode:
            return self._mock_search(query, limit)
        try:
            return self._real_search(query, limit)
        except Exception as exc:
            # Недоступность площадки не должна ронять страницу импорта:
            # рекрутёр получит пустой список и сообщение об ошибке.
            logger.warning("Площадка %s недоступна: %s", self.source, exc)
            return []

    def cache_to_db(self, vacancies: Iterable[dict], query: str) -> int:
        """Сохраняет выборку в хранилище внешних вакансий."""
        from core.models import ExternalVacancy

        saved = 0
        for item in vacancies:
            ExternalVacancy.objects.update_or_create(
                source=self.source,
                external_id=str(item.get("external_id", "")),
                defaults={
                    "query": query,
                    "title": item.get("title", "")[:200],
                    "description": item.get("description", ""),
                    "url": item.get("url", ""),
                    "salary_from": item.get("salary_from") or 0,
                    "salary_to": item.get("salary_to") or 0,
                    "keywords": item.get("keywords", []),
                },
            )
            saved += 1
        return saved

    # -- режим воспроизведения --------------------------------------------

    def _mock_search(self, query: str, limit: int) -> list[dict]:
        """Отдаёт сохранённый ответ площадки из файла фикстуры."""
        if not self.mock_filename:
            return []
        path = self.fixtures_path / self.mock_filename
        if not path.exists():
            logger.warning("Сохранённый ответ не найден: %s", path)
            return []
        try:
            items = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            logger.error("Ошибка чтения файла %s: %s", path, exc)
            return []

        # Отбор по запросу: сохранённый ответ содержит несколько вакансий,
        # и поиск должен вести себя так же, как на площадке.
        needle = query.lower().strip()
        if needle:
            items = [
                item for item in items
                if needle in (f'{item.get("title", "")} '
                              f'{item.get("description", "")}').lower()
            ] or items
        return items[:limit]

    @abc.abstractmethod
    def _real_search(self, query: str, limit: int) -> list[dict]:
        """Обращение к программному интерфейсу площадки."""
        raise NotImplementedError

    # -- вспомогательное ---------------------------------------------------

    @staticmethod
    def extract_keywords(text: str, limit: int = 12) -> list[str]:
        """Выделяет из текста требований технические термины.

        Отбираются слова длиннее трёх знаков, записанные латиницей либо
        начинающиеся с заглавной буквы: названия технологий в описаниях
        вакансий выглядят именно так.
        """
        import re

        words = re.findall(r"[A-Za-zА-Яа-яЁё][\w\-+.#]{2,}", text or "")
        keywords, seen = [], set()
        for word in words:
            token = word.strip(".,;:")
            if len(token) < 3:
                continue
            lowered = token.lower()
            if lowered in seen:
                continue
            if token.isascii() or token[0].isupper():
                seen.add(lowered)
                keywords.append(token)
            if len(keywords) >= limit:
                break
        return keywords
