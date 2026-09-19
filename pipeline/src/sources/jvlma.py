"""Jāzeps Vītols Latvian Academy of Music (JVLMA) — английский раздел,
две страницы направлений: field-of-study-arts и
field-of-study-education-and-pedagogy.

Структура найдена вручную в браузере 2026-09-19: у академии нет страниц
по отдельным программам, только два текстовых списка вида

  PROFESSIONAL BACHELOR'S STUDY PROGRAMME
  Music and Performing Arts with sub-programmes: ...
  ACADEMIC MASTER'S STUDY PROGRAMME
  Academic Master's Study Programme in Musicology with specializations: ...

Программ всего около семи (подпрограммы — инструменты, дирижирование и
т.п. — внутри них, отдельными записями каталога не являются), поэтому
разбор — по заголовкам уровня, а название берётся из первой непустой
строки под заголовком. Сроков обучения, языка, мест и стоимости на этих
страницах нет: язык 'lv' — предположение (как у lma.py), стоимость и
места остаются пустыми, funding_type='paid' — осторожный дефолт.
"""

from __future__ import annotations

import re

from playwright.sync_api import Page, sync_playwright

from models import ProgrammeDraft, UniversityDraft

BASE_URL = "https://www.jvlma.lv"
PAGES = [
    f"{BASE_URL}/en/studies/study-programmes/field-of-study-arts",
    f"{BASE_URL}/en/studies/study-programmes/field-of-study-education-and-pedagogy",
]

UNIVERSITY = UniversityDraft(
    slug="jvlma",
    name_lv="Jāzepa Vītola Latvijas Mūzikas akadēmija",
    name_en="Jāzeps Vītols Latvian Academy of Music",
    kind="public",
    city="riga",
    website_url=BASE_URL,
    source_url=f"{BASE_URL}/en/studies/study-programmes",
)

# заголовок -> уровень; "short cycle" — программа первого уровня
# профессионального высшего образования (по-нашему college)
HEADING = re.compile(
    r"^(?:PROFESSIONAL|ACADEMIC|SHORT CIRCLE PROFESSIONAL|SHORT CYCLE PROFESSIONAL)"
    r"[A-Z\s]*?(BACHELOR|MASTER|DOCTORAL|HIGHER EDUCATIONAL)[’'A-Z\s]*STUDY PROGRAMME$",
    re.I,
)


def _level(heading: str) -> str:
    lowered = heading.lower()
    if lowered.startswith("short"):
        return "college"
    if "doctoral" in lowered:
        return "doctoral"
    if "master" in lowered:
        return "master"
    return "bachelor"


def _clean_name(line: str) -> str:
    name = re.sub(r"\s*\(this specific.*?\)", "", line)
    name = re.sub(r"\s+with (sub-programmes|specializations)\b.*$", "", name, flags=re.I)
    name = re.sub(r"^Academic Master['’]s Study Programme in ", "", name, flags=re.I)
    name = re.sub(r"^Academic Doctoral Study Programme in ", "", name, flags=re.I)
    name = re.sub(r"^Study Programme\s+", "", name, flags=re.I)
    return name.strip(" ,.:;‘’“”'\"")


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _parse_page(text: str, url: str) -> list[ProgrammeDraft]:
    lines = [line.strip() for line in text.split("\n")]
    programmes: list[ProgrammeDraft] = []
    for index, line in enumerate(lines):
        if not HEADING.match(line):
            continue
        following = next((candidate for candidate in lines[index + 1 :] if candidate), "")
        name = _clean_name(following)
        if not name:
            continue
        level = _level(line)
        # "Doctoral": у профессиональной докторантуры вместо названия —
        # 'Study Programme “Arts”' (уже очищено выше), у академической —
        # "Musicology"; одинаковые названия различает уровень в слаге
        programmes.append(
            ProgrammeDraft(
                slug=f"{_slugify(name)}-{level}",
                name_en=name,
                degree_level=level,
                language_of_instruction="lv",
                study_mode="full_time",
                city=UNIVERSITY.city,
                funding_type="paid",
                source_url=url,
            )
        )
    return programmes


def _scrape_page(page: Page, url: str) -> list[ProgrammeDraft]:
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(800)
    main = page.locator("main")
    text = main.first.inner_text() if main.count() > 0 else page.locator("body").inner_text()
    return _parse_page(text, url)


def scrape() -> tuple[UniversityDraft, list[ProgrammeDraft]]:
    programmes: list[ProgrammeDraft] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        for url in PAGES:
            programmes.extend(_scrape_page(page, url))
        browser.close()

    # Если у академии две программы одного уровня с одним названием,
    # слаги совпали бы, и upsert молча оставил бы одну — лучше упасть
    slugs = [programme.slug for programme in programmes]
    if len(slugs) != len(set(slugs)):
        raise RuntimeError(f"jvlma: повторяющиеся слаги программ: {sorted(slugs)}")

    return UNIVERSITY, programmes
