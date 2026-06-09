# -*- coding: utf-8 -*-
"""
Создание реальных скриншотов работающего приложения через Playwright.

Скрипт открывает запущенный локально сервер, авторизуется под разными ролями
и сохраняет PNG-скриншоты ключевых экранов в docs/screens/. Эти изображения
вставляются в отчёт (раздел 3 «Технологическая реализация»).

Запуск (сервер должен быть запущен на 127.0.0.1:8009):
    python docs/make_screenshots.py
"""
import os
import time

from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:8009")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screens")
os.makedirs(OUT, exist_ok=True)

DESKTOP = {"width": 1366, "height": 900}
MOBILE = {"width": 390, "height": 844}


def login(page, username, password):
    """Авторизация через стандартную форму входа."""
    page.goto(f"{BASE}/login/", wait_until="networkidle")
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.click('form button')
    page.wait_for_load_state("networkidle")


def admin_login(page, username, password):
    page.goto(f"{BASE}/admin/login/", wait_until="networkidle")
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.click('input[type="submit"]')
    page.wait_for_load_state("networkidle")


def shot(page, url, name, full=True):
    page.goto(f"{BASE}{url}", wait_until="networkidle")
    time.sleep(0.4)
    page.screenshot(path=os.path.join(OUT, name), full_page=full)
    print("screenshot", name)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ---- Публичные страницы (десктоп) ----
        ctx = browser.new_context(viewport=DESKTOP, locale="ru-RU")
        page = ctx.new_page()
        shot(page, "/", "01_home.png")
        shot(page, "/vacancies/", "02_vacancies.png")
        shot(page, "/vacancies/1/", "03_vacancy_detail.png")
        shot(page, "/analytics/", "04_analytics_demo.png")
        shot(page, "/contacts/", "05_contacts.png")
        shot(page, "/help/", "06_help.png")
        shot(page, "/login/", "07_login.png")
        shot(page, "/register/", "08_register.png")
        shot(page, "/news/", "09_news.png")
        ctx.close()

        # ---- Кабинет рекрутёра ----
        ctx = browser.new_context(viewport=DESKTOP, locale="ru-RU")
        page = ctx.new_page()
        login(page, "recruiter", "Hr#Unitcode2026")
        shot(page, "/cabinet/recruiter/", "10_recruiter_dashboard.png")
        shot(page, "/cabinet/recruiter/vacancies/", "11_recruiter_vacancies.png")
        shot(page, "/cabinet/recruiter/candidates/", "12_recruiter_candidates.png")
        shot(page, "/cabinet/recruiter/candidates/1/", "13_candidate_detail.png")
        shot(page, "/cabinet/recruiter/applications/", "14_kanban.png")
        shot(page, "/cabinet/recruiter/interviews/", "15_interviews.png")
        shot(page, "/cabinet/recruiter/analytics/", "16_hr_analytics.png")
        ctx.close()

        # ---- Кабинет кандидата ----
        ctx = browser.new_context(viewport=DESKTOP, locale="ru-RU")
        page = ctx.new_page()
        login(page, "candidate", "User#Unitcode2026")
        shot(page, "/cabinet/candidate/", "17_candidate_dashboard.png")
        shot(page, "/cabinet/candidate/profile/", "18_candidate_profile.png")
        shot(page, "/cabinet/candidate/resumes/", "19_candidate_resumes.png")
        shot(page, "/cabinet/candidate/applications/", "20_candidate_applications.png")
        ctx.close()

        # ---- Панель администратора ----
        ctx = browser.new_context(viewport=DESKTOP, locale="ru-RU")
        page = ctx.new_page()
        admin_login(page, "admin", "Admin#Unitcode2026")
        shot(page, "/admin/", "21_admin_index.png")
        shot(page, "/admin/core/vacancy/", "22_admin_vacancies.png")
        shot(page, "/admin/core/candidate/", "23_admin_candidates.png")
        ctx.close()

        # ---- Мобильная версия (адаптивность) ----
        ctx = browser.new_context(viewport=MOBILE, locale="ru-RU",
                                  is_mobile=True, has_touch=True)
        page = ctx.new_page()
        shot(page, "/", "24_mobile_home.png")
        shot(page, "/vacancies/", "25_mobile_vacancies.png")
        ctx.close()

        browser.close()
    print("Готово. Скриншоты в", OUT)


if __name__ == "__main__":
    main()
