"""Latvijas Mākslas akadēmija (Art Academy of Latvia) — английский раздел,
специальности /en/studies/nozares/<slug>.

Структура найдена вручную в браузере 2026-09-19: у академии нет
страниц "программа за программой" — есть список специальностей
(painting, sculpture, fashion design...), и на странице каждой указано:

  DURATION OF STUDY: Bachelor 4 years / Master 2 years / Full-time
  DEGREE TO BE OBTAINED: Bachelor of Humanities in ... / Master of ...

Из одной страницы получается до двух программ каталога — бакалавриат
и магистратура; у специальностей с пометкой "(MA)" в названии есть
только магистратура. Слаг — "<специальность>-bachelor" / "-master".

Не вошло: докторантура (отдельная "Doctoral School", другой формат) и
международная магистратура SDSI — у неё свой сайт (sdsi.ma), не
lma.lv, поэтому сюда её не смешиваем.

Стоимость, бюджетные места и язык на этих страницах не указаны:
funding_type='paid' — осторожный дефолт без данных, а язык 'lv' —
предположение (академия преподаёт по-латышски; английский раздел сайта
описывает программы для иностранных абитуриентов, но не язык курса).
"""

from __future__ import annotations

import re

from playwright.sync_api import Page, sync_playwright

from models import ProgrammeDraft, UniversityDraft

BASE_URL = "https://www.lma.lv"
LISTING_URL = f"{BASE_URL}/en/studies/nozares"

UNIVERSITY = UniversityDraft(
    slug="lma",
    name_lv="Latvijas Mākslas akadēmija",
    name_en="Art Academy of Latvia",
    kind="public",
    city="riga",
    website_url=BASE_URL,
    source_url=LISTING_URL,
)

LEVELS = (("bachelor", r"Bachelor"), ("master", r"Master"))


def _discover(page: Page) -> dict[str, str]:
    page.goto(LISTING_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(2000)
    found: dict[str, str] = {}
    links = page.locator('a[href*="/studies/nozares/"]')
    for i in range(links.count()):
        href = links.nth(i).get_attribute("href") or ""
        title = links.nth(i).inner_text().strip()
        slug = href.rstrip("/").rsplit("/", 1)[-1]
        if slug and slug != "nozares" and title:
            found[slug] = title
    return found


def _durations(text: str) -> dict[str, float]:
    match = re.search(r"DURATION OF STUDY\s*\n+([^\n]+)", text, re.I)
    line = match.group(1) if match else ""
    result: dict[str, float] = {}
    for level, label in LEVELS:
        found = re.search(rf"{label}\s+(\d+(?:[.,]\d+)?)\s*years?", line, re.I)
        if found:
            result[level] = float(found.group(1).replace(",", "."))
    return result


def _scrape_specialisation(page: Page, slug: str, title: str) -> list[ProgrammeDraft]:
    url = f"{BASE_URL}/en/studies/nozares/{slug}"
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(700)
    body = page.locator("body").inner_text()
    durations = _durations(body)

    # "(MA)" в названии — только магистратура; в самом названии программы
    # эта пометка ни к чему, уровень — отдельное поле
    name = re.sub(r"\s*\((MA|BA)\)\s*$", "", title).strip()
    mode_line = re.search(r"DURATION OF STUDY\s*\n+([^\n]+)", body, re.I)
    part_time = bool(mode_line and "part-time" in mode_line.group(1).lower())

    return [
        ProgrammeDraft(
            slug=f"{slug}-{level}",
            name_en=name,
            degree_level=level,
            language_of_instruction="lv",
            study_mode="part_time" if part_time else "full_time",
            city=UNIVERSITY.city,
            funding_type="paid",
            duration_years=years,
            source_url=url,
        )
        for level, years in durations.items()
    ]


def scrape() -> tuple[UniversityDraft, list[ProgrammeDraft]]:
    programmes: list[ProgrammeDraft] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for slug, title in sorted(_discover(page).items()):
            programmes.extend(_scrape_specialisation(page, slug, title))

        browser.close()

    return UNIVERSITY, programmes
