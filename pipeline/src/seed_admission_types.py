"""Разовая загрузка типа отбора — ревью 2026-09, пункт 06. Как и
seed_formulas.py/seed_deadlines.py: находит существующий university по
slug и кладёт для него одну строку university_admission_type;
verified_at везде NULL, подтверждает только человек через Supabase
Studio (правило 6 CLAUDE.md).

Занесено только то, что уже твёрдо установлено в проекте, не всё
четырнадцать вузов (лучше меньше, но точно):

- ЛУ, РТУ, Вентспилс — 'competitive_score'. Это не новое наблюдение,
  а сама основа калькулятора: CLAUDE.md прямо называет их вузами,
  на которых подтверждена общая модель конкурсного балла.
- Turība — 'entrance_exam' (turiba.lv/en/admission/admission,
  проверено 2026-09-17): математический или социальный тест +
  собеседование + тест английского для всех абитуриентов бакалавриата,
  не сумма процентов ЦЭ.

Остальные десять вузов (LBTU, DU, VIA — гос.; RISEBA, BSA, SSE Riga,
RGSL, EKA, RNU, TSI — частные) сюда сознательно не попали: для
государственных нет причин считать, что у них та же модель без
проверки, а для частных нужно по одному заходу на сайт каждого —
не делали вслепую.

Запуск:
  python src/seed_admission_types.py             # записать черновики
  python src/seed_admission_types.py --selftest  # самотест без базы
"""

from __future__ import annotations

import sys

from dotenv import load_dotenv

from db import get_service_client

COMPETITIVE_SCORE_UNIVERSITIES = ["lu", "rtu", "venta", "rsu", "du", "lbtu", "juridiska-koledza", "psmk", "rnu", "bsa"]


def competitive_sources() -> dict[str, str]:
    """Источник типа «конкурс по баллам» — те же правила приёма, по которым
    записаны формулы и требования этих вузов (правило 5: без ссылки факт не
    показывается). RSU, DU, LBTU добавлены 2026-10-22: их правила
    считают конкурс из процентов ЦЭ (formulas_rsu.py, requirements_du.py,
    requirements_lbtu.py). У DU педагогические программы считают по
    аттестату и собеседованию — это тоже конкурс по баллам, только не по ЦЭ."""
    import formulas_rsu
    import requirements_du
    import requirements_private
    import requirements_lbtu
    import requirements_lu
    from seed_formulas import RTU_SOURCE_URL, VENTA_SOURCE_URL

    return {
        "lu": requirements_lu.SOURCE_URL,
        "rtu": RTU_SOURCE_URL,
        "venta": VENTA_SOURCE_URL,
        "rsu": formulas_rsu.SOURCE_URL,
        "du": requirements_du.SOURCE_URL,
        "lbtu": requirements_lbtu.SOURCE_URL,
        # частные вузы и колледжи (2026-10-22): правила приёма прямо говорят
        # «konkursa kārtībā, pamatojoties uz centralizēto eksāmenu rezultātiem»
        # (requirements_private.py; BSA — п. 10 своих правил)
        **{institution.slug: institution.source_url for institution in requirements_private.INSTITUTIONS},
        "bsa": "https://bsa.edu.lv/docs/admission/uznemsanas_noteikumi_BSA_2026_27.pdf",
    }

TURIBA_SOURCE_URL = "https://www.turiba.lv/en/admission/admission"


def seed(client, university_slug: str, selection_type: str, source_url: str | None = None) -> None:  # type: ignore[no-untyped-def]
    university = (
        client.table("university").select("id").eq("slug", university_slug).single().execute()
    )
    university_id = university.data["id"]

    # Тип отбора, который человек уже подтвердил, не трогаем: запись без
    # verified_at пометку не снимает, но selection_type под ней переписала
    # бы (аудит 2026-10-04, пункт 6; тот же приём, что в seed_deadlines.py).
    existing = (
        client.table("university_admission_type").select("verified_at").eq("university_id", university_id).execute().data
    )
    if existing and existing[0]["verified_at"]:
        print(f"{university_slug}: уже подтверждено — не трогаю")
        return

    row = {
        "university_id": university_id,
        "selection_type": selection_type,
        "source_url": source_url,
    }
    # upsert по primary key (university_id): повторный запуск не плодит
    # дубли. verified_at/verified_by в row нет — их ставит только человек.
    client.table("university_admission_type").upsert(row, on_conflict="university_id").execute()
    print(f"{university_slug}: {selection_type}")


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
    confirmed = _FakeClient(
        {
            "university": [{"id": "uni-1"}],
            "university_admission_type": [{"verified_at": "2026-12-14T10:00:00+00:00"}],
        }
    )
    seed(confirmed, "turiba", "entrance_exam", TURIBA_SOURCE_URL)
    assert confirmed.written.get("university_admission_type", []) == [], confirmed.written

    for rows in ([{"verified_at": None}], []):  # черновик и пустая таблица
        client = _FakeClient({"university": [{"id": "uni-1"}], "university_admission_type": rows})
        seed(client, "turiba", "entrance_exam", TURIBA_SOURCE_URL)
        written = client.written["university_admission_type"]
        assert len(written) == 1 and written[0]["selection_type"] == "entrance_exam", written
        assert "verified_at" not in written[0], written[0]
    print("самотест пройден")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        load_dotenv()
        client = get_service_client()
        sources = competitive_sources()
        for slug in COMPETITIVE_SCORE_UNIVERSITIES:
            seed(client, slug, "competitive_score", sources[slug])
        seed(client, "turiba", "entrance_exam", TURIBA_SOURCE_URL)
