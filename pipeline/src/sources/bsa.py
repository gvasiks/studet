"""BSA (Baltijas Starptautiskā Akadēmija / Baltic International Academy) —
английский раздел сайта, бакалавриат и магистратура.

Структура найдена вручную в браузере 2026-09-13: Joomla-сайт, на странице
программы факты идут plain-текстом вида "Label: значение", разделённые
пустой строкой (нет стабильных CSS-классов для значений — как у Turība,
парсим по тексту между метками, не по селекторам).

Важная находка, а не просто пропуск данных: направление "Science of Law"
(и бакалавриат, и магистратура) **не аккредитовано** по решению комиссии
от 26.02.2026, приём не ведётся, решение оспаривается в суде. Вместо
обычного блока фактов на этих страницах — текст об этом. Такую программу
в каталог включать нельзя: наличие в базе будет читаться как "можно сюда
поступить", а это неправда прямо сейчас.

Проверяем автоматически — если на странице нет "Course Degree:", пропускаем
её, а не гадаем. Та же проверка заодно отсеивает минимум одну страницу
без юридических проблем (аккредитована), где просто не заполнен блок
фактов ("Management of Communication..." в магистратуре) — и это тоже
правильное поведение: нет структурированных фактов — нет записи.
"""

from __future__ import annotations

import re
from urllib.parse import urljoin

from playwright.sync_api import Page, sync_playwright

from models import ProgrammeDraft, UniversityDraft

LISTING_PAGES = {
    "bachelor": "https://bsa.edu.lv/index.php/en/bachelor-study-programmes.html",
    "master": "https://bsa.edu.lv/index.php/en/master-study-programmes.html",
}

UNIVERSITY = UniversityDraft(
    slug="bsa",
    name_lv="Baltijas Starptautiskā Akadēmija",
    name_en="Baltic International Academy",
    kind="private",
    city="riga",
    website_url="https://bsa.edu.lv",
    source_url=LISTING_PAGES["bachelor"],
)


def _discover_links(page: Page, listing_url: str) -> list[str]:
    page.goto(listing_url, wait_until="domcontentloaded")
    links = page.locator("a", has_text="Course details")
    hrefs = {
        urljoin(listing_url, links.nth(i).get_attribute("href") or "")
        for i in range(links.count())
    }
    return sorted(h for h in hrefs if h)


def _extract_field(text: str, label: str) -> str:
    idx = text.find(label)
    if idx == -1:
        return ""
    start = idx + len(label)
    end = text.find("\n\n", start)
    if end == -1:
        end = len(text)
    return text[start:end].strip()


def _parse_years(text: str) -> float | None:
    match = re.search(r"(\d+(?:[.,]\d+)?)", text)
    return float(match.group(1).replace(",", ".")) if match else None


def _extract_languages(text: str) -> list[str]:
    lowered = text.lower()
    languages = []
    if "english" in lowered:
        languages.append("en")
    if "latvian" in lowered:
        languages.append("lv")
    return languages or ["en"]


def _extract_mode(text: str) -> str:
    lowered = text.lower()
    if "full" in lowered:
        return "full_time"
    if "part" in lowered:
        return "part_time"
    if "distance" in lowered:
        return "distance"
    return "full_time"


def _scrape_programme(page: Page, url: str, degree_level: str) -> list[ProgrammeDraft]:
    page.goto(url, wait_until="domcontentloaded")
    body_text = page.locator("body").inner_text()

    if "Course Degree:" not in body_text:
        # Не аккредитовано (см. модуль docstring) или структура страницы
        # другая — пропускаем, не подставляем частичные данные.
        return []

    name_en = page.locator("h1").first.inner_text().strip()
    slug_base = url.rstrip("/").rsplit("/", 1)[-1].removesuffix(".html")

    duration_years = _parse_years(_extract_field(body_text, "Course Length:"))
    languages = _extract_languages(_extract_field(body_text, "Course Language(-s):"))
    mode = _extract_mode(_extract_field(body_text, "Study Mode(-s):"))

    multiple = len(languages) > 1
    return [
        ProgrammeDraft(
            slug=f"{slug_base}-{language}" if multiple else slug_base,
            name_en=name_en,
            degree_level=degree_level,
            language_of_instruction=language,
            study_mode=mode,
            city=UNIVERSITY.city,
            funding_type="paid",
            duration_years=duration_years,
            source_url=url,
        )
        for language in languages
    ]


def scrape() -> tuple[UniversityDraft, list[ProgrammeDraft]]:
    programmes: list[ProgrammeDraft] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for degree_level, listing_url in LISTING_PAGES.items():
            for url in _discover_links(page, listing_url):
                programmes.extend(_scrape_programme(page, url, degree_level))

        browser.close()

    return UNIVERSITY, programmes
