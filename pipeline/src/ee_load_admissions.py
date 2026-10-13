"""Эстония: записать в базу последний конкурс каждой программы
(ee_admission) — сроки подачи и ссылку на страницу конкурса в SAIS.

Источник — тот же список программ государственного портала, из которого
собран каталог (sources/ee_haridusportaal.py). Портал хранит у программы
её последний конкурс, а не только открытый: на 2026-10-13 из 546 конкурсов
срок подачи ещё не прошёл у 16. Прошёл ли срок, решает сайт по closes_at.
Строки, конкурс которых с портала пропал, удаляются — иначе на сайте
остался бы срок, которого в источнике уже нет.

Сначала должен пройти сбор каталога:
  python src/main.py ee_haridusportaal

Таблица — миграция 20261013120000_ee_admission.sql.

Запуск:
  python src/ee_load_admissions.py --selftest
  python src/ee_load_admissions.py            # показать сводку, без записи
  python src/ee_load_admissions.py --apply
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from datetime import datetime, timezone

from sources.ee_haridusportaal import PORTAL, catalog_rows, university_slug

SAIS_URL = re.compile(r"^https://(www\.)?sais\.ee/AdmissionSearch/View/\d+$")


def moment(value: object) -> str | None:
    """Время портала — секунды с 1970 года строкой («1791147600»)."""
    try:
        seconds = int(str(value))
    except (TypeError, ValueError):
        return None
    if seconds <= 0:
        return None
    return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()


def admission_of(record: dict) -> dict | None:
    """Конкурс записи портала; None — конкурса нет или он записан непонятно."""
    url = str(record.get("fieldAdmissionLink") or "").strip()
    try:
        admission_id = int(str(record.get("fieldAdmissionId")))
    except (TypeError, ValueError):
        return None
    if not SAIS_URL.match(url) or not url.endswith(f"/{admission_id}"):
        return None
    return {
        "admission_id": admission_id,
        "sais_url": url,
        "opens_at": moment(record.get("fieldAdmissionBeginDate")),
        "closes_at": moment(record.get("fieldAdmissionEndDate")),
        "source_url": PORTAL + str(record["path"]),
    }


def admissions_by_slug(records: list[dict]) -> tuple[dict[tuple[str, str], dict], int]:
    """(код учреждения, код программы) -> конкурс. Второе значение — у
    скольких записей портала есть ссылка на конкурс, которую не удалось
    разобрать (не адрес SAIS или номер не совпал с адресом)."""
    result: dict[tuple[str, str], dict] = {}
    unreadable = 0
    for name, rows in catalog_rows(records).items():
        for record, _level, slug, _language in rows:
            admission = admission_of(record)
            if admission is None:
                if record.get("fieldAdmissionLink") or record.get("fieldAdmissionId"):
                    unreadable += 1
                continue
            result[(university_slug(name), slug)] = admission
    return result, unreadable


def _selftest() -> None:
    def record(nid: str, path: str, **fields: object) -> dict:
        base = {
            "nid": nid,
            "path": path,
            "title": "Õigusteadus",
            "fieldStudyProgrammeLevel": {"1": "Bakalaureuseõpe"},
            "fieldTeachingLanguage": {"1689": "eesti keel"},
            "fieldEducationalInstitution": {"5": {"title": "Tartu Ülikool"}},
            "fieldAdmissionId": "20554",
            "fieldAdmissionLink": "https://sais.ee/AdmissionSearch/View/20554",
            "fieldAdmissionBeginDate": "1791147600",
            "fieldAdmissionEndDate": 1792357140,
        }
        base.update(fields)
        return base

    assert moment("1791147600") == "2026-10-04T21:00:00+00:00", moment("1791147600")
    assert moment(None) is None and moment("") is None and moment("0") is None and moment("abc") is None

    found = admission_of(record("1", "/erialad/x"))
    assert found == {
        "admission_id": 20554,
        "sais_url": "https://sais.ee/AdmissionSearch/View/20554",
        "opens_at": "2026-10-04T21:00:00+00:00",
        "closes_at": "2026-10-18T20:59:00+00:00",
        "source_url": "https://haridusportaal.edu.ee/erialad/x",
    }, found
    # конкурса нет; чужой адрес; номер не совпал с адресом — не записывается
    assert admission_of(record("1", "/erialad/x", fieldAdmissionId=None, fieldAdmissionLink=None)) is None
    assert admission_of(record("1", "/erialad/x", fieldAdmissionLink="https://example.com/AdmissionSearch/View/20554")) is None
    assert admission_of(record("1", "/erialad/x", fieldAdmissionId="1")) is None
    # даты может не быть — конкурс остаётся, срок пустой
    assert admission_of(record("1", "/erialad/x", fieldAdmissionEndDate=None))["closes_at"] is None

    admissions, unreadable = admissions_by_slug(
        [
            record("1", "/erialad/%C3%B5igusteadus"),
            # два языка — две строки каталога, конкурс один
            record("2", "/erialad/informaatika", fieldTeachingLanguage={"1689": "eesti keel", "1690": "inglise keel"}),
            record("3", "/erialad/keemia", fieldAdmissionId=None, fieldAdmissionLink=None),
            record("4", "/erialad/ajalugu", fieldAdmissionLink="https://example.com/x"),
        ]
    )
    assert sorted(admissions) == [("ut", "informaatika"), ("ut", "informaatika-en"), ("ut", "oigusteadus")], sorted(admissions)
    assert unreadable == 1
    print("ee_load_admissions selftest: ok")


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
    admissions, unreadable = admissions_by_slug(collect())

    client = get_service_client()
    programmes = fetch_all(
        lambda: client.table("programme")
        .select("id, slug, university!inner(slug, country)")
        .eq("university.country", "EE")
        .order("id")
    )
    programme_id = {(row["university"]["slug"], row["slug"]): row["id"] for row in programmes}

    rows = [{"programme_id": programme_id[key], **admission} for key, admission in admissions.items() if key in programme_id]
    now = datetime.now(timezone.utc).isoformat()
    still_open = sum(1 for row in rows if row["closes_at"] is None or row["closes_at"] >= now)
    print(
        f"строк каталога с конкурсом: {len(admissions)} | ссылка не разобрана: {unreadable} | "
        f"программ в базе: {len(programme_id)} | к записи: {len(rows)} | срок ещё не прошёл: {still_open}"
    )
    print("по месяцам окончания подачи:", sorted(Counter((row["closes_at"] or "без срока")[:7] for row in rows).items()))

    if "--apply" not in args:
        print("\nзаписи не было (добавьте --apply)")
        return

    for row in rows:
        row["extracted_at"] = now
    for start in range(0, len(rows), 500):
        execute(client.table("ee_admission").upsert(rows[start : start + 500], on_conflict="programme_id"))

    # Конкурсы, которых на портале больше нет: строка удаляется.
    current = {row["programme_id"] for row in rows}
    stored = fetch_all(lambda: client.table("ee_admission").select("programme_id").order("programme_id"))
    stale = [row["programme_id"] for row in stored if row["programme_id"] not in current]
    # Конкурсы закрываются по одному, а не половиной сразу: если пропало
    # больше половины, скорее портал отдал неполный список — не удаляем.
    if stored and len(stale) > len(stored) / 2:
        print(
            f"записано: {len(rows)} | пропавших с портала {len(stale)} из {len(stored)} — больше половины, "
            "НЕ УДАЛЕНЫ: проверьте портал вручную и запустите ещё раз."
        )
        sys.exit(2)
    for start in range(0, len(stale), 200):
        execute(client.table("ee_admission").delete().in_("programme_id", stale[start : start + 200]))
    print(f"записано: {len(rows)} | удалено пропавших с портала: {len(stale)}")
    print(polite.report_and_reset())


if __name__ == "__main__":
    main()
