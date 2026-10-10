from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

import polite
from catalog_diff import (
    CONTENT_FIELDS,
    compute_diff,
    drop_new_without,
    fill_missing_keys,
    format_report,
    suspicious_names,
)
from db import get_service_client
from db_retry import execute
from scrape_scope import LOCAL_ONLY
from sources import bsa, du, eka, ekra, jvlma, lbtu, lka, lma, lnaa, lt_lamabpo, lu, lutera, niid_colleges, niid_universities, rai, rgsl, riseba, rnu, rsu, rtu_catalog, rtu_liepaja, sse_riga, tsi, turiba, venta, via

SOURCES = [turiba, riseba, rtu_liepaja, tsi, bsa, sse_riga, rgsl, lu, venta, lbtu, du, eka, rnu, rtu_catalog, via, rsu, lka, lma, jvlma, rai, lnaa, lutera, ekra, niid_colleges, niid_universities, lt_lamabpo]

# Источники, которые запускаются только по имени: `python src/main.py lt_lamabpo`.
# У Литвы своё расписание (.github/workflows/scrape-lithuania.yml) и своя
# команда для сбора с компьютера владельца (pipeline/src/lt_refresh.py): её
# сбор не должен попадать в недельный латвийский прогон и красить его, если
# литовский реестр не ответил. Остаётся здесь и после запуска Литвы.
BY_NAME_ONLY = {"lt_lamabpo"}

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
    # 2026-10-10: 163 -> 237. Двуязычная программа теперь пишется двумя записями
    # (rtu_languages.py): найдено 247, из них 83 английские. Порог ниже
    # найденного на 10, а не на 1: английская запись появляется только при
    # прочитанной карточке, и пара таймаутов сайта не должна срывать весь сбор.
    "sources.rtu_catalog": 237,
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
    # Литва: снимок 2026-10-05 (28 учреждений, 1020 строк каталога). Порог —
    # на учреждение. Срабатывает и тогда, когда реестр AIKOS отдал не все
    # карточки: строка без уровня или языка в каталог не попадает, и число
    # падает ниже порога. Список общего приёма обновляется раз в год —
    # после обновления пороги пересматриваются вручную, как у латвийских.
    "sources.lt_lamabpo:ehu": 14,
    "sources.lt_lamabpo:ilk": 12,
    "sources.lt_lamabpo:ism": 6,
    "sources.lt_lamabpo:kk": 63,
    "sources.lt_lamabpo:kok": 9,
    "sources.lt_lamabpo:ksu": 13,
    "sources.lt_lamabpo:ktu": 69,
    "sources.lt_lamabpo:ku": 44,
    "sources.lt_lamabpo:kvk": 34,
    "sources.lt_lamabpo:lcc": 6,
    "sources.lt_lamabpo:lik": 26,
    "sources.lt_lamabpo:lka-lt": 2,
    "sources.lt_lamabpo:lmta": 11,
    "sources.lt_lamabpo:lsmu": 18,
    "sources.lt_lamabpo:lsu": 11,
    "sources.lt_lamabpo:ltvk": 78,
    "sources.lt_lamabpo:mru": 34,
    "sources.lt_lamabpo:pk": 19,
    "sources.lt_lamabpo:smk": 92,
    "sources.lt_lamabpo:svk": 32,
    "sources.lt_lamabpo:uk": 22,
    "sources.lt_lamabpo:vda": 30,
    "sources.lt_lamabpo:vdk": 7,
    "sources.lt_lamabpo:vdu": 71,
    "sources.lt_lamabpo:vilnius-tech": 85,
    "sources.lt_lamabpo:vk": 71,
    "sources.lt_lamabpo:vu": 108,
    "sources.lt_lamabpo:vvk": 33,
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
    #
    # Два флага про источники, которые сервер GitHub собрать не может
    # (scrape_scope.py):
    #   --skip-local — все, кроме них (так запускает расписание GitHub);
    #   --local      — только они (так запускает владелец на своём компьютере).
    args = sys.argv[1:]
    skip_local = "--skip-local" in args
    only = {arg for arg in args if not arg.startswith("--")}
    if "--local" in args:
        only |= set(LOCAL_ONLY)

    def _name(source) -> str:  # type: ignore[no-untyped-def]
        return source.__name__.split(".")[-1]

    sources = [
        s
        for s in SOURCES
        if (not only or _name(s) in only) and not (skip_local and _name(s) in LOCAL_ONLY)
        and (_name(s) in only or _name(s) not in BY_NAME_ONLY)
    ]

    # План 2026-09-21, неделя 1, пункт 08: начало прогона фиксируется СРАЗУ,
    # до единого запроса к вузам, — если прогон упадёт необработанным
    # исключением (не через errors ниже) или зависнет на таймауте GitHub
    # Actions, в pipeline_run всё равно останется строка status='running',
    # и сторож (check_pipeline_health.py) увидит, что "последнего успешного"
    # давно не было, а не тишину. full_run=False у точечного перезапуска
    # (имена источников или --local в аргументах) — pipeline_health считает
    # "последний успешный сбор" только по полным прогонам, иначе починка
    # одного вуза молча обновляла бы дату, скрывая остановившееся
    # расписание. Прогон с --skip-local — полный: это всё, что расписание
    # GitHub вообще может собрать; за остальным следит
    # check_local_sources.py.
    _close_stale_runs(client)
    run_id = execute(client.table("pipeline_run").insert({"started_at": now, "full_run": not only})).data[0]["id"]

    # Один упавший источник не должен останавливать остальные: ночной прогон
    # иначе теряет всё, что стоит после него в списке. Ошибки копятся и
    # печатаются в конце, код возврата ненулевой — GitHub Actions покажет
    # прогон красным. Запись в базу для источника, не прошедшего проверку
    # полноты, не происходит: проверка стоит до неё.
    errors: list[str] = []
    programme_count = 0

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
                programme_count += _check_and_save(client, now, key, university, programmes)
            except CatalogCompletenessError as exc:
                errors.append(str(exc))
                print(f"ОШИБКА {exc}")
            except Exception as exc:  # noqa: BLE001
                # Сбой базы при записи этого вуза (после повторов в
                # db_retry.execute) или любая другая неожиданность. Раньше
                # такое исключение роняло весь прогон: вузы дальше по списку
                # не собирались, запись о прогоне оставалась «идёт».
                errors.append(f"{key}: запись в базу не удалась — {type(exc).__name__}: {exc}")
                print(f"ОШИБКА {errors[-1][:300]}")

        print(polite.report_and_reset())

    finished_at = datetime.now(timezone.utc).isoformat()
    note = "; ".join(error[:200] for error in errors[:5]) or None
    execute(
        client.table("pipeline_run")
        .update(
            {
                "finished_at": finished_at,
                "status": "failed" if errors else "success",
                "source_count": len(sources),
                "programme_count": programme_count,
                "error_count": len(errors),
                "note": note,
            }
        )
        .eq("id", run_id)
    )

    if errors:
        print(f"\nИтого сбоев: {len(errors)}")
        for error in errors:
            print(f" - {error[:300]}")
        sys.exit(1)


# Прогон идёт меньше часа; запись «идёт» старше этого — след прогона, который
# убили (таймаут GitHub Actions, закрытое окно терминала, выключенный
# компьютер) раньше, чем он успел записать итог.
STALE_RUN_HOURS = 6


def _close_stale_runs(client) -> None:  # type: ignore[no-untyped-def]
    """Пометить давно зависшие записи «идёт» как сбойные.

    Без этого pipeline_health показывал бы last_status='running' для прогона,
    которого давно нет. Свежие записи не трогаются: это может быть прогон,
    идущий прямо сейчас (расписание GitHub и локальный --local одновременно).
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=STALE_RUN_HOURS)).isoformat()
    closed = execute(
        client.table("pipeline_run")
        .update(
            {
                "status": "failed",
                "error_count": 1,
                "note": f"прогон прерван: итог не записан за {STALE_RUN_HOURS} ч (закрыто следующим прогоном)",
            }
        )
        .eq("status", "running")
        .lt("started_at", cutoff)
    ).data
    if closed:
        print(f"закрыто зависших записей о прогоне: {len(closed)}")


def _check_and_save(client, now: str, key: str, university, programmes) -> int:  # type: ignore[no-untyped-def]
    minimum = MIN_PROGRAMME_COUNT.get(key)
    if minimum is not None and len(programmes) < minimum:
        raise CatalogCompletenessError(
            f"{key}: нашёл {len(programmes)} программ, ожидал минимум {minimum}. "
            "Похоже на баг сборщика (например, тихо потерянный раздел сайта), а не на "
            "сокращение набора у вуза — проверьте вручную. Если сокращение подтвердится, "
            "поднимите порог в MIN_PROGRAMME_COUNT (main.py)."
        )

    # Название-адрес («www.rtu.lv») или пустое — признак, что сайт отдал
    # не карточку программы, а заглушку. Источник не записывается целиком:
    # прошлые данные лучше мусора (см. catalog_diff.suspicious_names).
    bad = suspicious_names([programme.model_dump(exclude_none=True) for programme in programmes])
    if bad:
        raise CatalogCompletenessError(
            f"{key}: у {len(bad)} программ вместо названия адрес сайта или пусто "
            f"({', '.join(bad[:5])}{' …' if len(bad) > 5 else ''}). Похоже, сайт отдал заглушку "
            "вместо страницы программы — источник не записан. Если сайт не отвечает серверу "
            "GitHub, добавьте источник в LOCAL_ONLY (scrape_scope.py)."
        )

    uni_row = university.model_dump(exclude_none=True)
    uni_row["extracted_at"] = now
    result = execute(client.table("university").upsert(uni_row, on_conflict="slug"))
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
        # План 2026-09-21, пункт 07: прежде чем перезаписать, сверяем с тем,
        # что было — апсерт сам по себе не трогает verified_at, но если
        # подтверждённое человеком поле изменилось, пометку надо снять, а
        # не молча оставить "Verified" висеть на уже неверных данных
        # (см. catalog_diff.py). Запрос перед апсертом, не после: изменение
        # должно попасть в ТУ ЖЕ запись, что мы вот-вот отправим.
        existing = execute(
            client.table("programme")
            .select("slug, verified_at, verified_by, " + ", ".join(CONTENT_FIELDS))
            .eq("university_id", university_id)
            .in_("slug", [row["slug"] for row in programme_rows])
        ).data
        existing_by_slug = {row["slug"]: row for row in existing}
        # Язык обучения сборщик мог не прочитать (страница не открылась,
        # значение не распознано) — тогда поля в строке нет. Догадку вместо
        # него не пишем: у программы из базы остаётся прежний язык, новая
        # программа без языка в этот раз не записывается.
        programme_rows, kept, dropped = drop_new_without(programme_rows, existing_by_slug, "language_of_instruction")
        if kept or dropped:
            print(
                f"  {university.slug}: язык обучения не прочитан у {len(kept) + len(dropped)} программ"
                + (f"; оставлен прежний — {', '.join(kept[:5])}{' …' if len(kept) > 5 else ''}" if kept else "")
                + (f"; новые НЕ ЗАПИСАНЫ — {', '.join(dropped[:5])}{' …' if len(dropped) > 5 else ''}" if dropped else "")
            )
        diff = compute_diff(existing_by_slug, programme_rows)  # мутирует programme_rows при сбросе
        if diff.has_changes:
            print(format_report(diff, university.slug))
        # Строки пачки должны иметь один набор ключей: недостающий ключ
        # PostgREST записал бы как NULL поверх значения в базе (см.
        # catalog_diff.fill_missing_keys). После compute_diff — чтобы
        # сравнение по-прежнему шло только по тому, что нашёл сборщик.
        fill_missing_keys(programme_rows, existing_by_slug)
    # Отдельная проверка, а не продолжение блока выше: после отсева новых
    # программ без языка строк могло не остаться вовсе.
    if programme_rows:
        execute(client.table("programme").upsert(programme_rows, on_conflict="university_id,slug"))

    missing = _count_missed(client, university_id, key, {row["slug"] for row in programme_rows})
    print(f"{key}: upserted 1 university, {len(programme_rows)} programmes" + _missed_note(missing))
    return len(programme_rows)


def _count_missed(client, university_id: str, key: str, seen_slugs: set[str]) -> list[dict]:  # type: ignore[no-untyped-def]
    """Программы этого источника, которых на сайте больше нет: +1 к счётчику
    пропусков. Вызывается только после прохождения проверки полноты и записи —
    сбойный прогон (сайт лёг, сборщик сломался) ничего не скрывает. Строки без
    source_key (записаны до миграции) считаются принадлежащими любому
    источнику вуза: это ровно те, что ни один источник не нашёл."""
    owned = execute(
        client.table("programme")
        .select("id,slug,name_lv,name_en,missed_runs")
        .eq("university_id", university_id)
        .or_(f"source_key.eq.{key},source_key.is.null")
    ).data
    missing = [row for row in owned if row["slug"] not in seen_slugs]
    for row in missing:
        # source_key здесь не трогаем: строка без отметки может принадлежать
        # другому источнику этого же вуза (лиепайские программы РТУ до первого
        # прогона rtu_liepaja), и чужой прогон не должен её присваивать
        # значение готовое (не «+1» на стороне базы) — повтор запроса счётчик не удвоит
        execute(client.table("programme").update({"missed_runs": row["missed_runs"] + 1}).eq("id", row["id"]))
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
