"""Повтор запроса к базе при временном сбое.

Зачем. Supabase изредка отвечает 502/503 (сбой на стороне Cloudflare или
PostgREST) или обрывает соединение. Для сбора каталога это означало падение
всего прогона на первом же таком ответе: вузы, стоящие дальше в списке, не
собирались, а запись о прогоне оставалась в состоянии «идёт» (замечено
2026-09-24 на `university.upsert`). Повтор через несколько секунд почти
всегда проходит.

Повторяется только то, что может пройти само:
- ответ с кодом 5xx или 429 (у supabase-py это APIError с числовым `code`);
- сетевой сбой: таймаут, обрыв, отказ соединения (httpx.TransportError).
Остальное — нарушение ограничения, неверный запрос, отказ в доступе — от
повтора не изменится и пробрасывается сразу.

Каждый запрос в main.py идемпотентен (upsert, select, update с готовым
значением), поэтому повторять его безопасно. Исключение — insert: если ответ
потерялся, а строка уже записана, повтор создаст вторую. Для pipeline_run это
терпимо: лишняя строка останется «идёт» и будет закрыта как прерванная.

  python src/db_retry.py --selftest   # самотест без сети и базы
"""

from __future__ import annotations

import sys
import time
from collections.abc import Callable
from typing import Any

import httpx

# Паузы перед второй и третьей попыткой, секунды.
PAUSES = (5.0, 15.0)


def is_transient(exc: BaseException) -> bool:
    """Может ли тот же запрос пройти, если его просто повторить."""
    if isinstance(exc, httpx.TransportError):
        return True
    # supabase-py: APIError.code — код PostgREST («PGRST116», «23505») или,
    # когда вместо JSON пришла страница ошибки, числовой HTTP-статус (502).
    code = getattr(exc, "code", None)
    try:
        status = int(code)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False
    return status == 429 or 500 <= status <= 599


def execute(query: Any, pauses: tuple[float, ...] = PAUSES, sleep: Callable[[float], None] = time.sleep) -> Any:
    """`query.execute()` с повтором при временном сбое.

    query — собранный запрос supabase-py (всё, у чего есть `.execute()`).
    Попыток — на одну больше, чем пауз. Последняя ошибка пробрасывается.
    """
    for attempt, pause in enumerate((*pauses, None), start=1):
        try:
            return query.execute()
        except Exception as exc:  # noqa: BLE001
            if pause is None or not is_transient(exc):
                raise
            print(
                f"база: временный сбой ({type(exc).__name__}: {str(exc)[:120]}), "
                f"попытка {attempt} из {len(pauses) + 1} — повтор через {pause:g} с"
            )
            sleep(pause)
    raise AssertionError("недостижимо")  # цикл всегда кончается return или raise


def selftest() -> None:
    class FakeApiError(Exception):
        def __init__(self, code: object) -> None:
            super().__init__(f"code={code}")
            self.code = code

    assert is_transient(FakeApiError(502)) and is_transient(FakeApiError("503")) and is_transient(FakeApiError(429))
    assert not is_transient(FakeApiError("23505")), "нарушение ограничения повтором не лечится"
    assert not is_transient(FakeApiError("PGRST116")) and not is_transient(FakeApiError(404))
    assert not is_transient(FakeApiError(None)) and not is_transient(ValueError("x"))
    assert is_transient(httpx.ConnectError("нет связи")) and is_transient(httpx.ReadTimeout("долго"))

    class FakeQuery:
        """Падает заданными ошибками по очереди, потом отвечает."""

        def __init__(self, failures: list[Exception]) -> None:
            self.failures = failures
            self.calls = 0

        def execute(self) -> str:
            self.calls += 1
            if self.failures:
                raise self.failures.pop(0)
            return "ok"

    waited: list[float] = []

    query = FakeQuery([FakeApiError(502), httpx.ReadTimeout("долго")])
    assert execute(query, sleep=waited.append) == "ok"
    assert query.calls == 3 and waited == [5.0, 15.0], (query.calls, waited)

    waited.clear()
    query = FakeQuery([FakeApiError(502), FakeApiError(502), FakeApiError(502)])
    try:
        execute(query, sleep=waited.append)
    except FakeApiError:
        pass
    else:
        raise AssertionError("после трёх сбоев ошибка должна дойти до вызывающего")
    assert query.calls == 3 and waited == [5.0, 15.0], "три попытки, не больше"

    waited.clear()
    query = FakeQuery([FakeApiError("23505")])
    try:
        execute(query, sleep=waited.append)
    except FakeApiError:
        pass
    else:
        raise AssertionError("постоянная ошибка пробрасывается сразу")
    assert query.calls == 1 and waited == [], "постоянную ошибку не повторяем"

    print("самотест пройден")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        print(__doc__)
