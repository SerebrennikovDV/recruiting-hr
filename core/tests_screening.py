"""Тесты подсистемы первичного отбора резюме."""
from core.screening.lemmatizer import (lemmatize_keywords, lemmatize_text,
                                       lemmatize_word)
from core.screening.parser import extract_experience_years
from core.screening.scorer import calculate_score
from django.test import TestCase


class LemmatizerTests(TestCase):
    """Приведение слов к начальной форме."""

    def test_russian_word_normalized(self):
        self.assertEqual(lemmatize_word("разработчику"), "разработчик")
        self.assertEqual(lemmatize_word("вакансиями"), "вакансия")

    def test_latin_word_lowercased_only(self):
        self.assertEqual(lemmatize_word("Django"), "django")
        self.assertEqual(lemmatize_word("PostgreSQL"), "postgresql")

    def test_empty_input(self):
        self.assertEqual(lemmatize_word(""), "")
        self.assertEqual(lemmatize_text(""), "")

    def test_text_normalized_wordwise(self):
        result = lemmatize_text("Опытом работы с базами данных")
        self.assertIn("база", result)
        self.assertIn("работа", result)

    def test_keywords_normalized(self):
        self.assertEqual(lemmatize_keywords(["Тестирование", "Docker"]),
                         ["тестирование", "docker"])


class ExperienceExtractionTests(TestCase):
    """Определение стажа по тексту резюме."""

    def test_common_wordings(self):
        cases = {
            "Опыт работы 5 лет в разработке": 5,
            "Стаж: 3 года": 3,
            "7+ лет опыта коммерческой разработки": 7,
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(extract_experience_years(text), expected)

    def test_largest_value_wins(self):
        """Кандидаты указывают и общий стаж, и стаж по местам работы."""
        text = "Опыт работы 8 лет. В последней компании стаж 3 года."
        self.assertEqual(extract_experience_years(text), 8)

    def test_no_experience_mentioned(self):
        self.assertIsNone(extract_experience_years("Резюме без стажа"))
        self.assertIsNone(extract_experience_years(""))

    def test_unrealistic_values_ignored(self):
        self.assertIsNone(extract_experience_years("Опыт работы 99 лет"))


class ScoringTests(TestCase):
    """Расчёт оценки соответствия."""

    def _score(self, resume_text, requirements, required_years=0,
               actual_years=None):
        return calculate_score(
            resume_text=resume_text,
            required_keywords=requirements,
            min_experience_years=required_years,
            experience_years=actual_years,
        )

    def test_all_requirements_found(self):
        result = self._score("python django postgresql",
                             [("python", 1.0, True),
                              ("django", 1.0, True)])
        self.assertEqual(float(result.score), 100.0)
        self.assertEqual(result.verdict, "recommended")
        self.assertEqual(len(result.matched_keywords), 2)

    def test_missing_requirements_lower_score(self):
        result = self._score("python", [("python", 1.0, True),
                                        ("kubernetes", 1.0, True)])
        self.assertLess(float(result.score), 100.0)
        self.assertIn("kubernetes", result.missing_keywords)

    def test_required_skill_weighs_double(self):
        """Пропуск обязательного навыка стоит дороже, чем желательного."""
        without_required = self._score(
            "django", [("python", 1.0, True), ("django", 1.0, False)])
        without_optional = self._score(
            "python", [("python", 1.0, True), ("django", 1.0, False)])
        self.assertLess(float(without_required.score),
                        float(without_optional.score))

    def test_empty_resume_scores_zero(self):
        result = self._score("", [("python", 1.0, True)])
        self.assertEqual(float(result.score), 0.0)
        self.assertTrue(result.reasons)
