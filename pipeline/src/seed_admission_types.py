"""Черновики типа отбора (university_admission_type): одна строка на вуз,
verified_at пустой — подтверждает только человек (правило 6 CLAUDE.md;
решения владельца исполняет confirm_admission_types.py).

Тип отбора и его источник — в таблице SELECTION_TYPES ниже: вуз -> тип
отбора; ссылка на правила приёма — из тех же модулей, по которым записаны
формулы и требования (правило 5: без источника факт не показывается).
Вуза нет в таблице — тип не записывается: лучше меньше, но точно.

Сознательно не записаны:
- Valsts policijas koledža — конкурс и по баллам ЦЭ, и по испытаниям
  (физподготовка, тест памяти и латышского), ни один тип не подходит
  (docs/checks/REQUIREMENTS-REVIEW.md);
- EKA, LKA, RAI, TSI, LMA, SSE Riga, RGSL и др. — правил не нашли или не
  читали, вопрос в письме комиссиям (docs/checks/ADMISSION-COMMITTEE-QUESTIONS.md).

Запуск:
  python src/seed_admission_types.py             # записать черновики
  python src/seed_admission_types.py --selftest  # самотест без базы
"""

from __future__ import annotations

import sys

from dotenv import load_dotenv

from db import get_service_client

# вуз -> тип отбора. «Конкурс по баллам»: правила считают конкурс из
# процентов ЦЭ (у DU педагогические программы — по аттестату и собеседованию,
# это тоже баллы). «Вступительные испытания»: Turība — тест и собеседование
# у всех абитуриентов бакалавриата (проверено 2026-09-17); JVLMA — испытания
# по специальности, сданные ЦЭ только допускают к ним (2026-10-25).
SELECTION_TYPES = {
    **{
        slug: "competitive_score"
        for slug in (
            "lu", "rtu", "venta", "rsu", "du", "lbtu",
            "juridiska-koledza", "psmk", "rnu", "bsa", "via", "riseba", "bvk", "rbk", "r1mk",
        )
    },
    "turiba": "entrance_exam",
    "jvlma": "entrance_exam",
}

TURIBA_SOURCE_URL = "https://www.turiba.lv/en/admission/admission"
BSA_SOURCE_URL = "https://bsa.edu.lv/docs/admission/uznemsanas_noteikumi_BSA_2026_27.pdf"  # п. 10 правил


def source_urls() -> dict[str, str]:
    """Вуз -> ссылка на правила приёма, по которым определён тип отбора."""
    import formulas_rsu
    import requirements_du
    import requirements_lbtu
    import requirements_lu
    import requirements_private
    from seed_formulas import RTU_SOURCE_URL, VENTA_SOURCE_URL

    urls = {
        "lu": requirements_lu.SOURCE_URL,
        "rtu": RTU_SOURCE_URL,
        "venta": VENTA_SOURCE_URL,
        "rsu": formulas_rsu.SOURCE_URL,
        "du": requirements_du.SOURCE_URL,
        "lbtu": requirements_lbtu.SOURCE_URL,
        "bsa": BSA_SOURCE_URL,
        "turiba": TURIBA_SOURCE_URL,
    }
    # Частные вузы и колледжи — их правила в requirements_private.py. У JVLMA
    # два документа; тип отбора взят из первого (направление «Mākslas»).
    for institution in requirements_private.INSTITUTIONS:
        urls.setdefault(institution.slug, institution.source_url)
    return urls


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

    # у каждого вуза из таблицы есть источник (правило 5)
    urls = source_urls()
    assert all(urls.get(slug) for slug in SELECTION_TYPES), [slug for slug in SELECTION_TYPES if not urls.get(slug)]
    assert "izglitibas" not in urls["jvlma"], "JVLMA — по документу направления «Mākslas»"
    print("самотест пройден")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        load_dotenv()
        client = get_service_client()
        urls = source_urls()
        for slug, selection_type in SELECTION_TYPES.items():
            seed(client, slug, selection_type, urls[slug])
