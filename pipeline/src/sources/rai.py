"""Rīgas Aeronavigācijas institūts (RAI) — частный вуз, сайт rai.lv.

Структура найдена вручную в браузере 2026-09-19: список программ на
/news/studijas/studiju-virziens/ (8 ссылок), у каждой программы своя
страница с блоком фактов:

  Iegūstamais grāds: Profesionālais Bakalaura grāds ...   (или Maģistra)
  Studiju ilgums: 4 - 4.5 gadi
  Programmas akreditācijas termiņš: 2028.g. 17.novembris

Язык: страница приёма 2026/2027 говорит "Apmācības valodas: latviešu (LV)
un angļu (EN)" для всех аккредитованных программ, а в таблице цен у
каждой программы есть отдельный тариф "Studijas angļu valodā". Поэтому
каждая программа пишется дважды — 'lv' и 'en' (так же, как у RISEBA).

Стоимость и бюджетные места здесь НЕ разбираются: таблица цен на
/news/uznemsana/studiju-maksa/ смешивает полный и неполный день, два
языка, сноски с исключениями и скидки для выпускников RAI — вытащить
из неё однозначную цифру нельзя без риска подставить чужую. Это и так
поле, которое подтверждает человек. funding_type='paid' — RAI частный,
бюджетных мест нет.

Срок в формате "4 - 4.5 gadi" — берётся верхняя граница: для оценки
стоимости обучения ошибиться в меньшую сторону хуже.
"""

from __future__ import annotations

import re
from datetime import date

from playwright.sync_api import Page, sync_playwright

from models import ProgrammeDraft, UniversityDraft

BASE_URL = "https://rai.lv"
LISTING_URL = f"{BASE_URL}/news/studijas/studiju-virziens/"

UNIVERSITY = UniversityDraft(
    slug="rai",
    name_lv="Rīgas Aeronavigācijas institūts",
    name_en="Riga Aeronautical Institute",
    kind="private",
    city="riga",
    website_url=BASE_URL,
    source_url=LISTING_URL,
)

MONTHS = {
    "janvāris": 1, "februāris": 2, "marts": 3, "aprīlis": 4, "maijs": 5, "jūnijs": 6,
    "jūlijs": 7, "augusts": 8, "septembris": 9, "oktobris": 10, "novembris": 11, "decembris": 12,
}
LANGUAGES = ("lv", "en")


def _facts(body_text: str) -> dict[str, str]:
    facts: dict[str, str] = {}
    for line in body_text.split("\n"):
        key, sep, value = line.partition(":")
        key = key.strip()
        if sep and key and len(key) < 50 and key not in facts:
            facts[key] = value.strip()
    return facts


def _max_years(text: str) -> float | None:
    numbers = re.findall(r"\d+(?:[.,]\d+)?", text)
    return max(float(n.replace(",", ".")) for n in numbers) if numbers else None


def _accreditation_date(text: str) -> date | None:
    found = re.search(r"(\d{4})\.\s*g\.\s*(\d{1,2})\.\s*([a-zāēīūčšžļņķģ]+)", text.lower())
    if not found or found.group(3) not in MONTHS:
        return None
    return date(int(found.group(1)), MONTHS[found.group(3)], int(found.group(2)))


def _discover(page: Page) -> dict[str, str]:
    page.goto(LISTING_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(1000)
    found: dict[str, str] = {}
    links = page.locator('a[href*="/studiju-virziens/"]')
    for i in range(links.count()):
        href = links.nth(i).get_attribute("href") or ""
        # ссылки на направления ("mehanika/") ведут на один уровень выше —
        # программа лежит на глубине направление/КОД
        parts = [part for part in href.split("/") if part]
        if "studiju-virziens" not in parts:
            continue
        depth = len(parts) - parts.index("studiju-virziens") - 1
        if depth == 2:
            found[parts[-1]] = href if href.startswith("http") else f"{BASE_URL}{href}"
    return found


def _scrape_programme(page: Page, code: str, url: str) -> list[ProgrammeDraft]:
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(600)
    facts = _facts(page.locator("body").inner_text())

    degree = facts.get("Iegūstamais grāds", "")
    if not degree:
        return []
    level = "master" if "maģistra" in degree.lower() else "bachelor"

    # у сайта нет h1 и пустой <title>: название программы — первый h2
    # (следующие h2 — "Kategorijas", "Par mums")
    heading = page.locator("h2").first
    name = heading.inner_text().strip() if heading.count() > 0 else ""

    return [
        ProgrammeDraft(
            slug=f"{code.lower()}-{language}",
            name_lv=name or None,
            degree_level=level,
            language_of_instruction=language,
            study_mode="full_time",
            city=UNIVERSITY.city,
            funding_type="paid",
            duration_years=_max_years(facts.get("Studiju ilgums", "")),
            accreditation_valid_until=_accreditation_date(facts.get("Programmas akreditācijas termiņš", "")),
            source_url=url,
        )
        for language in LANGUAGES
    ]


def scrape() -> tuple[UniversityDraft, list[ProgrammeDraft]]:
    programmes: list[ProgrammeDraft] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for code, url in sorted(_discover(page).items()):
            programmes.extend(_scrape_programme(page, code, url))

        browser.close()

    return UNIVERSITY, programmes
