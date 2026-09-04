"""
Маршруты основного приложения core.

Сгруппированы по разделам: публичные страницы, аутентификация, кабинет
рекрутёра, кабинет кандидата, выгрузка документов.
"""
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # --- Публичные страницы (доступны без авторизации) ---
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("how-it-works/", views.how_it_works, name="how_it_works"),
    path("employers/", views.employers, name="employers"),
    path("for-candidates/", views.candidates_info, name="candidates_info"),
    path("help/", views.help_page, name="help"),
    path("vacancies/", views.vacancies, name="vacancies"),
    path("vacancies/<int:pk>/", views.vacancy_detail, name="vacancy_detail"),
    path("analytics/", views.analytics_demo, name="analytics_demo"),
    path("news/", views.news, name="news"),
    path("news/<slug:slug>/", views.news_detail, name="news_detail"),
    path("contacts/", views.contacts, name="contacts"),

    # --- Аутентификация ---
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(
        template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("cabinet/", views.dashboard, name="dashboard"),

    # --- Кабинет рекрутёра ---
    path("cabinet/recruiter/", views.rec_dashboard, name="rec_dashboard"),
    path("cabinet/recruiter/vacancies/", views.rec_vacancies, name="rec_vacancies"),
    path("cabinet/recruiter/vacancies/new/", views.rec_vacancy_form,
         name="rec_vacancy_create"),
    path("cabinet/recruiter/vacancies/<int:pk>/edit/", views.rec_vacancy_form,
         name="rec_vacancy_edit"),
    path("cabinet/recruiter/candidates/", views.rec_candidates, name="rec_candidates"),
    path("cabinet/recruiter/candidates/new/", views.rec_candidate_form,
         name="rec_candidate_create"),
    path("cabinet/recruiter/candidates/<int:pk>/edit/", views.rec_candidate_form,
         name="rec_candidate_edit"),
    path("cabinet/recruiter/candidates/<int:pk>/", views.candidate_detail,
         name="candidate_detail"),
    path("cabinet/recruiter/applications/", views.rec_applications,
         name="rec_applications"),
    path("cabinet/recruiter/applications/<int:pk>/edit/",
         views.rec_application_edit, name="rec_application_edit"),
    path("cabinet/recruiter/interviews/", views.rec_interviews, name="rec_interviews"),
    path("cabinet/recruiter/analytics/", views.rec_analytics, name="rec_analytics"),
    path("cabinet/recruiter/candidates/<int:pk>/card.docx",
         views.export_candidate_docx, name="export_candidate_docx"),
    path("cabinet/recruiter/export/analytics.xlsx", views.export_analytics_xlsx,
         name="export_analytics_xlsx"),
    path("cabinet/recruiter/export/vacancies.xlsx", views.export_vacancies_xlsx,
         name="export_vacancies_xlsx"),

    # --- Кабинет кандидата ---
    path("cabinet/recruiter/import/", views.rec_import, name="rec_import"),
    path("cabinet/recruiter/import/<int:pk>/transfer/",
         views.rec_import_transfer, name="rec_import_transfer"),

    path("cabinet/candidate/", views.cand_dashboard, name="cand_dashboard"),
    path("cabinet/candidate/profile/", views.cand_profile, name="cand_profile"),
    path("cabinet/candidate/resumes/", views.cand_resumes, name="cand_resumes"),
    path("cabinet/candidate/resumes/<int:pk>/delete/", views.cand_resume_delete,
         name="cand_resume_delete"),
    path("cabinet/candidate/applications/", views.cand_applications,
         name="cand_applications"),
    path("cabinet/candidate/interviews/", views.cand_interviews,
         name="cand_interviews"),
    path("cabinet/candidate/apply/<int:vacancy_pk>/", views.cand_apply,
         name="cand_apply"),
]
