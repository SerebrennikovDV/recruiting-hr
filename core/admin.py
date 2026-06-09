"""
Настройка панели администратора Django.

Зарегистрированы все прикладные модели (более 5 разделов, доступных только
администратору). Для ключевых моделей настроены отображаемые столбцы
(list_display), поиск (search_fields), фильтры (list_filter), редактирование
связанных записей (inline) и кастомные массовые действия (actions).
"""
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils import timezone

from .models import (Application, Article, Candidate, CandidateSkill,
                     Department, Evaluation, Feedback, Interview, Offer, Role,
                     ResumeFile, Skill, Source, Stage, User, Vacancy,
                     VacancySkill, VacancyStatus)


# ---------------------------------------------------------------------------
#  Пользователи
# ---------------------------------------------------------------------------
@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Администрирование пользователей с дополнительными полями (роль, отдел)."""

    list_display = ("username", "get_full_name_ru", "role", "email",
                    "department", "is_active")
    list_filter = ("role", "is_active", "department")
    search_fields = ("username", "first_name", "last_name", "email")
    # Добавляем наши поля в стандартные секции формы Django.
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Профиль рекрутинговой ИС",
         {"fields": ("patronymic", "role", "phone", "position", "department")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Профиль", {"fields": ("first_name", "last_name", "email", "role")}),
    )

    @admin.display(description="ФИО")
    def get_full_name_ru(self, obj):
        return obj.get_full_name_ru()


# ---------------------------------------------------------------------------
#  Inline-редакторы связанных записей
# ---------------------------------------------------------------------------
class CandidateSkillInline(admin.TabularInline):
    model = CandidateSkill
    extra = 1
    autocomplete_fields = ("skill",)


class VacancySkillInline(admin.TabularInline):
    model = VacancySkill
    extra = 1
    autocomplete_fields = ("skill",)


class ResumeInline(admin.TabularInline):
    model = ResumeFile
    extra = 0


class InterviewInline(admin.TabularInline):
    model = Interview
    extra = 0


class EvaluationInline(admin.TabularInline):
    model = Evaluation
    extra = 1


# ---------------------------------------------------------------------------
#  Справочники
# ---------------------------------------------------------------------------
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "head", "headcount_plan", "vacancies_count")
    search_fields = ("name", "head")

    @admin.display(description="Вакансий")
    def vacancies_count(self, obj):
        return obj.vacancies.count()


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "cost_per_contact", "is_active",
                    "candidates_count")
    list_filter = ("is_active", "kind")
    search_fields = ("name",)

    @admin.display(description="Кандидатов")
    def candidates_count(self, obj):
        return obj.candidates.count()


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "description")
    list_filter = ("category",)
    search_fields = ("name",)


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ("order", "name", "is_terminal", "applications_count")
    ordering = ("order",)

    @admin.display(description="Заявок")
    def applications_count(self, obj):
        return obj.applications.count()


# ---------------------------------------------------------------------------
#  Кандидаты
# ---------------------------------------------------------------------------
@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("full_name", "city", "grade", "experience_years",
                    "desired_salary", "source", "is_archived", "created_at")
    list_filter = ("grade", "source", "is_archived", "city")
    search_fields = ("last_name", "first_name", "email", "phone")
    inlines = [CandidateSkillInline, ResumeInline]
    date_hierarchy = "created_at"
    actions = ["mark_archived", "mark_active"]

    @admin.action(description="Отправить в архив выбранных кандидатов")
    def mark_archived(self, request, queryset):
        updated = queryset.update(is_archived=True)
        self.message_user(
            request, f"В архив отправлено кандидатов: {updated}.",
            level=messages.SUCCESS)

    @admin.action(description="Вернуть из архива выбранных кандидатов")
    def mark_active(self, request, queryset):
        updated = queryset.update(is_archived=False)
        self.message_user(
            request, f"Возвращено из архива: {updated}.", level=messages.SUCCESS)


# ---------------------------------------------------------------------------
#  Вакансии
# ---------------------------------------------------------------------------
@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ("title", "department", "grade", "status", "salary_range",
                    "recruiter", "applications_count", "opened_at")
    list_filter = ("status", "grade", "department", "is_remote")
    search_fields = ("title", "description")
    inlines = [VacancySkillInline]
    date_hierarchy = "opened_at"
    autocomplete_fields = ("recruiter",)
    actions = ["close_vacancies", "reopen_vacancies"]

    @admin.display(description="Откликов")
    def applications_count(self, obj):
        return obj.applications.count()

    @admin.action(description="Закрыть выбранные вакансии")
    def close_vacancies(self, request, queryset):
        updated = queryset.update(status=VacancyStatus.CLOSED,
                                  closed_at=timezone.localdate())
        self.message_user(
            request, f"Закрыто вакансий: {updated}.", level=messages.SUCCESS)

    @admin.action(description="Открыть выбранные вакансии заново")
    def reopen_vacancies(self, request, queryset):
        updated = queryset.update(status=VacancyStatus.OPEN, closed_at=None)
        self.message_user(
            request, f"Снова открыто вакансий: {updated}.", level=messages.SUCCESS)


# ---------------------------------------------------------------------------
#  Отклики, собеседования, офферы
# ---------------------------------------------------------------------------
@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("candidate", "vacancy", "stage", "status", "score",
                    "applied_at")
    list_filter = ("status", "stage", "vacancy__department")
    search_fields = ("candidate__last_name", "vacancy__title")
    inlines = [InterviewInline]
    date_hierarchy = "applied_at"
    actions = ["advance_to_interview", "reject_applications"]

    @admin.action(description="Перевести выбранные заявки на этап «Собеседование»")
    def advance_to_interview(self, request, queryset):
        from .models import ApplicationStatus
        stage = Stage.objects.filter(name__icontains="собес").first()
        count = 0
        for app in queryset:
            app.status = ApplicationStatus.INTERVIEW
            if stage:
                app.stage = stage
            app.save()
            count += 1
        self.message_user(request, f"Переведено заявок: {count}.",
                          level=messages.SUCCESS)

    @admin.action(description="Отклонить выбранные заявки")
    def reject_applications(self, request, queryset):
        from .models import ApplicationStatus
        updated = queryset.update(status=ApplicationStatus.REJECTED)
        self.message_user(request, f"Отклонено заявок: {updated}.",
                          level=messages.WARNING)


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ("application", "kind", "scheduled_at", "interviewer",
                    "result", "score")
    list_filter = ("kind", "result")
    search_fields = ("application__candidate__last_name",)
    inlines = [EvaluationInline]
    date_hierarchy = "scheduled_at"


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("application", "salary", "status", "start_date", "sent_at")
    list_filter = ("status",)
    actions = ["mark_accepted"]

    @admin.action(description="Отметить офферы как принятые")
    def mark_accepted(self, request, queryset):
        from .models import OfferStatus
        updated = queryset.update(status=OfferStatus.ACCEPTED)
        self.message_user(request, f"Принято офферов: {updated}.",
                          level=messages.SUCCESS)


# ---------------------------------------------------------------------------
#  Контент и обратная связь
# ---------------------------------------------------------------------------
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "email", "is_processed", "created_at")
    list_filter = ("is_processed",)
    search_fields = ("name", "email", "subject", "message")
    date_hierarchy = "created_at"
    actions = ["mark_processed"]

    @admin.action(description="Отметить обращения как обработанные")
    def mark_processed(self, request, queryset):
        updated = queryset.update(is_processed=True)
        self.message_user(request, f"Обработано обращений: {updated}.",
                          level=messages.SUCCESS)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "author_name", "published_at", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title", "summary", "body")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"
    actions = ["publish", "unpublish"]

    @admin.action(description="Опубликовать выбранные статьи")
    def publish(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f"Опубликовано: {updated}.",
                          level=messages.SUCCESS)

    @admin.action(description="Снять с публикации выбранные статьи")
    def unpublish(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f"Снято с публикации: {updated}.",
                          level=messages.WARNING)


# Регистрируем справочные модели «навыки кандидата/вакансии» отдельно —
# это даёт администратору ещё две таблицы для прямого просмотра связей.
@admin.register(ResumeFile)
class ResumeFileAdmin(admin.ModelAdmin):
    list_display = ("candidate", "title", "filename", "uploaded_at")
    search_fields = ("candidate__last_name", "title")
