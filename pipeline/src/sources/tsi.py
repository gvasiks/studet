"""TSI (Transport and Telecommunication Institute) — английский раздел.

Структура найдена вручную в браузере 2026-09-13: сайт на Elementor +
JetEngine, у карточек листинга есть стабильный класс
(`.jet-listing-grid__item`, `data-url` со ссылкой на карточку программы),
но сама карточка программы вёрстана из авто-хэшированных Elementor-классов
(`elementor-element-41801960` и т.п.) — они меняются от виджета к виджету
и не переиспользуются между страницами. Разбирать их CSS-селекторами
ненадёжно, поэтому здесь (в отличие от Turība/RISEBA/RTU) фактовый блок
разбирается по тексту страницы между известными заголовками.

Раздел "TUITION & STUDY FORMATS" сознательно не парсим вообще: на разных
страницах он по-разному размечен (на одной — три блока FULL-TIME/PART-TIME/
BLENDED LEARNING, на другой — тот же заголовок FULL-TIME повторяется трижды
с разными ценами и длительностями, то есть на сайте отдельные форматы
обучения промаркированы одинаково — это ошибка разметки TSI, не наша).
Настолько ненадёжный кусок лучше не трогать, чем разобрать неверно.
Стоимость остаётся пустой, как и у Турибы.
"""

from __future__ import annotations

import re

from playwright.sync_api import Page, sync_playwright

from models import ProgrammeDraft, UniversityDraft

LISTING_URL = "https://tsi.lv/study_programmes/"

UNIVERSITY = UniversityDraft(
    slug="tsi",
    name_lv="Transporta un sakaru institūts",
    name_en="Transport and Telecommunication Institute",
    kind="private",
    city="riga",
    website_url="https://tsi.lv",
    source_url=LISTING_URL,
)


def _map_level(text: str) -> str | None:
    lowered = text.lower()
    if "bachelor" in lowered:
        return "bachelor"
    if "master" in lowered:
        return "master"
    if "phd" in lowered:
        return "doctoral"
    return None


def _discover_programmes(page: Page) -> list[tuple[str, str]]:
    page.goto(LISTING_URL, wait_until="domcontentloaded")
    cards = page.locator(".jet-listing-grid__item")
    results: list[tuple[str, str]] = []

    for i in range(cards.count()):
        card = cards.nth(i)
        wrap = card.locator(".jet-engine-listing-overlay-wrap").first
        if wrap.count() == 0:
            continue
        url = wrap.get_attribute("data-url")

        badge = card.locator(".elementor-heading-title").first
        level = _map_level(badge.inner_text().strip()) if badge.count() > 0 else None

        if url and level:
            results.append((url, level))

    return results


def _extract_between(text: str, start: str, ends: list[str]) -> str:
    start_index = text.find(start)
    if start_index == -1:
        return ""
    from_index = start_index + len(start)
    end_index = len(text)
    for marker in ends:
        idx = text.find(marker, from_index)
        if idx != -1:
            end_index = min(end_index, idx)
    return text[from_index:end_index].strip()


def _extract_languages(text: str) -> list[str]:
    lowered = text.lower()
    languages = []
    if "english" in lowered:
        languages.append("en")
    if "latvian" in lowered:
        languages.append("lv")
    return languages or ["en"]


def _first_mode_and_duration(study_form_text: str) -> tuple[str, float | None]:
    first_line = study_form_text.split("\n")[0] if study_form_text else ""
    lowered = first_line.lower()
    if "part-time" in lowered:
        mode = "part_time"
    elif "distance" in lowered or "blended" in lowered:
        mode = "distance"
    else:
        mode = "full_time"

    match = re.search(r"(\d+(?:\.\d+)?)", first_line)
    duration = float(match.group(1)) if match else None
    return mode, duration


def _scrape_programme(page: Page, url: str, degree_level: str) -> list[ProgrammeDraft]:
    page.goto(url, wait_until="domcontentloaded")
    name_en = page.locator("h1").first.inner_text().strip()
    body_text = page.locator("body").inner_text()

    language_block = _extract_between(body_text, "LANGUAGE", ["KEY DATA"])
    study_form_block = _extract_between(body_text, "STUDY FORM & DURATION", ["LANGUAGE"])
    mode, duration_years = _first_mode_and_duration(study_form_block)

    slug_base = url.rstrip("/").rsplit("/", 1)[-1]
    languages = _extract_languages(language_block)
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

        listed = _discover_programmes(page)
        for url, degree_level in listed:
            programmes.extend(_scrape_programme(page, url, degree_level))

        browser.close()

    return UNIVERSITY, programmes
