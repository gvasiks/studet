from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

from db import get_service_client
from sources import bsa, du, eka, jvlma, lbtu, lka, lma, lu, rai, rgsl, riseba, rnu, rsu, rtu_catalog, rtu_liepaja, sse_riga, tsi, turiba, venta, via

SOURCES = [turiba, riseba, rtu_liepaja, tsi, bsa, sse_riga, rgsl, lu, venta, lbtu, du, eka, rnu, rtu_catalog, via, rsu, lka, lma, jvlma, rai]

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
    "sources.lu": 55,
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
        university, programmes = source.scrape()

        minimum = MIN_PROGRAMME_COUNT.get(source.__name__)
        if minimum is not None and len(programmes) < minimum:
            raise CatalogCompletenessError(
                f"{source.__name__}: нашёл {len(programmes)} программ, ожидал минимум {minimum}. "
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

        print(f"{source.__name__}: upserted 1 university, {len(programme_rows)} programmes")


if __name__ == "__main__":
    main()
