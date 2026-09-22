"""Сторож конвейера сбора (план 2026-09-21, неделя 1, пункт 08).

main.py по расписанию отрабатывает по понедельникам в 01:00 UTC — время,
когда на статус в интерфейсе GitHub никто не смотрит. Красный прогон сам
по себе ничего не значит, если никто в него не заглянул; а если прогон
не запустился вовсе (например, GitHub Actions выключил расписание после
60 дней неактивности репозитория — так бывает), в интерфейсе не будет даже
красного — просто тишина.

Отдельный ежедневный workflow (.github/workflows/pipeline-health.yml)
запускает этот скрипт. Он не собирает ничего сам — только смотрит на
pipeline_health (см. миграцию 20260922090000) и падает, если последний
УСПЕШНЫЙ ПОЛНЫЙ сбор старше MAX_STALE_DAYS. GitHub Actions присылает
письмо на упавший запланированный workflow по умолчанию — этого достаточно
без Resend (CLAUDE.md: почта — только с выпуска 4).
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone

# Сбор — раз в неделю (понедельник); один день запаса на повторную попытку,
# если прогон в понедельник упал или GitHub Actions задержал расписание.
MAX_STALE_DAYS = 9


def is_stale(last_success_at: str | None, now: datetime | None = None) -> bool:
    """Чистая функция — тестируется без обращения к базе (--selftest ниже)."""
    if last_success_at is None:
        return True
    now = now or datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(last_success_at.replace("Z", "+00:00"))
    return now - parsed > timedelta(days=MAX_STALE_DAYS)


def check() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    from db import get_service_client

    client = get_service_client()
    row = client.table("pipeline_health").select("*").maybe_single().execute().data or {}
    last_success_at = row.get("last_success_at")
    last_status = row.get("last_status")
    last_error_count = row.get("last_error_count")

    if is_stale(last_success_at):
        print(
            f"ПРОСРОЧЕНО: последний успешный полный сбор — {last_success_at or 'ни разу'}, "
            f"порог {MAX_STALE_DAYS} дней. Последний прогон вообще: статус={last_status}, "
            f"ошибок={last_error_count}. Проверьте расписание в GitHub Actions (Scrape catalog) "
            "и вручную нажмите Run workflow, если оно не сработало само."
        )
        sys.exit(1)

    print(f"OK: последний успешный полный сбор — {last_success_at}")


def selftest() -> None:
    now = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)
    assert is_stale(None, now) is True, "нет ни одного сбора — считается просроченным"
    assert is_stale("2026-09-22T10:00:00+00:00", now) is False, "сбор два часа назад — не просрочен"
    assert is_stale("2026-09-10T00:00:00+00:00", now) is True, "12 дней назад — просрочен (порог 9)"
    assert is_stale("2026-09-14T00:00:00+00:00", now) is False, "8 дней назад — ещё не просрочен"
    # формат с "Z" (иногда так отдаёт PostgREST) парсится так же, как "+00:00"
    assert is_stale("2026-09-22T10:00:00Z", now) is False
    print("самотест пройден")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        check()
