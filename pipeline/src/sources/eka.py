"""ЭКА (Ekonomikas un kultūras augstskola / EKA University of Applied
Sciences) — английский раздел.

Формально частный вуз, но участвует в единой государственной подаче
(гибридный статус — CLAUDE.md, раздел "Кого включаем"). Старый сайт на
query-параметрах (`?parent=113&lng=eng`), без человекочитаемых slug —
свои слаги строим из английского названия программы.

Список программ и длительность взяты со страницы каталога (сайт группирует
по уровню с общим сроком на категорию: колледж 2 года, бакалавриат
3 года, профессиональный бакалавриат 4 года, магистратура 2 года) —
вручную сверено в браузере 2026-09-13, на странице отдельной программы
длительности нет вообще, только "Language:"/"Degree to Be Achieved:"/
"Accreditation:" в свободном тексте (парсим как у LU/BSA — по меткам,
не по классам).

Стоимость и бюджетные места нигде на этих страницах не публикуются.
"""

from __future__ import annotations

import re

from playwright.sync_api import Page, sync_playwright

from models import ProgrammeDraft, UniversityDraft

BASE_URL = "https://augstskola.lv/"

# (query, name_en, degree_level, duration_years) — вручную собрано со
# страницы каталога, см. docstring
PROGRAMMES = [
    ("?parent=345&lng=eng", "International Trade and Logistics", "college", 2),
    ("?parent=113&lng=eng", "Management", "bachelor", 3),
    ("?parent=114&lng=eng", "Business Economics", "bachelor", 3),
    ("index.php?parent=347&lng=eng", "Law", "bachelor", 3),
    ("index.php?parent=411&lng=eng", "Marketing", "bachelor", 3),
    ("index.php?parent=272&lng=eng", "Information Technologies (Programming)", "bachelor", 4),
    ("?parent=341&lng=eng", "Accounting and Finance Management", "bachelor", 4),
    ("?parent=342&lng=eng", "Interior Design", "bachelor", 4),
    ("?parent=344&lng=eng", "Culture Management", "bachelor", 4),
    ("?parent=340&lng=eng", "Computer Game Design", "bachelor", 4),
    ("?parent=123&lng=eng", "Business Administration", "master", 2),
    ("?parent=413&lng=eng", "Circular economy and social entrepreneurship", "master", 2),
    ("?parent=412&lng=eng", "International cultural project management", "master", 2),
    ("?parent=409&lng=eng", "Brand design", "master", 2),
]

UNIVERSITY = UniversityDraft(
    slug="eka",
    name_lv="Ekonomikas un kultūras augstskola",
    name_en="EKA University of Applied Sciences",
    kind="private",
    city="riga",
    website_url="https://www.eka.edu.lv",
    source_url=f"{BASE_URL}?parent=95&lng=eng",
)


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug


def _extract_field(text: str, label: str) -> str:
    idx = text.find(label)
    if idx == -1:
        return ""
    start = idx + len(label)
    end = text.find("\n", start)
    if end == -1:
        end = len(text)
    return text[start:end].strip()


def _extract_languages(text: str) -> list[str]:
    lowered = text.lower()
    languages = [lang for lang, key in (("en", "english"), ("lv", "latvian")) if key in lowered]
    return languages or ["lv"]


def _scrape_programme(
    page: Page, query: str, name_en: str, degree_level: str, duration_years: float
) -> list[ProgrammeDraft]:
    url = f"{BASE_URL}{query}"
    page.goto(url, wait_until="domcontentloaded")
    text = page.locator("main").first.inner_text()

    language_text = _extract_field(text, "Language:")
    languages = _extract_languages(language_text)
    base_slug = _slugify(name_en)
    multiple = len(languages) > 1

    return [
        ProgrammeDraft(
            slug=f"{base_slug}-{language}" if multiple else base_slug,
            name_en=name_en,
            degree_level=degree_level,
            language_of_instruction=language,
            study_mode="full_time",
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

        for query, name_en, degree_level, duration_years in PROGRAMMES:
            programmes.extend(_scrape_programme(page, query, name_en, degree_level, duration_years))

        browser.close()

    return UNIVERSITY, programmes
