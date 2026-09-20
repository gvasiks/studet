"""RTU (Rīgas Tehniskā universitāte) — весь реестр программ одной
страницы (rtu.lv/lv/studijas/visas-studiju-programmas), не только
Лиепая. Лиепаю по-прежнему покрывает отдельный источник
rtu_liepaja.py — там данные точнее (реальная квота подтверждена на
каждой странице программы отдельно), здесь Лиепаю сознательно
пропускаем, чтобы не задваивать записи под другими слагами.

Реестр — одна огромная таблица, разбитая на 9 визуально сворачиваемых
панелей по факультетам/академиям; всё уже есть в DOM, сворачивание
только через CSS — кликать ничего не нужно, но `inner_text()`
Playwright уважает видимость и вернёт пусто для скрытых панелей,
поэтому JS-эвакуация делается через `page.evaluate()` напрямую.

Многие программы реализуются сразу в нескольких городах (Rīga, Rēzekne,
Liepāja) с ОБЩЕЙ квотой бюджетных мест на все города разом. Первая
версия таких программ не брала вовсе ("честно не делим") — и потеряла
36 из 157 строк реестра, среди них самую востребованную "Datorsistēmas"
(200 бюджетных мест). Аудит полноты 2026-09-20 это вскрыл. Теперь:

- программа в нескольких городах — ПО СТРОКЕ НА КАЖДЫЙ город, слаг с
  суффиксом города, число бюджетных мест пустое (общая квота не делится
  честно), funding_type "both", если в реестре бюджет указан;
- программа только в Лиепае, которой нет среди трёх вручную отобранных
  в rtu_liepaja.py, — обычная строка с городом liepaja (квота её);
- программа без города в реестре — морские программы Latvijas Jūras
  akadēmija (подразделение 0J000, Ķīpsalas iela 6B): город riga.

Список городов реализации спрятан в HTML-комментарии внутри первой
ячейки каждой строки (`study_program_list_note`), не виден пользователю
на странице, но есть в разметке.

Отсюда в каталог впервые попадает Rēzekne — седьмой город (Rēzeknes
akadēmija, тоже в составе РТУ), добавлен в словари локалей.

Длительность и язык не видны в самой таблице реестра — дозапрашиваем
с индивидуальной страницы программы (тот же `td:has(div.course_title2_
container)`, что и в rtu_liepaja.py). Цена и бюджетные места — прямо
из таблицы реестра: первая из трёх колонок цены (очное обучение,
ЕС/Латвия).
"""

from __future__ import annotations

import re
from urllib.parse import urljoin

from playwright.sync_api import Page, sync_playwright

from models import ProgrammeDraft, UniversityDraft
from sources import rtu_liepaja

REGISTRY_URL = "https://www.rtu.lv/lv/studijas/visas-studiju-programmas"

UNIVERSITY = UniversityDraft(
    slug="rtu",
    name_lv="Rīgas Tehniskā universitāte",
    name_en="Riga Technical University",
    kind="public",
    city="riga",
    website_url="https://www.rtu.lv",
    source_url=REGISTRY_URL,
)

KNOWN_VENUES = {"Rīga": "riga", "Rēzekne": "rezekne", "Liepāja": "liepaja"}

_DISCOVER_JS = """
() => {
  const KNOWN = new Set(['Rīga', 'Rēzekne', 'Liepāja']);
  function extractVenues(note) {
    const parts = note.split(',').map(s => s.trim());
    const venues = [];
    for (let i = parts.length - 1; i >= 0; i--) {
      if (KNOWN.has(parts[i])) venues.unshift(parts[i]);
      else break;
    }
    return venues;
  }
  function parseRow(tr) {
    const link = tr.querySelector('a');
    if (!link) return null;
    const m = tr.innerHTML.match(/study_program_list_note[^]*?>\\s*([^<]*?)\\s*<\\/div>/);
    const note = m ? m[1].trim() : '';
    const cells = Array.from(tr.querySelectorAll('td'));
    return {
      href: link.getAttribute('href'),
      name: link.textContent.trim(),
      venues: extractVenues(note),
      budget: cells[1] ? cells[1].textContent.trim() : '',
      price: cells[2] ? cells[2].textContent.trim() : '',
    };
  }
  const panels = Array.from(document.querySelectorAll('.collapse-panel'));
  const all = new Map();
  for (const panel of panels) {
    const table = panel.querySelector('table');
    if (!table) continue;
    const trs = Array.from(table.querySelectorAll('tr'));
    let level = '';
    for (const tr of trs) {
      const divider = tr.querySelector('td[colspan] i b, td[colspan] b i');
      if (divider) { level = divider.textContent.trim(); continue; }
      const parsed = parseRow(tr);
      if (parsed && !all.has(parsed.href)) all.set(parsed.href, { ...parsed, level });
    }
  }
  return Array.from(all.values());
}
"""


def _map_level(text: str) -> str:
    lowered = text.lower()
    if "īsā cikla" in lowered:
        return "college"
    if "otrā cikla" in lowered or "maģistra" in lowered:
        return "master"
    if "trešā cikla" in lowered or "doktora" in lowered:
        return "doctoral"
    return "bachelor"


def _parse_budget(text: str) -> int | None:
    match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else None


def _parse_price(text: str) -> float | None:
    match = re.search(r"([\d\s ]+)", text)
    if not match:
        return None
    digits = re.sub(r"[\s ]", "", match.group(1))
    return float(digits) if digits else None


def _code_and_department(href: str) -> tuple[str, str]:
    path_part, _, query = href.partition("?")
    code = path_part.rstrip("/").rsplit("/", 1)[-1]
    match = re.search(r"department=([^&]+)", query)
    department = match.group(1) if match else ""
    return code, department


def _facts(page: Page) -> dict[str, str]:
    facts: dict[str, str] = {}
    rows = page.locator("td:has(div.course_title2_container)")
    for i in range(rows.count()):
        row = rows.nth(i)
        value_el = row.locator(".course_contents2_container")
        if value_el.count() == 0:
            continue  # не у каждой программы одинаковый набор полей
        key = row.locator(".course_title2_container").first.inner_text().strip().lower()
        facts[key] = value_el.first.inner_text().strip()
    return facts


def _parse_years(text: str) -> float | None:
    match = re.search(r"(\d+(?:[.,]\d+)?)", text)
    return float(match.group(1).replace(",", ".")) if match else None


def _is_legacy(row: dict) -> bool:
    """Строка, которую сборщик брал с самого начала: программа ровно в
    одном городе — Rīga или Rēzekne. Слаг таких строк не меняется: по нему
    в базе уже лежат данные и формулы. Остальным слаг получает суффикс
    города, потому что код+подразделение не уникальны ("GDI/0R000" —
    докторантура и в Лиепае, и в Резекне)."""
    return len(row["venues"]) == 1 and row["venues"][0] in ("Rīga", "Rēzekne")


def _scrape_detail(page: Page, url: str) -> tuple[float | None, str]:
    """Срок и язык с карточки программы. Один повтор при сбое: сайт РТУ
    изредка отвечает дольше таймаута. Не вышло и со второго раза — срок
    пустой, язык латышский (предположение), и об этом пишется в журнал:
    раньше это проглатывалось молча."""
    for attempt in (1, 2):
        try:
            page.goto(url, wait_until="domcontentloaded")
            facts = _facts(page)
            duration = _parse_years(facts.get("studiju ilgums", ""))
            language = "en" if "angļu" in facts.get("īstenošanas valoda", "").lower() else "lv"
            return duration, language
        except Exception as exc:  # noqa: BLE001
            if attempt == 2:
                print(f"rtu_catalog: не прочиталась {url}: {type(exc).__name__}; срок пуст, язык lv (предположение)")
    return None, "lv"


def scrape() -> tuple[UniversityDraft, list[ProgrammeDraft]]:
    programmes: list[ProgrammeDraft] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(5000)  # свежая программа, не 30с — падать быстро, не зависать
        page.goto(REGISTRY_URL, wait_until="domcontentloaded")

        rows = page.evaluate(_DISCOVER_JS)

        # Строки, которые брались с самого начала, идут первыми — при
        # совпадении именно они сохраняют слаг (см. _is_legacy)
        rows.sort(key=lambda row: 0 if _is_legacy(row) else 1)
        seen: set[tuple[str, str, str, str]] = set()

        for row in rows:
            cities = [KNOWN_VENUES[venue] for venue in row["venues"]] or ["riga"]
            # ^ пусто — морские программы Latvijas Jūras akadēmija (0J000), они в Риге

            url = urljoin(REGISTRY_URL, row["href"])
            code, department = _code_and_department(row["href"])
            if cities == ["liepaja"] and code in rtu_liepaja.PROGRAMMES:
                continue  # три программы, уже покрытые более точным источником

            # Реестр иногда даёт одну программу двумя строками под разными
            # подразделениями ("Būvniecība": 31000 и 0R000), каждая со всеми
            # тремя городами — одинаковые название, уровень, город и цена.
            # Одна карточка на такую программу, а не две
            fresh = [
                city for city in cities if (row["name"], row["level"], city, row["price"]) not in seen
            ]
            if not fresh:
                continue
            seen.update((row["name"], row["level"], city, row["price"]) for city in fresh)

            shared = len(cities) > 1  # общая квота на несколько городов
            base_slug = f"{code}-{department}".lower() if department else code.lower()
            legacy = _is_legacy(row)
            registry_budget = _parse_budget(row["budget"])
            duration_years, language = _scrape_detail(page, url)  # одна карточка на все города

            for city in fresh:
                programmes.append(
                    ProgrammeDraft(
                        slug=base_slug if legacy else f"{base_slug}-{city}",
                        name_lv=row["name"],
                        degree_level=_map_level(row["level"]),
                        language_of_instruction=language,
                        study_mode="full_time",
                        city=city,
                        funding_type="both" if registry_budget else "paid",
                        tuition_fee_amount=_parse_price(row["price"]),
                        budget_places=None if shared else registry_budget,
                        duration_years=duration_years,
                        source_url=url,
                    )
                )

        browser.close()

    return UNIVERSITY, programmes
