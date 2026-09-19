"""Latvijas Nacionālā aizsardzības akadēmija (Latvian National Defence
Academy) — naa.mil.lv/lv/studijas.

Структура найдена вручную в браузере 2026-09-19: всё на одной странице.
Вверху — меню из шести названий заглавными буквами, ниже — описание
каждой программы. Отдельных страниц с фактами (срок, язык) нет, поэтому
уровень задаётся словарём по названию, а не выводится из текста: из
описаний ("первый цикл", "короткий цикл", "профессиональная магистерская")
это пришлось бы вылавливать регулярками по свободному тексту.

Если в меню появится название, которого нет в словаре, сборщик падает —
новую программу должен классифицировать человек, а не угадывать код.

Все шесть программ на странице названы "valsts apmaksātās" (оплачены
государством) — funding_type='budget'; число мест не публикуется.
Обучение по-латышски (язык программы нигде не указан — предположение).
"""

from __future__ import annotations

import re

from playwright.sync_api import Page, sync_playwright

from models import ProgrammeDraft, UniversityDraft

BASE_URL = "https://www.naa.mil.lv"
STUDIES_URL = f"{BASE_URL}/lv/studijas"

UNIVERSITY = UniversityDraft(
    slug="lnaa",
    name_lv="Latvijas Nacionālā aizsardzības akadēmija",
    name_en="National Defence Academy of Latvia",
    kind="public",
    city="riga",
    website_url=BASE_URL,
    source_url=STUDIES_URL,
)

# название в меню (заглавными) -> (degree_level, срок в годах или None)
KNOWN_PROGRAMMES: dict[str, tuple[str, float | None]] = {
    "SAUSZEMES SPĒKU MILITĀRĀ VADĪBA": ("bachelor", None),
    "GAISA SPĒKU MILITĀRĀ VADĪBA": ("bachelor", None),
    "JŪRAS SPĒKU MILITĀRĀ VADĪBA": ("bachelor", None),
    # для выпускников других вузов, "divos gados" — за два года; первый
    # цикл профессионального высшего образования = наш bachelor
    "KOMANDĒJOŠĀ SASTĀVA VIRSNIEKS": ("bachelor", 2.0),
    # "īsā cikla" — короткий цикл, как наши колледжи
    "PRAKTISKĀ MILITĀRĀ VADĪBA": ("college", None),
    "MILITĀRĀ VADĪBA UN DROŠĪBA": ("master", None),
}

MENU_LINE = re.compile(r"^[A-ZĀČĒĢĪĶĻŅŠŪŽ ]{12,}$")


def _slugify(text: str) -> str:
    table = str.maketrans("āčēģīķļņšūž", "acegiklnsuz")
    return re.sub(r"[^a-z0-9]+", "-", text.lower().translate(table)).strip("-")


def _menu_titles(text: str) -> list[str]:
    seen: list[str] = []
    for line in text.split("\n"):
        line = line.strip()
        if MENU_LINE.match(line) and line not in seen:
            seen.append(line)
    return seen


def _title_case(title: str) -> str:
    # "GAISA SPĒKU MILITĀRĀ VADĪBA" -> "Gaisa spēku militārā vadība"
    return title.capitalize()


def scrape() -> tuple[UniversityDraft, list[ProgrammeDraft]]:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page: Page = browser.new_page()
        page.goto(STUDIES_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        text = page.locator("body").inner_text()
        browser.close()

    titles = _menu_titles(text)
    unknown = [title for title in titles if title not in KNOWN_PROGRAMMES]
    if unknown:
        raise RuntimeError(
            f"lnaa: в меню появились незнакомые названия {unknown} — добавьте их в "
            "KNOWN_PROGRAMMES (lnaa.py) с уровнем обучения, определив его вручную."
        )

    programmes = [
        ProgrammeDraft(
            slug=_slugify(title),
            name_lv=_title_case(title),
            degree_level=KNOWN_PROGRAMMES[title][0],
            language_of_instruction="lv",
            study_mode="full_time",
            city=UNIVERSITY.city,
            funding_type="budget",
            duration_years=KNOWN_PROGRAMMES[title][1],
            source_url=STUDIES_URL,
        )
        for title in titles
    ]
    return UNIVERSITY, programmes
