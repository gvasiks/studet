"""Разовая загрузка дедлайнов подачи — ревью 2026-09, пункт 04. Как и
seed_formulas.py: находит существующий university по slug и кладёт для
него application_round; verified_at везде NULL, подтверждает только
человек через Supabase Studio (правило 6 CLAUDE.md).

Живьём проверено 2026-09-17, что реально опубликовано:

- ЛУ (lu.lv/gribustudet/uznemsanas-kartiba/pamatstudijas/): "Šobrīd
  uzņemšana uz 2026./2027. akadēmiskā gada rudens semestri ir
  noslēgusies! Informācija par 2027./2028. akadēmiskā gada uzņemšanu
  tiks papildināta." — календаря на 2027/2028 нет, страница прямо это
  говорит.
- РТУ (rtu.lv/.../pieteiksanas-bakalaura-limena-studijam): "Līdz
  14. augustam turpinās uzņemšana..." без указания года — похоже на не
  до конца обновлённую страницу прошлого цикла, не факт, на который
  можно сослаться.
- Turība, латышский трек (turiba.lv/lv/uznemsana): даты даны на
  2026./2027. gadu (reģistrācija no 2026-01-05, līgumi no 2026-07-06) —
  тоже прошлый цикл, не 2027/2028.

Ни одно из трёх НЕ даёт дату, актуальную для сезона, к которому готовится
январский релиз 2027 — не потому что искали плохо, а потому что ни один
из вузов пока не опубликовал 2027./2028. gada календарь (сентябрь —
слишком рано, тот же разрыв, что и с таблицей коэффициентов ЛУ в
seed_formulas.py). Даты CLAUDE.md ("9–20 июля 2027", "Turība 5 января")
— это ориентир из бизнес-анализа, не подтверждённый источником факт;
использовать их здесь как правило 5 CLAUDE.md запрещает. Повторить
проверку ближе к делу (ноябрь-декабрь 2026) — тогда это и войдёт в
годовой цикл конвейера.

Единственное, что оказалось пригодно уже сейчас — международный (EN)
трек Turība: там расписание не привязано к учебному году, а
представляет собой два повторяющихся окна приёма (turiba.lv/en/admission/admission,
раздел INTAKES, проверено 2026-09-17). Год не указан вообще — значит
не устареет к январю 2027 само по себе.

Запуск:
  python src/seed_deadlines.py             # записать черновики
  python src/seed_deadlines.py --selftest  # самотест без базы
"""

from __future__ import annotations

import sys
from datetime import date

from dotenv import load_dotenv

from db import get_service_client

TURIBA_SOURCE_URL = "https://www.turiba.lv/en/admission/admission"

# opens_on/closes_on — год условный (текущий отсчётный), поле label и
# note объясняют, что окно повторяется ежегодно на эти же даты.
TURIBA_EN_ROUNDS = [
    {
        "language_of_instruction": "en",
        "label": "Autumn intake",
        "opens_on": date(2026, 2, 1),
        "closes_on": date(2026, 8, 1),
        "note": "Studies begin at the end of September. Window repeats yearly (Feb 1 – Aug 1), not tied to a specific academic year.",
    },
    {
        "language_of_instruction": "en",
        "label": "Winter intake",
        "opens_on": date(2026, 8, 2),
        "closes_on": date(2026, 12, 1),
        "note": "Studies begin in February. Window repeats yearly (Aug 2 – Dec 1), not tied to a specific academic year.",
    },
]


def seed(client, university_slug: str, rounds: list[dict], source_url: str) -> None:  # type: ignore[no-untyped-def]
    university = (
        client.table("university").select("id").eq("slug", university_slug).single().execute()
    )
    university_id = university.data["id"]

    # Сроки, которые человек уже подтвердил (правило 6 CLAUDE.md). Запись без
    # verified_at пометку не снимает, но даты под ней переписала бы: повторный
    # запуск вернул бы старые opens_on/closes_on под бейджем «проверено»
    # (аудит 2026-10-04, пункт 6). Поэтому подтверждённое не трогаем вовсе —
    # так же, как seed_formulas.py.
    existing = (
        client.table("application_round").select("label, verified_at").eq("university_id", university_id).execute().data
    )
    confirmed = {row["label"] for row in existing if row["verified_at"]}

    for entry in rounds:
        if entry["label"] in confirmed:
            print(f"{university_slug}: {entry['label']} — уже подтверждено, не трогаю")
            continue
        row = {
            "university_id": university_id,
            "degree_level": entry.get("degree_level"),
            "language_of_instruction": entry.get("language_of_instruction"),
            "label": entry["label"],
            "opens_on": entry["opens_on"].isoformat(),
            "closes_on": entry["closes_on"].isoformat(),
            "note": entry.get("note"),
            "source_url": source_url,
        }
        # upsert, не insert: повторный запуск не должен плодить дубли.
        # verified_at/verified_by в row нет вовсе — их ставит только человек.
        client.table("application_round").upsert(row, on_conflict="university_id,label").execute()
        print(f"{university_slug}: {entry['label']}")


class _FakeTable:
    """Поддельная таблица для самотеста: отдаёт заранее заданные строки и
    запоминает, что в неё пытались записать."""

    def __init__(self, rows: list[dict], written: list[dict]) -> None:
        self._rows = rows
        self._written = written
        self._single = False

    def select(self, *_columns):  # type: ignore[no-untyped-def]
        return self

    def eq(self, *_filter):  # type: ignore[no-untyped-def]
        return self

    def single(self):  # type: ignore[no-untyped-def]
        self._single = True
        return self

    def upsert(self, row, on_conflict=None):  # type: ignore[no-untyped-def]
        self._written.append(row)
        return self

    def execute(self):  # type: ignore[no-untyped-def]
        data = self._rows[0] if self._single else self._rows
        return type("Result", (), {"data": data})()


class _FakeClient:
    def __init__(self, tables: dict[str, list[dict]]) -> None:
        self._tables = tables
        self.written: dict[str, list[dict]] = {}

    def table(self, name: str) -> _FakeTable:
        return _FakeTable(self._tables.get(name, []), self.written.setdefault(name, []))


def selftest() -> None:
    client = _FakeClient(
        {
            "university": [{"id": "uni-1"}],
            "application_round": [
                {"label": "Autumn intake", "verified_at": "2026-12-14T10:00:00+00:00"},
                {"label": "Winter intake", "verified_at": None},
            ],
        }
    )
    seed(client, "turiba", TURIBA_EN_ROUNDS, TURIBA_SOURCE_URL)
    written = client.written["application_round"]
    assert [row["label"] for row in written] == ["Winter intake"], written
    assert "verified_at" not in written[0] and "verified_by" not in written[0], written[0]

    # в пустой базе пишутся оба срока
    empty = _FakeClient({"university": [{"id": "uni-1"}]})
    seed(empty, "turiba", TURIBA_EN_ROUNDS, TURIBA_SOURCE_URL)
    assert len(empty.written["application_round"]) == 2
    print("самотест пройден")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        load_dotenv()
        seed(get_service_client(), "turiba", TURIBA_EN_ROUNDS, TURIBA_SOURCE_URL)
