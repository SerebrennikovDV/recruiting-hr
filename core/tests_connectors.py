"""Тесты подсистемы интеграции с внешними площадками подбора.

Проверки идут в режиме сохранённых ответов площадок: тесты не должны
зависеть от доступности внешнего сервиса и от наличия ключей доступа.
"""
from django.test import TestCase, override_settings

from core.connectors import (REGISTRY, AvitoConnector, HHConnector,
                             SuperJobConnector, available_sources,
                             get_connector)
from core.models import ExternalVacancy


class ConnectorRegistryTests(TestCase):
    """Реестр площадок."""

    def test_registry_contains_three_sources(self):
        self.assertEqual(set(REGISTRY), {"hh", "superjob", "avito"})

    def test_get_connector_returns_instance(self):
        self.assertIsInstance(get_connector("hh"), HHConnector)
        self.assertIsInstance(get_connector("superjob"), SuperJobConnector)
        self.assertIsInstance(get_connector("avito"), AvitoConnector)

    def test_unknown_source_raises(self):
        with self.assertRaises(ValueError):
            get_connector("rabota")

    def test_available_sources_for_form(self):
        sources = dict(available_sources())
        self.assertEqual(sources["hh"], "hh.ru")
        self.assertEqual(len(sources), 3)


class ConnectorMockModeTests(TestCase):
    """Работа на сохранённых ответах площадок."""

    def test_search_returns_vacancies(self):
        for name in REGISTRY:
            with self.subTest(source=name):
                items = get_connector(name).search("разработчик", limit=5)
                self.assertTrue(items, f"площадка {name} вернула пустой ответ")
                self.assertLessEqual(len(items), 5)

    def test_result_has_common_format(self):
        item = get_connector("hh").search("разработчик", limit=1)[0]
        for key in ("external_id", "title", "description"):
            self.assertIn(key, item)

    def test_limit_is_respected(self):
        items = get_connector("hh").search("", limit=2)
        self.assertLessEqual(len(items), 2)
