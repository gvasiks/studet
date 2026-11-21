"""Источник коэффициентов уровня ЦЭ (1,00 / 0,75 / 0,50) — правило 5 CLAUDE.md.

Коэффициенты задаёт не вуз, а Кабинет министров: MK noteikumi Nr. 846, п. 10
(10.1 — оптимальный 0,75, 10.2 — общий 0,50, оба «pielīdzinot augstākā mācību
satura apguves līmeņa centralizētajiem eksāmeniem», то есть высший — 1) и п. 20
(экзамены по старым стандартам — как оптимальные, 0,75). На этот пункт ссылаются
правила приёма ЛУ 2026/27 (п. 1.11); у Вентспилса те же числа в приложении 2.
Текст нормы прочитан на likumi.lv 2026-11-21 (найдено в предрелизной проверке
2026-11-15: у коэффициентов не было ни источника, ни даты проверки).

Коэффициент — часть конкурсной формулы, поле правила 6: подтверждает только
человек. Поэтому два шага:

  python src/source_level_coefficients.py              # только проверка
  python src/source_level_coefficients.py --apply      # записать source_url
  python src/source_level_coefficients.py --confirm    # после «да» владельца:
                                                       # verified_at и verified_by

Скрипт ничего не меняет, если в базе не ровно три строки с ожидаемыми числами.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

SOURCE_URL = "https://likumi.lv/ta/id/146637-noteikumi-par-prasibam-kriterijiem-un-kartibu-uznemsanai-studiju-programmas"

# уровень → коэффициент, как в базе (миграция 20260913131517)
EXPECTED = {"augstakais": 1.00, "optimalais": 0.75, "vispaarigais": 0.50}

# Решение владельца в чате — вписать дословно перед --confirm.
OWNER_DECISION: str | None = (
    "Gvasiks (решение владельца 2026-11-21 в чате: «Да, подтверждаю» — коэффициенты 1,00 / 0,75 / 0,50 "
    "по MK noteikumi Nr. 846, п. 10 и 20)"
)


def main(apply: bool, confirm: bool) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    from dotenv import load_dotenv

    from db import get_service_client
    from db_retry import execute

    load_dotenv()
    client = get_service_client()
    rows = execute(client.table("level_coefficient").select("level, coefficient, valid_from, source_url, verified_at")).data
    found = {row["level"]: float(row["coefficient"]) for row in rows}
    for row in rows:
        print(f"  {row['level']:<13} {row['coefficient']}  с {row['valid_from']}  источник: {row['source_url'] or '—'}  проверено: {row['verified_at'] or '—'}")

    if len(rows) != len(EXPECTED) or found != EXPECTED:
        print("В базе не те строки, что ожидались — ничего не меняю.")
        sys.exit(1)

    if confirm:
        if not OWNER_DECISION:
            print("Нет решения владельца (OWNER_DECISION) — подтверждать нельзя.")
            sys.exit(1)
        if any(row["source_url"] != SOURCE_URL for row in rows):
            print("Сначала --apply: у строк нет источника.")
            sys.exit(1)
        now = datetime.now(timezone.utc).isoformat()
        for level in EXPECTED:
            execute(client.table("level_coefficient").update({"verified_at": now, "verified_by": OWNER_DECISION}).eq("level", level))
        print("Подтверждено: 3 строки.")
    elif apply:
        for level in EXPECTED:
            execute(client.table("level_coefficient").update({"source_url": SOURCE_URL}).eq("level", level))
        print("Источник записан: 3 строки (не подтверждены).")
    else:
        print("Сухой прогон: --apply запишет источник, --confirm подтвердит после решения владельца.")


if __name__ == "__main__":
    main("--apply" in sys.argv, "--confirm" in sys.argv)
