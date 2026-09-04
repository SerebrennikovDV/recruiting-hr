"""Коннектор к площадке hh.ru.

Поиск вакансий доступен через открытый программный интерфейс без
авторизации, поэтому именно эта площадка используется для показа
работы подсистемы в боевом режиме.
"""
from __future__ import annotations

import logging

from django.conf import settings

from .base import BaseVacancyConnector

logger = logging.getLogger(__name__)

MOSCOW_AREA_ID = 1


class HHConnector(BaseVacancyConnector):
    source = "hh"
    display_name = "hh.ru"
    mock_filename = "hh_sample.json"

    def _real_search(self, query: str, limit: int) -> list[dict]:
        import requests

        base = settings.CONNECTORS["HH_API_BASE"]
        response = requests.get(
            f"{base}/vacancies",
            params={
                "text": query,
                "per_page": min(limit, 100),
                "area": MOSCOW_AREA_ID,
            },
            # Площадка требует указывать приложение в заголовке запроса.
            headers={"User-Agent": "UnitHire/2.0 (student project)"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()

        result = []
        for item in payload.get("items", []):
            snippet = item.get("snippet") or {}
            requirement = snippet.get("requirement") or ""
            responsibility = snippet.get("responsibility") or ""
            description = f"{requirement} {responsibility}".strip()
            salary = item.get("salary") or {}
            result.append({
                "external_id": str(item.get("id", "")),
                "title": item.get("name", ""),
                "description": description,
                "keywords": self.extract_keywords(description),
                "url": item.get("alternate_url", ""),
                "salary_from": salary.get("from"),
                "salary_to": salary.get("to"),
            })
        return result
