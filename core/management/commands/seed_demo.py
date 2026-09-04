"""
Команда наполнения базы данных демонстрационными данными предметной области
«Подбор персонала в ООО ЮНИТКОД».

Запуск:  python manage.py seed_demo            — добавить данные (если их нет)
         python manage.py seed_demo --flush    — очистить прикладные таблицы и создать заново

Создаёт реалистичные данные: отделы, источники, навыки, этапы воронки,
кандидатов, вакансии (часть — закрытые, для метрики time-to-hire), отклики,
собеседования, офферы, новости и обращения. На каждую сущность приходится не
менее десяти записей, что обеспечивает содержательность HR-аналитики.
"""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from core.models import (Application, ApplicationStatus, Article, Candidate,
                         CandidateSkill, Department, Evaluation, Feedback,
                         Grade, IndustryBenchmark, Interview, InterviewResult,
                         InterviewType, Offer, OfferStatus, Role, Skill, Source,
                         Stage, User, Vacancy, VacancySkill, VacancyStatus)

# Транслитерация slug кириллицы для адресов новостей.
def ru_slug(text, idx):
    base = slugify(text, allow_unicode=False)
    return base or f"news-{idx}"


LAST_NAMES = ["Иванов", "Петров", "Смирнов", "Кузнецов", "Соколов", "Попов",
              "Лебедев", "Козлов", "Новиков", "Морозов", "Волков", "Алексеев",
              "Фёдоров", "Михайлов", "Беляев", "Тарасов", "Белов", "Комаров",
              "Орлов", "Киселёв", "Макаров", "Андреев", "Ковалёв", "Ильин"]
FIRST_M = ["Александр", "Дмитрий", "Максим", "Сергей", "Андрей", "Алексей",
           "Артём", "Илья", "Кирилл", "Никита", "Михаил", "Роман"]
FIRST_F = ["Анна", "Мария", "Елена", "Ольга", "Наталья", "Екатерина", "Юлия",
           "Татьяна", "Ирина", "Светлана", "Дарья", "Полина"]
PATR_M = ["Александрович", "Дмитриевич", "Сергеевич", "Андреевич", "Игоревич",
          "Михайлович", "Олегович", "Викторович"]
PATR_F = ["Александровна", "Дмитриевна", "Сергеевна", "Андреевна", "Игоревна",
          "Михайловна", "Олеговна", "Викторовна"]
CITIES = ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань",
          "Нижний Новгород", "Самара", "Воронеж", "Краснодар", "Пермь"]

VACANCY_TITLES = [
    ("Python-разработчик", "Отдел разработки", Grade.MIDDLE),
    ("Frontend-разработчик (React)", "Отдел разработки", Grade.MIDDLE),
    ("Бизнес-аналитик", "Отдел аналитики", Grade.MIDDLE),
    ("Системный аналитик", "Отдел аналитики", Grade.SENIOR),
    ("DevOps-инженер", "Отдел эксплуатации", Grade.SENIOR),
    ("QA-инженер (автоматизация)", "Отдел тестирования", Grade.MIDDLE),
    ("Data Scientist", "Отдел данных", Grade.SENIOR),
    ("Менеджер проектов", "Отдел проектного управления", Grade.SENIOR),
    ("UX/UI-дизайнер", "Отдел разработки", Grade.MIDDLE),
    ("Технический писатель", "Отдел аналитики", Grade.JUNIOR),
    ("Backend-разработчик (Go)", "Отдел разработки", Grade.SENIOR),
    ("Младший Python-разработчик", "Отдел разработки", Grade.JUNIOR),
    ("Инженер по данным (ETL)", "Отдел данных", Grade.MIDDLE),
    ("HR-бизнес-партнёр", "Отдел персонала", Grade.MIDDLE),
]

SKILLS = [
    ("Python", "lang"), ("JavaScript", "lang"), ("TypeScript", "lang"),
    ("Go", "lang"), ("SQL", "db"), ("PostgreSQL", "db"), ("Django", "framework"),
    ("React", "framework"), ("FastAPI", "framework"), ("Docker", "tool"),
    ("Kubernetes", "tool"), ("Git", "tool"), ("Linux", "tool"),
    ("CI/CD", "tool"), ("Pandas", "framework"), ("Machine Learning", "tool"),
    ("REST API", "tool"), ("Коммуникabельность", "soft"),
    ("Аналитическое мышление", "soft"), ("Английский язык", "soft"),
]

SOURCES = [
    ("hh.ru", "джоб-борд", 1200), ("Хабр Карьера", "джоб-борд", 900),
    ("Telegram-каналы", "соцсеть", 300), ("Реферальная программа", "реферал", 500),
    ("Карьерный сайт", "собственный сайт", 0), ("LinkedIn", "соцсеть", 1500),
    ("getmatch", "джоб-борд", 2000), ("Хантинг", "прямой поиск", 4000),
]

STAGES = [
    ("Скрининг резюме", 1, False),
    ("HR-интервью", 2, False),
    ("Техническое собеседование", 3, False),
    ("Финальное собеседование", 4, False),
    ("Оффер", 5, False),
    ("Принят в команду", 6, True),
]

ARTICLES = [
    ("ЮНИТКОД запускает платформу UnitHire для автоматизации найма",
     "Компания внедрила собственную рекрутинговую систему с HR-аналитикой."),
    ("Как мы сократили время закрытия вакансий на 35%",
     "Опыт перехода от Excel-таблиц к сквозной воронке подбора."),
    ("5 метрик рекрутинга, которые стоит отслеживать",
     "Разбираем time-to-hire, cost-per-hire, конверсию воронки и не только."),
    ("Источники кандидатов: где мы находим лучших разработчиков",
     "Сравнение эффективности джоб-бордов, рефералов и прямого поиска."),
    ("Что такое cost-per-hire и как его снижать",
     "Считаем стоимость найма и оптимизируем бюджет подбора."),
    ("Структурированное интервью: чек-лист для рекрутёра",
     "Делимся шаблоном оценки кандидатов по критериям."),
    ("HR-аналитика на службе бизнеса",
     "Как данные о подборе помогают принимать управленческие решения."),
    ("Онбординг в ЮНИТКОД: первые 90 дней",
     "Рассказываем, как устроена адаптация новых сотрудников."),
    ("Реферальная программа: сотрудники рекомендуют коллег",
     "Почему рекомендации дают самых лояльных кандидатов."),
    ("Открытые вакансии месяца",
     "Подборка актуальных позиций в командах разработки и аналитики."),
    ("Как устроена воронка подбора в UnitHire",
     "Подробно о шести этапах от скрининга до выхода на работу."),
    ("Карьерный трек разработчика в ЮНИТКОД",
     "От стажёра до техлида: грейды и ожидания."),
]


class Command(BaseCommand):
    help = "Наполнить базу данных демонстрационными данными предметной области"

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true",
                            help="Очистить прикладные таблицы перед наполнением")

    def handle(self, *args, **options):
        rnd = random.Random(2026)  # фиксированное зерно — воспроизводимые данные

        if options["flush"]:
            self.stdout.write("Очищаю прикладные таблицы…")
            for model in [Evaluation, Interview, Offer, Application, CandidateSkill,
                          VacancySkill, Vacancy, Candidate, Article, Feedback,
                          Stage, Skill, Source, Department]:
                model.objects.all().delete()
            User.objects.exclude(is_superuser=True).delete()

        # --- Пользователи и роли (3 уровня доступа) ---------------------
        admin = self._make_user(
            "admin", "Серебренников", "Дмитрий", "Валерьевич", Role.ADMIN,
            "Admin#Unitcode2026", is_staff=True, is_superuser=True,
            email="admin@unitcode.ru", position="Системный администратор")

        recruiter = self._make_user(
            "recruiter", "Соколова", "Анна", "Игоревна", Role.RECRUITER,
            "Hr#Unitcode2026", is_staff=False, email="recruiter@unitcode.ru",
            position="Ведущий HR-менеджер")

        # Дополнительные рекрутёры — для отчёта «загрузка рекрутёров».
        recruiters = [recruiter]
        for i, (ln, fn, pt) in enumerate([
                ("Морозова", "Елена", "Сергеевна"),
                ("Лебедев", "Артём", "Олегович"),
                ("Киселёва", "Ольга", "Дмитриевна")], start=1):
            recruiters.append(self._make_user(
                f"recruiter{i}", ln, fn, pt, Role.RECRUITER, "Hr#Unitcode2026",
                email=f"recruiter{i}@unitcode.ru", position="HR-менеджер"))

        candidate_user = self._make_user(
            "candidate", "Новиков", "Максим", "Андреевич", Role.CANDIDATE,
            "User#Unitcode2026", email="candidate@example.com")

        # --- Справочники -------------------------------------------------
        departments = {}
        dep_heads = ["Громов А. С.", "Зайцева М. П.", "Фролов И. В.",
                     "Сорокина Е. А.", "Власов Д. Н.", "Гусева Н. И."]
        dep_names = ["Отдел разработки", "Отдел аналитики", "Отдел эксплуатации",
                     "Отдел тестирования", "Отдел данных",
                     "Отдел проектного управления", "Отдел персонала"]
        for i, name in enumerate(dep_names):
            departments[name] = Department.objects.create(
                name=name, head=dep_heads[i % len(dep_heads)],
                headcount_plan=rnd.randint(8, 30),
                description=f"Подразделение «{name}» компании ООО «ЮНИТКОД».")

        sources = []
        for name, kind, cost in SOURCES:
            sources.append(Source.objects.create(
                name=name, kind=kind, cost_per_contact=cost))

        skills = []
        for name, cat in SKILLS:
            skills.append(Skill.objects.create(
                name=name, category=cat,
                description=f"Навык: {name}"))

        stages = []
        for name, order, terminal in STAGES:
            stages.append(Stage.objects.create(
                name=name, order=order, is_terminal=terminal,
                description=f"Этап воронки подбора: {name}."))

        recruiter.department = departments["Отдел персонала"]
        recruiter.save()

        # --- Кандидаты (≥10) --------------------------------------------
        candidates = []
        for i in range(24):
            female = rnd.random() < 0.4
            ln = rnd.choice(LAST_NAMES)
            if female:
                ln = ln + "а" if not ln.endswith(("ий", "ой", "ин", "ёв", "ов", "ев")) else ln + "а"
                fn = rnd.choice(FIRST_F)
                pt = rnd.choice(PATR_F)
            else:
                fn = rnd.choice(FIRST_M)
                pt = rnd.choice(PATR_M)
            grade = rnd.choice([Grade.JUNIOR, Grade.MIDDLE, Grade.SENIOR,
                                Grade.INTERN, Grade.MIDDLE, Grade.SENIOR])
            exp = {Grade.INTERN: 0.5, Grade.JUNIOR: 1.5, Grade.MIDDLE: 3.5,
                   Grade.SENIOR: 6.0, Grade.LEAD: 9.0}[grade] + rnd.uniform(-0.5, 1.5)
            created = timezone.now() - timedelta(days=rnd.randint(2, 50))
            c = Candidate.objects.create(
                user=candidate_user if i == 0 else None,
                last_name=ln, first_name=fn, patronymic=pt,
                email=f"candidate{i+1}@example.com",
                phone=f"+7 9{rnd.randint(10,99)} {rnd.randint(100,999)}-"
                      f"{rnd.randint(10,99)}-{rnd.randint(10,99)}",
                city=rnd.choice(CITIES),
                desired_salary=rnd.choice([80, 120, 150, 180, 220, 260, 300]) * 1000,
                experience_years=round(max(0, exp), 1),
                grade=grade, source=rnd.choice(sources),
                summary=f"Специалист уровня {grade}. Опыт коммерческой разработки "
                        f"и работы в команде.",
                created_at=created)
            # Навыки кандидата (3–6 штук).
            for sk in rnd.sample(skills, rnd.randint(3, 6)):
                CandidateSkill.objects.get_or_create(
                    candidate=c, skill=sk,
                    defaults={"level": rnd.randint(1, 4)})
            candidates.append(c)

        # --- Вакансии (≥10, часть закрыта) ------------------------------
        vacancies = []
        for i, (title, dep_name, grade) in enumerate(VACANCY_TITLES):
            opened = timezone.localdate() - timedelta(days=rnd.randint(15, 55))
            closed = None
            status = rnd.choice([VacancyStatus.OPEN, VacancyStatus.IN_PROGRESS,
                                 VacancyStatus.OPEN, VacancyStatus.CLOSED,
                                 VacancyStatus.IN_PROGRESS, VacancyStatus.ON_HOLD])
            if status == VacancyStatus.CLOSED:
                closed = opened + timedelta(days=rnd.randint(12, 40))
            smin = rnd.choice([80, 120, 150, 180]) * 1000
            smax = smin + rnd.choice([40, 60, 80, 100]) * 1000
            v = Vacancy.objects.create(
                title=title, department=departments[dep_name], grade=grade,
                salary_min=smin, salary_max=smax, status=status,
                recruiter=rnd.choice(recruiters),
                city=rnd.choice(CITIES), is_remote=rnd.random() < 0.5,
                opened_at=opened, closed_at=closed,
                planned_close=opened + timedelta(days=30),
                description=f"Мы ищем специалиста на позицию «{title}» в "
                            f"{dep_name.lower()}. Требуется опыт коммерческой "
                            f"разработки, умение работать в команде и желание "
                            f"профессионально расти.")
            for sk in rnd.sample(skills, rnd.randint(3, 6)):
                VacancySkill.objects.get_or_create(
                    vacancy=v, skill=sk,
                    defaults={"is_required": rnd.random() < 0.7})
            vacancies.append(v)

        # --- Отклики, собеседования, офферы -----------------------------
        status_by_stage = {
            1: ApplicationStatus.IN_REVIEW, 2: ApplicationStatus.IN_REVIEW,
            3: ApplicationStatus.INTERVIEW, 4: ApplicationStatus.INTERVIEW,
            5: ApplicationStatus.OFFER, 6: ApplicationStatus.HIRED,
        }
        pairs = set()
        for _ in range(70):
            c = rnd.choice(candidates)
            v = rnd.choice(vacancies)
            if (c.id, v.id) in pairs:
                continue
            pairs.add((c.id, v.id))
            stage = rnd.choices(stages, weights=[30, 22, 18, 12, 8, 10])[0]
            status = status_by_stage[stage.order]
            if rnd.random() < 0.18:
                status = ApplicationStatus.REJECTED
            applied = timezone.now() - timedelta(days=rnd.randint(1, 45),
                                                 hours=rnd.randint(0, 23))
            app = Application.objects.create(
                candidate=c, vacancy=v, stage=stage, status=status,
                score=rnd.randint(40, 98),
                cover_letter="Заинтересован в данной позиции, готов обсудить детали.",
                comment="" if rnd.random() < 0.5 else "Перспективный кандидат.",
                applied_at=applied)
            # Собеседования для продвинутых этапов.
            if stage.order >= 3 and status != ApplicationStatus.REJECTED:
                for kind in [InterviewType.HR, InterviewType.TECH]:
                    if kind == InterviewType.TECH and stage.order < 3:
                        continue
                    res = rnd.choice([InterviewResult.PASSED, InterviewResult.PASSED,
                                      InterviewResult.SCHEDULED, InterviewResult.FAILED])
                    iv = Interview.objects.create(
                        application=app, kind=kind,
                        scheduled_at=applied + timedelta(days=rnd.randint(2, 10)),
                        interviewer=v.recruiter, result=res,
                        score=rnd.randint(5, 10),
                        notes="Соответствует требованиям позиции."
                        if res == InterviewResult.PASSED else "Есть замечания.")
                    for crit in ["Технические навыки", "Коммуникация", "Мотивация"]:
                        Evaluation.objects.create(
                            interview=iv, criterion=crit,
                            score=rnd.randint(5, 10),
                            comment="")
            # Офферы для финальных этапов.
            if stage.order >= 5 and status in (ApplicationStatus.OFFER,
                                               ApplicationStatus.HIRED):
                Offer.objects.create(
                    application=app,
                    salary=rnd.randint(v.salary_min // 1000, v.salary_max // 1000) * 1000,
                    start_date=timezone.localdate() + timedelta(days=rnd.randint(7, 30)),
                    status=OfferStatus.ACCEPTED if status == ApplicationStatus.HIRED
                    else OfferStatus.SENT,
                    sent_at=timezone.localdate() - timedelta(days=rnd.randint(1, 15)))

        # --- Новости/блог (≥10) -----------------------------------------
        for i, (title, summary) in enumerate(ARTICLES):
            pub = timezone.localdate() - timedelta(days=rnd.randint(1, 60))
            Article.objects.create(
                title=title, slug=ru_slug(title, i) + f"-{i+1}",
                summary=summary,
                body=(summary + "\n\n") + " ".join([
                    "Команда ООО «ЮНИТКОД» развивает собственные инструменты "
                    "автоматизации подбора персонала.",
                    "Платформа UnitHire объединяет управление вакансиями, "
                    "кандидатами и аналитику в едином окне.",
                    "Это позволяет сократить рутину рекрутёров и принимать "
                    "решения на основе данных."] * 3),
                author_name="Пресс-служба ЮНИТКОД",
                published_at=pub, is_published=True)

        # --- Обращения (обратная связь, ≥10) ----------------------------
        subjects = ["Вопрос по вакансии", "Сотрудничество", "Партнёрство",
                    "Технический вопрос", "Предложение", "Отклик на позицию",
                    "Консультация", "Запрос на демонстрацию", "Обратная связь",
                    "Стажировка", "Вопрос по резюме", "Прочее"]
        for i in range(14):
            Feedback.objects.create(
                name=f"{rnd.choice(FIRST_M)} {rnd.choice(LAST_NAMES)}",
                email=f"user{i+1}@example.com",
                phone=f"+7 9{rnd.randint(10,99)} {rnd.randint(100,999)}-00-00",
                subject=rnd.choice(subjects),
                message="Здравствуйте! Прошу предоставить дополнительную "
                        "информацию по интересующему вопросу. Заранее благодарю.",
                is_processed=rnd.random() < 0.4,
                created_at=timezone.now() - timedelta(days=rnd.randint(0, 25)))

        # Эталонные значения отраслевых HR-метрик для дашборда (замечание 11).
        benchmarks = [
            # Единственный показатель, по которому есть публикуемая
            # отраслевая статистика. Остальные значения - целевые
            # ориентиры организации, что и указано в поле источника:
            # выдавать их за среднеотраслевые данные некорректно.
            dict(metric="time_to_hire", industry="ИТ в России", value=44.5,
                 unit="дней",
                 source="Поток Рекрутмент, отчёт о скорости закрытия "
                        "вакансий за 2025 год", year=2025),
            dict(metric="cost_per_hire", industry="ООО «ЮНИТКОД»",
                 value=85000, unit="р.",
                 source="Целевое значение организации, экспертная оценка",
                 year=2026),
            dict(metric="conversion", industry="ООО «ЮНИТКОД»", value=8.5,
                 unit="%",
                 source="Целевое значение организации, экспертная оценка",
                 year=2026),
            dict(metric="offer_acceptance", industry="ООО «ЮНИТКОД»",
                 value=75.0, unit="%",
                 source="Целевое значение организации, экспертная оценка",
                 year=2026),
        ]
        for b in benchmarks:
            IndustryBenchmark.objects.update_or_create(
                metric=b["metric"], industry=b["industry"], year=b["year"],
                defaults=b,
            )

        self.stdout.write(self.style.SUCCESS(
            "Демо-данные загружены: "
            f"пользователей={User.objects.count()}, "
            f"кандидатов={Candidate.objects.count()}, "
            f"вакансий={Vacancy.objects.count()}, "
            f"откликов={Application.objects.count()}, "
            f"собеседований={Interview.objects.count()}, "
            f"офферов={Offer.objects.count()}, "
            f"новостей={Article.objects.count()}, "
            f"обращений={Feedback.objects.count()}, "
            f"бенчмарков={IndustryBenchmark.objects.count()}."))

    def _make_user(self, username, last, first, patr, role, password,
                   is_staff=False, is_superuser=False, email="", position=""):
        """Создать/обновить пользователя с заданной ролью и паролем."""
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={"last_name": last, "first_name": first,
                      "patronymic": patr, "role": role, "email": email,
                      "position": position})
        user.last_name, user.first_name, user.patronymic = last, first, patr
        user.role, user.email, user.position = role, email, position
        # Администратор и рекрутёр получают доступ к Django-admin.
        user.is_staff = is_staff or role in (Role.ADMIN,)
        user.is_superuser = is_superuser
        user.set_password(password)
        user.save()
        return user
