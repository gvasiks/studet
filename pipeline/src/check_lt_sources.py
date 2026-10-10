"""Сторож литовских данных: давно ли они обновлялись.

Литовские данные собирает владелец со своего компьютера (lt_refresh.py):
реестр серверу GitHub отвечает ненадёжно. Этот скрипт ничего не собирает —
он смотрит, когда в последний раз обновлялись три вещи, от которых зависят
литовские страницы, и падает, если какая-то из них старше
LT_MAX_STALE_DAYS:

- каталог (программы литовских вузов) — пишет `main.py lt_lamabpo`;
- строки приёма и формулы — пишет `lt_load_formulas.py`;
- направления программ — пишет `lt_load_fields.py`.

Упавший запланированный workflow GitHub присылает письмо — тот же приём,
что у check_pipeline_health.py и check_local_sources.py.

Цифры прошлого приёма и показатели выпускников сюда не входят: их источники
обновляются раз в год, и проверять их «свежесть» по дням бессмысленно —
они стоят в годовом календаре (pipeline/README.md, «Литва: что обновлять в
течение года»).

  python src/check_lt_sources.py             # проверить
  python src/check_lt_sources.py --selftest  # самотест без базы
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone

# Источники меняются редко (список программ и правила балла — раз в год),
# обновлять достаточно раз в месяц; полтора месяца — время напомнить.
LT_MAX_STALE_DAYS = 45

# Чем обновить всё сразу — на компьютере владельца, в папке pipeline.
REFRESH_COMMAND = ".venv\\Scripts\\python.exe src\\lt_refresh.py"


def days_since(extracted_at: str | None, now: datetime) -> int | None:
    """Сколько полных дней назад было обновление; None — ни разу."""
    if extracted_at is None:
        return None
    parsed = datetime.fromisoformat(extracted_at.replace("Z", "+00:00"))
    return (now - parsed).days


def is_stale(extracted_at: str | None, now: datetime) -> bool:
    """Чистая функция — тестируется без обращения к базе."""
    if extracted_at is None:
        return True
    parsed = datetime.fromisoformat(extracted_at.replace("Z", "+00:00"))
    return now - parsed > timedelta(days=LT_MAX_STALE_DAYS)


def report(latest: dict[str, str | None], now: datetime) -> tuple[list[str], list[str]]:
    """Строки для печати и список устаревшего."""
    lines, stale = [], []
    for name, extracted_at in latest.items():
        age = days_since(extracted_at, now)
        lines.append(f"{name}: последнее обновление — {extracted_at or 'ни разу'}" + (f" ({age} дн. назад)" if age is not None else ""))
        if is_stale(extracted_at, now):
            stale.append(name)
    return lines, stale


def _latest(client, table: str, source_prefix: str | None = None) -> str | None:  # type: ignore[no-untyped-def]
    query = client.table(table).select("extracted_at").order("extracted_at", desc=True).limit(1)
    if source_prefix:
        query = query.like("source_key", f"{source_prefix}%")
    rows = query.execute().data
    return rows[0]["extracted_at"] if rows else None


def check() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    from db import get_service_client

    client = get_service_client()
    latest = {
        # main.py ставит extracted_at всем найденным программам источника
        "каталог": _latest(client, "programme", "sources.lt_lamabpo"),
        "строки приёма и формулы": _latest(client, "lt_admission_unit"),
        "направления программ": _latest(client, "lt_programme_field"),
    }
    lines, stale = report(latest, datetime.now(timezone.utc))
    print("\n".join(lines))
    if stale:
        print(
            f"\nПОРА ОБНОВИТЬ ЛИТОВСКИЕ ДАННЫЕ: {', '.join(stale)} не обновлялись дольше {LT_MAX_STALE_DAYS} дней.\n"
            "Литва собирается с вашего компьютера (реестр серверу GitHub отвечает ненадёжно).\n"
            "В папке pipeline:\n\n"
            f"    {REFRESH_COMMAND}\n\n"
            "Занимает около 25 минут. Подробности — pipeline/README.md, раздел «Литва: сбор и сторож»."
        )
        sys.exit(1)
    print("OK: литовские данные свежие")


def selftest() -> None:
    now = datetime(2026, 12, 1, 12, 0, tzinfo=timezone.utc)
    assert is_stale(None, now) is True, "ни разу не собиралось — устарело"
    assert is_stale("2026-11-30T12:00:00+00:00", now) is False
    assert is_stale("2026-10-17T13:00:00+00:00", now) is False, "без часа 45 дней — ещё свежее"
    assert is_stale("2026-10-17T11:00:00+00:00", now) is True, "45 дней и час — устарело"
    assert is_stale("2026-11-30T12:00:00Z", now) is False, "формат с Z читается так же"
    assert days_since("2026-10-17T11:00:00+00:00", now) == 45
    lines, stale = report({"каталог": "2026-11-30T12:00:00+00:00", "направления программ": None}, now)
    assert stale == ["направления программ"], stale
    assert lines[0].endswith("(1 дн. назад)") and "ни разу" in lines[1], lines
    assert REFRESH_COMMAND.endswith("lt_refresh.py")
    print("самотест пройден")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        check()
