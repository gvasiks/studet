"""Напоминание: пора запустить локальный сбор (см. scrape_scope.py).

Источники из LOCAL_ONLY сервер GitHub собрать не может, их запускает
владелец на своём компьютере. Этот скрипт ничего не собирает — он смотрит,
когда программы каждого такого источника обновлялись в последний раз
(programme.extracted_at по source_key), и падает, если прошло больше
LOCAL_MAX_STALE_DAYS. Упавший запланированный workflow GitHub присылает
письмо — тот же приём, что и у check_pipeline_health.py, без почтового
сервиса.

  python src/check_local_sources.py             # проверить
  python src/check_local_sources.py --selftest  # самотест без базы
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone

from scrape_scope import LOCAL_MAX_STALE_DAYS, LOCAL_ONLY


def days_since(extracted_at: str | None, now: datetime) -> int | None:
    """Сколько полных дней назад обновлялся источник; None — ни разу."""
    if extracted_at is None:
        return None
    parsed = datetime.fromisoformat(extracted_at.replace("Z", "+00:00"))
    return (now - parsed).days


def is_stale(extracted_at: str | None, now: datetime) -> bool:
    """Чистая функция — тестируется без обращения к базе."""
    if extracted_at is None:
        return True
    parsed = datetime.fromisoformat(extracted_at.replace("Z", "+00:00"))
    return now - parsed > timedelta(days=LOCAL_MAX_STALE_DAYS)


def check() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    from db import get_service_client

    client = get_service_client()
    now = datetime.now(timezone.utc)
    stale: list[str] = []

    for name in LOCAL_ONLY:
        # Самая свежая программа источника: main.py ставит extracted_at всем
        # найденным программам при каждой успешной записи.
        rows = (
            client.table("programme")
            .select("extracted_at")
            .eq("source_key", f"sources.{name}")
            .order("extracted_at", desc=True)
            .limit(1)
            .execute()
            .data
        )
        last = rows[0]["extracted_at"] if rows else None
        age = days_since(last, now)
        print(f"{name}: последнее обновление — {last or 'ни разу'}" + (f" ({age} дн. назад)" if age is not None else ""))
        if is_stale(last, now):
            stale.append(name)

    if stale:
        print(
            f"\nПОРА ЗАПУСТИТЬ ЛОКАЛЬНЫЙ СБОР: {', '.join(stale)} не обновлялись дольше "
            f"{LOCAL_MAX_STALE_DAYS} дней. На своём компьютере, в папке pipeline:\n\n"
            "    .venv\\Scripts\\python.exe src\\main.py --local\n\n"
            "Занимает около пяти минут. Подробности — pipeline/README.md, раздел «Локальный сбор»."
        )
        sys.exit(1)

    print("OK: локальные источники свежие")


def selftest() -> None:
    now = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)
    assert is_stale(None, now) is True, "ни разу не собирался — пора"
    assert is_stale("2026-10-09T12:00:00+00:00", now) is False, "вчера — свежий"
    assert is_stale("2026-10-03T13:00:00+00:00", now) is False, "без часа неделя — ещё свежий"
    assert is_stale("2026-10-03T11:00:00+00:00", now) is True, "неделя и час — пора"
    assert is_stale("2026-10-09T12:00:00Z", now) is False, "формат с Z читается так же"
    assert days_since("2026-10-03T11:00:00+00:00", now) == 7
    assert days_since(None, now) is None
    print("самотест пройден")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        check()
