"""LBTU (Latvijas Biozinātņu un tehnoloģiju universitāte / Latvia
University of Life Sciences and Technologies) — английский раздел.

Главный кампус в Елгаве, не в Риге (старое название — LLU, домен
llu.lv у содержательных страниц остался, у навигации — lbtu.lv).
Английских программ немного — 3 бакалаврских, 6 магистерских — сайт
прямо говорит "Study programmes available in English", остальной
(латышский) каталог сюда не входит.

Структура найдена вручную в браузере 2026-09-13: один `<p>` с парами
`<strong>Label:</strong> значение<br>` — тот же паттерн, что у LU и
BSA, разбираем по тексту, не по классам.
"""

from __future__ import annotations

import re

from playwright.sync_api import Page, sync_playwright

from models import ProgrammeDraft, UniversityDraft

LISTING_PAGES = {
    "bachelor": "https://www.lbtu.lv/en/bachelor-study-programmes",
    "master": "https://www.lbtu.lv/en/master-study-programmes",
}

UNIVERSITY = UniversityDraft(
    slug="lbtu",
    name_lv="Latvijas Biozinātņu un tehnoloģiju universitāte",
    name_en="Latvia University of Life Sciences and Technologies",
    kind="public",
    city="jelgava",
    website_url="https://www.lbtu.lv",
    source_url=LISTING_PAGES["bachelor"],
)


def _discover_links(page: Page, listing_url: str) -> list[str]:
    page.goto(listing_url, wait_until="domcontentloaded")
    links = page.locator("article a")
    hrefs = {links.nth(i).get_attribute("href") for i in range(links.count())}
    return sorted(h for h in hrefs if h and h.startswith("http"))


def _extract_field(text: str, label: str) -> str:
    idx = text.find(label)
    if idx == -1:
        return ""
    start = idx + len(label)
    end = text.find("\n", start)
    if end == -1:
        end = len(text)
    return text[start:end].strip()


def _parse_years(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(match.group(1)) if match else None


def _parse_price(text: str) -> float | None:
    match = re.search(r"([\d][\d\s ]*)\s*EUR", text)
    if not match:
        return None
    digits = re.sub(r"[\s ]", "", match.group(1))
    return float(digits) if digits else None


def _extract_mode(text: str) -> str:
    lowered = text.lower()
    if "part-time" in lowered or "part time" in lowered:
        return "part_time"
    if "distance" in lowered:
        return "distance"
    return "full_time"


def _scrape_programme(page: Page, url: str, degree_level: str) -> ProgrammeDraft | None:
    page.goto(url, wait_until="domcontentloaded")
    article = page.locator("article").first
    if article.count() == 0:
        return None

    text = article.inner_text()
    if "Degree:" not in text and "Language of instruction" not in text:
        return None

    h1 = page.locator("h1").first
    name_en = h1.inner_text().strip() if h1.count() > 0 else ""
    # заголовки вида "Academic study programme - X" / "Professional study
    # programme – X" — оставляем только название после тире (дефис или
    # en-dash, встречаются оба варианта)
    name_en = re.sub(r"^.*?study programme\s*[-–—]\s*", "", name_en, flags=re.IGNORECASE).strip() or name_en

    slug = url.rstrip("/").rsplit("/", 1)[-1]
    duration_text = _extract_field(text, "Duration of studies:")
    language_text = _extract_field(text, "Language of instruction:")
    fee_text = _extract_field(text, "Tuition fee per year:")

    return ProgrammeDraft(
        slug=slug,
        name_en=name_en,
        degree_level=degree_level,
        language_of_instruction="en" if "english" in language_text.lower() else "lv",
        study_mode=_extract_mode(duration_text),
        city=UNIVERSITY.city,
        funding_type="paid",  # бюджетные места не публикуются на этих страницах
        tuition_fee_amount=_parse_price(fee_text),
        duration_years=_parse_years(duration_text),
        source_url=url,
    )


def scrape() -> tuple[UniversityDraft, list[ProgrammeDraft]]:
    programmes: list[ProgrammeDraft] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for degree_level, listing_url in LISTING_PAGES.items():
            for url in _discover_links(page, listing_url):
                programme = _scrape_programme(page, url, degree_level)
                if programme:
                    programmes.append(programme)

        browser.close()

    return UNIVERSITY, programmes
