"""Черновики общих сумм для иностранных абитуриентов — таблица country_cost.

Продукт для иностранцев, шаг 1 (docs/PLAN-FOREIGNERS.md; решение владельца
2026-11-08). Суммы — поля правила 6 CLAUDE.md («стоимость» подтверждает только
человек), поэтому скрипт пишет ТОЛЬКО ЧЕРНОВИКИ: verified_at проставляет
владелец в Studio, до этого сайт сумму не показывает.

Суммы прочитаны вручную 2026-11-08 в действующих редакциях на likumi.lv;
у каждой — норма и дословная цитата:
- MK noteikumi Nr. 731 (26.11.2024) «Noteikumi par valsts nodevu par
  migrācijas pakalpojumiem», в силе с 01.01.2025 — пошлины;
- MK noteikumi Nr. 225 (25.04.2017), 11.7. apakšpunkts — средства на месяц
  «atbilstoši minimālajai mēneša darba algai»; для студента отдельной суммы нет
  (13.5. — только чем подтверждать: заявлением родителя);
- MK noteikumi Nr. 656, 2. punkts (редакция MK Nr. 680 от 19.11.2025, с
  01.01.2026) — минимальная зарплата 780 евро.

Что проверить в декабре (годовая сверка):
- минимальная зарплата 2027 года: изменится — новая строка means_per_month с
  valid_from 2027-01-01, у старой проставить valid_to;
- MK Nr. 731: iFinanses 03.11.2026 сообщил о проекте новых правил с тем же
  названием, которые заменят Nr. 731. Примут — пошлины переписать.

Цены страховки здесь нет: закон требует полис с минимальным покрытием, но цену
не задаёт — числом её показывать не из чего (правило 5).

  python src/seed_country_costs.py            # показать, что будет записано
  python src/seed_country_costs.py --apply    # записать черновики
  python src/seed_country_costs.py --selftest # проверка самой таблицы, без сети и базы

Уже подтверждённые строки скрипт не трогает.
"""

from __future__ import annotations

import sys

CODES = ("residence_permit_review", "residence_permit_registration", "long_stay_visa", "means_per_month")
PERIODS = ("once", "month")

MK_731 = "https://likumi.lv/ta/id/356656"
MK_225 = "https://likumi.lv/ta/id/290808"

ROWS: list[dict] = [
    {
        "code": "residence_permit_review",
        "amount": 160,
        "period": "once",
        "valid_from": "2025-01-01",
        "source_title": "MK noteikumi Nr. 731, 5.1.1. apakšpunkts",
        "source_url": MK_731,
        "source_excerpt": (
            "5. Valsts nodevas likmes par uzturēšanās atļaujas pieprasīšanai nepieciešamo dokumentu izskatīšanu ir "
            "šādas: 5.1. termiņuzturēšanās atļaujas pieprasīšanai iesniegto dokumentu izskatīšana: 5.1.1. 30 dienu "
            "laikā […] – 160 euro"
        ),
    },
    {
        "code": "residence_permit_registration",
        "amount": 75,
        "period": "once",
        "valid_from": "2025-01-01",
        "source_title": "MK noteikumi Nr. 731, 6.1.1. apakšpunkts",
        "source_url": MK_731,
        "source_excerpt": (
            "6.1. par termiņuzturēšanās atļaujas reģistrācijai iesniegto dokumentu izskatīšanu: "
            "6.1.1. 30 dienu laikā – 75 euro"
        ),
    },
    {
        "code": "long_stay_visa",
        "amount": 90,
        "period": "once",
        "valid_from": "2025-01-01",
        "source_title": "MK noteikumi Nr. 731, 2.1. apakšpunkts",
        "source_url": MK_731,
        "source_excerpt": (
            "2. Valsts nodevas likmes par ilgtermiņa vīzas pieprasīšanai nepieciešamo dokumentu izskatīšanu ir "
            "šādas: 2.1. 90 euro"
        ),
    },
    {
        "code": "means_per_month",
        "amount": 780,
        "period": "month",
        "valid_from": "2026-01-01",
        "source_title": "MK noteikumi Nr. 225, 11.7. apakšpunkts; MK noteikumi Nr. 656, 2. punkts",
        "source_url": MK_225,
        "source_excerpt": (
            "MK Nr. 225, 11.7.: finanšu līdzekļi atbilstoši minimālajai mēneša darba algai […]. "
            "MK Nr. 656, 2. (MK 19.11.2025. noteikumu Nr. 680 redakcijā, no 01.01.2026.): Minimālā mēneša darba "
            "alga normālā darba laika ietvaros ir 780 euro."
        ),
    },
]


def rows() -> list[dict]:
    """Строки к записи: все — Латвия и граждане не из ЕС (Р1 плана; гражданам
    ЕС ВНЖ и подтверждение средств не нужны)."""
    return [{"country": "LV", "applies_to": "non_eu", "currency": "EUR", **row} for row in ROWS]


def selftest() -> None:
    seen: set[tuple] = set()
    for row in rows():
        assert row["code"] in CODES, row
        assert row["period"] in PERIODS, row
        assert row["amount"] > 0, row
        assert row["source_url"].startswith("https://likumi.lv/"), row
        assert row["source_title"] and row["source_excerpt"], row
        # сумма из цитаты — та же, что в строке: опечатка в одном из двух мест
        assert f"{row['amount']} euro" in row["source_excerpt"], row
        key = (row["country"], row["code"], row["applies_to"], row["valid_from"])
        assert key not in seen, key
        seen.add(key)
    print(f"selftest ok: {len(rows())} строк")


def main(apply: bool) -> None:
    from dotenv import load_dotenv

    from db import get_service_client
    from db_retry import execute

    load_dotenv()
    client = get_service_client()
    existing = {
        (row["country"], row["code"], row["applies_to"], row["valid_from"]): row
        for row in execute(client.table("country_cost").select("country, code, applies_to, valid_from, verified_at")).data
    }

    written = skipped_verified = 0
    for row in rows():
        key = (row["country"], row["code"], row["applies_to"], row["valid_from"])
        prior = existing.get(key)
        if prior and prior["verified_at"]:
            skipped_verified += 1
            print(f"{row['code']}: уже подтверждено — не трогаю")
            continue
        print(f"{row['code']}: {row['amount']} EUR / {row['period']} с {row['valid_from']} — {row['source_title']}")
        if apply:
            # verified_at/verified_by в записи нет вовсе — их ставит только человек
            execute(client.table("country_cost").upsert(row, on_conflict="country,code,applies_to,valid_from"))
            written += 1

    print(
        f"\nчерновиков: {len(rows())}; записано: {written}; подтверждённых не тронуто: {skipped_verified}"
        + ("" if apply else " (сухой прогон — запись только с --apply)")
    )


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        main("--apply" in sys.argv)
