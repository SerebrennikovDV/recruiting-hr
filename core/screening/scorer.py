"""Расчёт оценки соответствия резюме требованиям вакансии.

Оценка складывается из взвешенной доли найденных требований и поправки
за стаж. Помимо числа возвращается обоснование: рекрутёр должен видеть,
почему кандидат получил такую оценку, а не только её значение.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

MAX_EXPERIENCE_BONUS = 15.0
MAX_EXPERIENCE_PENALTY = 20.0
UNKNOWN_EXPERIENCE_PENALTY = 5.0


@dataclass
class ScoringResult:
    """Оценка соответствия с разложением по составляющим."""

    score: Decimal = Decimal("0")
    verdict: str = "rejected"
    matched_keywords: list[str] = field(default_factory=list)
    missing_keywords: list[str] = field(default_factory=list)
    experience_match: bool = False
    experience_years: float | None = None
    reasons: list[str] = field(default_factory=list)


def calculate_score(*, resume_text: str,
                    required_keywords: list[tuple[str, float, bool]],
                    min_experience_years: int,
                    experience_years: float | None,
                    reject_threshold: float = 50.0,
                    recommend_threshold: float = 70.0) -> ScoringResult:
    """Оценка соответствия по шкале от 0 до 100.

    required_keywords - тройки «требование, вес, обязательность».
    Вес обязательного требования удваивается: пропуск обязательного
    навыка должен весить больше, чем пропуск желательного.
    """
    result = ScoringResult(experience_years=experience_years)

    if not resume_text:
        result.reasons.append("Не удалось извлечь текст резюме")
        return result

    lowered = resume_text.lower()
    total_weight = matched_weight = 0.0
    for term, weight, is_required in required_keywords:
        effective = float(weight) * (2.0 if is_required else 1.0)
        total_weight += effective
        if term and term.lower() in lowered:
            matched_weight += effective
            result.matched_keywords.append(term)
        elif term:
            result.missing_keywords.append(term)

    if total_weight == 0:
        keyword_score = 0.0
        result.reasons.append("Для вакансии не задан перечень требований")
    else:
        keyword_score = matched_weight / total_weight * 100.0

    bonus = _experience_bonus(result, min_experience_years,
                              experience_years)

    final = max(0.0, min(100.0, keyword_score + bonus))
    result.score = Decimal(f"{final:.2f}")
    result.verdict = _verdict(final, reject_threshold, recommend_threshold)

    if result.matched_keywords:
        result.reasons.insert(
            0, "Найдены требования: "
               + ", ".join(result.matched_keywords[:10]))
    if result.missing_keywords:
        result.reasons.append(
            "Не найдены: " + ", ".join(result.missing_keywords[:10]))
    return result


def _experience_bonus(result: ScoringResult, required: int,
                      actual: float | None) -> float:
    """Поправка за стаж: надбавка при запасе, вычет при нехватке."""
    if required <= 0:
        result.experience_match = True
        result.reasons.append("Требований к стажу нет")
        return 0.0

    if actual is None:
        result.experience_match = False
        result.reasons.append("Стаж в резюме не указан")
        return -UNKNOWN_EXPERIENCE_PENALTY

    if actual >= required:
        result.experience_match = True
        surplus = actual - required
        bonus = min(MAX_EXPERIENCE_BONUS, 5.0 + surplus * 1.5)
        result.reasons.append(
            f"Стаж {actual:.0f} лет при требуемых {required} "
            f"(+{bonus:.1f} балла)")
        return bonus

    result.experience_match = False
    gap = required - actual
    penalty = min(MAX_EXPERIENCE_PENALTY, 5.0 + gap * 3.0)
    result.reasons.append(
        f"Стаж {actual:.0f} лет меньше требуемых {required} "
        f"(-{penalty:.1f} балла)")
    return -penalty


def _verdict(score: float, reject_threshold: float,
             recommend_threshold: float) -> str:
    """Решение по оценке.

    Промежуточные значения остаются на решение рекрутёра: алгоритм
    работает по совпадению слов и не распознаёт опыт, описанный иными
    формулировками, поэтому автоматический отказ кандидату не выносится.
    """
    if score >= recommend_threshold:
        return "recommended"
    if score >= reject_threshold:
        return "review"
    return "rejected"
