"""LU (Latvijas Universitāte) — английский раздел сайта.

ЛУ огромен: только на бакалавриате около десятка факультетов, в одном
факультете экономики и социальных наук — уже 17 программ. Полный обход
всего университета — отдельная задача на будущее (как и с частными
вузами, "два вуза точно лучше восьми приблизительно" — CLAUDE.md).
В этом источнике — один факультет, Faculty of Economics and Social
Sciences, целиком, оба уровня LV/EN там, где они есть отдельными
программами. Он же, похоже, содержит ту самую программу "Economics" из
примера расчёта конкурсного балла в docs/PLAN.md (математика ×6,5) —
но саму формулу сюда не тащим, это отдельная задача с утверждённым PDF
(правило 6 CLAUDE.md), здесь только факты каталога.

Структура найдена вручную в браузере 2026-09-13: TYPO3-сайт, факты —
один блок `.ce-bodytext` с парами "Label: значение" через перенос
строки (не `<br>`-разделённые абзацы, как у BSA — здесь одна строка
на поле). Формат числа бюджетных мест и цены отличается от программы
к программе (иногда "Full time state-funded study places", иногда
просто "State-funded study places" для программ без очной/заочной
развилки) — ищем по общей подстроке "state-funded study places",
не по точной фразе целиком.
"""

from __future__ import annotations

import re
from urllib.parse import urljoin

from playwright.sync_api import Page, sync_playwright

from models import ProgrammeDraft, UniversityDraft

FACULTY_URL = (
    "https://www.lu.lv/en/studies/study-programmes-1/bachelors-study-programmes/"
    "faculty-of-economics-and-social-sciences/"
)

UNIVERSITY = UniversityDraft(
    slug="lu",
    name_lv="Latvijas Universitāte",
    name_en="University of Latvia",
    kind="public",
    city="riga",
    website_url="https://www.lu.lv",
    source_url=FACULTY_URL,
)


def _discover_links(page: Page) -> list[tuple[str, str]]:
    page.goto(FACULTY_URL, wait_until="domcontentloaded")
    links = page.locator("main a")

    seen: dict[str, str] = {}
    for i in range(links.count()):
        href = links.nth(i).get_attribute("href")
        text = links.nth(i).inner_text().strip()
        if not href or "/bachelors-study-programmes/" not in href:
            continue
        href = urljoin(FACULTY_URL, href)
        if href.rstrip("/") == FACULTY_URL.rstrip("/"):
            continue
        seen.setdefault(href, text)

    return list(seen.items())


def _extract_field(text: str, label: str) -> str:
    idx = text.find(label)
    if idx == -1:
        return ""
    start = idx + len(label)
    end = text.find("\n", start)
    if end == -1:
        end = len(text)
    return text[start:end].strip()


def _extract_mode(text: str) -> str:
    lowered = text.lower()
    if "full-time" in lowered or "full time" in lowered:
        return "full_time"
    if "part-time" in lowered or "part time" in lowered:
        return "part_time"
    return "full_time"


def _parse_duration_years(text: str) -> float | None:
    match = re.search(r"(\d+)\s*semester", text.lower())
    if match:
        return int(match.group(1)) / 2
    match = re.search(r"(\d+(?:\.\d+)?)\s*year", text.lower())
    return float(match.group(1)) if match else None


def _parse_budget_places(text: str) -> int | None:
    match = re.search(r"state-funded study places\D*(\d+)", text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def _parse_price(text: str) -> float | None:
    match = re.search(r"([\d][\d\s ]*)\s*EUR", text)
    if not match:
        return None
    digits = re.sub(r"[\s ]", "", match.group(1))
    return float(digits) if digits else None


def _scrape_programme(page: Page, url: str, link_text: str) -> ProgrammeDraft | None:
    page.goto(url, wait_until="domcontentloaded")
    body = page.locator(".ce-bodytext").first
    if body.count() == 0:
        return None

    text = body.inner_text()
    if "Programme level" not in text:
        return None

    slug = url.rstrip("/").rsplit("/", 1)[-1]
    # "(LV)"/"(EN)" в заголовке — язык и так отдельное поле; убираем из
    # читаемого названия, но не из slug (иначе lv/en варианты столкнутся)
    name_en = re.sub(r"\s*\((LV|EN)\)\s*$", "", link_text).strip()

    language_text = _extract_field(text, "Language of instruction:")
    duration_text = _extract_field(text, "Study form and duration:")
    places_text = _extract_field(text, "Number of study places for admission")
    fee_text = _extract_field(text, "Tuition fee per year")

    budget_places = _parse_budget_places(places_text)

    return ProgrammeDraft(
        slug=slug,
        name_en=name_en,
        degree_level="bachelor",
        language_of_instruction="en" if "english" in language_text.lower() else "lv",
        study_mode=_extract_mode(duration_text),
        city=UNIVERSITY.city,
        funding_type="both" if budget_places else "paid",
        tuition_fee_amount=_parse_price(fee_text),
        budget_places=budget_places,
        duration_years=_parse_duration_years(duration_text),
        source_url=url,
    )


def scrape() -> tuple[UniversityDraft, list[ProgrammeDraft]]:
    programmes: list[ProgrammeDraft] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for url, link_text in _discover_links(page):
            programme = _scrape_programme(page, url, link_text)
            if programme:
                programmes.append(programme)

        browser.close()

    return UNIVERSITY, programmes
