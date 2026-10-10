"""Самотест прогона main.py на подставной базе — без сети и без Supabase.

Проверяет то, что нельзя проверить на живой базе, не сломав её:
1. временный сбой базы (502) лечится повтором, и вуз записывается;
2. постоянный сбой при записи одного вуза не роняет прогон: остальные вузы
   собираются, а запись о прогоне получает итог 'failed' — не остаётся «идёт»;
3. источник, упавший при сборе, тоже не мешает остальным;
4. поле, которое сборщик нашёл не у всех программ вуза, не обнуляется у
   остальных: в базу уходят строки с одним набором ключей.

  python src/main_selftest.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent))

import db_retry
import main
from models import ProgrammeDraft, UniversityDraft


class ApiError(Exception):
    """Как postgrest.APIError: числовой code — HTTP-статус страницы ошибки."""

    def __init__(self, code: int) -> None:
        super().__init__(f"JSON could not be generated (HTTP {code})")
        self.code = code


class FakeQuery:
    def __init__(self, client: "FakeClient", table: str) -> None:
        self.client, self.table = client, table
        self.operation, self.payload = "select", None

    def insert(self, payload):  # type: ignore[no-untyped-def]
        self.operation, self.payload = "insert", payload
        return self

    def upsert(self, payload, on_conflict=None):  # type: ignore[no-untyped-def]
        self.operation, self.payload = "upsert", payload
        return self

    def update(self, payload):  # type: ignore[no-untyped-def]
        self.operation, self.payload = "update", payload
        return self

    def select(self, *_):  # type: ignore[no-untyped-def]
        return self

    # фильтры на ответ подставной базы не влияют
    def eq(self, *_):  # type: ignore[no-untyped-def]
        return self

    in_ = or_ = lt = eq

    def execute(self):  # type: ignore[no-untyped-def]
        return self.client.respond(self)


class FakeClient:
    """Запоминает записи; для вуза из `failures` отвечает ошибкой нужное число раз."""

    def __init__(self, failures: dict[str, int]) -> None:
        self.failures = failures  # university.slug -> сколько раз ответить 502
        self.saved_universities: list[str] = []
        self.saved_programmes: list[str] = []
        self.run_updates: list[dict] = []
        self.existing_programmes: list[dict] = []  # что «уже лежит» в таблице programme
        self.upserted_rows: list[dict] = []

    def table(self, name: str) -> FakeQuery:
        return FakeQuery(self, name)

    def respond(self, query: FakeQuery):  # type: ignore[no-untyped-def]
        if query.table == "pipeline_run":
            if query.operation == "insert":
                return SimpleNamespace(data=[{"id": "run-1"}])
            if "finished_at" in (query.payload or {}):
                self.run_updates.append(query.payload)
            return SimpleNamespace(data=[])  # зависших записей нет
        if query.table == "university":
            slug = query.payload["slug"]
            if self.failures.get(slug, 0) > 0:
                self.failures[slug] -= 1
                raise ApiError(502)
            self.saved_universities.append(slug)
            return SimpleNamespace(data=[{"id": f"id-{slug}"}])
        if query.table == "programme" and query.operation == "upsert":
            self.saved_programmes += [row["slug"] for row in query.payload]
            self.upserted_rows += query.payload
        if query.table == "programme" and query.operation == "select":
            return SimpleNamespace(data=self.existing_programmes)
        return SimpleNamespace(data=[])


def fake_programme(slug: str, **extra) -> ProgrammeDraft:  # type: ignore[no-untyped-def]
    fields = {
        "slug": slug,
        "name_lv": "Programma",
        "degree_level": "bachelor",
        "language_of_instruction": "lv",
        "study_mode": "full_time",
        "funding_type": "paid",
        "source_url": "https://example.lv/programma",
        **extra,  # может заменить любое поле выше, например language_of_instruction=None
    }
    return ProgrammeDraft(**fields)


def fake_source(slug: str, broken: bool = False, programmes: list[ProgrammeDraft] | None = None) -> SimpleNamespace:
    university = UniversityDraft(
        slug=slug, name_lv=f"Augstskola {slug}", kind="private", city="riga", source_url="https://example.lv"
    )
    found = programmes or [fake_programme(f"{slug}-programma")]

    def scrape():  # type: ignore[no-untyped-def]
        if broken:
            raise RuntimeError("сайт не ответил")
        return university, found

    return SimpleNamespace(__name__=f"sources.{slug}", scrape=scrape)


def run(client: FakeClient, sources: list[SimpleNamespace]) -> int:
    """Запустить main.main() на подставной базе; вернуть код выхода."""
    main.get_service_client = lambda: client  # type: ignore[assignment]
    main.load_dotenv = lambda: None  # type: ignore[assignment]
    main.polite = SimpleNamespace(install=lambda: None, report_and_reset=lambda: "")  # type: ignore[assignment]
    main.SOURCES = sources  # type: ignore[assignment]
    main.execute = lambda query: db_retry.execute(query, sleep=lambda _: None)  # type: ignore[assignment]
    sys.argv = ["main.py"]
    try:
        main.main()
    except SystemExit as exit_:
        return int(exit_.code or 0)
    return 0


def selftest() -> None:
    # 1) два временных сбоя подряд — третья попытка проходит, прогон успешный
    client = FakeClient({"b": 2})
    assert run(client, [fake_source("a"), fake_source("b"), fake_source("c")]) == 0
    assert client.saved_universities == ["a", "b", "c"], client.saved_universities
    assert client.run_updates[-1]["status"] == "success", client.run_updates

    # 2) база не отвечает для вуза «b» совсем — «a» и «c» всё равно записаны,
    #    итог прогона записан как 'failed' с одной ошибкой
    client = FakeClient({"b": 99})
    assert run(client, [fake_source("a"), fake_source("b"), fake_source("c")]) == 1
    assert client.saved_universities == ["a", "c"], client.saved_universities
    assert client.saved_programmes == ["a-programma", "c-programma"], client.saved_programmes
    final = client.run_updates[-1]
    assert final["status"] == "failed" and final["error_count"] == 1, final
    assert "sources.b" in final["note"] and "запись в базу не удалась" in final["note"], final["note"]
    assert final["programme_count"] == 2, final

    # 3) источник упал при сборе — остальные собраны, итог 'failed'
    client = FakeClient({})
    assert run(client, [fake_source("a", broken=True), fake_source("c")]) == 1
    assert client.saved_universities == ["c"], client.saved_universities
    assert client.run_updates[-1]["status"] == "failed"

    # 4) сборщик нашёл срок аккредитации только у первой программы; у второй
    #    он уже лежит в базе (дописан другим скриптом) и подтверждение стоит.
    #    В базу должны уйти строки с одним набором ключей, и значение второй
    #    программы — то, что было в базе, а не пустота.
    client = FakeClient({})
    in_db = {
        "slug": "d-2", "verified_at": "2026-09-02T00:00:00+00:00", "verified_by": "owner",
        **{field: None for field in main.CONTENT_FIELDS},
        "name_lv": "Programma", "degree_level": "bachelor", "language_of_instruction": "lv",
        "study_mode": "full_time", "funding_type": "paid", "tuition_fee_currency": "EUR",
        "source_url": "https://example.lv/programma", "accreditation_valid_until": "2027-08-05",
    }
    client.existing_programmes = [in_db]
    source = fake_source(
        "d", programmes=[fake_programme("d-1", accreditation_valid_until="2030-01-01"), fake_programme("d-2")]
    )
    assert run(client, [source]) == 0
    first, second = client.upserted_rows
    assert first.keys() == second.keys(), sorted(first.keys() ^ second.keys())
    assert second["accreditation_valid_until"] == "2027-08-05", second["accreditation_valid_until"]
    assert "verified_at" not in second, "подтверждение не сбрасывалось — ключа в записи нет вовсе"

    # 5) сборщик не прочитал язык обучения у трёх программ. У той, что уже
    #    лежит в базе с английским, язык остаётся английским и подтверждение
    #    на месте; две новые без языка не записываются; программа с
    #    прочитанным языком пишется как обычно.
    client = FakeClient({})
    client.existing_programmes = [{**in_db, "slug": "e-known", "language_of_instruction": "en"}]
    source = fake_source(
        "e",
        programmes=[
            fake_programme("e-known", language_of_instruction=None),
            fake_programme("e-new-1", language_of_instruction=None),
            fake_programme("e-new-2", language_of_instruction=None),
            fake_programme("e-read"),
        ],
    )
    assert run(client, [source]) == 0
    by_slug = {row["slug"]: row for row in client.upserted_rows}
    assert sorted(by_slug) == ["e-known", "e-read"], sorted(by_slug)
    assert by_slug["e-known"]["language_of_instruction"] == "en", by_slug["e-known"]
    assert by_slug["e-read"]["language_of_instruction"] == "lv"
    assert "verified_at" not in by_slug["e-known"], "нечитаемый язык подтверждение не снимает"

    # 6) язык не прочитан ни у одной программы, и все они новые: записывать
    #    нечего, но прогон не падает — вуз сохранён, программ ноль.
    client = FakeClient({})
    source = fake_source("f", programmes=[fake_programme("f-1", language_of_instruction=None)])
    assert run(client, [source]) == 0
    assert client.saved_universities == ["f"] and client.upserted_rows == []

    print("самотест пройден")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    selftest()
