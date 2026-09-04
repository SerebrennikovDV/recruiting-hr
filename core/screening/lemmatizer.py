"""Приведение слов русского языка к начальной форме.

Без этого шага требование «разработчик» не совпало бы с написанием
«разработчику» в резюме, и оценка соответствия занижалась бы на ровном
месте. Разбор выполняется локально, обращений к внешним сервисам нет.
"""
from __future__ import annotations

import re
from functools import lru_cache

try:
    import pymorphy3

    _morph = pymorphy3.MorphAnalyzer()
except ImportError:  # библиотека не установлена - работаем без разбора
    _morph = None

TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё0-9+\-_.#]*")
CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")


@lru_cache(maxsize=50_000)
def lemmatize_word(word: str) -> str:
    """Начальная форма слова.

    Латиница и аббревиатуры возвращаются в нижнем регистре без разбора:
    названия технологий не склоняются, а морфологический анализатор
    на них только тратит время.
    """
    if not word:
        return ""
    if _morph is None or not CYRILLIC_RE.search(word):
        return word.lower()
    return _morph.parse(word)[0].normal_form


def lemmatize_text(text: str) -> str:
    """Текст, приведённый к начальным формам слов."""
    if not text:
        return ""
    return " ".join(lemmatize_word(token)
                    for token in TOKEN_RE.findall(text))


def lemmatize_keywords(keywords) -> list[str]:
    """Начальные формы требований вакансии."""
    return [lemmatize_word(str(word)) for word in keywords if word]
