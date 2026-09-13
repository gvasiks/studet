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
Liepāja) с ОБЩЕЙ квотой бюджетных мест на все города разом — та же
проблема, что уже решалась для Лиепаи. То же решение: берём только
программы с ровно одним городом реализации — тогда квота однозначно
её. Список городов реализации спрятан в HTML-комментарии внутри первой
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


def _scrape_detail(page: Page, url: str) -> tuple[float | None, str]:
    page.goto(url, wait_until="domcontentloaded")
    facts = _facts(page)
    duration = _parse_years(facts.get("studiju ilgums", ""))
    language = "en" if "angļu" in facts.get("īstenošanas valoda", "").lower() else "lv"
    return duration, language


def scrape() -> tuple[UniversityDraft, list[ProgrammeDraft]]:
    programmes: list[ProgrammeDraft] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(5000)  # свежая программа, не 30с — падать быстро, не зависать
        page.goto(REGISTRY_URL, wait_until="domcontentloaded")

        rows = page.evaluate(_DISCOVER_JS)

        for row in rows:
            venues = row["venues"]
            if len(venues) != 1:
                continue  # общая квота на несколько городов — честно не делим
            city = KNOWN_VENUES[venues[0]]
            if city == "liepaja":
                continue  # уже покрыто отдельным, более точным источником

            url = urljoin(REGISTRY_URL, row["href"])
            try:
                duration_years, language = _scrape_detail(page, url)
            except Exception:
                # одна нестандартная страница не должна ронять весь прогон
                # по остальным ~120 программам
                duration_years, language = None, "lv"

            code, department = _code_and_department(row["href"])
            slug = f"{code}-{department}".lower() if department else code.lower()
            budget_places = _parse_budget(row["budget"])

            programmes.append(
                ProgrammeDraft(
                    slug=slug,
                    name_lv=row["name"],
                    degree_level=_map_level(row["level"]),
                    language_of_instruction=language,
                    study_mode="full_time",
                    city=city,
                    funding_type="both" if budget_places else "paid",
                    tuition_fee_amount=_parse_price(row["price"]),
                    budget_places=budget_places,
                    duration_years=duration_years,
                    source_url=url,
                )
            )

        browser.close()

    return UNIVERSITY, programmes
