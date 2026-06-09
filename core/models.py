"""
Модели предметной области «Подбор персонала и HR-аналитика» для ООО «ЮНИТКОД».

Схема данных нормализована до нормальной формы Бойса—Кодда (НФБК): каждый
неключевой атрибут зависит от полного первичного ключа, повторяющиеся группы
вынесены в справочники (отделы, источники, навыки, этапы воронки), а связи
«многие-ко-многим» реализованы через ассоциативные сущности с собственными
реквизитами (CandidateSkill, VacancySkill, Application).

Состав таблиц (16 прикладных + системные таблицы Django):
    User, Department, Source, Skill, Stage, Candidate, Vacancy, Application,
    Interview, Evaluation, Offer, ResumeFile, CandidateSkill, VacancySkill,
    Feedback, Article.
"""
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone


# ---------------------------------------------------------------------------
#  Перечисления (наборы допустимых значений атрибутов-классификаторов)
# ---------------------------------------------------------------------------
class Role(models.TextChoices):
    """Три уровня доступа к системе (роли пользователей)."""

    ADMIN = "admin", "Администратор"
    RECRUITER = "recruiter", "HR-менеджер (рекрутёр)"
    CANDIDATE = "candidate", "Кандидат (соискатель)"


class Grade(models.TextChoices):
    """Грейд (уровень) вакансии/кандидата."""

    INTERN = "intern", "Стажёр"
    JUNIOR = "junior", "Junior"
    MIDDLE = "middle", "Middle"
    SENIOR = "senior", "Senior"
    LEAD = "lead", "Lead"


class VacancyStatus(models.TextChoices):
    """Статус жизненного цикла вакансии."""

    OPEN = "open", "Открыта"
    IN_PROGRESS = "in_progress", "В работе"
    ON_HOLD = "on_hold", "Приостановлена"
    CLOSED = "closed", "Закрыта"
    CANCELLED = "cancelled", "Отменена"


class ApplicationStatus(models.TextChoices):
    """Статус отклика (заявки кандидата на вакансию)."""

    NEW = "new", "Новый отклик"
    IN_REVIEW = "in_review", "На рассмотрении"
    INTERVIEW = "interview", "Собеседование"
    OFFER = "offer", "Оффер"
    HIRED = "hired", "Принят"
    REJECTED = "rejected", "Отклонён"


class InterviewType(models.TextChoices):
    """Тип собеседования."""

    HR = "hr", "HR-интервью"
    TECH = "tech", "Техническое"
    FINAL = "final", "Финальное"


class InterviewResult(models.TextChoices):
    """Результат собеседования."""

    SCHEDULED = "scheduled", "Назначено"
    PASSED = "passed", "Пройдено"
    FAILED = "failed", "Не пройдено"
    NO_SHOW = "no_show", "Неявка"


class OfferStatus(models.TextChoices):
    """Статус оффера (предложения о работе)."""

    SENT = "sent", "Отправлен"
    ACCEPTED = "accepted", "Принят"
    DECLINED = "declined", "Отклонён"
    EXPIRED = "expired", "Истёк срок"


# ---------------------------------------------------------------------------
#  Пользователь системы (кастомная модель)
# ---------------------------------------------------------------------------
class User(AbstractUser):
    """
    Пользователь системы. Расширяет стандартную модель Django полем роли и
    дополнительными реквизитами. Роль определяет доступный функционал
    (см. core.decorators и разграничение прав в представлениях/админке).
    """

    patronymic = models.CharField("Отчество", max_length=100, blank=True)
    role = models.CharField(
        "Роль", max_length=20, choices=Role.choices, default=Role.CANDIDATE
    )
    phone = models.CharField("Телефон", max_length=20, blank=True)
    position = models.CharField("Должность", max_length=120, blank=True)
    department = models.ForeignKey(
        "Department",
        verbose_name="Отдел",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )
    created_at = models.DateTimeField("Дата регистрации", default=timezone.now)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return self.get_full_name_ru() or self.username

    def get_full_name_ru(self):
        """ФИО в формате «Фамилия Имя Отчество»."""
        parts = [self.last_name, self.first_name, self.patronymic]
        return " ".join(p for p in parts if p).strip()

    def short_name(self):
        """Фамилия и инициалы, например «Серебренников Д. В.»."""
        if not self.last_name:
            return self.username
        initials = ""
        if self.first_name:
            initials += f" {self.first_name[0]}."
        if self.patronymic:
            initials += f" {self.patronymic[0]}."
        return f"{self.last_name}{initials}".strip()

    @property
    def is_recruiter(self):
        return self.role == Role.RECRUITER or self.is_superuser

    @property
    def is_candidate_role(self):
        return self.role == Role.CANDIDATE

    @property
    def is_admin_role(self):
        return self.role == Role.ADMIN or self.is_superuser


# ---------------------------------------------------------------------------
#  Справочники (классификаторы предметной области)
# ---------------------------------------------------------------------------
class Department(models.Model):
    """Отдел-заказчик найма внутри ООО «ЮНИТКОД»."""

    name = models.CharField("Название отдела", max_length=120, unique=True)
    head = models.CharField("Руководитель", max_length=120, blank=True)
    headcount_plan = models.PositiveIntegerField("Плановая численность", default=0)
    description = models.TextField("Описание", blank=True)

    class Meta:
        verbose_name = "Отдел"
        verbose_name_plural = "Отделы"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Source(models.Model):
    """Источник привлечения кандидатов (для расчёта cost-per-hire)."""

    name = models.CharField("Название источника", max_length=120, unique=True)
    kind = models.CharField("Тип", max_length=60, blank=True,
                            help_text="например: джоб-борд, соцсеть, реферал")
    cost_per_contact = models.DecimalField(
        "Стоимость привлечения, ₽", max_digits=10, decimal_places=2, default=0,
        help_text="Усреднённые затраты на одного привлечённого кандидата")
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Источник кандидатов"
        verbose_name_plural = "Источники кандидатов"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Skill(models.Model):
    """Профессиональный навык/компетенция."""

    CATEGORY_CHOICES = [
        ("lang", "Язык программирования"),
        ("framework", "Фреймворк/библиотека"),
        ("db", "База данных"),
        ("tool", "Инструмент/технология"),
        ("soft", "Гибкий навык"),
    ]
    name = models.CharField("Навык", max_length=80, unique=True)
    category = models.CharField("Категория", max_length=20,
                                choices=CATEGORY_CHOICES, default="tool")
    description = models.CharField("Описание", max_length=255, blank=True)

    class Meta:
        verbose_name = "Навык"
        verbose_name_plural = "Навыки"
        ordering = ["category", "name"]

    def __str__(self):
        return self.name


class Stage(models.Model):
    """Этап воронки подбора (скрининг → HR → тех → финал → оффер → принят)."""

    name = models.CharField("Название этапа", max_length=80, unique=True)
    order = models.PositiveSmallIntegerField("Порядковый номер", default=0, unique=True)
    description = models.CharField("Описание", max_length=255, blank=True)
    is_terminal = models.BooleanField("Завершающий этап", default=False)

    class Meta:
        verbose_name = "Этап воронки"
        verbose_name_plural = "Этапы воронки"
        ordering = ["order"]

    def __str__(self):
        return f"{self.order}. {self.name}"


# ---------------------------------------------------------------------------
#  Основные сущности
# ---------------------------------------------------------------------------
class Candidate(models.Model):
    """Кандидат (соискатель). Центральная сущность подбора персонала."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, verbose_name="Учётная запись",
        on_delete=models.SET_NULL, null=True, blank=True, related_name="candidate_profile")
    last_name = models.CharField("Фамилия", max_length=80)
    first_name = models.CharField("Имя", max_length=80)
    patronymic = models.CharField("Отчество", max_length=80, blank=True)
    email = models.EmailField("Email")
    phone = models.CharField("Телефон", max_length=20, blank=True)
    city = models.CharField("Город", max_length=80, blank=True)
    desired_salary = models.PositiveIntegerField("Желаемая зарплата, ₽", default=0)
    experience_years = models.DecimalField(
        "Опыт работы, лет", max_digits=4, decimal_places=1, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(60)])
    grade = models.CharField("Грейд", max_length=20, choices=Grade.choices,
                             default=Grade.JUNIOR)
    source = models.ForeignKey(Source, verbose_name="Источник",
                               on_delete=models.PROTECT, related_name="candidates")
    skills = models.ManyToManyField(Skill, through="CandidateSkill",
                                    verbose_name="Навыки", related_name="candidates")
    summary = models.TextField("О кандидате", blank=True)
    is_archived = models.BooleanField("В архиве", default=False)
    created_at = models.DateTimeField("Дата добавления", default=timezone.now)

    class Meta:
        verbose_name = "Кандидат"
        verbose_name_plural = "Кандидаты"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["last_name", "first_name"])]

    def __str__(self):
        return self.full_name()

    def full_name(self):
        parts = [self.last_name, self.first_name, self.patronymic]
        return " ".join(p for p in parts if p).strip()

    def get_absolute_url(self):
        return reverse("candidate_detail", args=[self.pk])


class Vacancy(models.Model):
    """Вакансия — позиция, на которую ведётся подбор."""

    title = models.CharField("Название вакансии", max_length=150)
    department = models.ForeignKey(Department, verbose_name="Отдел",
                                   on_delete=models.PROTECT, related_name="vacancies")
    grade = models.CharField("Грейд", max_length=20, choices=Grade.choices,
                             default=Grade.MIDDLE)
    salary_min = models.PositiveIntegerField("Зарплата от, ₽", default=0)
    salary_max = models.PositiveIntegerField("Зарплата до, ₽", default=0)
    status = models.CharField("Статус", max_length=20, choices=VacancyStatus.choices,
                              default=VacancyStatus.OPEN)
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Ответственный рекрутёр",
        on_delete=models.SET_NULL, null=True, blank=True, related_name="vacancies",
        limit_choices_to={"role": Role.RECRUITER})
    required_skills = models.ManyToManyField(
        Skill, through="VacancySkill", verbose_name="Требуемые навыки",
        related_name="vacancies")
    description = models.TextField("Описание и требования", blank=True)
    city = models.CharField("Город", max_length=80, blank=True, default="Москва")
    is_remote = models.BooleanField("Удалённая работа", default=False)
    opened_at = models.DateField("Дата открытия", default=timezone.localdate)
    planned_close = models.DateField("Плановая дата закрытия", null=True, blank=True)
    closed_at = models.DateField("Фактическая дата закрытия", null=True, blank=True)

    class Meta:
        verbose_name = "Вакансия"
        verbose_name_plural = "Вакансии"
        ordering = ["-opened_at"]
        indexes = [models.Index(fields=["status"])]

    def __str__(self):
        return f"{self.title} ({self.get_grade_display()})"

    def get_absolute_url(self):
        return reverse("vacancy_detail", args=[self.pk])

    def salary_range(self):
        """Человекочитаемая зарплатная вилка."""
        if self.salary_min and self.salary_max:
            return f"{self.salary_min:,} – {self.salary_max:,} ₽".replace(",", " ")
        if self.salary_max:
            return f"до {self.salary_max:,} ₽".replace(",", " ")
        return "по договорённости"

    def time_to_hire(self):
        """Время закрытия вакансии в днях (если закрыта)."""
        if self.closed_at:
            return (self.closed_at - self.opened_at).days
        return None

    @property
    def is_open(self):
        return self.status in {VacancyStatus.OPEN, VacancyStatus.IN_PROGRESS}


class Application(models.Model):
    """
    Отклик (заявка) — ассоциативная сущность связи «кандидат ↔ вакансия»
    с собственными реквизитами (этап воронки, статус, оценка, комментарий).
    """

    candidate = models.ForeignKey(Candidate, verbose_name="Кандидат",
                                  on_delete=models.CASCADE, related_name="applications")
    vacancy = models.ForeignKey(Vacancy, verbose_name="Вакансия",
                                on_delete=models.CASCADE, related_name="applications")
    stage = models.ForeignKey(Stage, verbose_name="Текущий этап",
                              on_delete=models.PROTECT, related_name="applications")
    status = models.CharField("Статус", max_length=20,
                              choices=ApplicationStatus.choices,
                              default=ApplicationStatus.NEW)
    score = models.PositiveSmallIntegerField(
        "Оценка соответствия (0–100)", default=0,
        validators=[MaxValueValidator(100)])
    cover_letter = models.TextField("Сопроводительное письмо", blank=True)
    comment = models.TextField("Комментарий рекрутёра", blank=True)
    applied_at = models.DateTimeField("Дата отклика", default=timezone.now)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Отклик (заявка)"
        verbose_name_plural = "Отклики (заявки)"
        ordering = ["-applied_at"]
        # Один кандидат может откликнуться на конкретную вакансию только один раз.
        constraints = [
            models.UniqueConstraint(fields=["candidate", "vacancy"],
                                    name="uniq_candidate_vacancy")
        ]

    def __str__(self):
        return f"{self.candidate} → {self.vacancy.title}"


class Interview(models.Model):
    """Собеседование по конкретному отклику."""

    application = models.ForeignKey(Application, verbose_name="Отклик",
                                    on_delete=models.CASCADE, related_name="interviews")
    kind = models.CharField("Тип", max_length=20, choices=InterviewType.choices,
                            default=InterviewType.HR)
    scheduled_at = models.DateTimeField("Дата и время")
    interviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Интервьюер",
        on_delete=models.SET_NULL, null=True, related_name="interviews")
    result = models.CharField("Результат", max_length=20,
                              choices=InterviewResult.choices,
                              default=InterviewResult.SCHEDULED)
    score = models.PositiveSmallIntegerField(
        "Балл (0–10)", default=0, validators=[MaxValueValidator(10)])
    notes = models.TextField("Заметки", blank=True)

    class Meta:
        verbose_name = "Собеседование"
        verbose_name_plural = "Собеседования"
        ordering = ["-scheduled_at"]

    def __str__(self):
        return f"{self.get_kind_display()} — {self.application.candidate}"


class Evaluation(models.Model):
    """Оценка кандидата по критерию в рамках собеседования (фидбек)."""

    interview = models.ForeignKey(Interview, verbose_name="Собеседование",
                                  on_delete=models.CASCADE, related_name="evaluations")
    criterion = models.CharField("Критерий", max_length=120)
    score = models.PositiveSmallIntegerField(
        "Балл (0–10)", default=0, validators=[MaxValueValidator(10)])
    comment = models.CharField("Комментарий", max_length=255, blank=True)

    class Meta:
        verbose_name = "Оценка по критерию"
        verbose_name_plural = "Оценки по критериям"
        ordering = ["interview", "criterion"]

    def __str__(self):
        return f"{self.criterion}: {self.score}"


class Offer(models.Model):
    """Оффер — формальное предложение о работе по итогам подбора."""

    application = models.OneToOneField(Application, verbose_name="Отклик",
                                       on_delete=models.CASCADE, related_name="offer")
    salary = models.PositiveIntegerField("Предлагаемая зарплата, ₽", default=0)
    start_date = models.DateField("Дата выхода", null=True, blank=True)
    status = models.CharField("Статус", max_length=20, choices=OfferStatus.choices,
                              default=OfferStatus.SENT)
    sent_at = models.DateField("Дата отправки", default=timezone.localdate)
    comment = models.CharField("Комментарий", max_length=255, blank=True)

    class Meta:
        verbose_name = "Оффер"
        verbose_name_plural = "Офферы"
        ordering = ["-sent_at"]

    def __str__(self):
        return f"Оффер: {self.application.candidate} ({self.salary:,} ₽)".replace(",", " ")


class ResumeFile(models.Model):
    """Файл резюме кандидата (реализация доступа к файловой системе)."""

    candidate = models.ForeignKey(Candidate, verbose_name="Кандидат",
                                  on_delete=models.CASCADE, related_name="resumes")
    file = models.FileField("Файл резюме", upload_to="resumes/%Y/%m/")
    title = models.CharField("Название", max_length=150, blank=True)
    uploaded_at = models.DateTimeField("Дата загрузки", default=timezone.now)

    class Meta:
        verbose_name = "Резюме (файл)"
        verbose_name_plural = "Резюме (файлы)"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.title or f"Резюме {self.candidate}"

    def filename(self):
        import os
        return os.path.basename(self.file.name) if self.file else ""


# ---------------------------------------------------------------------------
#  Ассоциативные сущности связей «многие-ко-многим» с реквизитами
# ---------------------------------------------------------------------------
class CandidateSkill(models.Model):
    """Связь «кандидат ↔ навык» с уровнем владения."""

    LEVEL_CHOICES = [(1, "Базовый"), (2, "Уверенный"), (3, "Продвинутый"),
                     (4, "Эксперт")]
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE,
                                  verbose_name="Кандидат")
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, verbose_name="Навык")
    level = models.PositiveSmallIntegerField("Уровень владения", choices=LEVEL_CHOICES,
                                             default=2)

    class Meta:
        verbose_name = "Навык кандидата"
        verbose_name_plural = "Навыки кандидатов"
        constraints = [
            models.UniqueConstraint(fields=["candidate", "skill"],
                                    name="uniq_candidate_skill")
        ]

    def __str__(self):
        return f"{self.candidate} — {self.skill} ({self.get_level_display()})"


class VacancySkill(models.Model):
    """Связь «вакансия ↔ требуемый навык» с признаком обязательности."""

    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE,
                                verbose_name="Вакансия")
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, verbose_name="Навык")
    is_required = models.BooleanField("Обязательный", default=True)

    class Meta:
        verbose_name = "Навык вакансии"
        verbose_name_plural = "Навыки вакансий"
        constraints = [
            models.UniqueConstraint(fields=["vacancy", "skill"],
                                    name="uniq_vacancy_skill")
        ]

    def __str__(self):
        return f"{self.vacancy.title} — {self.skill}"


# ---------------------------------------------------------------------------
#  Вспомогательные сущности (контент и обратная связь)
# ---------------------------------------------------------------------------
class Feedback(models.Model):
    """Сообщение из формы обратной связи (сохраняется в БД, не отправляется почтой)."""

    name = models.CharField("Имя", max_length=120)
    email = models.EmailField("Email")
    phone = models.CharField("Телефон", max_length=20, blank=True)
    subject = models.CharField("Тема", max_length=160)
    message = models.TextField("Сообщение")
    is_processed = models.BooleanField("Обработано", default=False)
    created_at = models.DateTimeField("Дата отправки", default=timezone.now)

    class Meta:
        verbose_name = "Обращение (обратная связь)"
        verbose_name_plural = "Обращения (обратная связь)"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} — {self.name}"


class Article(models.Model):
    """Новость/статья блога компании (наполнение публичных страниц контентом)."""

    title = models.CharField("Заголовок", max_length=200)
    slug = models.SlugField("Ссылка (slug)", max_length=210, unique=True)
    summary = models.CharField("Краткое описание", max_length=300)
    body = models.TextField("Текст статьи")
    author_name = models.CharField("Автор", max_length=120,
                                   default="Пресс-служба ЮНИТКОД")
    published_at = models.DateField("Дата публикации", default=timezone.localdate)
    is_published = models.BooleanField("Опубликовано", default=True)

    class Meta:
        verbose_name = "Статья/новость"
        verbose_name_plural = "Статьи и новости"
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("news_detail", args=[self.slug])
