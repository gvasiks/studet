"""RISEBA — английский раздел сайта, бакалаврские программы.

Структура проверена вручную в браузере 2026-09-13:
- каждая программа — своя карточка на `.general-information li.list-group-item`
  вида `<div class="key">Label:</div><div class="value">...</div>`
- один "Type"/"Language" на странице может описывать НЕСКОЛЬКО вариантов
  обучения сразу (например, "English (distance learning), Latvian
  (part-time, distance learning)") с разной ценой — в отличие от Турибы,
  где одна страница = одна программа = один язык/форма. Источник правды
  для вариантов — секция "Tuition fee per year", там язык+форма+цена
  расписаны построчно.

Список программ захардкожен, а не собран с главной страницы: виджет на
главной для секций Bachelor's/Master's/Doctoral ссылается на ОДИН и тот
же URL независимо от уровня (проверено — это баг разметки сайта RISEBA,
не наша ошибка). Обходить его для несуществующего пока Master's/Doctoral
не стоит; бакалаврские 6 ссылок проверены вручную по отдельности.
Ограничиваемся бакалавриатом в этом источнике.

Стоимость и дедлайн — как и у Турибы, не единственный факт на программу
здесь (несколько тарифов сразу), поэтому verified_at всё равно остаётся
null: правило 6 CLAUDE.md требует подтверждения человеком независимо от
того, насколько чисто она распарсилась.
"""

from __future__ import annotations

import re

from playwright.sync_api import Page, sync_playwright

from models import ProgrammeDraft, UniversityDraft

BASE_URL = "https://riseba.lv/en"

BACHELOR_PROGRAMMES = {
    "business-management-3": "Business Management",
    "european-business-studies": "European Business Studies",
    "audiovisual-arts-and-media-arts": "Audiovisual Arts and Media Arts",
    "architecture": "Architecture",
    "public-relations-and-advertising-management": "Public Relations and Advertising Management",
    "business-psychology": "Business Psychology",
}

UNIVERSITY = UniversityDraft(
    slug="riseba",
    name_lv="RISEBA",
    name_en="RISEBA University of Applied Sciences",
    kind="private",
    city="riga",
    website_url="https://riseba.lv",
    source_url=BASE_URL,
)


def _general_info(page: Page) -> dict[str, str]:
    info: dict[str, str] = {}
    rows = page.locator(".general-information li.list-group-item")
    for i in range(rows.count()):
        row = rows.nth(i)
        key = row.locator(".key").first.inner_text().strip().rstrip(":").lower()
        value = row.locator(".value").first.inner_text().strip()
        info[key] = value
    return info


def _extract_mode(text: str) -> str | None:
    lowered = text.lower()
    if "distance" in lowered:
        return "distance"
    if "part-time" in lowered or "part time" in lowered:
        return "part_time"
    if "full-time" in lowered or "full time" in lowered:
        return "full_time"
    return None


def _extract_language(text: str) -> str | None:
    lowered = text.lower()
    if "english" in lowered:
        return "en"
    if "latvian" in lowered:
        return "lv"
    return None


def _parse_eu_tuition_variants(fee_text: str) -> list[tuple[str, str, float]]:
    """Возвращает (mode, language, eur_per_year) для тарифа ЕС/Латвия —
    он касается местной аудитории (А), а не иностранной (Б, выпуск 4)."""
    variants: list[tuple[str, str, float]] = []
    in_eu_section = False
    for raw_line in fee_text.split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        lowered = line.lower()
        if lowered.startswith("citizens and permanent residents"):
            in_eu_section = True
            continue
        if lowered.startswith("other countries"):
            break
        if not in_eu_section:
            continue

        match = re.match(r"([\d,.]+)\s*EUR\s*\(([^)]+)\)", line, re.IGNORECASE)
        if not match:
            continue

        amount = float(match.group(1).replace(",", ""))
        descriptor = match.group(2)
        mode = _extract_mode(descriptor)
        language = _extract_language(descriptor)
        if mode and language:
            variants.append((mode, language, amount))

    return variants


def _parse_years(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(match.group(1)) if match else None


def _scrape_programme(page: Page, slug: str) -> list[ProgrammeDraft]:
    url = f"{BASE_URL}/program/{slug}/"
    page.goto(url, wait_until="domcontentloaded")

    name_en = page.locator("h1").first.inner_text().strip()
    info = _general_info(page)
    duration_years = _parse_years(info.get("duration", ""))

    variants = _parse_eu_tuition_variants(info.get("tuition fee per year", ""))
    if not variants:
        # Не удалось разобрать тарифы построчно — берём язык/форму верхнего
        # уровня без цены, лучше неполная запись, чем никакой.
        mode = _extract_mode(info.get("type", "")) or "full_time"
        language = _extract_language(info.get("language", "")) or "en"
        variants = [(mode, language, None)]

    multiple = len(variants) > 1
    programmes = []
    for mode, language, fee in variants:
        variant_slug = f"{slug}-{mode}-{language}" if multiple else slug
        programmes.append(
            ProgrammeDraft(
                slug=variant_slug,
                name_en=name_en,
                degree_level="bachelor",
                language_of_instruction=language,
                study_mode=mode,
                city=UNIVERSITY.city,
                funding_type="paid",
                tuition_fee_amount=fee,
                duration_years=duration_years,
                source_url=url,
            )
        )
    return programmes


def scrape() -> tuple[UniversityDraft, list[ProgrammeDraft]]:
    programmes: list[ProgrammeDraft] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for slug in BACHELOR_PROGRAMMES:
            programmes.extend(_scrape_programme(page, slug))

        browser.close()

    return UNIVERSITY, programmes
