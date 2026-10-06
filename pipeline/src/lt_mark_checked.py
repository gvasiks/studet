"""Литва: отметить формулы сверенными с официальным калькулятором.

Формула без отметки checked_at посетителям не видна (политика доступа в
миграции 20261006120000_lt_formulas.sql). Отметку ставит только этот скрипт
и только при записи о проведённой сверке в
docs/checks/lt-calculator-cases-<год>.json (блок owner_check).

Порог — 13 совпавших случаев. В плане стояло 30; владелец снизил порог
2026-10-06 («13 достаточно»), сверив 13 случаев вручную на странице
официального калькулятора.

Отмечаются НЕ ВСЕ формулы. Сверялся расчёт по школьным предметам; как
официальный калькулятор считает вступительный экзамен и спортивные
достижения, не проверял никто. Формулы, где такая составляющая есть
(искусство, архитектура, спорт), остаются закрытыми — расчёта для этих
программ на сайте нет.

Запуск:
  python src/lt_mark_checked.py --selftest
  python src/lt_mark_checked.py           # показать, что будет отмечено
  python src/lt_mark_checked.py --apply
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ADMISSION_YEAR = 2026
REQUIRED_CASES = 13
CASES_FILE = Path(__file__).resolve().parent.parent.parent / "docs" / "checks" / f"lt-calculator-cases-{ADMISSION_YEAR}.json"

# Составляющие, расчёт которых не сверялся. Оценка профессиональной
# квалификации (competence_assessment) сюда не входит: она встречается только
# как одна из многих замен в третьей составляющей, сайт её просто не
# предлагает, и на расчёт по школьным предметам она не влияет.
UNCHECKED_SUBJECTS = {"entrance_exam", "sport_achievements"}


def check_record(data: dict) -> str:
    """Текст отметки по записи о сверке; ошибка, если сверки недостаточно."""
    record = data.get("owner_check")
    if not record:
        raise ValueError("в файле случаев нет записи о сверке (owner_check)")
    if not record.get("all_matched"):
        raise ValueError("в записи о сверке есть расхождения — отмечать формулы нельзя")
    if int(record.get("cases_checked", 0)) < REQUIRED_CASES:
        raise ValueError(f"сверено {record.get('cases_checked')} случаев, нужно не меньше {REQUIRED_CASES}")
    return (
        f"Сверено с официальным калькулятором LAMA BPO вручную {record['checked_on']}: "
        f"{record['cases_checked']} случаев, все совпали."
    )


def can_mark(components: list[dict]) -> bool:
    """Формулу можно показывать, если все её составляющие — школьные предметы."""
    return bool(components) and not any(set(c["subjects"]) & UNCHECKED_SUBJECTS for c in components)


def _selftest() -> None:
    good = {"owner_check": {"checked_on": "2026-10-06", "cases_checked": 13, "all_matched": True}}
    assert check_record(good).startswith("Сверено с официальным калькулятором LAMA BPO вручную 2026-10-06: 13 случаев")
    for bad in (
        {},
        {"owner_check": None},
        {"owner_check": {"checked_on": "x", "cases_checked": 12, "all_matched": True}},
        {"owner_check": {"checked_on": "x", "cases_checked": 30, "all_matched": False}},
    ):
        try:
            check_record(bad)
        except ValueError:
            continue
        raise AssertionError(f"должно быть ошибкой: {bad}")

    school = [{"subjects": ["mathematics"]}, {"subjects": ["history", "geography"]}]
    assert can_mark(school)
    assert can_mark(school + [{"subjects": ["biology", "competence_assessment"]}]), "замена в третьей составляющей не мешает"
    assert not can_mark([{"subjects": ["entrance_exam"]}])
    assert not can_mark(school + [{"subjects": ["sport_achievements"]}])
    assert not can_mark([]), "формула без составляющих — не формула"
    print("selftest: OK")


def main() -> None:
    args = sys.argv[1:]
    if "--selftest" in args:
        _selftest()
        return
    sys.stdout.reconfigure(encoding="utf-8")
    from dotenv import load_dotenv

    from db import get_service_client
    from db_retry import execute

    load_dotenv()
    note = check_record(json.loads(CASES_FILE.read_text(encoding="utf-8")))
    client = get_service_client()
    formulas = execute(
        client.table("lt_formula").select("id, number, checked_at, lt_formula_component(subjects)").eq("admission_year", ADMISSION_YEAR)
    ).data

    to_mark = [f for f in formulas if can_mark(f["lt_formula_component"]) and not f["checked_at"]]
    already = [f for f in formulas if f["checked_at"]]
    closed = sorted((f["number"] for f in formulas if not can_mark(f["lt_formula_component"])), key=int)
    print(note)
    print(f"формул года {ADMISSION_YEAR}: {len(formulas)} | уже отмечено: {len(already)} | будет отмечено: {len(to_mark)}")
    print(f"остаются закрытыми (вступительный экзамен или спорт): {len(closed)} — {closed}")

    if "--apply" not in args:
        print("\nзаписи не было (добавьте --apply)")
        return
    now = datetime.now(timezone.utc).isoformat()
    for formula in to_mark:
        execute(client.table("lt_formula").update({"checked_at": now, "checked_note": note}).eq("id", formula["id"]))
    print(f"отмечено: {len(to_mark)}")


if __name__ == "__main__":
    main()
