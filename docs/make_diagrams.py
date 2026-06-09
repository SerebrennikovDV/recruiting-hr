# -*- coding: utf-8 -*-
"""
Генератор диаграмм для отчёта по преддипломной практике.

Все схемы строятся программно средствами matplotlib (в окружении недоступен
бинарный graphviz), сохраняются как PNG в каталог docs/. Шрифт DejaVu Sans
корректно отображает кириллицу.

Состав:
    as_is.png        — модель AS-IS (DFD, нотация Гейна—Сарсона);
    to_be.png        — модель TO-BE (DFD, та же нотация);
    func_tree.png    — дерево функций ПО;
    components.png   — диаграмма компонентов (UML);
    er_info.png      — инфологическая ER-диаграмма (без атрибутов);
    er_logic.png     — логическая (уточнённая) ER-диаграмма;
    db_schema.png    — схема данных (реляционная, связи 1:M и M:M);
    user_flow.png    — User Flow Diagram;
    gantt.png        — диаграмма Ганта плана разработки;
    wireframe.png    — прототип интерфейса (wireframe);
    mockup.png       — макет страницы веб-сервиса.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Circle

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["font.size"] = 9

OUT = os.path.dirname(os.path.abspath(__file__))

C_PRIMARY = "#2563eb"
C_LIGHT = "#dbeafe"
C_GREEN = "#16a34a"
C_GREENL = "#dcfce7"
C_GRAY = "#e2e8f0"
C_ORANGE = "#f59e0b"
C_ORANGEL = "#fef3c7"


# ---------------------------------------------------------------------------
#  Базовые примитивы рисования
# ---------------------------------------------------------------------------
def _ax(w=12, h=8):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, fc=C_LIGHT, ec=C_PRIMARY, rounded=True,
        fontsize=9, bold=False, text_color="#0f172a"):
    """Прямоугольник со скруглением и подписью по центру."""
    style = "round,pad=0.02,rounding_size=2" if rounded else "square,pad=0.02"
    p = FancyBboxPatch((x, y), w, h, boxstyle=style, fc=fc, ec=ec, lw=1.4)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, color=text_color,
            fontweight="bold" if bold else "normal", wrap=True)
    return (x + w / 2, y + h / 2)


def ext_entity(ax, x, y, w, h, text):
    """Внешняя сущность DFD — прямоугольник (квадратные углы)."""
    return box(ax, x, y, w, h, text, fc="#fde68a", ec="#b45309",
               rounded=False, bold=True)


def process(ax, x, y, w, h, text):
    """Процесс DFD (Гейн—Сарсон) — скруглённый прямоугольник."""
    return box(ax, x, y, w, h, text, fc=C_LIGHT, ec=C_PRIMARY, bold=False)


def datastore(ax, x, y, w, h, text):
    """Хранилище данных DFD — открытый прямоугольник."""
    ax.add_patch(Rectangle((x, y), w, h, fc="#f1f5f9", ec="#475569", lw=1.4))
    ax.plot([x, x + w], [y + h, y + h], color="#475569", lw=1.4)
    ax.plot([x, x + w], [y, y], color="#475569", lw=1.4)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8.5)
    return (x + w / 2, y + h / 2)


def arrow(ax, p1, p2, text="", color="#334155", rad=0.0, fs=8, ls="-"):
    """Стрелка между двумя точками с необязательной подписью."""
    a = FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=14,
                        color=color, lw=1.3, ls=ls,
                        connectionstyle=f"arc3,rad={rad}")
    ax.add_patch(a)
    if text:
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        ax.text(mx, my + 1.5, text, ha="center", va="center", fontsize=fs,
                color="#1e293b",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none",
                          alpha=0.85))


def title(ax, text):
    ax.text(50, 97, text, ha="center", va="top", fontsize=13, fontweight="bold",
            color="#0f172a")


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=130, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", name)


# ---------------------------------------------------------------------------
#  1. AS-IS (DFD Гейна—Сарсона)
# ---------------------------------------------------------------------------
def diagram_as_is():
    fig, ax = _ax(12, 8)
    title(ax, "Модель AS-IS: подбор персонала «как есть» (DFD, нотация Гейна—Сарсона)")
    rук = ext_entity(ax, 4, 78, 20, 9, "Нанимающий\nруководитель")
    cand = ext_entity(ax, 76, 12, 20, 9, "Кандидат")

    p1 = process(ax, 40, 78, 22, 10, "1. Приём заявки\nна подбор")
    p2 = process(ax, 40, 56, 22, 10, "2. Поиск и скрининг\nкандидатов")
    p3 = process(ax, 40, 34, 22, 10, "3. Организация\nсобеседований")
    p4 = process(ax, 40, 12, 22, 10, "4. Принятие\nрешения о найме")

    ds1 = datastore(ax, 6, 56, 22, 8, "Excel-таблица\n«Кандидаты»")
    ds2 = datastore(ax, 6, 34, 22, 8, "Электронная\nпочта / мессенджеры")

    arrow(ax, rук, p1, "заявка")
    arrow(ax, p1, p2, "")
    arrow(ax, p2, p3, "")
    arrow(ax, p3, p4, "")
    arrow(ax, p2, ds1, "запись вручную", rad=0.1)
    arrow(ax, ds1, p2, "", rad=-0.25)
    arrow(ax, p2, ds2, "переписка", rad=-0.1)
    arrow(ax, cand, p2, "резюме", rad=0.15)
    arrow(ax, p3, cand, "приглашение", rad=-0.2)
    arrow(ax, p4, rук, "согласование", rad=-0.25)

    ax.text(50, 4, "Недостатки: ручной перенос данных, отсутствие единой базы, "
                   "нет аналитики и контроля сроков, потеря информации в переписке.",
            ha="center", fontsize=8.5, style="italic", color="#b91c1c")
    save(fig, "as_is.png")


# ---------------------------------------------------------------------------
#  2. TO-BE (DFD Гейна—Сарсона)
# ---------------------------------------------------------------------------
def diagram_to_be():
    fig, ax = _ax(12, 8)
    title(ax, "Модель TO-BE: подбор персонала с веб-сервисом UnitHire (DFD)")
    cand = ext_entity(ax, 4, 70, 18, 9, "Кандидат\n(личный кабинет)")
    rec = ext_entity(ax, 4, 30, 18, 9, "Рекрутёр\n(кабинет)")
    head = ext_entity(ax, 4, 8, 18, 9, "Руководитель\n(аналитика)")

    p1 = process(ax, 34, 72, 22, 9, "1. Управление\nвакансиями")
    p2 = process(ax, 34, 54, 22, 9, "2. Приём откликов\nи скрининг")
    p3 = process(ax, 34, 36, 22, 9, "3. Воронка и\nсобеседования")
    p4 = process(ax, 34, 18, 22, 9, "4. Офферы и\nнайм")
    p5 = process(ax, 34, 2, 22, 9, "5. HR-аналитика\nи отчёты")

    db = datastore(ax, 70, 36, 24, 26, "База данных\nUnitHire\n(PostgreSQL,\n16 таблиц)")
    docs = datastore(ax, 70, 12, 24, 9, "Документы\n.docx / .xlsx")

    arrow(ax, cand, p2, "отклик")
    arrow(ax, rec, p1, "")
    arrow(ax, rec, p3, "")
    arrow(ax, head, p5, "запрос")
    for p in [p1, p2, p3, p4, p5]:
        arrow(ax, p, db, "", rad=0.05, color="#2563eb")
    arrow(ax, db, p5, "", rad=0.2, color="#2563eb")
    arrow(ax, p5, docs, "выгрузка")
    arrow(ax, p5, head, "дашборды", rad=-0.2)
    arrow(ax, p3, cand, "статусы", rad=0.25)

    ax.text(50, -2, "Преимущества: единая база, автоматическая воронка и метрики, "
                    "разграничение прав, выгрузка отчётов, прозрачность сроков найма.",
            ha="center", fontsize=8.5, style="italic", color=C_GREEN)
    save(fig, "to_be.png")


# ---------------------------------------------------------------------------
#  3. Дерево функций
# ---------------------------------------------------------------------------
def diagram_func_tree():
    fig, ax = _ax(13, 8)
    title(ax, "Дерево функций веб-сервиса UnitHire")
    root = box(ax, 38, 86, 24, 8, "UnitHire —\nрекрутинговая ИС", fc=C_PRIMARY,
               ec="#1e3a8a", bold=True, text_color="white")
    groups = [
        (3, "Публичная\nчасть", ["Просмотр вакансий", "Поиск и фильтры",
                                 "Новости / блог", "Аналитика-демо",
                                 "Обратная связь"]),
        (28, "Кабинет\nрекрутёра", ["Вакансии (CRUD)", "Кандидаты (CRUD)",
                                    "Канбан откликов", "Собеседования",
                                    "HR-аналитика", "Выгрузка docx/xlsx"]),
        (53, "Кабинет\nкандидата", ["Профиль", "Загрузка резюме",
                                    "Отклики", "Собеседования"]),
        (78, "Админи-\nстрирование", ["Пользователи и роли", "Справочники",
                                      "Массовые действия", "Контент"]),
    ]
    for gx, gname, leaves in groups:
        g = box(ax, gx, 64, 19, 9, gname, fc=C_LIGHT, ec=C_PRIMARY, bold=True)
        arrow(ax, (50, 86), (gx + 9.5, 73), color="#94a3b8")
        for i, leaf in enumerate(leaves):
            ly = 56 - i * 9
            box(ax, gx, ly, 19, 7, leaf, fc="white", ec="#64748b", fontsize=7.5)
            arrow(ax, (gx + 9.5, 64 if i == 0 else 56 - (i - 1) * 9),
                  (gx + 9.5, ly + 7), color="#cbd5e1")
    save(fig, "func_tree.png")


# ---------------------------------------------------------------------------
#  4. Диаграмма компонентов (UML)
# ---------------------------------------------------------------------------
def diagram_components():
    fig, ax = _ax(11, 8)
    title(ax, "Диаграмма компонентов веб-сервиса (UML)")

    def comp(x, y, w, h, text, fc=C_LIGHT):
        box(ax, x, y, w, h, text, fc=fc, ec=C_PRIMARY, bold=True)
        ax.add_patch(Rectangle((x - 2, y + h - 6), 4, 2.4, fc=fc, ec=C_PRIMARY))
        ax.add_patch(Rectangle((x - 2, y + h - 11), 4, 2.4, fc=fc, ec=C_PRIMARY))
        return (x + w / 2, y + h / 2)

    browser = box(ax, 38, 84, 24, 8, "Браузер пользователя\n(Chrome/Firefox/Edge/Яндекс)",
                  fc="#fde68a", ec="#b45309", bold=True)
    wn = comp(34, 66, 32, 9, "WhiteNoise + Gunicorn\n(статика, WSGI-сервер)")
    urls = comp(8, 50, 24, 9, "URL-маршрутизация\n(urls.py)")
    views = comp(38, 50, 24, 9, "Представления\n(views.py)")
    tmpl = comp(68, 50, 24, 9, "Шаблоны\n(templates, Bootstrap)")
    forms = comp(8, 33, 24, 9, "Формы и валидация\n(forms.py)")
    logic = comp(38, 33, 24, 9, "Бизнес-логика\n(analytics, documents)")
    auth = comp(68, 33, 24, 9, "Аутентификация\nи роли (decorators)")
    models = comp(30, 17, 40, 9, "Модели данных (ORM)\nmodels.py — 16 сущностей")
    db = datastore(ax, 36, 2, 28, 9, "СУБД PostgreSQL")

    arrow(ax, browser, wn, "HTTP/HTTPS")
    arrow(ax, wn, (50, 59))
    arrow(ax, (20, 59), views, "")
    arrow(ax, views, tmpl, "render")
    arrow(ax, views, forms, "", rad=0.1)
    arrow(ax, views, logic, "")
    arrow(ax, views, auth, "", rad=-0.1)
    arrow(ax, logic, models, "")
    arrow(ax, forms, models, "", rad=0.1)
    arrow(ax, models, db, "SQL")
    save(fig, "components.png")


# ---------------------------------------------------------------------------
#  5. ER инфологическая (без атрибутов)
# ---------------------------------------------------------------------------
def diagram_er_info():
    fig, ax = _ax(13, 8.5)
    title(ax, "Инфологическая модель данных (ER-диаграмма)")
    ent = {
        "Пользователь": (6, 80), "Отдел": (6, 55), "Источник": (6, 30),
        "Вакансия": (40, 80), "Кандидат": (40, 30),
        "Отклик": (40, 55),
        "Навык": (74, 80), "Собеседование": (74, 55), "Оффер": (74, 30),
        "Этап воронки": (40, 6), "Оценка": (74, 6), "Резюме": (6, 6),
    }
    pts = {}
    for name, (x, y) in ent.items():
        fc = C_GREENL if name in ("Отдел", "Источник", "Навык", "Этап воронки") else C_LIGHT
        pts[name] = box(ax, x, y, 20, 9, name, fc=fc, ec=C_PRIMARY, bold=True)
    rels = [
        ("Вакансия", "Отдел", "1:М"), ("Вакансия", "Пользователь", "М:1"),
        ("Кандидат", "Источник", "М:1"), ("Отклик", "Кандидат", "М:1"),
        ("Отклик", "Вакансия", "М:1"), ("Отклик", "Этап воронки", "М:1"),
        ("Собеседование", "Отклик", "М:1"), ("Оффер", "Отклик", "1:1"),
        ("Оценка", "Собеседование", "М:1"), ("Резюме", "Кандидат", "М:1"),
        ("Кандидат", "Навык", "М:М"), ("Вакансия", "Навык", "М:М"),
    ]
    for a, b, card in rels:
        ls = "--" if card == "М:М" else "-"
        col = C_ORANGE if card == "М:М" else "#64748b"
        arrow(ax, pts[a], pts[b], card, color=col, ls=ls, fs=7)
    ax.text(50, 1, "Сплошные линии — связи 1:М/1:1; пунктир (оранжевый) — связи М:М "
                   "(реализуются ассоциативными таблицами).",
            ha="center", fontsize=8, style="italic", color="#475569")
    save(fig, "er_info.png")


# ---------------------------------------------------------------------------
#  6. ER логическая (с атрибутами)
# ---------------------------------------------------------------------------
def diagram_er_logic():
    fig, ax = _ax(13, 8.5)
    title(ax, "Логическая модель данных (уточнённая ER-диаграмма с атрибутами)")

    def entity(x, y, name, attrs, fc=C_LIGHT):
        h = 6 + len(attrs) * 4.0
        ax.add_patch(FancyBboxPatch((x, y - h), 26, h,
                     boxstyle="round,pad=0.1,rounding_size=1.5",
                     fc="white", ec=C_PRIMARY, lw=1.4))
        ax.add_patch(FancyBboxPatch((x, y - 5.5), 26, 5.5,
                     boxstyle="round,pad=0.1,rounding_size=1.5",
                     fc=fc, ec=C_PRIMARY, lw=1.4))
        ax.text(x + 13, y - 2.7, name, ha="center", va="center", fontweight="bold",
                fontsize=9)
        for i, a in enumerate(attrs):
            ax.text(x + 1.5, y - 8.5 - i * 4, a, ha="left", va="center", fontsize=7.3)
        return (x + 13, y - h / 2)

    cand = entity(4, 92, "Кандидат (candidates)",
                  ["PK id", "ФИО, email, телефон", "город, грейд",
                   "опыт (лет), желаемая ЗП", "FK источник", "дата создания"],
                  fc=C_LIGHT)
    vac = entity(70, 92, "Вакансия (vacancies)",
                 ["PK id", "название, грейд", "FK отдел, FK рекрутёр",
                  "зарплата (мин/макс)", "статус, город", "даты открытия/закрытия"],
                 fc=C_LIGHT)
    app = entity(37, 60, "Отклик (applications)",
                 ["PK id", "FK кандидат", "FK вакансия", "FK этап",
                  "статус, оценка", "комментарий, дата"],
                 fc=C_GREENL)
    intv = entity(4, 36, "Собеседование (interviews)",
                  ["PK id", "FK отклик", "тип, дата/время",
                   "FK интервьюер", "результат, балл"],
                  fc=C_LIGHT)
    offer = entity(70, 36, "Оффер (offers)",
                   ["PK id", "FK отклик (1:1)", "зарплата",
                    "дата выхода, статус"],
                   fc=C_LIGHT)
    arrow(ax, (cand[0], 70), (app[0] - 6, 60), "1:М", color="#64748b")
    arrow(ax, (vac[0], 70), (app[0] + 6, 60), "1:М", color="#64748b")
    arrow(ax, (app[0] - 6, 40), intv, "1:М", color="#64748b", rad=0.1)
    arrow(ax, (app[0] + 6, 40), offer, "1:1", color="#64748b", rad=-0.1)
    save(fig, "er_logic.png")


# ---------------------------------------------------------------------------
#  7. Схема данных (реляционная)
# ---------------------------------------------------------------------------
def diagram_db_schema():
    fig, ax = _ax(14, 9)
    ax.text(50, 99, "Схема данных (реляционная модель, 16 таблиц, связи 1:M и M:M)",
            ha="center", va="top", fontsize=12, fontweight="bold", color="#0f172a")

    COLS = [2.5, 26.5, 50.5, 74.5]   # X левых границ четырёх колонок
    ROWS = [92, 70, 47, 24]          # Y верхних границ четырёх рядов
    W = 22

    def table(col, row, name, fields):
        x, y = COLS[col], ROWS[row]
        h = 4.5 + len(fields) * 3.1
        ax.add_patch(Rectangle((x, y - h), W, h, fc="white", ec="#334155", lw=1.2))
        ax.add_patch(Rectangle((x, y - 4.2), W, 4.2, fc=C_PRIMARY, ec="#334155"))
        ax.text(x + W / 2, y - 2.1, name, ha="center", va="center", color="white",
                fontweight="bold", fontsize=8)
        for i, f in enumerate(fields):
            ax.text(x + 1, y - 6.4 - i * 3.1, f, ha="left", va="center", fontsize=6.6)
        return {"top": (x + W / 2, y), "bot": (x + W / 2, y - h),
                "left": (x, y - h / 2), "right": (x + W, y - h / 2),
                "x": x, "y": y, "h": h}

    # Ряд 1 — основные сущности
    users = table(0, 0, "users", ["PK id", "username, ФИО", "role", "FK department"])
    vac = table(1, 0, "vacancies", ["PK id", "title, grade", "FK department",
                                    "FK recruiter", "salary, status"])
    cand = table(2, 0, "candidates", ["PK id", "ФИО, email", "grade, FK source",
                                      "desired_salary"])
    app = table(3, 0, "applications", ["PK id", "FK candidate", "FK vacancy",
                                       "FK stage", "status, score"])
    # Ряд 2 — справочники
    dep = table(0, 1, "departments", ["PK id", "name", "head"])
    src = table(1, 1, "sources", ["PK id", "name", "cost_per_contact"])
    skill = table(2, 1, "skills", ["PK id", "name", "category"])
    stage = table(3, 1, "stages", ["PK id", "name", "order"])
    # Ряд 3 — зависимые сущности
    intv = table(0, 2, "interviews", ["PK id", "FK application", "kind, result",
                                      "FK interviewer"])
    offer = table(1, 2, "offers", ["PK id", "FK application", "salary, status"])
    evalt = table(2, 2, "evaluations", ["PK id", "FK interview", "criterion, score"])
    resume = table(3, 2, "resume_files", ["PK id", "FK candidate", "file"])
    # Ряд 4 — ассоциативные (M:M) и контент
    cs = table(0, 3, "candidate_skills", ["PK id", "FK candidate", "FK skill", "level"])
    vs = table(1, 3, "vacancy_skills", ["PK id", "FK vacancy", "FK skill"])
    fb = table(2, 3, "feedback", ["PK id", "name, email", "subject, message"])
    art = table(3, 3, "articles", ["PK id", "title, slug", "body, published"])

    def link(a, b, card, color="#334155", rad=0.0, ls="-"):
        arrow(ax, a, b, card, color=color, rad=rad, fs=6.3, ls=ls)

    link(dep["top"], users["bot"], "1:M", rad=0.0)
    link(dep["right"], vac["bot"], "1:M", rad=0.25)
    link(users["right"], vac["left"], "1:M", rad=0.0)
    link(src["top"], cand["bot"], "1:M", rad=0.1)
    link(vac["right"], app["left"], "1:M", rad=0.0)
    link(cand["right"], app["left"], "1:M", rad=0.15)
    link(stage["top"], app["bot"], "1:M", rad=0.0)
    link(app["bot"], intv["top"], "1:M", rad=0.3)
    link(app["bot"], offer["top"], "1:1", rad=0.15)
    link(intv["bot"], evalt["top"], "1:M", rad=0.2)
    link(cand["bot"], resume["top"], "1:M", rad=-0.2)
    link(cand["bot"], cs["top"], "M:M", color=C_ORANGE, rad=0.35, ls="--")
    link(skill["bot"], cs["top"], "", color=C_ORANGE, rad=0.2, ls="--")
    link(vac["bot"], vs["top"], "M:M", color=C_ORANGE, rad=-0.25, ls="--")
    link(skill["bot"], vs["top"], "", color=C_ORANGE, rad=-0.2, ls="--")

    ax.text(50, 1.5, "Сплошные линии — связи 1:M / 1:1; оранжевый пунктир — связи M:M "
                     "(через ассоциативные таблицы candidate_skills и vacancy_skills).",
            ha="center", fontsize=7.8, style="italic", color="#475569")
    save(fig, "db_schema.png")


# ---------------------------------------------------------------------------
#  8. User Flow Diagram
# ---------------------------------------------------------------------------
def diagram_user_flow():
    fig, ax = _ax(13, 7.5)
    title(ax, "User Flow Diagram — логика переходов между экранами")
    home = box(ax, 40, 84, 20, 8, "Главная", fc=C_PRIMARY, text_color="white", bold=True)
    vac = box(ax, 40, 68, 20, 8, "Список вакансий")
    det = box(ax, 40, 52, 20, 8, "Карточка вакансии")
    login = box(ax, 8, 52, 20, 8, "Вход / Регистрация", fc=C_ORANGEL, ec="#b45309")
    cabc = box(ax, 8, 30, 20, 8, "Кабинет кандидата", fc=C_GREENL, ec=C_GREEN, bold=True)
    apply = box(ax, 40, 30, 20, 8, "Отклик на вакансию")
    track = box(ax, 40, 14, 20, 8, "Мои отклики / статусы")
    cabr = box(ax, 74, 52, 20, 8, "Кабинет рекрутёра", fc=C_GREENL, ec=C_GREEN, bold=True)
    manage = box(ax, 74, 34, 20, 8, "Вакансии / отклики /\nсобеседования")
    anal = box(ax, 74, 16, 20, 8, "HR-аналитика /\nвыгрузка отчётов")

    arrow(ax, home, vac)
    arrow(ax, vac, det)
    arrow(ax, det, login, "не авторизован", rad=0.1)
    arrow(ax, det, apply, "авторизован")
    arrow(ax, login, cabc, "кандидат")
    arrow(ax, login, cabr, "рекрутёр", rad=-0.2)
    arrow(ax, cabc, apply, "", rad=0.1)
    arrow(ax, apply, track)
    arrow(ax, cabr, manage)
    arrow(ax, manage, anal)
    save(fig, "user_flow.png")


# ---------------------------------------------------------------------------
#  9. Диаграмма Ганта
# ---------------------------------------------------------------------------
def diagram_gantt():
    fig, ax = plt.subplots(figsize=(12, 7))
    tasks = [
        ("Анализ организации и бизнес-процесса (AS-IS)", 0, 4),
        ("Сбор требований, составление ТЗ (ГОСТ 34.602)", 3, 5),
        ("Проектирование модели TO-BE и архитектуры", 6, 4),
        ("Проектирование БД (ER, схема, нормализация)", 8, 5),
        ("Настройка репозитория, прототип и макет", 7, 4),
        ("Разработка моделей и панели администратора", 10, 6),
        ("Публичные страницы, меню, хлебные крошки", 13, 6),
        ("Роли, кабинеты рекрутёра и кандидата", 16, 6),
        ("HR-аналитика, выгрузка docx/xlsx", 19, 5),
        ("Тестирование (тест-план, кейсы, автотесты)", 22, 4),
        ("Деплой на хостинг, оформление отчёта", 24, 4),
    ]
    colors = [C_PRIMARY, C_PRIMARY, C_GREEN, C_GREEN, C_ORANGE, C_PRIMARY,
              C_PRIMARY, C_PRIMARY, C_PRIMARY, "#dc2626", C_GREEN]
    for i, (name, start, dur) in enumerate(tasks):
        y = len(tasks) - i
        ax.barh(y, dur, left=start, height=0.55, color=colors[i],
                edgecolor="white")
        ax.text(start + dur + 0.2, y, f"{dur} дн.", va="center", fontsize=7.5)
        ax.text(-0.5, y, name, va="center", ha="right", fontsize=8)
    # Недельные деления (практика 11.05–07.06.2026, 4 недели).
    for wk, label in [(0, "11.05"), (7, "18.05"), (14, "25.05"),
                      (21, "01.06"), (28, "07.06")]:
        ax.axvline(wk, color="#cbd5e1", ls="--", lw=0.8)
        ax.text(wk, len(tasks) + 0.8, label, ha="center", fontsize=8,
                color="#475569")
    ax.set_xlim(0, 30)
    ax.set_ylim(0, len(tasks) + 1.5)
    ax.set_yticks([])
    ax.set_xlabel("Дни практики (11.05.2026 – 07.06.2026)")
    ax.set_title("Диаграмма Ганта: план разработки веб-сервиса", fontweight="bold")
    ax.spines[["top", "right", "left"]].set_visible(False)
    save(fig, "gantt.png")


# ---------------------------------------------------------------------------
#  10. Прототип интерфейса (wireframe)
# ---------------------------------------------------------------------------
def diagram_wireframe():
    fig, ax = _ax(11, 8)
    title(ax, "Прототип (wireframe) страницы «Список вакансий»")
    gray = "#cbd5e1"

    def wbox(x, y, w, h, label="", hatch=None, fc="#f1f5f9"):
        ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec="#64748b", lw=1.2,
                               hatch=hatch))
        if label:
            ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
                    fontsize=8, color="#475569")

    wbox(8, 84, 84, 7, "Шапка: логотип ▢ | меню (10 пунктов) | Вход/Регистрация",
         fc="#e2e8f0")
    wbox(8, 78, 84, 4, "Хлебные крошки: Главная / Вакансии", fc="#f8fafc")
    wbox(8, 68, 84, 8, "Панель поиска и фильтров: [ поле поиска ] [грейд ▾] "
                        "[статус ▾] (Найти)")
    # Карточки вакансий 3 x 2
    for r in range(2):
        for c in range(3):
            x = 8 + c * 29
            y = 40 - r * 24
            wbox(x, y, 26, 20)
            ax.text(x + 2, y + 16, "▭ Название вакансии", fontsize=7.5,
                    color="#334155")
            ax.text(x + 2, y + 12, "Отдел · город", fontsize=7, color="#64748b")
            ax.text(x + 2, y + 8, "ЗП: ___ – ___ ₽", fontsize=7, color="#334155")
            wbox(x + 2, y + 1.5, 10, 4, "Подробнее", fc="#dbeafe")
    wbox(8, 8, 84, 5, "Пагинация: ‹ 1 2 3 ›", fc="#f8fafc")
    wbox(8, 1.5, 84, 5, "Подвал: ФИО автора — Серебренников Д. В. · © 2026",
         fc="#e2e8f0")
    save(fig, "wireframe.png")


# ---------------------------------------------------------------------------
#  11. Макет страницы (блочная структура)
# ---------------------------------------------------------------------------
def diagram_mockup():
    fig, ax = _ax(11, 8)
    title(ax, "Макет веб-сервиса (блочная структура страницы)")

    def mbox(x, y, w, h, label, fc):
        ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec="#1e293b", lw=1.3))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
                fontsize=9, fontweight="bold", color="#0f172a")

    mbox(6, 84, 88, 8, "HEADER — навигационная панель (Bootstrap navbar, 10 пунктов меню)",
         "#bfdbfe")
    mbox(6, 78, 88, 4.5, "BREADCRUMBS — хлебные крошки", "#e0e7ff")
    mbox(6, 70, 88, 6, "HERO / заголовок раздела", "#dbeafe")
    mbox(6, 30, 26, 38, "SIDEBAR\nменю кабинета /\nфильтры", "#dcfce7")
    mbox(34, 30, 60, 38, "MAIN CONTENT\nкарточки, таблицы, формы,\nграфики аналитики",
         "#f1f5f9")
    mbox(6, 18, 88, 10, "СЕКЦИЯ КОНТЕНТА (адаптивная сетка 12 колонок Bootstrap)",
         "#eff6ff")
    mbox(6, 6, 88, 10, "FOOTER — разделы, контакты, ФИО автора (Серебренников Д. В.), © 2026",
         "#1e293b")
    ax.text(50, 11, "FOOTER — разделы · контакты · ФИО автора: Серебренников Д. В. · © 2026",
            ha="center", va="center", fontsize=8.5, color="white")
    save(fig, "mockup.png")


def main():
    diagram_as_is()
    diagram_to_be()
    diagram_func_tree()
    diagram_components()
    diagram_er_info()
    diagram_er_logic()
    diagram_db_schema()
    diagram_user_flow()
    diagram_gantt()
    diagram_wireframe()
    diagram_mockup()
    print("Все диаграммы сохранены в", OUT)


if __name__ == "__main__":
    main()
