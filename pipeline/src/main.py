from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

import polite
from db import get_service_client
from sources import bsa, du, eka, ekra, jvlma, lbtu, lka, lma, lnaa, lu, lutera, niid_colleges, niid_universities, rai, rgsl, riseba, rnu, rsu, rtu_catalog, rtu_liepaja, sse_riga, tsi, turiba, venta, via

SOURCES = [turiba, riseba, rtu_liepaja, tsi, bsa, sse_riga, rgsl, lu, venta, lbtu, du, eka, rnu, rtu_catalog, via, rsu, lka, lma, jvlma, rai, lnaa, lutera, ekra, niid_colleges, niid_universities]

# Ревью 2026-09, пункт 05: конвейер должен падать, если число найденных
# программ у источника резко просело — lu.py однажды тихо потерял целый
# факультет (Eksakto zinātņu un tehnoloģiju), и это обнаружилось только
# при ручной сверке формул, не автоматически (см. коммент в
# seed_formulas.py и коммит "Fix lu.py scraper missing Eksakto faculty
# programmes entirely"). Порог — снимок числа программ на 2026-09-17,
# по каждому источнику отдельно (не по вузу): у РТУ их два,
# rtu_catalog.py и rtu_liepaja.py, оба пишут в один и тот же
# university.slug="rtu".
#
# Проверка односторонняя (len(programmes) < порог) — рост нормален, вуз
# может добавить программу в любой момент. Если число ЗАКОНОМЕРНО
# уменьшилось (вуз реально снял программу с набора), проверьте это на
# сайте вуза вручную и поднимите порог здесь же, а не удаляйте проверку.
MIN_PROGRAMME_COUNT = {
    "sources.turiba": 17,
    "sources.riseba": 13,
    "sources.rtu_liepaja": 3,
    "sources.tsi": 27,
    # 2026-09-20: 13 -> 12, BSA закрыла "Digital Visualization Design"
    # (computer-design.html отдаёт 404, в списке бакалавриата её нет)
    "sources.bsa": 12,
    "sources.sse_riga": 1,
    "sources.rgsl": 4,
    "sources.lu": 166,
    "sources.venta": 13,
    "sources.lbtu": 9,
    "sources.du": 10,
    "sources.eka": 21,
    "sources.rnu": 8,
    # 2026-09-20: 124 -> 163. Раньше терялись программы в нескольких городах, только
    # в Лиепае и морские (Jūras akadēmija) — см. docstring rtu_catalog.py
    "sources.rtu_catalog": 163,
    "sources.via": 21,
    "sources.rsu": 58,
    "sources.lka": 15,
    "sources.lma": 35,
    "sources.jvlma": 7,
    "sources.rai": 16,
    "sources.lnaa": 6,
    "sources.lutera": 1,
    "sources.ekra": 6,
    # niid_colleges отдаёт много учреждений сразу — порог по каждому
    # ("модуль:slug"), снимок на 2026-09-20
    "sources.niid_colleges:dmk": 7,
    "sources.niid_colleges:psmk": 12,
    "sources.niid_colleges:rmk": 4,
    "sources.niid_colleges:r1mk": 2,
    "sources.niid_colleges:ljk": 5,
    "sources.niid_colleges:malnavas-koledza": 6,
    "sources.niid_colleges:rbk": 5,
    "sources.niid_colleges:skmk": 6,
    "sources.niid_colleges:rtk": 8,
    "sources.niid_colleges:siva": 4,
    "sources.niid_colleges:ucak": 1,
    "sources.niid_colleges:vpk": 1,
    "sources.niid_colleges:vrsk": 1,
    "sources.niid_colleges:alberta": 9,
    "sources.niid_colleges:gfk": 2,
    "sources.niid_colleges:juridiska-koledza": 23,
    "sources.niid_colleges:bvk": 8,
    "sources.niid_colleges:rmenk": 2,
    "sources.niid_colleges:hotel-school": 2,
    "sources.niid_colleges:novikonta": 2,
    "sources.niid_colleges:rti": 1,
    "sources.niid_colleges:rarzi": 1,
    # niid_universities: добор недостающих программ из NIID (аудит 2026-09-20),
    # снимок на тот же день
    "sources.niid_universities:lbtu": 56,
    "sources.niid_universities:du": 56,
    "sources.niid_universities:turiba": 17,
    "sources.niid_universities:riseba": 15,
    "sources.niid_universities:rsu": 9,
}


# Со скольки пропусков подряд программа скрывается от публики. То же число
# в политике RLS программы (supabase/migrations/20260920133000_*.sql).
HIDE_AFTER_MISSED_RUNS = 2


class CatalogCompletenessError(RuntimeError):
    pass


def main() -> None:
    load_dotenv()
    polite.install()  # честный User-Agent, паузы, robots.txt — см. polite.py
    client = get_service_client()
    now = datetime.now(timezone.utc).isoformat()

    # python src/main.py rsu lmu — прогнать только перечисленные источники
    # (по имени модуля); без аргументов — все. Так новый вуз добавляется,
    # не перескрапливая остальные четырнадцать.
    only = set(sys.argv[1:])
    sources = [s for s in SOURCES if not only or s.__name__.split(".")[-1] in only]

    # Один упавший источник не должен останавливать остальные: ночной прогон
    # иначе теряет всё, что стоит после него в списке. Ошибки копятся и
    # печатаются в конце, код возврата ненулевой — GitHub Actions покажет
    # прогон красным. Запись в базу для источника, не прошедшего проверку
    # полноты, не происходит: проверка стоит до неё.
    errors: list[str] = []

    for source in sources:
        multi = hasattr(source, "scrape_all")  # колледжи из NIID — много учреждений сразу
        try:
            results = source.scrape_all() if multi else [source.scrape()]
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{source.__name__}: {type(exc).__name__}: {exc}")
            print(f"ОШИБКА {errors[-1]}")
            print(polite.report_and_reset())
            continue

        # учреждение, у которого есть порог, но которого нет в результате
        # (колледж пропал целиком), — тоже сбой, а не "ноль программ"
        if multi:
            got = {f"{source.__name__}:{university.slug}" for university, _ in results}
            for lost in (k for k in MIN_PROGRAMME_COUNT if k.startswith(f"{source.__name__}:") and k not in got):
                errors.append(f"{lost}: учреждение не вернуло ни одной программы — проверьте вручную.")
                print(f"ОШИБКА {errors[-1]}")

        for university, programmes in results:
            key = f"{source.__name__}:{university.slug}" if multi else source.__name__
            try:
                _check_and_save(client, now, key, university, programmes)
            except CatalogCompletenessError as exc:
                errors.append(str(exc))
                print(f"ОШИБКА {exc}")

        print(polite.report_and_reset())

    if errors:
        print(f"\nИтого сбоев: {len(errors)}")
        for error in errors:
            print(f" - {error[:300]}")
        sys.exit(1)


def _check_and_save(client, now: str, key: str, university, programmes) -> None:  # type: ignore[no-untyped-def]
    minimum = MIN_PROGRAMME_COUNT.get(key)
    if minimum is not None and len(programmes) < minimum:
        raise CatalogCompletenessError(
            f"{key}: нашёл {len(programmes)} программ, ожидал минимум {minimum}. "
            "Похоже на баг сборщика (например, тихо потерянный раздел сайта), а не на "
            "сокращение набора у вуза — проверьте вручную. Если сокращение подтвердится, "
            "поднимите порог в MIN_PROGRAMME_COUNT (main.py)."
        )

    uni_row = university.model_dump(exclude_none=True)
    uni_row["extracted_at"] = now
    result = client.table("university").upsert(uni_row, on_conflict="slug").execute()
    university_id = result.data[0]["id"]

    programme_rows = []
    for programme in programmes:
        row = programme.model_dump(exclude_none=True, mode="json")
        row["university_id"] = university_id
        row["extracted_at"] = now
        row["source_key"] = key
        row["missed_runs"] = 0  # найдена на сайте — счётчик пропусков обнуляется
        programme_rows.append(row)

    if programme_rows:
        client.table("programme").upsert(programme_rows, on_conflict="university_id,slug").execute()

    missing = _count_missed(client, university_id, key, {row["slug"] for row in programme_rows})
    print(f"{key}: upserted 1 university, {len(programme_rows)} programmes" + _missed_note(missing))


def _count_missed(client, university_id: str, key: str, seen_slugs: set[str]) -> list[dict]:  # type: ignore[no-untyped-def]
    """Программы этого источника, которых на сайте больше нет: +1 к счётчику
    пропусков. Вызывается только после прохождения проверки полноты и записи —
    сбойный прогон (сайт лёг, сборщик сломался) ничего не скрывает. Строки без
    source_key (записаны до миграции) считаются принадлежащими любому
    источнику вуза: это ровно те, что ни один источник не нашёл."""
    owned = (
        client.table("programme")
        .select("id,slug,name_lv,name_en,missed_runs")
        .eq("university_id", university_id)
        .or_(f"source_key.eq.{key},source_key.is.null")
        .execute()
        .data
    )
    missing = [row for row in owned if row["slug"] not in seen_slugs]
    for row in missing:
        # source_key здесь не трогаем: строка без отметки может принадлежать
        # другому источнику этого же вуза (лиепайские программы РТУ до первого
        # прогона rtu_liepaja), и чужой прогон не должен её присваивать
        client.table("programme").update({"missed_runs": row["missed_runs"] + 1}).eq("id", row["id"]).execute()
        row["missed_runs"] += 1
    return missing


def _missed_note(missing: list[dict]) -> str:
    if not missing:
        return ""
    hidden = [row for row in missing if row["missed_runs"] >= HIDE_AFTER_MISSED_RUNS]
    names = ", ".join((row["name_en"] or row["name_lv"] or row["slug"]) for row in missing[:3])
    return (
        f"\n  не найдено на сайте: {len(missing)} ({names}{' …' if len(missing) > 3 else ''}); "
        f"скрыто от публики: {len(hidden)} (порог — {HIDE_AFTER_MISSED_RUNS} прогона подряд)"
    )


if __name__ == "__main__":
    main()
