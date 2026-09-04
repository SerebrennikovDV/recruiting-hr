"""Сервисный слой подсистемы отбора.

Связывает разбор резюме, нормализацию текста и расчёт оценки
с моделями системы. Представления вызывают только функции этого
модуля и не знают о внутреннем устройстве подсистемы.
"""
from __future__ import annotations

import logging
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

from core.models import Match, ResumeParse

from .lemmatizer import lemmatize_keywords, lemmatize_text
from .parser import extract_experience_years, extract_text
from .scorer import calculate_score

logger = logging.getLogger(__name__)


def parse_resume(resume) -> ResumeParse:
    """Разбирает файл резюме и сохраняет результат."""
    limit = settings.SCREENING["MAX_TEXT_LENGTH"]
    raw_text = extract_text(resume.file.path)
    normalized = lemmatize_text(raw_text)
    years = extract_experience_years(raw_text)

    parsed, _ = ResumeParse.objects.update_or_create(
        resume=resume,
        defaults={
            "raw_text": raw_text[:limit],
            "normalized_text": normalized[:limit],
            "years_experience": (Decimal(f"{years:.1f}")
                                 if years is not None else None),
            "parser_version": settings.SCREENING["PARSER_VERSION"],
            "parsed_at": timezone.now(),
        },
    )
    logger.info("Резюме %s разобрано, стаж: %s", resume.pk, years)
    return parsed


def score_application(application) -> Match | None:
    """Рассчитывает оценку соответствия для отклика.

    Возвращает None, если у кандидата нет резюме: оценивать нечего,
    и отклик остаётся на обычном ручном рассмотрении.
    """
    candidate = application.candidate
    # Берётся последнее загруженное резюме: признака основного файла
    # в модели нет, а актуальным кандидат считает свежий.
    resume = candidate.resumes.order_by("-uploaded_at").first()
    if resume is None:
        logger.info("У кандидата %s нет резюме, отбор не выполняется",
                    candidate.pk)
        return None

    parsed = getattr(resume, "parsed", None) or parse_resume(resume)

    requirements = []
    for link in application.vacancy.vacancy_skills.select_related("skill"):
        lemma = lemmatize_keywords([link.skill.name])[0]
        requirements.append((lemma, 1.0, link.is_required))

    result = calculate_score(
        resume_text=parsed.normalized_text,
        required_keywords=requirements,
        min_experience_years=_required_experience(application.vacancy),
        experience_years=(float(parsed.years_experience)
                          if parsed.years_experience is not None else None),
        reject_threshold=settings.SCREENING["AUTO_REJECT_THRESHOLD"],
        recommend_threshold=settings.SCREENING["RECOMMEND_THRESHOLD"],
    )

    match, _ = Match.objects.update_or_create(
        application=application,
        defaults={
            "score": result.score,
            "verdict": result.verdict,
            "matched_keywords": result.matched_keywords,
            "missing_keywords": result.missing_keywords,
            "experience_match": result.experience_match,
            "reasons": result.reasons,
            "calculated_at": timezone.now(),
        },
    )
    return match


def _required_experience(vacancy) -> int:
    """Требуемый стаж по уровню квалификации вакансии.

    Отдельного поля со стажем в вакансии нет, поэтому требование
    выводится из грейда - так же, как это делает рекрутёр вручную.
    """
    mapping = {"intern": 0, "junior": 1, "middle": 2,
               "senior": 4, "lead": 6}
    return mapping.get(getattr(vacancy, "grade", ""), 0)
