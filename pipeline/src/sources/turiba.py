"""Turība University — английский раздел сайта.

Структура проверена вручную в браузере 2026-09-11:
- списки программ: ссылки a[href*="/admission/study-programs/"]
- карточка программы: h1.b1-title (название) + блоки div.b8-text
  вида "<b>Label</b>: value" (Degree awarded, Duration, Study language, ...)

Стоимость и дедлайн подачи сюда сознательно не включены: это поля из
правила 6 CLAUDE.md (подтверждает только человек), а на сайте они не
привязаны к конкретной программе (общая таблица цен на отдельной
странице) — надёжнее внести их вручную через Supabase Studio, чем
парсить текстовую таблицу вслепую.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from urllib.parse import urljoin

from playwright.sync_api import Page, sync_playwright

from models import ProgrammeDraft, UniversityDraft

BASE_URL = "https://www.turiba.lv/en"

LISTING_PAGES = {
    "college": f"{BASE_URL}/admission/study-programs/college",
    "bachelor": f"{BASE_URL}/admission/study-programs/bachelor-studies",
    "master": f"{BASE_URL}/admission/study-programs/master-studies",
    "doctoral": f"{BASE_URL}/admission/study-programs/doctoral-studies",
    "foundation": f"{BASE_URL}/admission/study-programs/english-foundation-program",
}

UNIVERSITY = UniversityDraft(
    slug="turiba",
    name_lv="Turība",
    name_en="Turība University",
    kind="private",
    city="riga",
    website_url="https://www.turiba.lv",
    source_url=BASE_URL,
)

LANGUAGE_MAP = {"english": "en", "latvian": "lv"}


def _parse_years(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(match.group(1)) if match else None


def _parse_accreditation(body_text: str) -> date | None:
    match = re.search(r"accredited until (\w+ \d{1,2}, \d{4})", body_text, re.IGNORECASE)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%B %d, %Y").date()
    except ValueError:
        return None


def _scrape_detail(page: Page, url: str, degree_level: str) -> ProgrammeDraft:
    page.goto(url, wait_until="domcontentloaded")
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    name_en = page.locator("h1.b1-title").first.inner_text().strip()

    facts: dict[str, str] = {}
    blocks = page.locator(".b8-text")
    for i in range(blocks.count()):
        block = blocks.nth(i)
        label = block.locator("b").first.inner_text().strip().lower()
        value = block.inner_text().split(":", 1)[-1].strip()
        facts[label] = value

    body_text = page.locator("body").inner_text()

    return ProgrammeDraft(
        slug=slug,
        name_en=name_en,
        degree_level=degree_level,
        language_of_instruction=LANGUAGE_MAP.get(facts.get("study language", "").lower(), "en"),
        study_mode="distance" if "e-studies" in slug else "full_time",
        city=UNIVERSITY.city,
        funding_type="paid",
        duration_years=_parse_years(facts.get("duration", "")),
        accreditation_valid_until=_parse_accreditation(body_text),
        source_url=url,
    )


def scrape() -> tuple[UniversityDraft, list[ProgrammeDraft]]:
    excluded = {url.rstrip("/") for url in LISTING_PAGES.values()}
    excluded.add(f"{BASE_URL}/admission/study-programs")

    programmes: list[ProgrammeDraft] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for degree_level, listing_url in LISTING_PAGES.items():
            page.goto(listing_url, wait_until="domcontentloaded")
            links = page.locator('a[href*="/admission/study-programs/"]')
            raw_hrefs = {links.nth(i).get_attribute("href") for i in range(links.count())}
            hrefs = {urljoin(listing_url, h) for h in raw_hrefs if h}
            detail_hrefs = sorted(h for h in hrefs if h.rstrip("/") not in excluded)

            for href in detail_hrefs:
                programmes.append(_scrape_detail(page, href, degree_level))

        browser.close()

    return UNIVERSITY, programmes
