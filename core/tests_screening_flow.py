"""Тесты сквозного сценария первичного отбора резюме."""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from core.models import (Application, ApplicationStatus, Candidate,
                         Department, Match, ResumeFile, Role, Skill, Source,
                         Stage, User, Vacancy, VacancySkill, VacancyStatus)
from core.screening.services import parse_resume, score_application


class ScreeningFlowTests(TestCase):
    """Разбор резюме и расчёт оценки на реальных объектах системы."""

    @classmethod
    def setUpTestData(cls):
        cls.dep = Department.objects.create(name="Отдел разработки")
        cls.src = Source.objects.create(name="hh.ru", cost_per_contact=1000)
        cls.stage = Stage.objects.create(name="Скрининг", order=1)
        cls.user = User.objects.create_user(
            "cand", password="User#Unitcode2026", role=Role.CANDIDATE)
        cls.candidate = Candidate.objects.create(
            user=cls.user, last_name="Новиков", first_name="Максим",
            email="cand@example.com", source=cls.src)
        cls.vacancy = Vacancy.objects.create(
            title="Python-разработчик", department=cls.dep,
            grade="middle", status=VacancyStatus.OPEN)
        for name, required in (("Python", True), ("Django", True),
                               ("Kubernetes", False)):
            skill = Skill.objects.create(name=name)
            VacancySkill.objects.create(vacancy=cls.vacancy, skill=skill,
                                        is_required=required)

    def _attach_resume(self, text: str) -> ResumeFile:
        """Готовит файл резюме в формате .docx.

        Формат .txt не входит в список разрешённых, такой файл
        сохраняется с расширением .bin и разборщиком не читается.
        """
        import io

        from docx import Document

        document = Document()
        for line in text.splitlines() or [text]:
            document.add_paragraph(line)
        buffer = io.BytesIO()
        document.save(buffer)
        return ResumeFile.objects.create(
            candidate=self.candidate, title="Резюме",
            file=SimpleUploadedFile("resume.docx", buffer.getvalue()))

    def test_parse_resume_saves_text_and_experience(self):
        resume = self._attach_resume("Python Django. Опыт работы 4 года.")
        parsed = parse_resume(resume)

        self.assertIn("python", parsed.normalized_text.lower())
        self.assertEqual(float(parsed.years_experience), 4.0)

    def test_matching_resume_gets_high_score(self):
        self._attach_resume("Python Django PostgreSQL. Опыт работы 5 лет.")
        application = Application.objects.create(
            candidate=self.candidate, vacancy=self.vacancy,
            stage=self.stage, status=ApplicationStatus.NEW)

        match = score_application(application)
        self.assertIsNotNone(match)
        self.assertGreaterEqual(float(match.score), 70)
        self.assertEqual(match.verdict, "recommended")
        self.assertIn("python", [k.lower() for k in match.matched_keywords])

    def test_application_without_resume_is_not_scored(self):
        application = Application.objects.create(
            candidate=self.candidate, vacancy=self.vacancy,
            stage=self.stage, status=ApplicationStatus.NEW)
        self.assertIsNone(score_application(application))
        self.assertEqual(Match.objects.count(), 0)

    def test_reasons_explain_decision(self):
        """Рекрутёр должен видеть обоснование, а не только число."""
        self._attach_resume("Только Python. Опыт работы 1 год.")
        application = Application.objects.create(
            candidate=self.candidate, vacancy=self.vacancy,
            stage=self.stage, status=ApplicationStatus.NEW)

        match = score_application(application)
        self.assertTrue(match.reasons)
        self.assertTrue(match.missing_keywords)
