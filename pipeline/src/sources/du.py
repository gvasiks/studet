"""Daugavpils Universitāte (Daugavpils University) — английский раздел,
только Academic Bachelor's programmes (9 штук; professional bachelor's,
master's и doctoral — отдельные категории на сайте, не в этом заходе).

Структура найдена вручную в браузере 2026-09-13: обычная HTML-таблица
`<table><tr><td><strong>Label</strong></td><td>значение</td></tr></table>` —
самая простая разметка фактов из всех источников пока что. Но сайт
непоследователен между программами: у большинства нет ни языка, ни
формы явно ("Programme Duration"/"Forms of the Programme
Implementation"), а у "Environmental Science" — другой шаблон таблицы
("Duration in full years"/"Study type and form"/"Language" — и там же
прямо сказано "Latvian (for studies in Latvian); English (for studies
in English)", то есть это две отдельные программы на одной странице).
Ищем факты по нескольким возможным названиям метки, не по одному.

Стоимость и бюджетные места нигде на этих страницах не публикуются —
университет их просто не показывает (в отличие от ЛУ и Вентспилса).
`language_of_instruction` по умолчанию 'lv', когда язык не указан явно —
предположение, не факт со страницы: DU преподаёт почти всё на латышском,
английский раздел сайта — язык описания для иностранных абитуриентов,
не свидетельство о языке курса. `funding_type='paid'` — тот же
осторожный дефолт при отсутствии данных, а не утверждение, что
бюджетных мест нет (DU — государственный вуз в единой подаче, места
почти наверняка есть, просто не показаны на этой странице).
"""

from __future__ import annotations

import re

from playwright.sync_api import Page, sync_playwright

from models import ProgrammeDraft, UniversityDraft

LISTING_URL = "https://du.lv/en/studies/study-programmes/academic-bachelors-study-programmes/"

UNIVERSITY = UniversityDraft(
    slug="du",
    name_lv="Daugavpils Universitāte",
    name_en="Daugavpils University",
    kind="public",
    city="daugavpils",
    website_url="https://du.lv",
    source_url=LISTING_URL,
)


def _discover_links(page: Page) -> list[str]:
    page.goto(LISTING_URL, wait_until="domcontentloaded")
    links = page.locator('a[href*="/academic-bachelors-study-programmes/"]')
    hrefs = {links.nth(i).get_attribute("href") for i in range(links.count())}
    excluded = LISTING_URL.rstrip("/")
    return sorted(h for h in hrefs if h and h.rstrip("/") != excluded)


def _facts(page: Page) -> dict[str, str]:
    facts: dict[str, str] = {}
    rows = page.locator("table tr")
    for i in range(rows.count()):
        cells = rows.nth(i).locator("td")
        if cells.count() < 2:
            continue
        key = cells.nth(0).inner_text().strip()
        value = cells.nth(1).inner_text().strip()
        facts[key] = value
    return facts


def _find(facts: dict[str, str], *keys: str) -> str:
    for key in keys:
        if key in facts:
            return facts[key]
    return ""


def _parse_years(text: str) -> float | None:
    match = re.search(r"(\d+(?:[.,]\d+)?)", text)
    return float(match.group(1).replace(",", ".")) if match else None


def _extract_mode(text: str) -> str:
    lowered = text.lower()
    if "part-time" in lowered or "part time" in lowered:
        return "part_time"
    if "distance" in lowered or "extramural" in lowered:
        return "distance"
    return "full_time"


def _extract_languages(text: str) -> list[str]:
    if not text:
        return ["lv"]
    lowered = text.lower()
    languages = [lang for lang, key in (("lv", "latvian"), ("en", "english")) if key in lowered]
    return languages or ["lv"]


def _scrape_programme(page: Page, url: str) -> list[ProgrammeDraft]:
    page.goto(url, wait_until="domcontentloaded")
    facts = _facts(page)

    duration_text = _find(facts, "Programme Duration", "Duration in full years")
    if not duration_text:
        return []

    h1 = page.locator("h1").first
    name_en = h1.inner_text().strip() if h1.count() > 0 else ""
    base_slug = url.rstrip("/").rsplit("/", 1)[-1]

    mode_text = _find(facts, "Forms of the Programme Implementation", "Study type and form")
    languages = _extract_languages(facts.get("Language", ""))
    multiple = len(languages) > 1

    return [
        ProgrammeDraft(
            slug=f"{base_slug}-{language}" if multiple else base_slug,
            name_en=name_en,
            degree_level="bachelor",
            language_of_instruction=language,
            study_mode=_extract_mode(mode_text),
            city=UNIVERSITY.city,
            funding_type="paid",
            duration_years=_parse_years(duration_text),
            source_url=url,
        )
        for language in languages
    ]


def scrape() -> tuple[UniversityDraft, list[ProgrammeDraft]]:
    programmes: list[ProgrammeDraft] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for url in _discover_links(page):
            programmes.extend(_scrape_programme(page, url))

        browser.close()

    return UNIVERSITY, programmes
