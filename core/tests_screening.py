"""Тесты подсистемы первичного отбора резюме."""
from core.screening.lemmatizer import (lemmatize_keywords, lemmatize_text,
                                       lemmatize_word)
from core.screening.parser import extract_experience_years
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
