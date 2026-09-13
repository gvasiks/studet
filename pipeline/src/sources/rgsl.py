"""RGSL (Riga Graduate School of Law) — английский сайт (единственный,
здесь вуз целиком международный).

Структура найдена вручную в браузере 2026-09-13: у каждой программы
таблица фактов `.programme-table .table-row` из пар `.table-cell`
(метка + значение) прямо вверху страницы. Метки чуть отличаются между
программами (bachelor: "Study language"/"Tuition fee"/"Programme
duration"/"Study form" отдельными строками; master: "Language"/"Fee"/
"Duration" — форма обучения слита в строку длительности), поэтому ищем
по ключевым словам в названии метки, а не по точному совпадению.

Список программ — вручную отобранные из /programmes: там же есть
Intensive Programme, Specialised online courses, Other capacity-building
projects — это не программы на степень, не берём.
"""

from __future__ import annotations

import re

from playwright.sync_api import Page, sync_playwright

from models import ProgrammeDraft, UniversityDraft

BASE_URL = "https://www.rgsl.edu.lv/programmes"

PROGRAMMES = {
    "law-and-business": "bachelor",
    "law-and-diplomacy": "bachelor",
    "technology-law": "master",
    "law-and-finance-": "master",
}

UNIVERSITY = UniversityDraft(
    slug="rgsl",
    name_lv="Rīgas Juridiskā augstskola",
    name_en="Riga Graduate School of Law",
    kind="private",
    city="riga",
    website_url="https://www.rgsl.edu.lv",
    source_url=BASE_URL,
)


def _facts(page: Page) -> dict[str, str]:
    facts: dict[str, str] = {}
    rows = page.locator(".programme-table .table-row")
    for i in range(rows.count()):
        cells = rows.nth(i).locator(".table-cell")
        if cells.count() < 2:
            continue
        key = cells.nth(0).inner_text().strip().lower()
        value = cells.nth(1).inner_text().strip()
        facts[key] = value
    return facts


def _find_by_keyword(facts: dict[str, str], keyword: str) -> str:
    for key, value in facts.items():
        if keyword in key:
            return value
    return ""


def _find_eu_fee(facts: dict[str, str]) -> str:
    for key, value in facts.items():
        if "fee" in key and "non" not in key:
            return value
    return ""


def _parse_price(text: str) -> float | None:
    match = re.search(r"([\d\s ]+)\s*EUR", text)
    if not match:
        return None
    digits = re.sub(r"[\s ]", "", match.group(1))
    return float(digits) if digits else None


def _parse_years(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(match.group(1)) if match else None


def _extract_mode(facts: dict[str, str], duration_text: str) -> str:
    # У бакалаврских страниц форма — отдельное поле ("Study form: Full time"),
    # у магистерских слита в длительность ("Full time attendance - 1 year:
    # Part-time attendance - 2 years") — full time там всегда указан первым.
    combined = f"{_find_by_keyword(facts, 'form')} {duration_text}".lower()
    if "full" in combined:
        return "full_time"
    if "part" in combined:
        return "part_time"
    return "full_time"


def _extract_name(heading: str) -> str:
    # h1 у RGSL — целиком "First-Cycle (Bachelor) programme "Law and
    # Business"", само название всегда в кавычках внутри.
    match = re.search(r"“([^”]+)”|\"([^\"]+)\"", heading)
    if not match:
        return heading
    return match.group(1) or match.group(2)


def _scrape_programme(page: Page, slug: str, degree_level: str) -> ProgrammeDraft:
    url = f"{BASE_URL}/{slug}"
    page.goto(url, wait_until="domcontentloaded")
    name_en = _extract_name(page.locator("h1").first.inner_text().strip())

    facts = _facts(page)
    duration_text = _find_by_keyword(facts, "duration")

    return ProgrammeDraft(
        slug=slug.rstrip("-"),
        name_en=name_en,
        degree_level=degree_level,
        # У всех проверенных страниц RGSL — "English"/"Study language: English";
        # вуз целиком англоязычный, отдельного парсинга не требуется.
        language_of_instruction="en",
        study_mode=_extract_mode(facts, duration_text),
        city=UNIVERSITY.city,
        funding_type="paid",
        tuition_fee_amount=_parse_price(_find_eu_fee(facts)),
        duration_years=_parse_years(duration_text),
        source_url=url,
    )


def scrape() -> tuple[UniversityDraft, list[ProgrammeDraft]]:
    programmes: list[ProgrammeDraft] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for slug, degree_level in PROGRAMMES.items():
            programmes.append(_scrape_programme(page, slug, degree_level))

        browser.close()

    return UNIVERSITY, programmes
