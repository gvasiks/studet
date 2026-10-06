"""Литва: записать в базу формулы конкурсного балла и строки общего приёма.

Что пишет (таблицы миграции 20261006120000_lt_formulas.sql):
- lt_formula и lt_formula_component — формулы из файла официального
  калькулятора LAMA BPO (разбор — lt_formulas.py);
- lt_admission_unit — строки общего приёма, каждая привязана к программе
  каталога и к своей формуле.

Чего НЕ делает: не ставит checked_at. Формула без этой отметки посетителям
не видна (политика доступа в миграции); отметку ставит отдельный шаг — после
сверки расчёта с официальным калькулятором. Если состав формулы в файле
изменился, отметка снимается: сверенным был прежний состав.

Строка приёма привязывается к программе по тем же кодам, которые даёт сбор
каталога (sources/lt_lamabpo.py), поэтому сначала должен пройти он:
  python src/main.py lt_lamabpo

Запуск:
  python src/lt_load_formulas.py --selftest
  python src/lt_load_formulas.py --save-payload .cache/lt_formulas.json   # собрать и показать сводку, без записи
  python src/lt_load_formulas.py --payload .cache/lt_formulas.json        # сводка по сохранённому, без сети
  python src/lt_load_formulas.py --payload .cache/lt_formulas.json --apply

Сбор открывает около 700 страниц реестра (как сбор каталога). --save-payload
сохраняет собранное в файл, чтобы --apply не собирал заново.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from lt_formulas import COMPETITIONS_URL, Component, parse_formulas
from sources.lt_lamabpo import PROGRAMS_URL, catalog_rows

# Год приёма, правила которого сейчас лежат в файлах калькулятора. LAMA BPO
# обновляет файлы раз в год; когда появятся правила 2027 года, поменять здесь
# — прошлогодние строки останутся в таблицах под своим годом.
ADMISSION_YEAR = 2026


def build_payload(
    rows: dict[tuple[str, str], list[dict[str, str]]], formulas: dict[str, list[Component]]
) -> dict:
    """Чистая функция: из разобранных файлов — то, что уйдёт в базу."""
    units = []
    for (university_slug, programme_slug), entries in rows.items():
        for entry in entries:
            units.append(
                {
                    "lamabpo_id": entry["e"],
                    "university_slug": university_slug,
                    "programme_slug": programme_slug,
                    "formula_number": entry["p"],
                    "study_form": entry.get("o") or None,
                    "schedule": entry.get("n") or None,
                    "note": entry.get("y") or None,
                }
            )
    used = {unit["formula_number"] for unit in units}
    unknown = sorted(used - formulas.keys())
    if unknown:
        raise ValueError(f"у строк приёма стоят номера формул, которых нет в таблице формул: {unknown}")
    ids = [unit["lamabpo_id"] for unit in units]
    if len(set(ids)) != len(ids):
        raise ValueError("номер строки приёма повторяется в файле программ")
    return {
        "admission_year": ADMISSION_YEAR,
        "formulas": {
            number: [
                {"position": c.position, "weight": c.weight, "mode": c.mode, "subjects": list(c.subjects)}
                for c in components
            ]
            for number, components in formulas.items()
        },
        "units": units,
    }


def same_components(stored: list[dict], fresh: list[dict]) -> bool:
    """Совпадает ли состав формулы в базе с тем, что в файле. Вес из базы
    приходит строкой или числом — сравнивается как число."""

    def normal(rows: list[dict]) -> list[tuple]:
        return sorted((int(r["position"]), round(float(r["weight"]), 2), r["mode"], tuple(r["subjects"])) for r in rows)

    return normal(stored) == normal(fresh)


def summary(payload: dict) -> str:
    units = payload["units"]
    by_programme: dict[tuple[str, str], set[str]] = defaultdict(set)
    for unit in units:
        by_programme[(unit["university_slug"], unit["programme_slug"])].add(unit["formula_number"])
    mixed = sorted(key for key, numbers in by_programme.items() if len(numbers) > 1)
    used = Counter(unit["formula_number"] for unit in units)
    lines = [
        f"год приёма: {payload['admission_year']}",
        f"формул в файле: {len(payload['formulas'])} | используются строками приёма: {len(used)}",
        f"строк приёма: {len(units)} | программ каталога: {len(by_programme)}",
        f"программ, у строк которых разные формулы (расчёт для них не показывается): {len(mixed)}",
    ]
    lines += [f"   {university}/{programme}: формулы {sorted(by_programme[(university, programme)])}" for university, programme in mixed[:10]]
    return "\n".join(lines)


def apply(client, payload: dict, execute) -> None:  # type: ignore[no-untyped-def]
    """Запись. Сервисный ключ — как у остального конвейера."""
    now = datetime.now(timezone.utc).isoformat()
    year = payload["admission_year"]

    # --- программы каталога: код вуза + код программы -> id
    universities = execute(client.table("university").select("id, slug").eq("country", "LT")).data
    university_ids = {row["slug"]: row["id"] for row in universities}
    programme_ids: dict[tuple[str, str], str] = {}
    for slug, university_id in university_ids.items():
        for row in execute(client.table("programme").select("id, slug").eq("university_id", university_id)).data:
            programme_ids[(slug, row["slug"])] = row["id"]

    # --- формулы: прежний состав нужен, чтобы понять, изменилась ли формула
    stored = execute(
        client.table("lt_formula").select("id, number, checked_at, checked_note, lt_formula_component(position, weight, mode, subjects)").eq("admission_year", year)
    ).data
    stored_by_number = {row["number"]: row for row in stored}

    formula_rows = []
    reset = []
    for number, components in payload["formulas"].items():
        before = stored_by_number.get(number)
        unchanged = before is not None and same_components(before["lt_formula_component"], components)
        if before is not None and before["checked_at"] and not unchanged:
            reset.append(number)
        # У всех строк пачки один набор ключей: иначе недостающий ключ
        # записался бы как NULL (см. catalog_diff.fill_missing_keys).
        formula_rows.append(
            {
                "admission_year": year,
                "number": number,
                "source_url": COMPETITIONS_URL,
                "extracted_at": now,
                "checked_at": before["checked_at"] if unchanged else None,
                "checked_note": before["checked_note"] if unchanged else None,
            }
        )
    saved = execute(client.table("lt_formula").upsert(formula_rows, on_conflict="admission_year,number")).data
    formula_ids = {row["number"]: row["id"] for row in saved}

    changed = [n for n in payload["formulas"] if n not in stored_by_number or not same_components(stored_by_number[n]["lt_formula_component"], payload["formulas"][n])]
    for number in changed:
        execute(client.table("lt_formula_component").delete().eq("formula_id", formula_ids[number]))
        execute(
            client.table("lt_formula_component").insert(
                [{"formula_id": formula_ids[number], **component} for component in payload["formulas"][number]]
            )
        )

    # --- строки приёма
    unit_rows, orphans = [], []
    for unit in payload["units"]:
        programme_id = programme_ids.get((unit["university_slug"], unit["programme_slug"]))
        if programme_id is None:
            orphans.append(f"{unit['university_slug']}/{unit['programme_slug']}")
            continue
        unit_rows.append(
            {
                "programme_id": programme_id,
                "admission_year": year,
                "lamabpo_id": unit["lamabpo_id"],
                "formula_id": formula_ids[unit["formula_number"]],
                "study_form": unit["study_form"],
                "schedule": unit["schedule"],
                "note": unit["note"],
                "source_url": PROGRAMS_URL,
                "extracted_at": now,
            }
        )
    for start in range(0, len(unit_rows), 500):
        execute(client.table("lt_admission_unit").upsert(unit_rows[start:start + 500], on_conflict="admission_year,lamabpo_id"))

    # строки, которых в файле больше нет, — удалить (только этого года)
    kept = {row["lamabpo_id"] for row in unit_rows}
    existing = []
    for start in range(0, 100000, 1000):
        page = execute(client.table("lt_admission_unit").select("id, lamabpo_id").eq("admission_year", year).range(start, start + 999)).data
        existing += page
        if len(page) < 1000:
            break
    stale = [row["id"] for row in existing if row["lamabpo_id"] not in kept]
    for start in range(0, len(stale), 200):
        execute(client.table("lt_admission_unit").delete().in_("id", stale[start:start + 200]))

    print(f"формул записано: {len(formula_rows)} (состав изменён или новый: {len(changed)})")
    if reset:
        print(f"ВНИМАНИЕ: состав изменился у сверенных формул {sorted(reset)} — отметка о сверке снята")
    print(f"строк приёма записано: {len(unit_rows)} | удалено устаревших: {len(stale)}")
    if orphans:
        unique = sorted(set(orphans))
        print(f"строк приёма без программы в каталоге: {len(orphans)} ({len(unique)} программ) — сначала запустите сбор каталога")
        for name in unique[:10]:
            print(f"   {name}")


def _selftest() -> None:
    rows = {
        ("ktu", "aviacijos-inzinerija-lt"): [
            {"e": "177", "p": "53", "o": "Nuolatinė (NL)", "n": "Dieninė", "y": "LIETUVIŲ K."},
            {"e": "179", "p": "53", "o": "Nuolatinė (NL)", "n": "Sesijinė", "y": ""},
        ],
        ("vu", "lietuviu-filologija"): [
            {"e": "368", "p": "3", "o": "Nuolatinė (NL)", "n": "Dieninė", "y": "a"},
            {"e": "369", "p": "4", "o": "Nuolatinė (NL)", "n": "Dieninė", "y": "b"},
        ],
    }
    formulas = {
        "53": [Component(1, 0.4, "one_of", ("mathematics",)), Component(2, 0.6, "one_of", ("physics", "chemistry"))],
        "3": [Component(1, 1.0, "one_of", ("lithuanian",))],
        "4": [Component(1, 1.0, "one_of", ("lithuanian",))],
        "99": [Component(1, 1.0, "one_of", ("history",))],
    }
    payload = build_payload(rows, formulas)
    assert payload["admission_year"] == ADMISSION_YEAR
    assert len(payload["units"]) == 4 and len(payload["formulas"]) == 4
    assert payload["units"][1] == {
        "lamabpo_id": "179", "university_slug": "ktu", "programme_slug": "aviacijos-inzinerija-lt",
        "formula_number": "53", "study_form": "Nuolatinė (NL)", "schedule": "Sesijinė", "note": None,
    }, payload["units"][1]
    assert payload["formulas"]["53"][1] == {"position": 2, "weight": 0.6, "mode": "one_of", "subjects": ["physics", "chemistry"]}
    text = summary(payload)
    assert "программ, у строк которых разные формулы (расчёт для них не показывается): 1" in text, text
    assert "vu/lietuviu-filologija" in text
    json.dumps(payload)  # сохраняется в файл как есть

    try:
        build_payload({("vu", "x"): [{"e": "1", "p": "777"}]}, formulas)
    except ValueError:
        pass
    else:
        raise AssertionError("номер формулы, которого нет в таблице, — ошибка")
    try:
        build_payload({("vu", "x"): [{"e": "1", "p": "3"}], ("vu", "y"): [{"e": "1", "p": "3"}]}, formulas)
    except ValueError:
        pass
    else:
        raise AssertionError("повтор номера строки приёма — ошибка")

    fresh = payload["formulas"]["53"]
    stored = [
        {"position": 2, "weight": "0.60", "mode": "one_of", "subjects": ["physics", "chemistry"]},
        {"position": 1, "weight": 0.4, "mode": "one_of", "subjects": ["mathematics"]},
    ]
    assert same_components(stored, fresh), "порядок строк и вид числа не важны"
    assert not same_components([{**stored[0], "weight": "0.50"}, stored[1]], fresh), "другой вес — другой состав"
    assert not same_components([{**stored[0], "subjects": ["chemistry", "physics"]}, stored[1]], fresh), "порядок предметов значим"
    assert not same_components(stored[:1], fresh)
    print("selftest: OK")


def main() -> None:
    args = sys.argv[1:]
    if "--selftest" in args:
        _selftest()
        return
    sys.stdout.reconfigure(encoding="utf-8")

    def option(name: str) -> str | None:
        return args[args.index(name) + 1] if name in args else None

    payload_path = option("--payload")
    if payload_path:
        payload = json.loads(Path(payload_path).read_text(encoding="utf-8"))
    else:
        from dotenv import load_dotenv
        from playwright.sync_api import sync_playwright

        import polite
        from sources.lt_lamabpo import collect

        load_dotenv()
        polite.install()
        entries, cards, _ = collect()
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            formulas = parse_formulas(page.goto(COMPETITIONS_URL, timeout=45000).text())
            browser.close()
        payload = build_payload(catalog_rows(entries, cards), formulas)
        print(polite.report_and_reset())
        save_path = option("--save-payload")
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            Path(save_path).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            print(f"собранное сохранено: {save_path}")

    print(summary(payload))
    if "--apply" not in args:
        print("\nзаписи не было (добавьте --apply)")
        return

    from dotenv import load_dotenv

    from db import get_service_client
    from db_retry import execute

    load_dotenv()
    apply(get_service_client(), payload, execute)


if __name__ == "__main__":
    main()
