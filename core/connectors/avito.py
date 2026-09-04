"""Коннектор к площадке Avito.

Раздел вакансий доступен по программному интерфейсу с токеном, который
выдаётся после подключения делового кабинета. Как и для SuperJob,
разбор ответа реализован полностью, а работа по умолчанию идёт
на сохранённом ответе площадки.
"""
from __future__ import annotations

import logging

from django.conf import settings

from .base import BaseVacancyConnector

logger = logging.getLogger(__name__)


class AvitoConnector(BaseVacancyConnector):
    source = "avito"
    display_name = "Avito Работа"
    mock_filename = "avito_sample.json"

    def _real_search(self, query: str, limit: int) -> list[dict]:
        import requests

        token = settings.CONNECTORS["AVITO_TOKEN"]
        if not token:
            logger.info("Токен доступа Avito не задан, выборка пуста")
            return []

        base = settings.CONNECTORS["AVITO_API_BASE"]
        response = requests.get(
            f"{base}/job/v1/vacancies",
            params={"query": query, "limit": min(limit, 100)},
            headers={"Authorization": f"Bearer {token}"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()

        result = []
        for item in payload.get("resources", payload.get("items", [])):
            description = (item.get("description") or "").strip()
            salary = item.get("salary") or {}
            result.append({
                "external_id": str(item.get("id", "")),
                "title": item.get("title", ""),
                "description": description,
                "keywords": self.extract_keywords(description),
                "url": item.get("url", ""),
                "salary_from": salary.get("from") or item.get("salary_from"),
                "salary_to": salary.get("to") or item.get("salary_to"),
            })
        return result
