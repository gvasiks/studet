"""Эстония: записать в базу направление каждой программы (ee_programme_field).

Источник — тот же список программ государственного портала, из которого
собран каталог (sources/ee_haridusportaal.py): у записи стоят область,
направление и группу программ по классификатору ISCED-F. Запись портала
привязывается к программе каталога тем же разбором, что и при сборе
(catalog_rows), поэтому сначала должен пройти сбор каталога:
  python src/main.py ee_haridusportaal

Таблица — миграция 20261011180000_ee_programme_field.sql.

Запуск:
  python src/ee_load_fields.py --selftest
  python src/ee_load_fields.py            # показать сводку, без записи
  python src/ee_load_fields.py --apply
"""

from __future__ import annotations

import sys
from collections import Counter
from datetime import datetime, timezone

from sources.ee_haridusportaal import PORTAL, catalog_rows, university_slug


def single(node: object) -> tuple[str, str] | None:
    """Поле-справочник портала с одним значением: {"2464": "Ärindus ja haldus"}
    -> ("2464", "Ärindus ja haldus"). Пустое или из нескольких значений — None."""
    if isinstance(node, dict) and len(node) == 1:
        code, name = next(iter(node.items()))
        return str(code), str(name)
    return None


def fields_by_slug(records: list[dict]) -> tuple[dict[tuple[str, str], dict], int]:
    """(код учреждения, код программы) -> направление. Второе значение —
    сколько строк каталога осталось без направления (портал его не назвал)."""
    result: dict[tuple[str, str], dict] = {}
    without = 0
    for name, rows in catalog_rows(records).items():
        for record, _level, slug, _language in rows:
            broad = single(record.get("fieldIscedfBoard"))
            narrow = single(record.get("fieldIscedfNarrow"))
            detailed = single(record.get("fieldIscedfDetailed"))
            if broad is None or narrow is None:
                without += 1
                continue
            result[(university_slug(name), slug)] = {
                "broad_name": broad[1],
                "field_code": narrow[0],
                "field_name": narrow[1],
                "detailed_name": detailed[1] if detailed else None,
                "source_url": PORTAL + str(record["path"]),
            }
    return result, without


def _selftest() -> None:
    def record(nid: str, path: str, **fields: object) -> dict:
        base = {
            "nid": nid,
            "path": path,
            "title": "Õigusteadus",
            "fieldStudyProgrammeLevel": {"1": "Bakalaureuseõpe"},
            "fieldTeachingLanguage": {"1689": "eesti keel"},
            "fieldEducationalInstitution": {"5": {"title": "Tartu Ülikool"}},
            "fieldIscedfBoard": {"2463": "Ärindus, haldus ja õigus"},
            "fieldIscedfNarrow": {"2481": "Õigus"},
            "fieldIscedfDetailed": {"2482": "Õigus"},
        }
        base.update(fields)
        return base

    assert single({"2464": "Ärindus ja haldus"}) == ("2464", "Ärindus ja haldus")
    assert single([]) is None and single(None) is None and single({"1": "a", "2": "b"}) is None

    fields, without = fields_by_slug(
        [
            record("1", "/erialad/%C3%B5igusteadus"),
            # два языка — две строки каталога, направление одно
            record("2", "/erialad/informaatika", fieldTeachingLanguage={"1689": "eesti keel", "1690": "inglise keel"},
                   fieldIscedfBoard={"2525": "IKT"}, fieldIscedfNarrow={"2526": "IKT"}, fieldIscedfDetailed=[]),
            # направления нет — строка без него
            record("3", "/erialad/keemia", fieldIscedfNarrow=[]),
        ]
    )
    assert without == 1
    assert sorted(fields) == [("ut", "informaatika"), ("ut", "informaatika-en"), ("ut", "oigusteadus")], sorted(fields)
    law = fields[("ut", "oigusteadus")]
    assert (law["field_code"], law["field_name"], law["broad_name"], law["detailed_name"]) == ("2481", "Õigus", "Ärindus, haldus ja õigus", "Õigus")
    assert law["source_url"] == "https://haridusportaal.edu.ee/erialad/%C3%B5igusteadus"
    assert fields[("ut", "informaatika-en")]["detailed_name"] is None
    print("ee_load_fields selftest: ok")


def main() -> None:
    args = sys.argv[1:]
    sys.stdout.reconfigure(encoding="utf-8")
    if "--selftest" in args:
        _selftest()
        return
    from dotenv import load_dotenv

    import polite
    from db import fetch_all, get_service_client
    from db_retry import execute
    from sources.ee_haridusportaal import collect

    load_dotenv()
    polite.install()
    fields, without = fields_by_slug(collect())

    client = get_service_client()
    programmes = fetch_all(
        lambda: client.table("programme")
        .select("id, slug, university!inner(slug, country)")
        .eq("university.country", "EE")
        .order("id")
    )
    programme_id = {(row["university"]["slug"], row["slug"]): row["id"] for row in programmes}

    rows = [{"programme_id": programme_id[key], **field} for key, field in fields.items() if key in programme_id]
    missing = [key for key in fields if key not in programme_id]
    print(
        f"строк каталога с направлением: {len(fields)} | без направления на портале: {without} | "
        f"программ в базе: {len(programme_id)} | нет в базе: {len(missing)}"
    )
    print("по направлениям:", Counter(row["field_name"] for row in rows).most_common())

    if "--apply" not in args:
        print("\nзаписи не было (добавьте --apply)")
        return
    now = datetime.now(timezone.utc).isoformat()
    for row in rows:
        row["extracted_at"] = now
    for start in range(0, len(rows), 500):
        execute(client.table("ee_programme_field").upsert(rows[start : start + 500], on_conflict="programme_id"))
    print(f"записано: {len(rows)}")
    print(polite.report_and_reset())


if __name__ == "__main__":
    main()
