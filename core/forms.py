"""
Формы приложения с серверной валидацией данных.

Каждая форма снабжена понятными подписями и сообщениями об ошибках; для всех
полей автоматически проставляются CSS-классы Bootstrap, чтобы интерфейс
выглядел единообразно. Валидация проверяет типы, обязательность и диапазоны
значений (например, корректность зарплатной вилки и размер файла резюме).
"""
import os

from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm

from .models import (Application, Candidate, Feedback, Interview, ResumeFile,
                     Role, User, Vacancy)


class BootstrapMixin:
    """Примесь: проставляет Bootstrap-классы всем виджетам формы."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            css = "form-check-input" if isinstance(
                widget, (forms.CheckboxInput,)) else "form-control"
            if isinstance(widget, forms.Select):
                css = "form-select"
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing} {css}".strip()


class FeedbackForm(BootstrapMixin, forms.ModelForm):
    """Форма обратной связи (сообщение сохраняется в БД)."""

    # Honeypot-поле против простейших спам-ботов: люди его не видят и не заполняют.
    website = forms.CharField(required=False, widget=forms.HiddenInput,
                              label="")

    class Meta:
        model = Feedback
        fields = ["name", "email", "phone", "subject", "message"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 5}),
        }

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Обнаружена подозрительная активность.")
        return ""

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 10:
            raise forms.ValidationError(
                "Опишите вопрос подробнее (не менее 10 символов).")
        return message


class SignUpForm(BootstrapMixin, UserCreationForm):
    """Регистрация соискателя. Создаёт пользователя с ролью «кандидат»."""

    first_name = forms.CharField(label="Имя", max_length=80)
    last_name = forms.CharField(label="Фамилия", max_length=80)
    email = forms.EmailField(label="Email")
    phone = forms.CharField(label="Телефон", max_length=20, required=False)
    city = forms.CharField(label="Город", max_length=80, required=False)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "phone",
                  "password1", "password2"]

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Пользователь с таким email уже зарегистрирован.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = Role.CANDIDATE
        user.email = self.cleaned_data["email"]
        user.phone = self.cleaned_data.get("phone", "")
        if commit:
            user.save()
            # Сразу создаём анкету кандидата, связанную с учётной записью.
            from .models import Source
            default_source, _ = Source.objects.get_or_create(
                name="Карьерный сайт",
                defaults={"kind": "собственный сайт", "cost_per_contact": 0})
            Candidate.objects.create(
                user=user,
                last_name=user.last_name,
                first_name=user.first_name,
                email=user.email,
                phone=user.phone,
                city=self.cleaned_data.get("city", ""),
                source=default_source,
            )
        return user


class CandidateProfileForm(BootstrapMixin, forms.ModelForm):
    """Редактирование соискателем собственной анкеты."""

    class Meta:
        model = Candidate
        fields = ["last_name", "first_name", "patronymic", "email", "phone",
                  "city", "desired_salary", "experience_years", "grade", "summary"]
        widgets = {"summary": forms.Textarea(attrs={"rows": 4})}

    def clean_desired_salary(self):
        value = self.cleaned_data["desired_salary"]
        if value and value > 2_000_000:
            raise forms.ValidationError("Укажите реалистичную сумму (до 2 000 000 ₽).")
        return value


class ResumeUploadForm(BootstrapMixin, forms.ModelForm):
    """Загрузка файла резюме с проверкой расширения и размера."""

    class Meta:
        model = ResumeFile
        fields = ["title", "file"]

    def clean_file(self):
        f = self.cleaned_data["file"]
        ext = os.path.splitext(f.name)[1].lower()
        if ext not in settings.RESUME_ALLOWED_EXT:
            raise forms.ValidationError(
                "Допустимы файлы форматов: "
                + ", ".join(settings.RESUME_ALLOWED_EXT))
        if f.size > settings.RESUME_MAX_SIZE_MB * 1024 * 1024:
            raise forms.ValidationError(
                f"Размер файла не должен превышать {settings.RESUME_MAX_SIZE_MB} МБ.")
        return f


class ApplicationCandidateForm(BootstrapMixin, forms.ModelForm):
    """Отклик кандидата на вакансию (сопроводительное письмо)."""

    class Meta:
        model = Application
        fields = ["cover_letter"]
        widgets = {"cover_letter": forms.Textarea(
            attrs={"rows": 4, "placeholder": "Почему вы подходите на эту позицию?"})}


class VacancyForm(BootstrapMixin, forms.ModelForm):
    """Создание/редактирование вакансии рекрутёром."""

    class Meta:
        model = Vacancy
        fields = ["title", "department", "grade", "salary_min", "salary_max",
                  "status", "recruiter", "city", "is_remote", "description",
                  "planned_close"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "planned_close": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        smin, smax = cleaned.get("salary_min"), cleaned.get("salary_max")
        if smin and smax and smin > smax:
            self.add_error("salary_max",
                           "Верхняя граница вилки не может быть меньше нижней.")
        return cleaned


class CandidateForm(BootstrapMixin, forms.ModelForm):
    """Создание/редактирование карточки кандидата рекрутёром."""

    class Meta:
        model = Candidate
        fields = ["last_name", "first_name", "patronymic", "email", "phone",
                  "city", "desired_salary", "experience_years", "grade",
                  "source", "summary"]
        widgets = {"summary": forms.Textarea(attrs={"rows": 4})}


class InterviewForm(BootstrapMixin, forms.ModelForm):
    """Назначение/редактирование собеседования."""

    class Meta:
        model = Interview
        fields = ["application", "kind", "scheduled_at", "interviewer",
                  "result", "score", "notes"]
        widgets = {
            "scheduled_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, recruiter=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["scheduled_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        # Интервьюеров выбираем только из числа рекрутёров/администраторов.
        self.fields["interviewer"].queryset = User.objects.filter(
            role__in=[Role.RECRUITER, Role.ADMIN])


class ApplicationStageForm(BootstrapMixin, forms.ModelForm):
    """Изменение этапа/статуса/оценки отклика рекрутёром."""

    class Meta:
        model = Application
        fields = ["stage", "status", "score", "comment"]
        widgets = {"comment": forms.Textarea(attrs={"rows": 3})}
