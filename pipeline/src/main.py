from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

from db import get_service_client
from sources import bsa, du, eka, ekra, jvlma, lbtu, lka, lma, lnaa, lu, lutera, niid_colleges, rai, rgsl, riseba, rnu, rsu, rtu_catalog, rtu_liepaja, sse_riga, tsi, turiba, venta, via

SOURCES = [turiba, riseba, rtu_liepaja, tsi, bsa, sse_riga, rgsl, lu, venta, lbtu, du, eka, rnu, rtu_catalog, via, rsu, lka, lma, jvlma, rai, lnaa, lutera, ekra, niid_colleges]

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
    "sources.bsa": 13,
    "sources.sse_riga": 1,
    "sources.rgsl": 4,
    "sources.lu": 166,
    "sources.venta": 13,
    "sources.lbtu": 9,
    "sources.du": 10,
    "sources.eka": 21,
    "sources.rnu": 8,
    "sources.rtu_catalog": 124,
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
}


class CatalogCompletenessError(RuntimeError):
    pass


def main() -> None:
    load_dotenv()
    client = get_service_client()
    now = datetime.now(timezone.utc).isoformat()

    # python src/main.py rsu lmu — прогнать только перечисленные источники
    # (по имени модуля); без аргументов — все. Так новый вуз добавляется,
    # не перескрапливая остальные четырнадцать.
    only = set(sys.argv[1:])
    sources = [s for s in SOURCES if not only or s.__name__.split(".")[-1] in only]

    for source in sources:
        # у большинства источников один вуз (scrape), у колледжей из NIID
        # — много сразу (scrape_all)
        results = source.scrape_all() if hasattr(source, "scrape_all") else [source.scrape()]

        # учреждение, у которого есть порог, но которого нет в результате
        # (колледж пропал целиком), — тоже сбой, а не "ноль программ"
        if hasattr(source, "scrape_all"):
            got = {f"{source.__name__}:{university.slug}" for university, _ in results}
            lost = [k for k in MIN_PROGRAMME_COUNT if k.startswith(f"{source.__name__}:") and k not in got]
            if lost:
                raise CatalogCompletenessError(f"{lost}: учреждение не вернуло ни одной программы — проверьте вручную.")

        for university, programmes in results:
            key = f"{source.__name__}:{university.slug}" if hasattr(source, "scrape_all") else source.__name__
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
                programme_rows.append(row)

            if programme_rows:
                client.table("programme").upsert(
                    programme_rows, on_conflict="university_id,slug"
                ).execute()

            print(f"{key}: upserted 1 university, {len(programme_rows)} programmes")


if __name__ == "__main__":
    main()
