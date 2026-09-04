"""Коннектор к площадке SuperJob.

Промышленный интерфейс требует ключа приложения, который выдаётся
юридическому лицу после модерации. Пока ключа нет, коннектор работает
на сохранённом ответе площадки - структура запроса и разбора ответа
при этом реализована полностью.
"""
from __future__ import annotations

import logging

from django.conf import settings

from .base import BaseVacancyConnector

logger = logging.getLogger(__name__)


class SuperJobConnector(BaseVacancyConnector):
    source = "superjob"
    display_name = "SuperJob"
    mock_filename = "superjob_sample.json"

    def _real_search(self, query: str, limit: int) -> list[dict]:
        import requests

        secret = settings.CONNECTORS["SUPERJOB_SECRET"]
        if not secret:
            logger.info("Ключ доступа SuperJob не задан, выборка пуста")
            return []

        base = settings.CONNECTORS["SUPERJOB_API_BASE"]
        response = requests.get(
            f"{base}/vacancies/",
            params={"keyword": query, "count": min(limit, 100)},
            headers={"X-Api-App-Id": secret},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()

        result = []
        for item in payload.get("objects", []):
            description = (item.get("candidat") or "").strip()
            result.append({
                "external_id": str(item.get("id", "")),
                "title": item.get("profession", ""),
                "description": description,
                "keywords": self.extract_keywords(description),
                "url": item.get("link", ""),
                "salary_from": item.get("payment_from"),
                "salary_to": item.get("payment_to"),
            })
        return result
