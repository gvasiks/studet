"""Rīgas Ziemeļvalstu augstskola (Riga Nordic University, RNU) —
английский раздел.

Участвует в единой государственной подаче (vienotauznemsana.lv называет
её в числе восьми вузов), но по структуре сайта и полному отсутствию
упоминания бюджетных мест на странице оплаты — скорее частный вуз с
доступом к общей платформе подачи, как и ЭКА, а не государственный в
смысле собственного финансирования. `kind='private'`, как у ЭКА;
это предположение по косвенным признакам, не факт с сайта — стоит
перепроверить отдельно, если понадобится точная классификация.

Структура найдена вручную в браузере 2026-09-13: список программ —
на /studies/study-programs/, ссылки содержат уровень прямо в пути
(/bachelor/, /masters-degree/, /short-cycle/). Факты на странице
программы — свободный текст "Label: значение" (как у LU/BSA), без
цены — цена только на отдельной странице /admission/tuition-fees/,
и это плоский тариф по категории (2700 EUR — бакалавриат, короткий
цикл и 2-летняя магистратура; 3300 EUR — ускоренная магистратура
1,1 года), не за программу. Опубликовано открыто — не подтверждено
человеком (правило 6), поэтому verified_at всё равно не выставляем.
"""

from __future__ import annotations

import re
from urllib.parse import urljoin

from playwright.sync_api import Page, sync_playwright

from models import ProgrammeDraft, UniversityDraft

LISTING_URL = "https://rnu.lv/en/studies/study-programs/"

UNIVERSITY = UniversityDraft(
    slug="rnu",
    name_lv="Rīgas Ziemeļvalstu augstskola",
    name_en="Riga Nordic University",
    kind="private",
    city="riga",
    website_url="https://rnu.lv",
    source_url=LISTING_URL,
)

LEVEL_BY_PATH = {
    "/bachelor/": "bachelor",
    "/masters-degree/": "master",
    "/short-cycle/": "college",
}

CATEGORY_INDEX_PATHS = set(LEVEL_BY_PATH)


def _level_for(url: str) -> str | None:
    for path, level in LEVEL_BY_PATH.items():
        if path in url:
            return level
    return None


def _discover_links(page: Page) -> list[tuple[str, str]]:
    page.goto(LISTING_URL, wait_until="domcontentloaded")
    links = page.locator('a[href*="/study-programs/"]')
    hrefs = {urljoin(LISTING_URL, links.nth(i).get_attribute("href") or "") for i in range(links.count())}

    results = []
    for href in hrefs:
        if any(href.rstrip("/").endswith(p.rstrip("/")) for p in CATEGORY_INDEX_PATHS):
            continue  # это страница-категория (/bachelor/ и т.п.), не программа
        level = _level_for(href)
        if level:
            results.append((href, level))
    return results


def _extract_field(text: str, *labels: str) -> str:
    # У RNU подписи не унифицированы между страницами программ —
    # "Duration of Studies:" на одной, "Duration of study:" на другой —
    # ищем без учёта регистра и пробуем несколько вариантов подряд.
    lowered = text.lower()
    for label in labels:
        idx = lowered.find(label.lower())
        if idx == -1:
            continue
        start = idx + len(label)
        end = text.find("\n", start)
        if end == -1:
            end = len(text)
        return text[start:end].strip()
    return ""


def _parse_years(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(match.group(1)) if match else None


def _fee_for(degree_level: str, duration_years: float | None) -> float:
    # см. docstring — плоский тариф по категории, не за программу
    if degree_level == "master" and duration_years is not None and duration_years < 2:
        return 3300.0
    return 2700.0


def _scrape_programme(page: Page, url: str, degree_level: str) -> ProgrammeDraft | None:
    page.goto(url, wait_until="domcontentloaded")
    main = page.locator("main").first
    if main.count() == 0:
        return None

    text = main.inner_text()
    duration_text = _extract_field(text, "Duration of Studies:", "Duration of study:")
    if not duration_text:
        return None

    h1 = page.locator("h1").first
    name_en = h1.inner_text().strip() if h1.count() > 0 else ""
    # "Business Administration" существует и в бакалавриате, и в
    # магистратуре с одинаковым последним сегментом URL — суффикс
    # уровня всегда, не только при обнаруженной коллизии.
    slug = f"{url.rstrip('/').rsplit('/', 1)[-1]}-{degree_level}"

    language_text = _extract_field(text, "Language:")
    duration_years = _parse_years(duration_text)

    return ProgrammeDraft(
        slug=slug,
        name_en=name_en,
        degree_level=degree_level,
        language_of_instruction="en" if "english" in language_text.lower() else "lv",
        study_mode="full_time",
        city=UNIVERSITY.city,
        funding_type="paid",
        tuition_fee_amount=_fee_for(degree_level, duration_years),
        duration_years=duration_years,
        source_url=url,
    )


def scrape() -> tuple[UniversityDraft, list[ProgrammeDraft]]:
    programmes: list[ProgrammeDraft] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for url, degree_level in _discover_links(page):
            programme = _scrape_programme(page, url, degree_level)
            if programme:
                programmes.append(programme)

        browser.close()

    return UNIVERSITY, programmes
