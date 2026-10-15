"""Сторож эстонских данных: давно ли они обновлялись.

Эстонские данные собирает прогон по расписанию на GitHub
(.github/workflows/scrape-estonia.yml). Этот скрипт ничего не собирает — он
смотрит, когда в последний раз обновлялись три вещи, от которых зависят
эстонские страницы, и падает, если какая-то из них старше
EE_MAX_STALE_DAYS (тот же срок, что у Литвы, check_lt_sources.py):

- каталог (программы эстонских учреждений) — пишет `main.py ee_haridusportaal`;
- направления программ — пишет `ee_load_fields.py`;
- сроки приёма и ссылка на конкурс — пишет `ee_load_admissions.py`.

Все три шага ставят отметку времени при каждом запуске. Условия конкурса
(ee_load_admission_details.py) и правила (ee_load_rules.py) сюда не входят:
они перечитывают только новые и открытые конкурсы, и в межсезонье их
отметки законно стоят на месте.

Упавший запланированный workflow GitHub присылает письмо — тот же приём,
что у check_lt_sources.py.

  python src/check_ee_sources.py             # проверить
  python src/check_ee_sources.py --selftest  # самотест без базы
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

from check_lt_sources import LT_MAX_STALE_DAYS, _latest, report

# Сбор по расписанию — раз в месяц; полтора месяца без обновления значит,
# что не прошёл ни он, ни следующий — пора собрать руками.
EE_MAX_STALE_DAYS = LT_MAX_STALE_DAYS

# Чем обновить всё сразу — на компьютере владельца, в папке pipeline.
REFRESH_COMMAND = ".venv\\Scripts\\python.exe src\\ee_refresh.py"


def check() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    from db import get_service_client

    client = get_service_client()
    latest = {
        # main.py ставит extracted_at всем найденным программам источника
        "каталог": _latest(client, "programme", "sources.ee_haridusportaal"),
        "направления программ": _latest(client, "ee_programme_field"),
        "сроки приёма": _latest(client, "ee_admission"),
    }
    lines, stale = report(latest, datetime.now(timezone.utc))
    print("\n".join(lines))
    if stale:
        print(
            f"\nПОРА ОБНОВИТЬ ЭСТОНСКИЕ ДАННЫЕ: {', '.join(stale)} не обновлялись дольше {EE_MAX_STALE_DAYS} дней.\n"
            "Сбор по расписанию на GitHub давно не проходил.\n"
            "Соберите данные со своего компьютера, в папке pipeline:\n\n"
            f"    {REFRESH_COMMAND}\n\n"
            "Подробности — pipeline/README.md, раздел «Эстония»."
        )
        sys.exit(1)
    print("OK: эстонские данные свежие")


def selftest() -> None:
    now = datetime(2026, 12, 1, 12, 0, tzinfo=timezone.utc)
    lines, stale = report({"каталог": "2026-11-30T12:00:00+00:00", "сроки приёма": "2026-10-01T12:00:00+00:00"}, now)
    assert stale == ["сроки приёма"], stale
    assert EE_MAX_STALE_DAYS == 45
    assert REFRESH_COMMAND.endswith("ee_refresh.py")
    print("самотест пройден")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        check()
