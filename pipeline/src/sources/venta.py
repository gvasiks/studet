"""Ventspils Augstskola (Ventspils University of Applied Sciences) —
латышский сайт (английского каталога программ нет).

Одна сводная таблица (venta.lv/nac-studet) даёт сразу все факты для
бакалавриата/колледжа и магистратуры: срок, бюджетные и платные места,
стоимость — не нужно обходить каждую программу отдельно, как у
остальных источников. Структура найдена вручную в браузере 2026-09-13:
`table.table > tr.row`, первая ячейка каждой строки — ссылка на
программу (`td.cell.linked > a`), из неё же берём slug.

Докторантура в эту таблицу не попадает (нет мест/оплаты в том же
формате) — не берём в этом заходе, тот же принцип, что и везде:
лучше меньше, но точно.

Отдельная находка, не использованная здесь: на странице конкретной
программы (например /program/datorzinatnes-bakalaurs) прямо
опубликована формула конкурсного балла — и она совпадает с примером
из docs/PLAN.md (математика×0,6 + английский×0,2 + латышский×0,1 +
среднее×0,1). Формулы — отдельная задача (таблицы formula/formula_term,
правило 6 CLAUDE.md требует утверждённый PDF, а не веб-страницу как
источник) — не смешиваем с этим каталожным заходом, но повод вернуться.
"""

from __future__ import annotations

import re
from collections import Counter
from urllib.parse import urljoin

from playwright.sync_api import Page, sync_playwright

from models import ProgrammeDraft, UniversityDraft

FEES_URL = "https://venta.lv/nac-studet"

UNIVERSITY = UniversityDraft(
    slug="venta",
    name_lv="Ventspils Augstskola",
    name_en="Ventspils University of Applied Sciences",
    kind="public",
    city="ventspils",
    website_url="https://venta.lv",
    source_url=FEES_URL,
)


def _parse_table_rows(page: Page, table_index: int) -> list[dict[str, object]]:
    rows = page.locator("table.table").nth(table_index).locator("tr.row")
    results: list[dict[str, object]] = []

    for i in range(1, rows.count()):  # 0 — заголовок
        row = rows.nth(i)
        cells = row.locator("td.cell")
        link = cells.nth(0).locator("a")
        if link.count() == 0:
            continue
        results.append(
            {
                "href": link.get_attribute("href"),
                "name": cells.nth(0).inner_text().strip(),
                "values": [cells.nth(j).inner_text().strip() for j in range(1, cells.count())],
            }
        )
    return results


def _clean_name(name: str) -> str:
    return re.sub(r"\s*\([^)]*\)\s*", " ", name).strip().rstrip("*").strip()


def _extract_language(name: str) -> str:
    return "en" if "angļu valodā" in name.lower() else "lv"


def _extract_mode(name: str) -> str:
    lowered = name.lower()
    if "neklātiene" in lowered:
        return "distance"
    if "nepilna laika" in lowered:
        return "part_time"
    return "full_time"


def _parse_years(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(match.group(1)) if match else None


def _parse_int(text: str) -> int | None:
    match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else None


def _rows_to_programmes(rows: list[dict], degree_level_for) -> list[ProgrammeDraft]:
    # "Vadībzinātne" в таблице бакалавриата — две строки (англ. полный
    # день / латыш. неполный заочно) с ОДНОЙ и той же ссылкой на
    # программу. Различаем такие слаги суффиксом язык+форма.
    href_counts = Counter(row["href"] for row in rows)

    programmes = []
    for row in rows:
        duration_text, budget_text, _paid_text, fee_text = row["values"]
        language = _extract_language(row["name"])
        mode = _extract_mode(row["name"])
        budget_places = _parse_int(budget_text)

        base_slug = row["href"].rstrip("/").rsplit("/", 1)[-1]
        slug = f"{base_slug}-{language}-{mode}" if href_counts[row["href"]] > 1 else base_slug

        programmes.append(
            ProgrammeDraft(
                slug=slug,
                name_lv=_clean_name(row["name"]),
                degree_level=degree_level_for(row["name"]),
                language_of_instruction=language,
                study_mode=mode,
                city=UNIVERSITY.city,
                funding_type="both" if budget_places else "paid",
                tuition_fee_amount=_parse_int(fee_text),
                budget_places=budget_places,
                duration_years=_parse_years(duration_text),
                source_url=urljoin(FEES_URL, row["href"]),
            )
        )
    return programmes


def scrape() -> tuple[UniversityDraft, list[ProgrammeDraft]]:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(FEES_URL, wait_until="domcontentloaded")

        college_and_bachelor_rows = _parse_table_rows(page, 0)
        master_rows = _parse_table_rows(page, 1)

        browser.close()

    programmes = _rows_to_programmes(
        college_and_bachelor_rows,
        lambda name: "college" if "īsā cikla" in name.lower() else "bachelor",
    ) + _rows_to_programmes(master_rows, lambda name: "master")

    return UNIVERSITY, programmes
