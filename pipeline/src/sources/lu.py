"""LU (Latvijas Universitāte) — английский раздел сайта, все 6
факультетов бакалавриата целиком (их оказалось всего 6, не десяток,
как выглядело до проверки — Economics and Social Sciences, Science
and Technology, Humanities, Education Sciences and Psychology, Law,
Medicine and Life Sciences).

Магистратура, докторантура и короткие программы (college) добавлены
2026-09-20: раздел /study-programmes-1/ устроен одинаково для всех
уровней — страница раздела -> списки по факультетам (у докторантуры и
коротких программ список сразу на странице раздела) -> страница программы
с блоком фактов. Уровень берётся из раздела сайта, где программа лежит,
а не из текста "Programme level" (там бывает "Second level professional
higher education" для одноуровневой медицины — у нас это bachelor, как и
раньше). Кроме шести факультетов, в бакалавриате и магистратуре есть
ещё "UL FinTech Business School" (бывшая Banku augstskola) и
"Regional branches" — они тоже обходятся.

У докторантуры значения полей стоят на следующей строке после метки
("Study form and duration:" и строка "Full-time - 6 semesters" ниже),
поэтому значение поля — всё до следующей известной метки, а не до конца
строки.

В выборке — та самая программа "Economics" из примера расчёта
конкурсного балла в docs/PLAN.md (математика ×6,5) — но саму формулу
сюда не тащим, это отдельная задача с утверждённым PDF (правило 6
CLAUDE.md), здесь только факты каталога.

Структура найдена вручную в браузере 2026-09-13: TYPO3-сайт, факты —
один блок `.ce-bodytext` с парами "Label: значение" через перенос
строки (не `<br>`-разделённые абзацы, как у BSA — здесь одна строка
на поле). Формат числа бюджетных мест и цены отличается от программы
к программе (иногда "Full time state-funded study places", иногда
просто "State-funded study places" для программ без очной/заочной
развилки) — ищем по общей подстроке "state-funded study places",
не по точной фразе целиком.
"""

from __future__ import annotations

import re
from datetime import date
from urllib.parse import urljoin

from playwright.sync_api import Page, sync_playwright

from models import ProgrammeDraft, UniversityDraft

STUDY_BASE = "https://www.lu.lv/en/studies/study-programmes-1/"
BACHELOR_BASE = f"{STUDY_BASE}bachelors-study-programmes/"

_FACULTIES = [
    "faculty-of-economics-and-social-sciences/",
    "faculty-of-science-and-technology/",
    "faculty-of-humanities/",
    "faculty-of-education-sciences-and-psychology/",
    "faculty-of-law/",
    "faculty-of-medicine-and-life-sciences/",
    "ba-school-of-business-and-finance-of-the-ul/",  # UL FinTech Business School
    "regional-branches/",
]

# (папка раздела на сайте, наш degree_level, страницы-списки внутри раздела;
#  "" — список программ прямо на странице раздела)
SECTIONS = [
    ("bachelors-study-programmes", "bachelor", _FACULTIES),
    ("masters-study-programmes", "master", _FACULTIES),
    ("short-cycle-study-programmes", "college", [""]),
    ("doctoral-studies", "doctoral", [""]),
]

# Папки, в которых лежат страницы самих программ. У коротких программ
# одна лежит в college-level-study-programmes/ (Sports Coach), хотя
# ссылка стоит в списке short-cycle.
PROGRAMME_DIRS = [section for section, _, _ in SECTIONS] + ["college-level-study-programmes"]

CITY_WORDS = {
    "riga": "riga", "rīga": "riga",
    "daugavpils": "daugavpils",
    "liepāja": "liepaja", "liepaja": "liepaja",
    "rēzekne": "rezekne", "rezekne": "rezekne",
    "valmiera": "valmiera",
    "ventspils": "ventspils",
    "jelgava": "jelgava",
    "jūrmala": "jurmala", "jurmala": "jurmala",
}

# У разных факультетов метки называются по-разному. Известно три
# формата страниц:
#   1) "Programme level / Language of instruction / Study form and
#      duration / Number of study places for admission / Tuition fee per
#      year / Study location" (бакалавриат и магистратура большинства
#      факультетов; у нескольких — "Program level", "Language of study");
#   2) то же у докторантуры, но значения на следующей строке;
#   3) "Level of study / Duration / Form of study / Language / Location /
#      Amount of spaces" и его вариант "Level / Length / Study form /
#      Study language / Place / Study fee" (Science and Technology и
#      короткие программы).
# Метка — начало строки до первого двоеточия. Поле -> с каких слов метка
# начинается; короткие метки, которые нельзя сравнивать по началу
# ("place" совпало бы с "places ..."), — в EXACT_ALIASES.
FIELD_ALIASES = {
    "level": ("programme level", "program level", "level of study"),
    "language": ("language", "study language"),
    "duration": ("study form and duration", "form and duration", "duration"),
    "form": ("form of study", "study form"),
    "credits": ("credits", "amount in credit", "number of credits"),
    "degree": ("obtainable degree", "degree awarded", "degree"),
    "places": (
        "number of study places", "number of places", "number of students accepted",
        "amount of spaces", "student places",
    ),
    "fee": ("tuition fee", "study fee"),
    "location": ("study location", "location"),
    "accredited": ("accredited until",),
}
EXACT_ALIASES = {
    "level": ("level",),
    "duration": ("length",),
    "location": ("place",),
}

# Поля, у которых нужна только первая строка значения: под последним
# полем на страницах без пустой строки идёт описание программы, и оно
# не должно попасть ни в язык, ни в город
SINGLE_LINE_FIELDS = {"level", "language", "form", "credits", "location", "accredited"}

UNIVERSITY = UniversityDraft(
    slug="lu",
    name_lv="Latvijas Universitāte",
    name_en="University of Latvia",
    kind="public",
    city="riga",
    website_url="https://www.lu.lv",
    source_url=BACHELOR_BASE,
)


def _list_urls() -> list[tuple[str, str, str]]:
    """(URL страницы-списка, папка раздела, degree_level)."""
    return [
        (f"{STUDY_BASE}{section}/{sub}", section, level)
        for section, level, subs in SECTIONS
        for sub in subs
    ]


def _discover_links(page: Page, list_url: str, list_urls: set[str]) -> list[tuple[str, str]]:
    page.goto(list_url, wait_until="domcontentloaded")
    links = page.locator("main a")

    seen: dict[str, str] = {}
    for i in range(links.count()):
        href = links.nth(i).get_attribute("href")
        text = links.nth(i).inner_text().strip()
        if not href:
            continue
        href = urljoin(list_url, href)
        if not any(f"/{directory}/" in href for directory in PROGRAMME_DIRS):
            continue
        # страницы-списки и корни разделов — не программы
        if href.rstrip("/") in list_urls or href.rstrip("/").rsplit("/", 1)[-1] in PROGRAMME_DIRS:
            continue
        seen.setdefault(href, text)

    return list(seen.items())


def _field_for(label: str) -> str | None:
    lowered = label.strip().lower()
    for field, exact in EXACT_ALIASES.items():
        if lowered in exact:
            return field
    for field, prefixes in FIELD_ALIASES.items():
        if lowered.startswith(prefixes):
            return field
    return None


def _parse_facts(text: str) -> dict[str, str]:
    """Блок фактов -> {поле: значение}. Значение — строки от метки до
    следующей метки или до первой пустой строки после значения (за ней
    на странице идёт описание программы). У докторантуры значение стоит
    на следующей строке после метки, у бакалавриата — в той же."""
    collected: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.split("\n"):
        stripped = line.strip().replace("\xa0", " ").strip()
        key, colon, rest = stripped.partition(":")
        field = _field_for(key) if colon else None
        if field:
            current = field
            collected.setdefault(field, [])
            if rest.strip():
                collected[field].append(rest.strip())
        elif not stripped:
            if current and collected[current]:
                current = None
        elif current:
            collected[current].append(stripped)

    facts: dict[str, str] = {}
    for field, lines in collected.items():
        if not lines:
            continue
        facts[field] = lines[0] if field in SINGLE_LINE_FIELDS else " ".join(lines)
    return facts


def _language_from(text: str) -> str:
    lowered = text.lower()
    english, latvian = lowered.find("english"), lowered.find("latvian")
    if english == -1:
        return "lv"
    return "en" if latvian == -1 or english < latvian else "lv"


def _extract_mode(text: str) -> str:
    lowered = text.lower()
    if "full-time" in lowered or "full time" in lowered:
        return "full_time"
    if "part-time" in lowered or "part time" in lowered:
        return "part_time"
    return "full_time"


def _parse_duration_years(text: str) -> float | None:
    # "4 semesters" и "six (6) semesters"
    match = re.search(r"(\d+)\)?\s*semester", text.lower())
    if match:
        return int(match.group(1)) / 2
    match = re.search(r"(\d+(?:\.\d+)?)\s*year", text.lower())
    return float(match.group(1)) if match else None


def _budget_places_from(text: str) -> tuple[int | None, bool]:
    """(число мест, есть ли бюджетные места вообще). Если на странице
    несколько подпрограмм с разными числами ("Biology - ... 60",
    "Biomedicine - ... 8"), общего числа нет — вернём None, чтобы не
    приписать одной программе места другой."""
    matches = re.findall(r"state-funded study places\D*(\d+)", text, re.IGNORECASE)
    if not matches:
        # третий формат страниц: "50 state funded/ 30 self funded"
        matches = re.findall(r"(\d+)\s*state[- ]funded", text, re.IGNORECASE)
    numbers = [int(match) for match in matches]
    has_budget = any(number > 0 for number in numbers)
    return (numbers[0] if len(numbers) == 1 and numbers[0] > 0 else None), has_budget


# "Biology - 2700 EUR ... Biomedicine - 3500 EUR": цены подпрограмм, а не
# тарифы для граждан ЕС и других стран. "Tuition fee per year - 3100 EUR"
# (два тарифа одной программы) сюда не попадает.
_PER_SUBPROGRAMME_FEE = re.compile(r"\b(?!Tuition fee per year\b)[A-Z][\w' ]{2,40} - \d{3,5} EUR")


def _parse_price(text: str) -> float | None:
    if len(_PER_SUBPROGRAMME_FEE.findall(text)) > 1:
        return None
    match = re.search(r"([\d][\d\s ]*)\s*EUR", text)
    if not match:
        return None
    digits = re.sub(r"[\s ]", "", match.group(1))
    return float(digits) if digits else None


def _city_from(location_text: str) -> str:
    lowered = location_text.lower()
    for word, key in CITY_WORDS.items():
        if word in lowered:
            return key
    return UNIVERSITY.city


def _parse_accredited_until(text: str) -> date | None:
    match = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", text)
    return date(int(match.group(3)), int(match.group(2)), int(match.group(1))) if match else None


def _scrape_programme(page: Page, url: str, link_text: str, level: str) -> ProgrammeDraft | None:
    page.goto(url, wait_until="domcontentloaded")
    blocks = page.locator(".ce-bodytext")
    if blocks.count() == 0:
        return None

    # факты обычно в первом блоке, но не всегда — берём все и разбираем по
    # меткам; страница без срока обучения — не страница программы
    text = "\n".join(blocks.nth(i).inner_text() for i in range(blocks.count()))
    facts = _parse_facts(text)
    if "duration" not in facts:
        return None

    slug = url.rstrip("/").rsplit("/", 1)[-1]
    # бакалавры сохраняют прежний слаг (по нему уже записаны строки в
    # базе); остальным уровням — суффикс уровня: "law" есть и в
    # бакалавриате, и в магистратуре
    if level != "bachelor":
        slug = f"{slug}-{level}"
    # "(LV)"/"(EN)" в заголовке — язык и так отдельное поле; убираем из
    # читаемого названия, но не из slug (иначе lv/en варианты столкнутся).
    # "(2 years)"/"(1,5 years)" у FinTech Business School остаются: это
    # разные программы с одним названием
    name_en = re.sub(r"\s*\((LV|EN)\)", "", link_text).strip()

    language_text = facts.get("language", "")
    duration_text = facts["duration"]
    places_text = facts.get("places", "")
    fee_text = facts.get("fee", "")
    accredited_text = facts.get("accredited", "")

    budget_places, has_budget = _budget_places_from(places_text)

    return ProgrammeDraft(
        slug=slug,
        name_en=name_en,
        degree_level=level,
        language_of_instruction=_language_from(language_text),
        study_mode=_extract_mode(f"{facts.get('form', '')} {duration_text}"),
        city=_city_from(facts.get("location", "")),
        funding_type="both" if has_budget else "paid",
        tuition_fee_amount=_parse_price(fee_text),
        budget_places=budget_places,
        duration_years=_parse_duration_years(duration_text),
        accreditation_valid_until=_parse_accredited_until(accredited_text),
        source_url=url,
    )


def _collect(
    page: Page,
    url: str,
    link_text: str,
    level: str,
    list_urls: set[str],
    seen_urls: set[str],
    programmes: list[ProgrammeDraft],
    depth: int = 0,
) -> None:
    if url in seen_urls:
        return  # программа может значиться на стыке двух факультетов
    seen_urls.add(url)
    programme = None
    for attempt in (1, 2):
        try:
            programme = _scrape_programme(page, url, link_text, level)
            break
        except Exception as exc:
            # сайт изредка отвечает дольше таймаута; вторая попытка обычно
            # проходит. Не прошла и она — программа пропущена, но не молча:
            # порог MIN_PROGRAMME_COUNT в main.py поймает потерю
            if attempt == 2:
                print(f"lu: пропущена {url}: {exc!r}")
    if programme:
        programmes.append(programme)
        return

    # Страница без фактов — возможно, промежуточный список: докторантура
    # "Natural Sciences" — это страница с двенадцатью подпрограммами.
    # Углубляемся на один уровень, не больше.
    if depth == 0:
        for child_url, child_text in _discover_links(page, url, list_urls | {url.rstrip("/")}):
            _collect(page, child_url, child_text, level, list_urls, seen_urls, programmes, depth=1)


def scrape() -> tuple[UniversityDraft, list[ProgrammeDraft]]:
    programmes: list[ProgrammeDraft] = []
    seen_urls: set[str] = set()
    lists = _list_urls()
    list_urls = {url.rstrip("/") for url, _, _ in lists}

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(8000)

        for list_url, _, level in lists:
            for url, link_text in _discover_links(page, list_url, list_urls):
                _collect(page, url, link_text, level, list_urls, seen_urls, programmes)

        browser.close()

    return UNIVERSITY, programmes
