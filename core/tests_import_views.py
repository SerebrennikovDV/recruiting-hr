"""Тесты страницы импорта вакансий с внешних площадок."""
from django.test import TestCase
from django.urls import reverse

from core.connectors import get_connector
from core.models import (Candidate, Department, ExternalVacancy, Role,
                         Source, User, Vacancy, VacancyStatus)


class ImportPageTests(TestCase):
    """Доступ к странице импорта и загрузка выборки."""

    @classmethod
    def setUpTestData(cls):
        cls.dep = Department.objects.create(name="Отдел разработки")
        cls.recruiter = User.objects.create_user(
            "rec", password="Hr#Unitcode2026", role=Role.RECRUITER)
        cls.candidate_user = User.objects.create_user(
            "cand", password="User#Unitcode2026", role=Role.CANDIDATE)

    def test_recruiter_sees_import_page(self):
        self.client.login(username="rec", password="Hr#Unitcode2026")
        response = self.client.get(reverse("rec_import"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Импорт вакансий")

    def test_candidate_has_no_access(self):
        self.client.login(username="cand", password="User#Unitcode2026")
        response = self.client.get(reverse("rec_import"))
        self.assertNotEqual(response.status_code, 200)

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(reverse("rec_import"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_search_saves_vacancies(self):
        self.client.login(username="rec", password="Hr#Unitcode2026")
        response = self.client.post(reverse("rec_import"), {
            "source": "hh", "query": "разработчик", "limit": 3,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ExternalVacancy.objects.exists())


class ImportTransferTests(TestCase):
    """Перенос внешней вакансии во внутренний реестр."""

    @classmethod
    def setUpTestData(cls):
        cls.dep = Department.objects.create(name="Отдел разработки")
        cls.recruiter = User.objects.create_user(
            "rec", password="Hr#Unitcode2026", role=Role.RECRUITER)

    def setUp(self):
        connector = get_connector("hh")
        connector.cache_to_db(connector.search("", limit=2), "")
        self.external = ExternalVacancy.objects.first()
        self.client.login(username="rec", password="Hr#Unitcode2026")

    def test_transfer_creates_vacancy(self):
        before = Vacancy.objects.count()
        self.client.get(reverse("rec_import_transfer",
                                args=[self.external.pk]), follow=True)

        self.assertEqual(Vacancy.objects.count(), before + 1)
        self.external.refresh_from_db()
        self.assertIsNotNone(self.external.imported_vacancy)
        vacancy = self.external.imported_vacancy
        self.assertEqual(vacancy.status, VacancyStatus.OPEN)
        self.assertEqual(vacancy.recruiter, self.recruiter)

    def test_transfer_is_not_repeated(self):
        """Повторный перенос не создаёт вторую вакансию."""
        url = reverse("rec_import_transfer", args=[self.external.pk])
        self.client.get(url, follow=True)
        before = Vacancy.objects.count()
        self.client.get(url, follow=True)
        self.assertEqual(Vacancy.objects.count(), before)
