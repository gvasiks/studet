"""Eiropas Kristīgā akadēmija (EKrA, ранее Latvijas Kristīgā akadēmija;
Jūrmala) — kra.lv.

Структура найдена вручную в браузере 2026-09-19: у академии шесть
программ, перечисленных списком на странице приёма
/studiju-programmas/studentu-uznemsana/, плюс страницы pamatstudijas и
magistra-studijas с описаниями свободным текстом. Отдельных страниц по
каждой программе и таблицы фактов нет, поэтому:

- список программ задан словарём KNOWN_PROGRAMMES, а сборщик ПРОВЕРЯЕТ,
  что название каждой всё ещё есть на странице приёма (иначе программу
  сняли или переименовали — падаем, а не пишем устаревшее);
- стоимость берётся регуляркой из блока "Studiju maksa" только если у
  программы ОДНА цифра. "Karitatīvais sociālais darbs" (магистратура)
  имеет две (2200 и 2100 для выпускников EKrA), а магистратура "Bībeles
  māksla" — только цену для выпускников; там поле остаётся пустым.

Срок обучения указан на страницах программ только для части программ
(Bībeles māksla бакалавр — 4 года; обе магистерские профессиональные —
2 года очно); для остальных он не публикуется в явном виде — None.
Язык 'lv' — предположение (в тексте языка нет; сайт и приём на
латышском). Сайт-источник называет академию и "Latvijas Kristīgā
akadēmija" (старое название), и "Eiropas Kristīgā akadēmija" — это одно
юрлицо (рег. № 2994801398).
"""

from __future__ import annotations

import re

from playwright.sync_api import sync_playwright

from models import ProgrammeDraft, UniversityDraft

BASE_URL = "https://kra.lv"
ADMISSIONS_URL = f"{BASE_URL}/studiju-programmas/studentu-uznemsana/"

UNIVERSITY = UniversityDraft(
    slug="ekra",
    name_lv="Eiropas Kristīgā akadēmija",
    name_en="European Christian Academy",
    kind="private",
    city="jurmala",
    website_url=BASE_URL,
    source_url=ADMISSIONS_URL,
)

# (slug, name_lv, level, years, как название выглядит в списке приёма,
#  regex стоимости или None). Регулярка стоимости должна давать одинаковое
#  число во всех совпадениях, иначе цена не записывается.
Q = "[“\"]"
QE = "[”\"]"
KNOWN_PROGRAMMES = [
    (
        "biblijas-maksla-bachelor", "Bībeles māksla", "bachelor", 4.0,
        r"akadēmiskā bakalaura\) studiju programma „Bībeles māksla”",
        r"Bakalaura studijas\s*[–-]\s*(\d+)\s*EUR gadā",
    ),
    (
        "biblijas-maksla-master", "Bībeles māksla", "master", None,
        r"akadēmiskā maģistra\) studiju programma [“„]Bībeles māksla”",
        None,
    ),
    (
        "karitativais-socialais-darbs-bachelor", "Karitatīvais sociālais darbs", "bachelor", None,
        r"profesionālā bakalaura\) studiju programma [“„]Karitatīvais sociālais darbs”",
        rf"BAKALAURA STUDIJAS {Q}KARITATĪVAIS[^\n]*\n\s*(\d+)\s*EUR gadā",
    ),
    (
        "socialais-darbs-bachelor", "Sociālais darbs", "bachelor", None,
        r"profesionālās augstākās izglītības studiju programma\s+[“„]Sociālais darbs”",
        rf"{Q}SOCIĀLAIS DARBS{QE}:\s*(\d+)\s*EUR gadā",
    ),
    (
        "karitativais-socialais-darbs-master", "Karitatīvais sociālais darbs", "master", 2.0,
        r"profesionālā maģistra\) studiju programma [“„]Karitatīvais sociālais darbs",
        None,
    ),
    (
        "supervizija-master", "Supervīzija", "master", 2.0,
        r"profesionālā maģistra\) studiju programma [“„]Supervīzija”",
        r"Supervīzija\s*[–-]\s*(\d+)\s*EUR gadā",
    ),
]


def _single_fee(text: str, pattern: str | None) -> float | None:
    if pattern is None:
        return None
    amounts = {float(match) for match in re.findall(pattern, text)}
    return amounts.pop() if len(amounts) == 1 else None


def scrape() -> tuple[UniversityDraft, list[ProgrammeDraft]]:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(ADMISSIONS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        text = page.locator("body").inner_text()
        browser.close()

    programmes: list[ProgrammeDraft] = []
    missing: list[str] = []
    for slug, name, level, years, listing_pattern, fee_pattern in KNOWN_PROGRAMMES:
        if not re.search(listing_pattern, text):
            missing.append(slug)
            continue
        programmes.append(
            ProgrammeDraft(
                slug=slug,
                name_lv=name,
                degree_level=level,
                language_of_instruction="lv",
                study_mode="full_time",
                city=UNIVERSITY.city,
                funding_type="paid",
                tuition_fee_amount=_single_fee(text, fee_pattern),
                duration_years=years,
                source_url=ADMISSIONS_URL,
            )
        )

    if missing:
        raise RuntimeError(
            f"ekra: этих программ больше нет в списке приёма: {missing}. Возможно, их сняли "
            "или переименовали — проверьте kra.lv вручную и поправьте KNOWN_PROGRAMMES."
        )
    return UNIVERSITY, programmes
