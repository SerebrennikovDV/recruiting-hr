"""
Представления (views) рекрутинговой ИС «UnitHire».

Структура:
    • Публичная часть — ≥10 страниц, доступных без авторизации (главная,
      вакансии, новости, аналитика-демо, контакты с формой обратной связи и т. д.).
    • Аутентификация — регистрация соискателя, вход, выход, диспетчер кабинетов.
    • Кабинет рекрутёра — управление вакансиями, кандидатами, заявками,
      собеседованиями, HR-аналитика, выгрузка документов (≥5 разделов).
    • Кабинет кандидата — профиль, резюме, отклики, собеседования (≥5 разделов).

Каждое представление формирует «хлебные крошки» (breadcrumbs) и передаёт их в
шаблон, поэтому навигационная цепочка присутствует на всех страницах сайта.
"""
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from . import analytics, documents
from .decorators import candidate_required, recruiter_required
from .forms import (ApplicationCandidateForm, ApplicationStageForm,
                    CandidateForm, CandidateProfileForm, FeedbackForm,
                    InterviewForm, ResumeUploadForm, SignUpForm, VacancyForm)
from .models import (Application, ApplicationStatus, Article, Candidate,
                     Interview, Role, Stage, Vacancy, VacancyStatus)


def _crumbs(*pairs):
    """Сформировать список «хлебных крошек»: [(подпись, url|None), …]."""
    return list(pairs)


def _querystring(request):
    """Строка GET-параметров без `page` — чтобы фильтры сохранялись при пагинации."""
    params = request.GET.copy()
    params.pop("page", None)
    return params.urlencode()


# ===========================================================================
#  ПУБЛИЧНАЯ ЧАСТЬ
# ===========================================================================
def home(request):
    """Главная страница: приветствие, ключевые цифры, свежие вакансии и новости."""
    context = {
        "breadcrumbs": _crumbs(("Главная", None)),
        "kpi": analytics.kpi_summary(),
        "fresh_vacancies": Vacancy.objects.filter(
            status__in=[VacancyStatus.OPEN, VacancyStatus.IN_PROGRESS]
        ).select_related("department")[:6],
        "fresh_news": Article.objects.filter(is_published=True)[:3],
        "top_skills": _top_skills(),
    }
    return render(request, "public/home.html", context)


def _top_skills(limit=8):
    """Наиболее востребованные навыки (по числу вакансий) — для главной."""
    from .models import Skill
    return (Skill.objects.annotate(n=Count("vacancies"))
            .filter(n__gt=0).order_by("-n")[:limit])


def about(request):
    return render(request, "public/about.html",
                  {"breadcrumbs": _crumbs(("Главная", reverse("home")),
                                          ("О компании", None))})


def how_it_works(request):
    steps = [
        (1, "Скрининг резюме",
         "Рекрутёр оценивает соответствие резюме требованиям вакансии."),
        (2, "HR-интервью",
         "Знакомство, обсуждение опыта, ожиданий по зарплате и условиям."),
        (3, "Техническое собеседование",
         "Проверка профессиональных навыков техническим специалистом."),
        (4, "Финальное собеседование",
         "Встреча с нанимающим руководителем и принятие решения."),
        (5, "Оффер",
         "Формирование и отправка предложения о работе кандидату."),
        (6, "Выход на работу",
         "Принятие оффера, оформление и адаптация нового сотрудника."),
    ]
    return render(request, "public/how_it_works.html",
                  {"breadcrumbs": _crumbs(("Главная", reverse("home")),
                                          ("Как это работает", None)),
                   "steps": steps})


def employers(request):
    return render(request, "public/employers.html",
                  {"breadcrumbs": _crumbs(("Главная", reverse("home")),
                                          ("Работодателям", None))})


def candidates_info(request):
    return render(request, "public/candidates_info.html",
                  {"breadcrumbs": _crumbs(("Главная", reverse("home")),
                                          ("Соискателям", None))})


def help_page(request):
    """Справка по системе с указанием ФИО автора работы."""
    faq = [
        ("Как зарегистрироваться соискателю?",
         "Нажмите «Регистрация» в правом верхнем углу, заполните форму — после "
         "этого автоматически создаётся личный кабинет кандидата."),
        ("Как откликнуться на вакансию?",
         "Откройте карточку вакансии и нажмите «Откликнуться». Отклик появится "
         "в разделе «Мои отклики» с текущим статусом."),
        ("Какие форматы резюме поддерживаются?",
         "PDF, DOC, DOCX, RTF, ODT размером до 5 МБ."),
        ("Чем отличаются роли в системе?",
         "Администратор управляет всеми данными, рекрутёр ведёт подбор и "
         "аналитику, кандидат откликается на вакансии."),
        ("Как рекрутёру выгрузить отчёт?",
         "В кабинете рекрутёра доступна выгрузка аналитики и списка вакансий в "
         "Excel, а карточки кандидата — в Word."),
    ]
    return render(request, "public/help.html",
                  {"breadcrumbs": _crumbs(("Главная", reverse("home")),
                                          ("Справка", None)),
                   "faq": faq})


def vacancies(request):
    """Список вакансий с поиском и фильтрами (доступен без авторизации)."""
    qs = Vacancy.objects.select_related("department", "recruiter").all()

    # Ручные фильтры по строке поиска, грейду, статусу, формату работы.
    query = request.GET.get("q", "").strip()
    grade = request.GET.get("grade", "")
    status = request.GET.get("status", "")
    remote = request.GET.get("remote", "")
    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query)
                       | Q(department__name__icontains=query))
    if grade:
        qs = qs.filter(grade=grade)
    if status:
        qs = qs.filter(status=status)
    if remote == "1":
        qs = qs.filter(is_remote=True)

    paginator = Paginator(qs, 8)
    page = paginator.get_page(request.GET.get("page"))
    context = {
        "breadcrumbs": _crumbs(("Главная", reverse("home")), ("Вакансии", None)),
        "page_obj": page, "querystring": _querystring(request),
        "query": query,
        "grade": grade,
        "status": status,
        "remote": remote,
        "grade_choices": Vacancy._meta.get_field("grade").choices,
        "status_choices": VacancyStatus.choices,
        "total": qs.count(),
    }
    return render(request, "public/vacancies.html", context)


def vacancy_detail(request, pk):
    """Карточка вакансии: описание, требуемые навыки, кнопка отклика."""
    vacancy = get_object_or_404(
        Vacancy.objects.select_related("department", "recruiter"), pk=pk)
    already_applied = False
    if request.user.is_authenticated and request.user.role == Role.CANDIDATE:
        candidate = getattr(request.user, "candidate_profile", None)
        if candidate:
            already_applied = Application.objects.filter(
                candidate=candidate, vacancy=vacancy).exists()
    context = {
        "breadcrumbs": _crumbs(("Главная", reverse("home")),
                               ("Вакансии", reverse("vacancies")),
                               (vacancy.title, None)),
        "vacancy": vacancy,
        "required_skills": vacancy.vacancyskill_set.select_related("skill"),
        "similar": Vacancy.objects.filter(
            department=vacancy.department).exclude(pk=vacancy.pk)[:4],
        "already_applied": already_applied,
    }
    return render(request, "public/vacancy_detail.html", context)


def analytics_demo(request):
    """Публичная демонстрация возможностей HR-аналитики (без приватных данных).

    Тяжёлые отчёты и графики matplotlib кешируются на 60 секунд, чтобы под
    параллельной нагрузкой не пересчитываться на каждый запрос.
    """
    from django.core.cache import cache
    cached = cache.get("public_analytics_demo")
    if cached is None:
        funnel = analytics.funnel_report()
        cached = {
            "kpi": analytics.kpi_summary(),
            "funnel": funnel,
            "chart_funnel": analytics.funnel_chart(funnel),
            "chart_dynamics": analytics.dynamics_chart(),
            "sources": analytics.source_efficiency_report(),
        }
        cache.set("public_analytics_demo", cached, 60)
    context = {
        "breadcrumbs": _crumbs(("Главная", reverse("home")),
                               ("HR-аналитика", None)),
        **cached,
    }
    return render(request, "public/analytics_demo.html", context)


def news(request):
    """Лента новостей/блога компании."""
    qs = Article.objects.filter(is_published=True)
    paginator = Paginator(qs, 6)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "public/news.html",
                  {"breadcrumbs": _crumbs(("Главная", reverse("home")),
                                          ("Новости", None)),
                   "page_obj": page})


def news_detail(request, slug):
    article = get_object_or_404(Article, slug=slug, is_published=True)
    return render(request, "public/news_detail.html",
                  {"breadcrumbs": _crumbs(("Главная", reverse("home")),
                                          ("Новости", reverse("news")),
                                          (article.title, None)),
                   "article": article,
                   "other": Article.objects.filter(is_published=True)
                   .exclude(pk=article.pk)[:4]})


def contacts(request):
    """Контакты и форма обратной связи (сообщение сохраняется в БД)."""
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Спасибо! Ваше обращение принято — мы свяжемся с вами в "
                "ближайшее время.")
            return redirect("contacts")
        messages.error(request, "Проверьте правильность заполнения формы.")
    else:
        form = FeedbackForm()
    return render(request, "public/contacts.html",
                  {"breadcrumbs": _crumbs(("Главная", reverse("home")),
                                          ("Контакты", None)),
                   "form": form})


# ===========================================================================
#  АУТЕНТИФИКАЦИЯ
# ===========================================================================
def register(request):
    """Регистрация нового соискателя."""
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request, "Регистрация завершена. Заполните профиль и "
                         "откликайтесь на вакансии!")
            return redirect("cand_dashboard")
        messages.error(request, "Исправьте ошибки в форме регистрации.")
    else:
        form = SignUpForm()
    return render(request, "registration/register.html",
                  {"breadcrumbs": _crumbs(("Главная", reverse("home")),
                                          ("Регистрация", None)),
                   "form": form})


@login_required
def dashboard(request):
    """Диспетчер: направляет пользователя в кабинет согласно его роли."""
    user = request.user
    if user.is_superuser or user.role == Role.ADMIN:
        return redirect("/admin/")
    if user.role == Role.RECRUITER:
        return redirect("rec_dashboard")
    return redirect("cand_dashboard")


# ===========================================================================
#  КАБИНЕТ РЕКРУТЁРА (≥5 разделов)
# ===========================================================================
@recruiter_required
def rec_dashboard(request):
    """Сводка кабинета рекрутёра: показатели, задачи на сегодня."""
    today = timezone.localdate()
    context = {
        "breadcrumbs": _crumbs(("Кабинет рекрутёра", None)),
        "kpi": analytics.kpi_summary(),
        "my_vacancies": Vacancy.objects.filter(
            recruiter=request.user).order_by("-opened_at")[:6],
        "new_applications": Application.objects.filter(
            status=ApplicationStatus.NEW).select_related(
            "candidate", "vacancy")[:8],
        "upcoming_interviews": Interview.objects.filter(
            scheduled_at__date__gte=today,
            result=Interview._meta.get_field("result").default
        ).select_related("application__candidate")[:8],
    }
    return render(request, "cabinet/recruiter/dashboard.html", context)


@recruiter_required
def rec_vacancies(request):
    """Список вакансий рекрутёра с фильтром по статусу + выгрузка в Excel."""
    qs = Vacancy.objects.select_related("department", "recruiter").annotate(
        apps=Count("applications")).order_by("-opened_at")
    status = request.GET.get("status", "")
    query = request.GET.get("q", "").strip()
    if status:
        qs = qs.filter(status=status)
    if query:
        qs = qs.filter(title__icontains=query)
    paginator = Paginator(qs, 10)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "cabinet/recruiter/vacancies.html",
                  {"breadcrumbs": _crumbs(
                      ("Кабинет рекрутёра", reverse("rec_dashboard")),
                      ("Вакансии", None)),
                   "page_obj": page, "querystring": _querystring(request), "status": status, "query": query,
                   "status_choices": VacancyStatus.choices})


@recruiter_required
def rec_vacancy_form(request, pk=None):
    """Создание или редактирование вакансии."""
    vacancy = get_object_or_404(Vacancy, pk=pk) if pk else None
    if request.method == "POST":
        form = VacancyForm(request.POST, instance=vacancy)
        if form.is_valid():
            obj = form.save(commit=False)
            if not obj.recruiter:
                obj.recruiter = request.user
            obj.save()
            form.save_m2m()
            messages.success(request, "Вакансия сохранена.")
            return redirect("rec_vacancies")
        messages.error(request, "Проверьте поля формы.")
    else:
        form = VacancyForm(instance=vacancy)
    title = "Редактирование вакансии" if vacancy else "Новая вакансия"
    return render(request, "cabinet/recruiter/vacancy_form.html",
                  {"breadcrumbs": _crumbs(
                      ("Кабинет рекрутёра", reverse("rec_dashboard")),
                      ("Вакансии", reverse("rec_vacancies")), (title, None)),
                   "form": form, "title": title, "vacancy": vacancy})


@recruiter_required
def rec_candidates(request):
    """Список кандидатов с поиском и фильтром по грейду."""
    qs = Candidate.objects.select_related("source").all()
    query = request.GET.get("q", "").strip()
    grade = request.GET.get("grade", "")
    if query:
        qs = qs.filter(Q(last_name__icontains=query) |
                       Q(first_name__icontains=query) |
                       Q(email__icontains=query))
    if grade:
        qs = qs.filter(grade=grade)
    paginator = Paginator(qs, 10)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "cabinet/recruiter/candidates.html",
                  {"breadcrumbs": _crumbs(
                      ("Кабинет рекрутёра", reverse("rec_dashboard")),
                      ("Кандидаты", None)),
                   "page_obj": page, "querystring": _querystring(request), "query": query, "grade": grade,
                   "grade_choices": Candidate._meta.get_field("grade").choices})


@recruiter_required
def rec_candidate_form(request, pk=None):
    candidate = get_object_or_404(Candidate, pk=pk) if pk else None
    if request.method == "POST":
        form = CandidateForm(request.POST, instance=candidate)
        if form.is_valid():
            form.save()
            messages.success(request, "Карточка кандидата сохранена.")
            return redirect("rec_candidates")
        messages.error(request, "Проверьте поля формы.")
    else:
        form = CandidateForm(instance=candidate)
    title = "Редактирование кандидата" if candidate else "Новый кандидат"
    return render(request, "cabinet/recruiter/candidate_form.html",
                  {"breadcrumbs": _crumbs(
                      ("Кабинет рекрутёра", reverse("rec_dashboard")),
                      ("Кандидаты", reverse("rec_candidates")), (title, None)),
                   "form": form, "title": title})


@recruiter_required
def candidate_detail(request, pk):
    """Карточка кандидата для рекрутёра (с откликами и навыками)."""
    candidate = get_object_or_404(Candidate, pk=pk)
    return render(request, "cabinet/recruiter/candidate_detail.html",
                  {"breadcrumbs": _crumbs(
                      ("Кабинет рекрутёра", reverse("rec_dashboard")),
                      ("Кандидаты", reverse("rec_candidates")),
                      (candidate.full_name(), None)),
                   "candidate": candidate,
                   "skills": candidate.candidateskill_set.select_related("skill"),
                   "apps": candidate.applications.select_related("vacancy", "stage"),
                   "resumes": candidate.resumes.all()})


@recruiter_required
def rec_applications(request):
    """Список откликов (канбан по этапам) с фильтрами."""
    qs = Application.objects.select_related(
        "candidate", "vacancy", "stage").all()
    status = request.GET.get("status", "")
    if status:
        qs = qs.filter(status=status)
    stages = Stage.objects.order_by("order")
    by_stage = {s: [] for s in stages}
    for app in qs[:200]:
        by_stage.setdefault(app.stage, []).append(app)
    return render(request, "cabinet/recruiter/applications.html",
                  {"breadcrumbs": _crumbs(
                      ("Кабинет рекрутёра", reverse("rec_dashboard")),
                      ("Отклики", None)),
                   "by_stage": by_stage, "status": status,
                   "status_choices": ApplicationStatus.choices})


@recruiter_required
def rec_application_edit(request, pk):
    """
    Изменить этап/статус/оценку отклика.

    Атомарность (замечание рецензента 9): при переводе на терминальный этап
    воронки со статусом «Принят» одновременно с обновлением отклика
    закрываем связанную вакансию. Обе операции — в одной транзакции;
    либо изменения применятся целиком, либо ни одно не применится, что
    гарантирует целостность данных подбора.
    """
    app = get_object_or_404(
        Application.objects.select_related("candidate", "vacancy", "stage"), pk=pk)
    if request.method == "POST":
        form = ApplicationStageForm(request.POST, instance=app)
        if form.is_valid():
            with transaction.atomic():
                form.save()
                # Перечитываем app, т.к. form.save() мог изменить stage/status.
                app.refresh_from_db()
                if (app.stage.is_terminal
                        and app.status == ApplicationStatus.HIRED
                        and app.vacancy.status != VacancyStatus.CLOSED):
                    app.vacancy.status = VacancyStatus.CLOSED
                    app.vacancy.closed_at = timezone.localdate()
                    app.vacancy.save(update_fields=["status", "closed_at"])
            messages.success(request, "Отклик обновлён.")
            return redirect("rec_applications")
    else:
        form = ApplicationStageForm(instance=app)
    return render(request, "cabinet/recruiter/application_form.html",
                  {"breadcrumbs": _crumbs(
                      ("Кабинет рекрутёра", reverse("rec_dashboard")),
                      ("Отклики", reverse("rec_applications")),
                      (str(app), None)),
                   "form": form, "app": app,
                   "interviews": app.interviews.all()})


@recruiter_required
def rec_interviews(request):
    """Список собеседований + назначение нового."""
    if request.method == "POST":
        form = InterviewForm(request.POST, recruiter=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Собеседование назначено.")
            return redirect("rec_interviews")
        messages.error(request, "Проверьте поля формы.")
    else:
        form = InterviewForm(recruiter=request.user)
    interviews = Interview.objects.select_related(
        "application__candidate", "application__vacancy",
        "interviewer").order_by("-scheduled_at")[:50]
    return render(request, "cabinet/recruiter/interviews.html",
                  {"breadcrumbs": _crumbs(
                      ("Кабинет рекрутёра", reverse("rec_dashboard")),
                      ("Собеседования", None)),
                   "form": form, "interviews": interviews})


@recruiter_required
def rec_analytics(request):
    """Полная панель HR-аналитики (дашборды + сложные отчёты)."""
    context = analytics.dashboard_context()
    context["breadcrumbs"] = _crumbs(
        ("Кабинет рекрутёра", reverse("rec_dashboard")),
        ("HR-аналитика", None))
    return render(request, "cabinet/recruiter/analytics.html", context)


# ---- выгрузка документов (рекрутёр) ----------------------------------------
@recruiter_required
def export_candidate_docx(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    return documents.candidate_card_docx(candidate)


@recruiter_required
def export_analytics_xlsx(request):
    return documents.analytics_xlsx()


@recruiter_required
def export_vacancies_xlsx(request):
    return documents.vacancies_xlsx()


# ===========================================================================
#  КАБИНЕТ КАНДИДАТА (≥5 разделов)
# ===========================================================================
def _get_candidate(request):
    """Получить анкету кандидата текущего пользователя (создать при отсутствии)."""
    candidate = getattr(request.user, "candidate_profile", None)
    if candidate is None:
        from .models import Source
        src, _ = Source.objects.get_or_create(
            name="Карьерный сайт",
            defaults={"kind": "собственный сайт", "cost_per_contact": 0})
        candidate = Candidate.objects.create(
            user=request.user,
            last_name=request.user.last_name or request.user.username,
            first_name=request.user.first_name,
            email=request.user.email or f"{request.user.username}@example.com",
            source=src)
    return candidate


@candidate_required
def cand_dashboard(request):
    candidate = _get_candidate(request)
    apps = candidate.applications.select_related("vacancy", "stage")
    return render(request, "cabinet/candidate/dashboard.html",
                  {"breadcrumbs": _crumbs(("Личный кабинет", None)),
                   "candidate": candidate,
                   "apps": apps[:6],
                   "apps_count": apps.count(),
                   "resumes_count": candidate.resumes.count(),
                   "interviews": Interview.objects.filter(
                       application__candidate=candidate).select_related(
                       "application__vacancy")[:5],
                   "recommended": Vacancy.objects.filter(
                       status__in=[VacancyStatus.OPEN, VacancyStatus.IN_PROGRESS]
                   ).exclude(applications__candidate=candidate)[:4]})


@candidate_required
def cand_profile(request):
    candidate = _get_candidate(request)
    if request.method == "POST":
        form = CandidateProfileForm(request.POST, instance=candidate)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль обновлён.")
            return redirect("cand_profile")
        messages.error(request, "Проверьте поля формы.")
    else:
        form = CandidateProfileForm(instance=candidate)
    return render(request, "cabinet/candidate/profile.html",
                  {"breadcrumbs": _crumbs(
                      ("Личный кабинет", reverse("cand_dashboard")),
                      ("Профиль", None)),
                   "form": form, "candidate": candidate})


@candidate_required
def cand_resumes(request):
    """Загрузка и просмотр резюме (доступ к файловой системе)."""
    candidate = _get_candidate(request)
    if request.method == "POST":
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save(commit=False)
            resume.candidate = candidate
            resume.save()
            messages.success(request, "Резюме загружено.")
            return redirect("cand_resumes")
        messages.error(request, "Не удалось загрузить файл — проверьте формат и размер.")
    else:
        form = ResumeUploadForm()
    return render(request, "cabinet/candidate/resumes.html",
                  {"breadcrumbs": _crumbs(
                      ("Личный кабинет", reverse("cand_dashboard")),
                      ("Мои резюме", None)),
                   "form": form, "resumes": candidate.resumes.all()})


@candidate_required
def cand_resume_delete(request, pk):
    candidate = _get_candidate(request)
    resume = get_object_or_404(candidate.resumes, pk=pk)
    if request.method == "POST":
        resume.file.delete(save=False)
        resume.delete()
        messages.info(request, "Резюме удалено.")
    return redirect("cand_resumes")


@candidate_required
def cand_applications(request):
    candidate = _get_candidate(request)
    apps = candidate.applications.select_related(
        "vacancy", "stage").order_by("-applied_at")
    return render(request, "cabinet/candidate/applications.html",
                  {"breadcrumbs": _crumbs(
                      ("Личный кабинет", reverse("cand_dashboard")),
                      ("Мои отклики", None)),
                   "apps": apps})


@candidate_required
def cand_interviews(request):
    candidate = _get_candidate(request)
    interviews = Interview.objects.filter(
        application__candidate=candidate).select_related(
        "application__vacancy", "interviewer").order_by("-scheduled_at")
    return render(request, "cabinet/candidate/interviews.html",
                  {"breadcrumbs": _crumbs(
                      ("Личный кабинет", reverse("cand_dashboard")),
                      ("Мои собеседования", None)),
                   "interviews": interviews})


@candidate_required
def cand_apply(request, vacancy_pk):
    """Отклик кандидата на вакансию."""
    candidate = _get_candidate(request)
    vacancy = get_object_or_404(Vacancy, pk=vacancy_pk)
    if Application.objects.filter(candidate=candidate, vacancy=vacancy).exists():
        messages.warning(request, "Вы уже откликались на эту вакансию.")
        return redirect("vacancy_detail", pk=vacancy.pk)
    first_stage = Stage.objects.order_by("order").first()
    if request.method == "POST":
        form = ApplicationCandidateForm(request.POST)
        if form.is_valid():
            app = form.save(commit=False)
            app.candidate = candidate
            app.vacancy = vacancy
            app.stage = first_stage
            app.status = ApplicationStatus.NEW
            app.save()
            messages.success(
                request, f"Отклик на вакансию «{vacancy.title}» отправлен!")
            return redirect("cand_applications")
    else:
        form = ApplicationCandidateForm()
    return render(request, "cabinet/candidate/apply.html",
                  {"breadcrumbs": _crumbs(
                      ("Вакансии", reverse("vacancies")),
                      (vacancy.title, reverse("vacancy_detail", args=[vacancy.pk])),
                      ("Отклик", None)),
                   "form": form, "vacancy": vacancy})
