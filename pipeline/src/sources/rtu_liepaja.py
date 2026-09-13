"""RTU (Rīgas Tehniskā universitāte) — programmas Liepājas akadēmijā,
latviešu sadaļa.

Третий источник специально ради разнородности города и финансирования
(проверить фильтр /programmes на данных, которые не только "Рига,
всё платно"):
- РТУ — государственный вуз (`kind: 'public'`, первая такая запись
  в каталоге), у части программ есть реальные бюджетные места;
- эти конкретные программы физически читаются в Лиепае, не в Риге.

Структура найдена вручную в браузере 2026-09-13: у РТУ единый реестр
программ (`/lv/studijas/visas-studiju-programmas/atvert/{code}`) с той
же вёрсткой карточки фактов, что и на английской странице кампуса —
`td:has(div.course_title2_container)` (метка) + `.course_contents2_container`
(значение).

Список программ — не обход реестра, а вручную отобранные три кода.
В фильтруемой таблице программ Лиепайской академии часть строк учится
ОДНОВРЕМЕННО в нескольких городах (Rīga, Rēzekne, Liepāja) с ОБЩЕЙ
квотой бюджетных мест на все города сразу — сноска на сайте это прямо
говорит. Чтобы не приписывать Лиепае долю чужой квоты, берём только
три программы, которые учатся ИСКЛЮЧИТЕЛЬНО в Лиепае: там число
бюджетных мест однозначно её собственное (проверено на карточке
каждой программы отдельно, поле "Budžeta vietu kvotu sadalījums").
"""

from __future__ import annotations

import re

from playwright.sync_api import Page, sync_playwright

from models import ProgrammeDraft, UniversityDraft

BASE_URL = "https://www.rtu.lv/lv/studijas/visas-studiju-programmas/atvert"

# code -> degree_level. Все три — бакалавриат, единственно в Лиепае.
PROGRAMMES = {
    "HBE": "bachelor",  # Eiropas valodu un kultūras studijas
    "HBM": "bachelor",  # Jauno mediju māksla un dizains
    "GCL": "bachelor",  # Logopēdija
}

UNIVERSITY = UniversityDraft(
    slug="rtu",
    name_lv="Rīgas Tehniskā universitāte",
    name_en="Riga Technical University",
    kind="public",
    city="riga",  # головной кампус; у этих программ city переопределён на liepaja
    website_url="https://www.rtu.lv",
    source_url="https://www.rtu.lv/lv/liepaja",
)


def _facts(page: Page) -> dict[str, str]:
    facts: dict[str, str] = {}
    rows = page.locator("td:has(div.course_title2_container)")
    for i in range(rows.count()):
        row = rows.nth(i)
        key = row.locator(".course_title2_container").first.inner_text().strip().lower()
        value = row.locator(".course_contents2_container").first.inner_text().strip()
        facts[key] = value
    return facts


def _parse_leading_int(text: str) -> int | None:
    match = re.match(r"(\d+)", text.strip())
    return int(match.group(1)) if match else None


def _parse_price(text: str) -> float | None:
    match = re.search(r"€\s*([\d\s ]+)", text)
    if not match:
        return None
    digits = re.sub(r"[\s ]", "", match.group(1))
    return float(digits) if digits else None


def _parse_years(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(match.group(1)) if match else None


def _extract_language(text: str) -> str:
    return "en" if "angļu" in text.lower() else "lv"


def _extract_mode(text: str) -> str:
    lowered = text.lower()
    if "nepilna" in lowered:
        return "part_time"
    return "full_time"


def _scrape_programme(page: Page, code: str, degree_level: str) -> ProgrammeDraft:
    url = f"{BASE_URL}/{code}?department=0L000&type=P"
    page.goto(url, wait_until="domcontentloaded")

    name_lv = page.locator("h1").first.inner_text().strip()
    facts = _facts(page)

    return ProgrammeDraft(
        slug=code.lower(),
        name_lv=name_lv,
        degree_level=degree_level,
        language_of_instruction=_extract_language(facts.get("īstenošanas valoda", "")),
        study_mode=_extract_mode(facts.get("īstenošanas forma", "")),
        city="liepaja",
        funding_type="both",  # есть и бюджетные, и платные места — см. budget_places
        tuition_fee_amount=_parse_price(facts.get("maksa gadā", "")),
        budget_places=_parse_leading_int(facts.get("budžeta vietu kvotu sadalījums studiju uzsākšanai", "")),
        duration_years=_parse_years(facts.get("studiju ilgums", "")),
        source_url=url,
    )


def scrape() -> tuple[UniversityDraft, list[ProgrammeDraft]]:
    programmes: list[ProgrammeDraft] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for code, degree_level in PROGRAMMES.items():
            programmes.append(_scrape_programme(page, code, degree_level))

        browser.close()

    return UNIVERSITY, programmes
