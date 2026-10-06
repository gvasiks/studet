"""Литва: записать в базу направление каждой программы (lt_programme_field).

Источник — открытый файл программ официального калькулятора LAMA BPO: у
каждой строки общего приёма стоят группа направлений и направление
(поля a, b, c, d). Строка приёма уже привязана к программе каталога
(lt_admission_unit, её пишет lt_load_formulas.py), поэтому обходить реестр
заново не нужно: читается один файл и одна таблица.

Таблица — миграция 20261006200000_lt_programme_field.sql.

Запуск:
  python src/lt_load_fields.py --selftest
  python src/lt_load_fields.py            # показать сводку, без записи
  python src/lt_load_fields.py --apply
"""

from __future__ import annotations

import sys
from collections import Counter
from datetime import datetime, timezone

from sources.lt_lamabpo import PROGRAMS_URL, parse_programs


def fields_by_programme(entries: list[dict[str, str]], programme_by_unit: dict[str, str]) -> tuple[dict[str, dict], list[str]]:
    """Программа -> её направление. Второе значение — строки приёма, которых
    нет в базе (сначала должен пройти lt_load_formulas.py).

    У всех строк приёма одной программы направление одно — так устроена
    группировка каталога. Если оно вдруг разное, это ошибка данных, а не
    повод выбрать первое."""
    result: dict[str, dict] = {}
    unknown: list[str] = []
    for entry in entries:
        programme_id = programme_by_unit.get(entry["e"])
        if programme_id is None:
            unknown.append(entry["e"])
            continue
        field = {
            "group_code": entry["a"],
            "group_name": entry["b"],
            "field_code": entry["c"],
            "field_name": entry["d"],
        }
        before = result.get(programme_id)
        if before is not None and before != field:
            raise ValueError(f"у программы {programme_id} два направления: {before['field_code']} и {field['field_code']}")
        result[programme_id] = field
    return result, unknown


def _selftest() -> None:
    entries = [
        {"e": "1", "a": "E", "b": "Inžinerijos mokslai", "c": "E14", "d": "Aeronautikos inžinerija"},
        {"e": "2", "a": "E", "b": "Inžinerijos mokslai", "c": "E14", "d": "Aeronautikos inžinerija"},
        {"e": "3", "a": "K", "b": "Teisė", "c": "K01", "d": "Teisė"},
        {"e": "4", "a": "K", "b": "Teisė", "c": "K01", "d": "Teisė"},
    ]
    fields, unknown = fields_by_programme(entries, {"1": "p1", "2": "p1", "3": "p2"})
    assert fields == {
        "p1": {"group_code": "E", "group_name": "Inžinerijos mokslai", "field_code": "E14", "field_name": "Aeronautikos inžinerija"},
        "p2": {"group_code": "K", "group_name": "Teisė", "field_code": "K01", "field_name": "Teisė"},
    }, fields
    assert unknown == ["4"]
    try:
        fields_by_programme(entries, {"1": "p1", "3": "p1"})
    except ValueError:
        pass
    else:
        raise AssertionError("два направления у одной программы — ошибка")
    print("selftest: OK")


def main() -> None:
    args = sys.argv[1:]
    if "--selftest" in args:
        _selftest()
        return
    sys.stdout.reconfigure(encoding="utf-8")
    from dotenv import load_dotenv
    from playwright.sync_api import sync_playwright

    import polite
    from db import get_service_client
    from db_retry import execute

    load_dotenv()
    polite.install()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        entries = parse_programs(page.goto(PROGRAMS_URL, timeout=45000).text())
        browser.close()

    client = get_service_client()
    programme_by_unit: dict[str, str] = {}
    for start in range(0, 100000, 1000):
        rows = execute(client.table("lt_admission_unit").select("lamabpo_id, programme_id").order("id").range(start, start + 999)).data
        programme_by_unit.update({row["lamabpo_id"]: row["programme_id"] for row in rows})
        if len(rows) < 1000:
            break

    fields, unknown = fields_by_programme(entries, programme_by_unit)
    print(f"строк приёма в файле: {len(entries)} | программ с направлением: {len(fields)} | строк без программы в базе: {len(unknown)}")
    print("по группам:", dict(sorted(Counter(field["group_code"] for field in fields.values()).items())))

    if "--apply" not in args:
        print("\nзаписи не было (добавьте --apply)")
        return
    now = datetime.now(timezone.utc).isoformat()
    rows = [{"programme_id": programme_id, **field, "source_url": PROGRAMS_URL, "extracted_at": now} for programme_id, field in fields.items()]
    for start in range(0, len(rows), 500):
        execute(client.table("lt_programme_field").upsert(rows[start:start + 500], on_conflict="programme_id"))
    print(f"записано: {len(rows)}")


if __name__ == "__main__":
    main()
