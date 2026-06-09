# История изменений (CHANGELOG)

Проект «UnitHire» — рекрутинговая ИС с HR-аналитикой.

## v2 — исправления по замечаниям рецензента (2026-06-09)

- Миграция 0002: индексы на created_at/applied_at/opened_at/closed_at, CHECK 1..4 на CandidateSkill.level.
- Миграция 0003: модель IndustryBenchmark + seed-фикстуры с бенчмарками отрасли.
- Аналитика: исправлены SQL-листинги воронки, time-to-hire, cost-per-hire; добавлена функция benchmark_comparison и блок «Сравнение с бенчмарками отрасли» на дашборде рекрутёра.
- Безопасность загрузки резюме: UUID-имя файла, MIME-валидация, проверка пустых файлов.
- Атомарность: rec_application_edit обёрнут в @transaction.atomic, при HIRED + терминальный этап вакансия закрывается в одной транзакции.
- Кабинет кандидата: badge-индикация этапа и статуса откликов.
- Тесты: добавлены классы CyrillicRoundTripTests, PerformanceTests, ResumeSecurityTests, ApplicationTransactionTests, CandidateStatusVisibilityTests, BenchmarkTests, BenchmarkComparisonTests (общее число тестов 42).
- Деплой: Dockerfile, docker-compose.yml (web + nginx + postgres:15), nginx/nginx.conf, обновлённый .env.example для Yandex Cloud.
- Settings: env-driven CSRF/cookies для HTTP-only IP-деплоя.
- README, ИНСТРУКЦИЯ_YANDEX_CLOUD.md, СВОДКА_ИСПРАВЛЕНИЙ.md.

## v1 — первая редакция

- Добавлены массовые действия в панели администратора.
- Реализованы сложные отчёты HR-аналитики с агрегатами.
- Исправлен конфликт имени аннотации applications в funnel_report.
- Уточнены стили карточек KPI и адаптивная сетка.
- Добавлена пагинация с сохранением параметров фильтра.
- Подключены всплывающие уведомления (Django messages).
- Усилена валидация форм: вилка ЗП и размер резюме.
- Оптимизированы запросы списков (select_related, annotate).
- Хлебные крошки добавлены на все страницы сайта.
- Добавлены сценарные тесты основных пользовательских путей.
- Проверены все роли, страницы и выгрузка документов.
