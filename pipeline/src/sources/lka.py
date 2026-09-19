"""Latvijas Kultūras akadēmija (Latvian Academy of Culture) — английский
раздел сайта, /en/studies/study-programmes/{bachelor,master,doctoral}-studies/.

Структура найдена вручную в браузере 2026-09-19: три списка по уровням,
у каждой программы своя страница с блоком "Course Brief":

  Language of study: Latvian
  Full-time undergraduate programme
  Number of budget and paid study places: to be specified
  Tuition fee per year: to be specified
  Duration of studies: three years (6 semesters)
  Degree to be obtained / Place of study / ...

"to be specified" встречается и у мест, и у стоимости — сама академия
пока их не указала, поэтому budget_places и tuition_fee_amount
остаются пустыми, а не угадываются; funding_type='paid' — тот же
осторожный дефолт, что у остальных источников без данных о местах
(LKA — государственная академия, бюджетные места у неё есть).
"""

from __future__ import annotations

import re

from playwright.sync_api import Page, sync_playwright

from models import ProgrammeDraft, UniversityDraft

BASE_URL = "https://lka.edu.lv"

LISTINGS = {
    "bachelor": f"{BASE_URL}/en/studies/study-programmes/bachelor-studies/",
    "master": f"{BASE_URL}/en/studies/study-programmes/master-studies/",
    "doctoral": f"{BASE_URL}/en/studies/study-programmes/doctoral-studies/",
}

UNIVERSITY = UniversityDraft(
    slug="lka",
    name_lv="Latvijas Kultūras akadēmija",
    name_en="Latvian Academy of Culture",
    kind="public",
    city="riga",
    website_url=BASE_URL,
    source_url=f"{BASE_URL}/en/studies/study-programmes/",
)

NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}


def _facts(body_text: str) -> dict[str, str]:
    facts: dict[str, str] = {}
    for line in body_text.split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            if key and len(key) < 60 and key not in facts:
                facts[key] = value.strip()
    return facts


def _parse_years(text: str) -> float | None:
    semesters = re.search(r"(\d+)\s*semesters?", text, re.I)
    if semesters:
        return int(semesters.group(1)) / 2
    digits = re.search(r"(\d+(?:[.,]\d+)?)\s*years?", text, re.I)
    if digits:
        return float(digits.group(1).replace(",", "."))
    word = re.search(r"\b(one|two|three|four|five|six)\b(?:\s+and\s+a\s+half)?\s*years?", text, re.I)
    if word:
        base = NUMBER_WORDS[word.group(1).lower()]
        return base + (0.5 if "half" in word.group(0).lower() else 0)
    return None


def _study_mode(body_text: str) -> str:
    lowered = body_text.lower()
    if "part-time" in lowered:
        return "part_time"
    if "distance" in lowered:
        return "distance"
    return "full_time"


def _discover(page: Page) -> list[tuple[str, str]]:
    found: dict[str, tuple[str, str]] = {}
    for level, listing in LISTINGS.items():
        page.goto(listing, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        links = page.locator(f'a[href*="/study-programmes/{level}-studies/"]')
        for i in range(links.count()):
            href = links.nth(i).get_attribute("href") or ""
            slug = href.rstrip("/").rsplit("/", 1)[-1]
            if slug and slug != f"{level}-studies":
                found[f"{level}/{slug}"] = (level, href if href.startswith("http") else f"{BASE_URL}{href}")
    return [found[key] for key in sorted(found)]


def _scrape_programme(page: Page, level: str, url: str) -> ProgrammeDraft | None:
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(600)
    body = page.locator("body").inner_text()
    facts = _facts(body)

    duration_text = facts.get("Duration of studies", "")
    if not duration_text:
        return None

    h1 = page.locator("h1").first
    name = h1.inner_text().strip() if h1.count() > 0 else ""
    language = "en" if "english" in facts.get("Language of study", "").lower() else "lv"

    return ProgrammeDraft(
        slug=url.rstrip("/").rsplit("/", 1)[-1],
        name_en=name or None,
        degree_level=level,
        language_of_instruction=language,
        study_mode=_study_mode(body),
        city=UNIVERSITY.city,
        funding_type="paid",
        duration_years=_parse_years(duration_text),
        source_url=url,
    )


def scrape() -> tuple[UniversityDraft, list[ProgrammeDraft]]:
    programmes: list[ProgrammeDraft] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for level, url in _discover(page):
            programme = _scrape_programme(page, level, url)
            if programme is not None:
                programmes.append(programme)

        browser.close()

    return UNIVERSITY, programmes
