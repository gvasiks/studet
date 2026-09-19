"""Rīgas Stradiņa universitāte (Rīga Stradiņš University) — английский
раздел сайта, страницы программ /en/study-programme/<slug>.

Структура найдена вручную в браузере 2026-09-19: списки программ —
/en/undergraduate-programmes, /en/postgraduate-programmes,
/en/doctoral-studies; каждая программа — отдельная страница с блоком
"Programme Fact File" (одинаковый на всех 58 страницах):

  Study direction / уровень ("Bachelor’s study programme", "First level
  study programme", "Second level study programme", "Professional
  Master’s study programme", "3. cikla (Doktora) study programme") /
  accredited until dd.mm.yyyy / Degree conferred / Language: X / ECTS /
  Study location / "N years" / расписание / Places: "N government
  subsidised", "N full fee" / "N EUR/year".

Не вошло: Graduate Medical Training (резидентура, /en/graduate-medical-
training) — там нет страниц /study-programme/, это отдельный формат.

Уровень берётся из строки карточки, а не из раздела списка: в разделе
"Undergraduate" лежат и колледжный уровень ("First level"), и
одноуровневые профессиональные программы ("Second level" — медицина,
стоматология, фармация; у ЛУ те же программы в каталоге как bachelor).

Стоимость ставится только когда на странице ровно одно значение
"N EUR/year": у части программ их два ("3800 EUR/year", "900
EUR/year") при двух типах мест ("full fee" и "paid*"), и какое к какому
относится — из текста не следует. Лучше пусто, чем угаданное (правило 6
CLAUDE.md всё равно требует подтверждения человеком).

Язык обучения — из строки "Language:"; у RSU каждый язык — отдельная
страница ("Dentistry" и "Dentistry (LV)"), так что дублей внутри одной
страницы не бывает.
"""

from __future__ import annotations

import re
from datetime import date

from playwright.sync_api import Page, sync_playwright

from models import ProgrammeDraft, UniversityDraft

BASE_URL = "https://www.rsu.lv"

LISTING_PAGES = [
    f"{BASE_URL}/en/undergraduate-programmes",
    f"{BASE_URL}/en/postgraduate-programmes",
    f"{BASE_URL}/en/doctoral-studies",
]

UNIVERSITY = UniversityDraft(
    slug="rsu",
    name_lv="Rīgas Stradiņa universitāte",
    name_en="Rīga Stradiņš University",
    kind="public",
    city="riga",
    website_url=BASE_URL,
    source_url=f"{BASE_URL}/en/study-programmes",
)

CITY_KEYS = {"rīga": "riga", "liepāja": "liepaja", "daugavpils": "daugavpils"}


def _degree_level(level_line: str) -> str:
    lowered = level_line.lower()
    if "cikla" in lowered or "phd" in lowered:
        return "doctoral"
    if "first level" in lowered:
        return "college"
    if "master" in lowered or "doctor's" in lowered:
        return "master"
    return "bachelor"


def _fact_file(body_text: str) -> str:
    start = body_text.find("Programme Fact File")
    if start < 0:
        return ""
    end = body_text.find("Director of Programme", start)
    return body_text[start : end if end > 0 else start + 1500]


def _find(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None


def _parse_duration(fact: str) -> float | None:
    raw = _find(r"(\d+(?:[.,]\d+)?)\s*years?", fact)
    return float(raw.replace(",", ".")) if raw else None


def _parse_accreditation(fact: str) -> date | None:
    match = re.search(r"accredited until (\d{2})\.(\d{2})\.(\d{4})", fact)
    if not match:
        return None
    day, month, year = (int(part) for part in match.groups())
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _parse_study_mode(fact: str) -> str:
    # расписание — между сроком обучения и "Places:"
    match = re.search(r"years?\s*\*?\s*\n(.*?)Places", fact, re.DOTALL)
    schedule = match.group(1).strip() if match else ""
    if "distance" in schedule.lower():
        return "distance"
    if not schedule or "weekdays" in schedule.lower():
        return "full_time"
    return "part_time"


def _parse_places(fact: str) -> tuple[str, int | None]:
    def count(label: str) -> int:
        match = re.search(rf"(\d+)\s+{label}", fact)
        return int(match.group(1)) if match else 0

    subsidised = count("government subsidised")
    paying = count("full fee") + count("paid")
    if subsidised and paying:
        return "both", subsidised
    if subsidised:
        return "budget", subsidised
    return "paid", None


def _parse_fee(fact: str) -> float | None:
    values = {int(v.replace(" ", "")) for v in re.findall(r"(\d[\d ]*\d|\d)\s*EUR/year", fact)}
    return float(values.pop()) if len(values) == 1 else None


def _discover_links(page: Page) -> list[str]:
    hrefs: dict[str, str] = {}
    for listing in LISTING_PAGES:
        page.goto(listing, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        links = page.locator('a[href*="/study-programme/"]')
        for i in range(links.count()):
            href = links.nth(i).get_attribute("href")
            if href:
                hrefs[href.rstrip("/").rsplit("/", 1)[-1].lower()] = f"{BASE_URL}{href}"
    return [hrefs[slug] for slug in sorted(hrefs)]


def _scrape_programme(page: Page, url: str) -> ProgrammeDraft | None:
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(600)
    fact = _fact_file(page.locator("body").inner_text())
    if not fact:
        return None

    language_text = (_find(r"Language:\s*([^\n]+)", fact) or "").lower()
    language = "en" if "english" in language_text else "lv"

    level_line = next(
        (line for line in fact.split("\n") if re.search(r"study programme|bachelor|master|cikla", line, re.I)),
        "",
    )
    location = (_find(r"Study location:\s*([^\n/]+)", fact) or "").strip().lower()
    funding_type, budget_places = _parse_places(fact)

    h1 = page.locator("h1").first
    name = h1.inner_text().strip() if h1.count() > 0 else ""
    # язык — отдельное поле; суффикс "(LV)" в названии дублировал бы его
    name = re.sub(r"\s*\((LV|EN)\)\s*$", "", name)

    return ProgrammeDraft(
        slug=url.rstrip("/").rsplit("/", 1)[-1].lower(),
        name_en=name or None,
        degree_level=_degree_level(level_line),
        language_of_instruction=language,
        study_mode=_parse_study_mode(fact),
        city=CITY_KEYS.get(location, UNIVERSITY.city),
        funding_type=funding_type,
        tuition_fee_amount=_parse_fee(fact),
        budget_places=budget_places,
        duration_years=_parse_duration(fact),
        accreditation_valid_until=_parse_accreditation(fact),
        source_url=url,
    )


def scrape() -> tuple[UniversityDraft, list[ProgrammeDraft]]:
    programmes: list[ProgrammeDraft] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for url in _discover_links(page):
            programme = _scrape_programme(page, url)
            if programme is not None:
                programmes.append(programme)

        browser.close()

    return UNIVERSITY, programmes
