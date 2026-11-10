"""Черновики цены общежитий вузов — таблица housing_cost.

Продукт для иностранцев, шаг 1 (docs/PLAN-FOREIGNERS.md): жильё на карточке —
диапазоном и с источником; где источника нет, строки нет. Стоимость — поле
правила 6 CLAUDE.md, поэтому скрипт пишет ТОЛЬКО ЧЕРНОВИКИ: verified_at
проставляет владелец в Studio. Уже подтверждённые строки не трогаются.

Цены прочитаны вручную 2026-11-10 на страницах вузов:
- ЛУ (lu.lv/en/studies/student-life/accommodation/): «Rental Fees (per month)»,
  общежития Krišjāņa Valdemāra 161 и Prima, с 1 июля 2026 года. Самое дешёвое
  место — четырёхместная комната, 114 €; самое дорогое — одноместная в Prima,
  291 €.
- РТУ (rtu.lv/en/studies/student-life/accommodation) и RSU
  (rsu.lv/en/rsu-student-hostels) цен на этих страницах не называют — строк
  для них нет.

Что проверить при каждом обновлении: ЛУ меняет цены с 1 июля — тогда новая
строка с новой датой valid_from.

  python src/seed_housing_costs.py            # показать, что будет записано
  python src/seed_housing_costs.py --apply    # записать черновики
  python src/seed_housing_costs.py --selftest # проверка самой таблицы, без сети и базы
"""

from __future__ import annotations

import re
import sys

ROWS: list[dict] = [
    {
        "university": "lu",
        "amount_min": 114,
        "amount_max": 291,
        "valid_from": "2026-07-01",
        "source_title": "LU dormitories, rental fees per month",
        "source_url": "https://www.lu.lv/en/studies/student-life/accommodation/",
        "source_excerpt": (
            "Rental Fees (per month) Krišjāņa Valdemāra 161 Single: 170–256 EUR (220 - 272 EUR from July 1, 2026) "
            "Double: 136–180 EUR (152 - 181 EUR from July 1, 2026) Triple: 124–160 EUR (142 - 161 EUR from July 1, "
            "2026) Quadruple: 114 EUR Prima Double: 187 EUR (202 EUR from July 1, 2026) Single: 267 EUR (291 EUR from "
            "July 1, 2026)"
        ),
    },
]


def selftest() -> None:
    seen: set[tuple] = set()
    for row in ROWS:
        assert 0 <= row["amount_min"] <= row["amount_max"], row
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["valid_from"]), row
        assert row["source_url"].startswith("https://"), row
        # обе границы диапазона — из цитаты: опечатка в одном из двух мест
        for amount in (row["amount_min"], row["amount_max"]):
            assert re.search(rf"\b{amount} EUR", row["source_excerpt"]), (amount, row)
        key = (row["university"], row["valid_from"])
        assert key not in seen, key
        seen.add(key)
    print(f"selftest ok: {len(ROWS)} строк")


def main(apply: bool) -> None:
    from dotenv import load_dotenv

    from db import get_service_client
    from db_retry import execute

    load_dotenv()
    client = get_service_client()
    universities = {row["slug"]: row["id"] for row in execute(client.table("university").select("id, slug")).data}
    try:
        existing = {
            (row["university_id"], row["valid_from"]): row
            for row in execute(client.table("housing_cost").select("university_id, valid_from, verified_at")).data
        }
    except Exception as exc:  # noqa: BLE001
        if apply:
            raise SystemExit(f"housing_cost не читается ({exc}) — сначала примените миграцию в Studio") from exc
        print("housing_cost ещё нет в базе (миграция не применена) — показываю черновики без сверки\n")
        existing = {}

    written = 0
    for source in ROWS:
        row = {key: value for key, value in source.items() if key != "university"}
        row["university_id"] = universities[source["university"]]
        prior = existing.get((row["university_id"], row["valid_from"]))
        if prior and prior["verified_at"]:
            print(f"{source['university']}: уже подтверждено — не трогаю")
            continue
        print(f"{source['university']}: {row['amount_min']}–{row['amount_max']} EUR / месяц с {row['valid_from']}")
        if apply:
            # verified_at/verified_by в записи нет — их ставит только человек
            execute(client.table("housing_cost").upsert(row, on_conflict="university_id,valid_from"))
            written += 1
    print(f"\nзаписано: {written}" + ("" if apply else " (сухой прогон — запись только с --apply)"))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        main("--apply" in sys.argv)
