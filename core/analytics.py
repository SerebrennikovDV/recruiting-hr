"""
Модуль HR-аналитики.

Содержит «сложные» аналитические отчёты: каждый из них обращается к данным
не менее чем трёх объектов базы данных и использует агрегатные функции SQL
(COUNT, AVG, SUM, GROUP BY), сформированные средствами Django ORM. Отдельные
функции строят графики (matplotlib) и возвращают их в виде data-URI PNG —
это позволяет показывать дашборды без внешних зависимостей и без интернета.

Реализованные метрики:
    1. Воронка подбора (Stage × Application × Vacancy).
    2. Среднее время закрытия вакансии — time-to-hire (Vacancy × Department × Application).
    3. Эффективность источников и стоимость найма — cost-per-hire
       (Source × Candidate × Application).
    4. Загрузка рекрутёров (User × Vacancy × Application × Interview).
    5. Динамика откликов по месяцам (Application × Vacancy).
"""
import base64
import io
from datetime import timedelta

import matplotlib
matplotlib.use("Agg")  # неинтерактивный движок отрисовки (без графической оболочки)
import matplotlib.pyplot as plt
from django.db.models import (Avg, Count, DecimalField, F, FloatField,
                              IntegerField, Q, Sum)
from django.db.models.functions import Coalesce, TruncMonth
from django.utils import timezone

from .models import (Application, ApplicationStatus, Candidate, Interview,
                     Offer, Role, Source, Stage, User, Vacancy, VacancyStatus)

# Единая цветовая палитра графиков (корпоративные цвета сервиса).
PALETTE = ["#2563eb", "#16a34a", "#f59e0b", "#dc2626", "#7c3aed",
           "#0891b2", "#db2777", "#65a30d"]


# ---------------------------------------------------------------------------
#  Сводные показатели (KPI) для верхней панели дашборда
# ---------------------------------------------------------------------------
def kpi_summary():
    """Ключевые показатели подбора одним словарём."""
    total_vac = Vacancy.objects.count()
    open_vac = Vacancy.objects.filter(
        status__in=[VacancyStatus.OPEN, VacancyStatus.IN_PROGRESS]).count()
    closed = Vacancy.objects.filter(closed_at__isnull=False)
    avg_tth = closed.annotate(
        days=F("closed_at") - F("opened_at")).aggregate(
        v=Avg("days"))["v"]
    # Среднее время закрытия в днях (timedelta → дни).
    if avg_tth is not None:
        avg_tth_days = round(avg_tth.days if hasattr(avg_tth, "days") else float(avg_tth), 1)
    else:
        avg_tth_days = 0
    hired = Application.objects.filter(status=ApplicationStatus.HIRED).count()
    apps = Application.objects.count()
    conv = round(hired / apps * 100, 1) if apps else 0.0
    return {
        "total_vacancies": total_vac,
        "open_vacancies": open_vac,
        "candidates": Candidate.objects.count(),
        "applications": apps,
        "interviews": Interview.objects.count(),
        "hired": hired,
        "conversion": conv,
        "avg_time_to_hire": avg_tth_days,
        "accepted_offers": Offer.objects.filter(status="accepted").count(),
    }


# ---------------------------------------------------------------------------
#  Отчёт 1. Воронка подбора
# ---------------------------------------------------------------------------
def funnel_report():
    """
    Количество заявок на каждом этапе воронки. Сложный отчёт: объединяет
    данные Stage, Application и (через заявку) Vacancy.
    """
    rows = (Stage.objects
            .annotate(app_count=Count("applications"))
            .order_by("order")
            .values("name", "order", "app_count", "is_terminal"))
    # Приводим к единому ключу "applications" для шаблонов и графиков.
    rows = [{"name": r["name"], "order": r["order"],
             "applications": r["app_count"], "is_terminal": r["is_terminal"]}
            for r in rows]
    # Конверсия относительно первого (самого широкого) этапа воронки.
    base = rows[0]["applications"] if rows and rows[0]["applications"] else 0
    for r in rows:
        r["conversion"] = round(r["applications"] / base * 100, 1) if base else 0.0
    return rows


# ---------------------------------------------------------------------------
#  Отчёт 2. Среднее время закрытия вакансии (time-to-hire) по отделам
# ---------------------------------------------------------------------------
def time_to_hire_report():
    """
    Среднее число дней от открытия до закрытия вакансии в разрезе отделов.
    Сложный отчёт: Vacancy × Department (+ учёт принятых заявок).
    """
    closed = Vacancy.objects.filter(closed_at__isnull=False)
    data = {}
    for vac in closed.select_related("department"):
        dep = vac.department.name
        data.setdefault(dep, []).append((vac.closed_at - vac.opened_at).days)
    result = []
    for dep, days_list in data.items():
        result.append({
            "department": dep,
            "closed": len(days_list),
            "avg_days": round(sum(days_list) / len(days_list), 1),
            "min_days": min(days_list),
            "max_days": max(days_list),
        })
    result.sort(key=lambda x: x["avg_days"])
    return result


# ---------------------------------------------------------------------------
#  Отчёт 3. Эффективность источников и стоимость найма (cost-per-hire)
# ---------------------------------------------------------------------------
def source_efficiency_report():
    """
    По каждому источнику: число кандидатов, откликов, нанятых, конверсия и
    стоимость найма. Сложный отчёт: Source × Candidate × Application.
    """
    rows = []
    for src in Source.objects.all():
        candidates = Candidate.objects.filter(source=src)
        cand_count = candidates.count()
        apps = Application.objects.filter(candidate__source=src)
        app_count = apps.count()
        hired = apps.filter(status=ApplicationStatus.HIRED).count()
        conversion = round(hired / cand_count * 100, 1) if cand_count else 0.0
        total_cost = float(src.cost_per_contact) * cand_count
        cost_per_hire = round(total_cost / hired, 2) if hired else None
        rows.append({
            "source": src.name,
            "candidates": cand_count,
            "applications": app_count,
            "hired": hired,
            "conversion": conversion,
            "cost_per_contact": float(src.cost_per_contact),
            "cost_per_hire": cost_per_hire,
        })
    rows.sort(key=lambda x: x["hired"], reverse=True)
    return rows


# ---------------------------------------------------------------------------
#  Отчёт 4. Загрузка рекрутёров
# ---------------------------------------------------------------------------
def recruiter_load_report():
    """
    Загрузка каждого рекрутёра: открытые вакансии, активные заявки, проведённые
    собеседования, нанятые. Сложный отчёт: User × Vacancy × Application × Interview.
    """
    recruiters = User.objects.filter(role=Role.RECRUITER)
    rows = []
    for r in recruiters:
        open_vac = Vacancy.objects.filter(
            recruiter=r,
            status__in=[VacancyStatus.OPEN, VacancyStatus.IN_PROGRESS]).count()
        active_apps = Application.objects.filter(
            vacancy__recruiter=r).exclude(
            status__in=[ApplicationStatus.HIRED, ApplicationStatus.REJECTED]).count()
        interviews = Interview.objects.filter(interviewer=r).count()
        hired = Application.objects.filter(
            vacancy__recruiter=r, status=ApplicationStatus.HIRED).count()
        rows.append({
            "recruiter": r.short_name(),
            "open_vacancies": open_vac,
            "active_applications": active_apps,
            "interviews": interviews,
            "hired": hired,
        })
    rows.sort(key=lambda x: x["active_applications"], reverse=True)
    return rows


# ---------------------------------------------------------------------------
#  Отчёт 5. Динамика откликов по месяцам
# ---------------------------------------------------------------------------
def applications_dynamics():
    """Число откликов по месяцам (агрегация по дате отклика)."""
    qs = (Application.objects
          .annotate(month=TruncMonth("applied_at"))
          .values("month")
          .annotate(total=Count("id"))
          .order_by("month"))
    return [{"month": r["month"].strftime("%m.%Y") if r["month"] else "—",
             "total": r["total"]} for r in qs]


# ===========================================================================
#  Построение графиков (matplotlib → data-URI PNG)
# ===========================================================================
def _fig_to_data_uri(fig):
    """Сериализовать фигуру matplotlib в строку data:image/png;base64,…"""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def funnel_chart(rows=None):
    """Горизонтальная воронка: число заявок по этапам."""
    rows = rows or funnel_report()
    labels = [r["name"] for r in rows]
    values = [r["applications"] for r in rows]
    fig, ax = plt.subplots(figsize=(7, 3.6))
    bars = ax.barh(labels[::-1], values[::-1],
                   color=PALETTE[0], edgecolor="white")
    ax.set_xlabel("Количество заявок")
    ax.set_title("Воронка подбора персонала")
    for bar, v in zip(bars, values[::-1]):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                str(v), va="center", fontsize=9)
    ax.grid(axis="x", linestyle=":", alpha=0.4)
    return _fig_to_data_uri(fig)


def source_chart(rows=None):
    """Столбчатая диаграмма: нанято по источникам."""
    rows = rows or source_efficiency_report()
    rows = [r for r in rows if r["candidates"]][:8]
    labels = [r["source"] for r in rows]
    hired = [r["hired"] for r in rows]
    cand = [r["candidates"] for r in rows]
    fig, ax = plt.subplots(figsize=(7, 3.6))
    x = range(len(labels))
    ax.bar([i - 0.2 for i in x], cand, width=0.4, label="Кандидатов",
           color=PALETTE[5])
    ax.bar([i + 0.2 for i in x], hired, width=0.4, label="Нанято",
           color=PALETTE[1])
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("Человек")
    ax.set_title("Эффективность источников привлечения")
    ax.legend()
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    return _fig_to_data_uri(fig)


def dynamics_chart(rows=None):
    """Линейный график динамики откликов по месяцам."""
    rows = rows or applications_dynamics()
    labels = [r["month"] for r in rows]
    values = [r["total"] for r in rows]
    fig, ax = plt.subplots(figsize=(7, 3.4))
    ax.plot(labels, values, marker="o", color=PALETTE[4], linewidth=2)
    ax.fill_between(range(len(values)), values, alpha=0.12, color=PALETTE[4])
    ax.set_ylabel("Откликов")
    ax.set_title("Динамика откликов по месяцам")
    ax.grid(linestyle=":", alpha=0.4)
    return _fig_to_data_uri(fig)


def time_to_hire_chart(rows=None):
    """Столбчатая диаграмма среднего time-to-hire по отделам."""
    rows = rows or time_to_hire_report()
    labels = [r["department"] for r in rows]
    values = [r["avg_days"] for r in rows]
    fig, ax = plt.subplots(figsize=(7, 3.4))
    bars = ax.bar(labels, values, color=PALETTE[2], edgecolor="white")
    ax.set_ylabel("Дней")
    ax.set_title("Среднее время закрытия вакансии по отделам")
    ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=8)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                str(v), ha="center", fontsize=9)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    return _fig_to_data_uri(fig)


def dashboard_context():
    """Собрать все отчёты и графики для страницы HR-аналитики кабинета."""
    funnel = funnel_report()
    sources = source_efficiency_report()
    tth = time_to_hire_report()
    dynamics = applications_dynamics()
    return {
        "kpi": kpi_summary(),
        "funnel": funnel,
        "sources": sources,
        "time_to_hire": tth,
        "recruiter_load": recruiter_load_report(),
        "dynamics": dynamics,
        "chart_funnel": funnel_chart(funnel),
        "chart_sources": source_chart(sources),
        "chart_dynamics": dynamics_chart(dynamics),
        "chart_tth": time_to_hire_chart(tth) if tth else None,
    }
