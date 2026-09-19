"""Lutera Akadēmija (Lutheran Academy, Rīga) — luteraakademija.lv.

Структура найдена вручную в браузере 2026-09-19: страница
?ct=studijas содержит нумерованный список "1) Profesionālā bakalaura
studiju programma “TEOLOĢIJA”" с таблицей фактов:

  Grāds / Kvalifikācija / Akreditācija: Studiju virziens akreditēts līdz 08.02.2030.
  Ilgums: 4 gadi        Studiju veids: Pilna laika
  Mācību valoda: latviešu (LV)
  Mācību/studiju maksa: 1200 EUR/gadā (2026./2027.)

Пункт 2 там — "Atvērtās akadēmijas mūžizglītības programma" (курсы
непрерывного образования, не степень) — в каталог не берётся: берутся
только пункты со словами bakalaura/maģistra/doktora в названии.

Дата "akreditēts līdz" относится к studiju virziens (направлению), а не
к самой программе — это записывается как accreditation_valid_until с
оговоркой в комментарии, потому что другого срока на странице нет; поле
и так подтверждает человек.
"""

from __future__ import annotations

import re
from datetime import date

from playwright.sync_api import sync_playwright

from models import ProgrammeDraft, UniversityDraft

BASE_URL = "https://luteraakademija.lv"
STUDIES_URL = f"{BASE_URL}/?ct=studijas"

UNIVERSITY = UniversityDraft(
    slug="lutera",
    name_lv="Lutera Akadēmija",
    name_en="Luther Academy",
    kind="private",
    city="riga",
    website_url=BASE_URL,
    source_url=STUDIES_URL,
)

LEVELS = (("bakalaura", "bachelor"), ("maģistra", "master"), ("doktora", "doctoral"))
LANGUAGES = {"latviešu": "lv", "angļu": "en"}


def _slugify(text: str) -> str:
    table = str.maketrans("āčēģīķļņšūž", "acegiklnsuz")
    return re.sub(r"[^a-z0-9]+", "-", text.lower().translate(table)).strip("-")


def _sections(text: str) -> list[str]:
    """Куски текста, каждый начинается с "N) ...studiju programma “X”"."""
    parts = re.split(r"(?m)^\s*\d+\)\s+", text)
    return parts[1:]


def _parse_section(section: str) -> ProgrammeDraft | None:
    title = re.match(r"([^\n“]*)[“\"]([^”\"\n]+)[”\"]", section)
    if not title:
        return None
    kind_text = title.group(1).lower()
    level = next((code for word, code in LEVELS if word in kind_text), None)
    if level is None or "studiju programma" not in kind_text:
        return None
    name = title.group(2).strip().capitalize()

    years = re.search(r"Ilgums\s*(\d+(?:[.,]\d+)?)\s*gad", section)
    fee = re.search(r"Mācību/studiju maksa\s*(\d[\d ]*)\s*EUR\s*/\s*gad", section)
    language = re.search(r"Mācību valoda\s*(\w+)", section)
    accreditation = re.search(r"akreditēts līdz\s*(\d{2})\.(\d{2})\.(\d{4})", section)

    return ProgrammeDraft(
        slug=f"{_slugify(name)}-{level}",
        name_lv=name,
        degree_level=level,
        language_of_instruction=LANGUAGES.get(language.group(1).lower(), "lv") if language else "lv",
        study_mode="part_time" if re.search(r"Nepilna laika", section) else "full_time",
        city=UNIVERSITY.city,
        funding_type="paid",
        tuition_fee_amount=float(fee.group(1).replace(" ", "")) if fee else None,
        duration_years=float(years.group(1).replace(",", ".")) if years else None,
        accreditation_valid_until=(
            date(int(accreditation.group(3)), int(accreditation.group(2)), int(accreditation.group(1)))
            if accreditation
            else None
        ),
        source_url=STUDIES_URL,
    )


def scrape() -> tuple[UniversityDraft, list[ProgrammeDraft]]:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(STUDIES_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        text = page.locator("body").inner_text()
        browser.close()

    programmes = [programme for section in _sections(text) if (programme := _parse_section(section))]
    return UNIVERSITY, programmes
