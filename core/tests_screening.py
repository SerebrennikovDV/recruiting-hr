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
